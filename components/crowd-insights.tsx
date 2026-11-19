"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";
import { RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  REFRESH_MS,
  STALE_MS,
  apiUrl,
  buildRows,
  formatTime,
  hourlyTicks,
  nearest,
  splitSegments,
  toPoints,
  todayInSingapore,
  type Gym,
  type HistoryResponse,
  type Point,
} from "@/lib/crowd-history";
import { cn } from "@/lib/utils";

const chartConfig = {
  actual: { label: "Actual", color: "var(--chart-1)" },
  predicted: { label: "Predicted", color: "var(--chart-2)" },
} satisfies ChartConfig;

type SeriesKey = keyof typeof chartConfig;

function useNow(intervalMs: number) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

export default function CrowdInsights() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [gyms, setGyms] = useState<Gym[] | null>(null);
  const [gymsError, setGymsError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [hidden, setHidden] = useState<Record<SeriesKey, boolean>>({
    actual: false,
    predicted: false,
  });
  const now = useNow(30 * 1000);

  const requestedSlug = searchParams.get("gym");
  const gym =
    gyms?.find((g) => g.slug === requestedSlug) ??
    gyms?.find((g) => g.slug === "usc-gym") ??
    gyms?.[0] ??
    null;
  const date = todayInSingapore(new Date(now));

  useEffect(() => {
    fetch(apiUrl("/gyms"))
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then(setGyms)
      .catch((e) => setGymsError(String(e.message ?? e)));
  }, []);

  const loadHistory = useCallback(async (slug: string, day: string) => {
    setLoading(true);
    try {
      const r = await fetch(apiUrl("/history", { gym: slug, date: day }));
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      setHistory(await r.json());
      setHistoryError(null);
      setFetchedAt(Date.now());
    } catch (e) {
      setHistoryError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  // Load on gym/day change, then poll. `date` changes at SGT midnight.
  useEffect(() => {
    if (!gym) return;
    loadHistory(gym.slug, date);
    const id = setInterval(() => loadHistory(gym.slug, date), REFRESH_MS);
    return () => clearInterval(id);
  }, [gym, date, loadHistory]);

  const selectGym = (slug: string | null) => {
    if (!slug) return;
    setHistory(null);
    const params = new URLSearchParams(searchParams.toString());
    params.set("gym", slug);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const view = useMemo(() => {
    if (!history || history.gym_slug !== gym?.slug) return null;
    const actual = toPoints(history.actual);
    const predicted = toPoints(history.predicted);
    const segments = splitSegments(actual);
    const start = new Date(history.opens_at).getTime();
    const end = new Date(history.closes_at).getTime();
    const lastReading = history.last_reading_at
      ? new Date(history.last_reading_at).getTime()
      : null;
    return {
      actual,
      predicted,
      segments,
      rows: buildRows(segments, predicted),
      start,
      end,
      lastReading,
      latest: actual[actual.length - 1] ?? null,
    };
  }, [history, gym?.slug]);

  if (gymsError) {
    return <ErrorCard message={`Couldn't load gyms: ${gymsError}`} />;
  }

  const phase = view
    ? now < view.start
      ? "before"
      : now > view.end
        ? "after"
        : "open"
    : null;
  const delayed =
    phase === "open" && view && (!view.lastReading || now - view.lastReading > STALE_MS);
  const forecastNow = view && phase === "open" ? nearest(view.predicted, now, 15 * 60 * 1000) : null;

  return (
    <Card className="w-full">
      <CardHeader className="gap-4 sm:flex sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5">
          <CardTitle className="text-xl">{gym?.name ?? "Loading gyms…"}</CardTitle>
          <CardDescription>
            Today ({date}) ·{" "}
            {gym ? `${gym.opens_at.slice(0, 5)}–${gym.closes_at.slice(0, 5)}` : "—"} · % of
            capacity
          </CardDescription>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {phase === "before" && <Badge variant="secondary">Opens at {gym?.opens_at.slice(0, 5)}</Badge>}
            {phase === "after" && <Badge variant="secondary">Closed</Badge>}
            {delayed && <Badge variant="destructive">Data delayed</Badge>}
            {view && view.predicted.length === 0 && (
              <Badge variant="outline">No forecast for today</Badge>
            )}
          </div>
        </div>

        <Select
          value={gym?.slug ?? null}
          onValueChange={selectGym}
          items={(gyms ?? []).map((g) => ({ value: g.slug, label: g.name }))}
        >
          <SelectTrigger className="w-full sm:w-72" aria-label="Select gym">
            <SelectValue placeholder="Select a gym" />
          </SelectTrigger>
          <SelectContent>
            {(gyms ?? []).map((g) => (
              <SelectItem key={g.slug} value={g.slug}>
                {g.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardHeader>

      <CardContent className="space-y-4">
        {view && (
          <div className="grid grid-cols-2 gap-3 sm:max-w-md">
            <Stat
              label="Latest reading"
              value={view.latest ? `${Math.round(view.latest.pct)}%` : "—"}
              detail={
                view.latest
                  ? `${view.latest.occupancy}/${view.latest.capacity} at ${formatTime(view.latest.t)}`
                  : "No readings yet today"
              }
              color="var(--chart-1)"
            />
            <Stat
              label="Forecast now"
              value={forecastNow ? `${Math.round(forecastNow.pct)}%` : "—"}
              detail={
                forecastNow
                  ? `${forecastNow.occupancy}/${forecastNow.capacity} at ${formatTime(forecastNow.t)}`
                  : phase === "open"
                    ? "No forecast for this slot"
                    : "Outside opening hours"
              }
              color="var(--chart-2)"
            />
          </div>
        )}

        <div className="flex items-center gap-2">
          {(Object.keys(chartConfig) as SeriesKey[]).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setHidden((h) => ({ ...h, [key]: !h[key] }))}
              aria-pressed={!hidden[key]}
              className={cn(
                "flex items-center gap-2 rounded-md border px-2.5 py-1 text-sm transition-opacity",
                hidden[key] && "opacity-40",
              )}
            >
              <span
                className={cn("h-0.5 w-4", key === "predicted" && "border-t-2 border-dashed bg-transparent")}
                style={
                  key === "predicted"
                    ? { borderColor: chartConfig[key].color }
                    : { backgroundColor: chartConfig[key].color, height: 2 }
                }
              />
              {chartConfig[key].label}
            </button>
          ))}
        </div>

        {historyError && !view ? (
          <ErrorCard message={`Couldn't load crowd data: ${historyError}`} />
        ) : !view ? (
          <div className="h-[340px] animate-pulse rounded-lg bg-muted" />
        ) : (
          <ChartContainer config={chartConfig} className="aspect-auto h-[340px] w-full">
            <LineChart data={view.rows} margin={{ top: 16, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="t"
                type="number"
                scale="time"
                domain={[view.start, view.end]}
                ticks={hourlyTicks(view.start, view.end)}
                tickFormatter={formatTime}
                tickLine={false}
                axisLine={false}
                minTickGap={16}
              />
              <YAxis
                domain={[0, 100]}
                ticks={[0, 25, 50, 75, 100]}
                tickFormatter={(v) => `${v}%`}
                tickLine={false}
                axisLine={false}
                width={44}
              />
              <ChartTooltip
                cursor={{ strokeDasharray: "3 3" }}
                content={({ active, label }) =>
                  active && typeof label === "number" ? (
                    <TooltipCard t={label} actual={view.actual} predicted={view.predicted} hidden={hidden} />
                  ) : null
                }
              />
              {phase === "open" && (
                <ReferenceLine
                  x={now}
                  stroke="var(--muted-foreground)"
                  strokeDasharray="4 4"
                  label={{ value: "Now", position: "top", fill: "var(--muted-foreground)", fontSize: 12 }}
                />
              )}
              <Line
                dataKey="predicted"
                name="Predicted"
                type="monotone"
                stroke="var(--color-predicted)"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
                connectNulls
                hide={hidden.predicted}
                isAnimationActive={false}
              />
              {view.segments.map((seg, i) => (
                <Line
                  key={`a${i}`}
                  dataKey={`a${i}`}
                  name="Actual"
                  type="linear"
                  stroke="var(--color-actual)"
                  strokeWidth={2.5}
                  dot={seg.length === 1 ? { r: 3, fill: "var(--color-actual)" } : false}
                  activeDot={{ r: 4 }}
                  connectNulls
                  hide={hidden.actual}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ChartContainer>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>
            Readings every 15 min · Forecast made before opening
            {history?.model_version ? ` · model ${history.model_version}` : ""}
          </span>
          <span className="flex items-center gap-1.5">
            {historyError && view && <span className="text-destructive">Refresh failed · </span>}
            {fetchedAt ? `Updated ${minutesAgo(now, fetchedAt)}` : ""}
            <button
              type="button"
              onClick={() => gym && loadHistory(gym.slug, date)}
              disabled={!gym || loading}
              aria-label="Refresh now"
              className="rounded p-1 hover:bg-muted disabled:opacity-50"
            >
              <RefreshCw className={cn("size-3.5", loading && "animate-spin")} />
            </button>
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function minutesAgo(now: number, t: number) {
  const m = Math.floor((now - t) / 60000);
  return m <= 0 ? "just now" : `${m} min ago`;
}

function Stat({
  label,
  value,
  detail,
  color,
}: {
  label: string;
  value: string;
  detail: string;
  color: string;
}) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="size-2 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-muted-foreground tabular-nums">{detail}</div>
    </div>
  );
}

function TooltipCard({
  t,
  actual,
  predicted,
  hidden,
}: {
  t: number;
  actual: Point[];
  predicted: Point[];
  hidden: Record<SeriesKey, boolean>;
}) {
  const a = hidden.actual ? null : nearest(actual, t, 45 * 60 * 1000);
  const p = hidden.predicted ? null : nearest(predicted, t, 15 * 60 * 1000);
  if (!a && !p) return null;
  return (
    <div className="grid min-w-44 gap-1.5 rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="font-medium">{formatTime(t)}</div>
      {a && (
        <Row color="var(--chart-1)" label={`Actual (${formatTime(a.t)})`} point={a} />
      )}
      {p && (
        <Row color="var(--chart-2)" label={`Predicted (${formatTime(p.t)})`} point={p} />
      )}
    </div>
  );
}

function Row({ color, label, point }: { color: string; label: string; point: Point }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <span className="size-2 rounded-[2px]" style={{ backgroundColor: color }} />
        {label}
      </span>
      <span className="font-mono font-medium tabular-nums">
        {Math.round(point.pct)}% · {point.occupancy}/{point.capacity}
      </span>
    </div>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
      {message}
    </div>
  );
}
