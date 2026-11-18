export const SG_TIMEZONE = "Asia/Singapore";
export const REFRESH_MS = 5 * 60 * 1000;
export const GAP_BREAK_MS = 90 * 60 * 1000;
export const STALE_MS = 2 * 60 * 60 * 1000;

export interface Gym {
  id: string;
  slug: string;
  name: string;
  capacity: number;
  opens_at: string;
  closes_at: string;
}

export interface HistoryPoint {
  at: string;
  occupancy: number;
  capacity: number;
  occupancy_pct: number;
}

export interface HistoryResponse {
  gym_slug: string;
  gym_name: string;
  date: string;
  opens_at: string;
  closes_at: string;
  capacity: number;
  model_version: string | null;
  last_reading_at: string | null;
  actual: HistoryPoint[];
  predicted: HistoryPoint[];
}

export interface Point {
  t: number;
  pct: number;
  occupancy: number;
  capacity: number;
}

export function apiUrl(path: string, params?: Record<string, string>) {
  const qs = params ? `?${new URLSearchParams(params).toString()}` : "";
  return `${process.env.NEXT_PUBLIC_API_URL}/api${path}${qs}`;
}

export function todayInSingapore(now = new Date()) {
  return now.toLocaleDateString("en-CA", { timeZone: SG_TIMEZONE });
}

export function formatTime(t: number | string) {
  return new Date(t).toLocaleTimeString("en-GB", {
    timeZone: SG_TIMEZONE,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function toPoints(rows: HistoryPoint[]): Point[] {
  return rows
    .map((r) => ({
      t: new Date(r.at).getTime(),
      pct: Math.round(r.occupancy_pct * 1000) / 10,
      occupancy: r.occupancy,
      capacity: r.capacity,
    }))
    .sort((a, b) => a.t - b.t);
}

/** Split readings into runs with no gap longer than GAP_BREAK_MS. */
export function splitSegments(points: Point[]): Point[][] {
  const segments: Point[][] = [];
  for (const p of points) {
    const current = segments[segments.length - 1];
    if (current && p.t - current[current.length - 1].t <= GAP_BREAK_MS) {
      current.push(p);
    } else {
      segments.push([p]);
    }
  }
  return segments;
}

/**
 * One row per timestamp for Recharts. Actual segment i lives under key `a${i}`
 * so each segment connects its own points but never bridges a gap.
 */
export function buildRows(actualSegments: Point[][], predicted: Point[]) {
  const rows = new Map<number, Record<string, number>>();
  const row = (t: number) => {
    let r = rows.get(t);
    if (!r) {
      r = { t };
      rows.set(t, r);
    }
    return r;
  };
  actualSegments.forEach((seg, i) => seg.forEach((p) => (row(p.t)[`a${i}`] = p.pct)));
  predicted.forEach((p) => (row(p.t).predicted = p.pct));
  return [...rows.values()].sort((a, b) => a.t - b.t);
}

export function nearest(points: Point[], t: number, withinMs: number) {
  let best: Point | null = null;
  for (const p of points) {
    if (Math.abs(p.t - t) <= withinMs && (!best || Math.abs(p.t - t) < Math.abs(best.t - t))) {
      best = p;
    }
  }
  return best;
}

export function hourlyTicks(start: number, end: number) {
  const ticks: number[] = [];
  for (let t = start; t <= end; t += 60 * 60 * 1000) ticks.push(t);
  return ticks;
}
