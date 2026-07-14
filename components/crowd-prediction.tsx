"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { Button } from "@base-ui/react/button";

interface CrowdPredictionProps {
  gymName: string;
  disablePredict?: boolean;
}

interface CrowdLevelResponse {
  gym_slug: string;
  gym_name: string;
  timestamp: string;
  occupancy: number;
  capacity: number;
  occupancy_pct: number;
  model_version: string;
}

interface CrowdLevel {
  gymSlug: string;
  gymName: string;
  timestamp: string;
  occupancy: number;
  capacity: number;
  occupancyPercentage: number;
  modelVersion: string;
}

const LEVELS = {
  Low: { level: "Low", threshold: 20, color: "bg-green-500" },
  Medium: { level: "Medium", threshold: 55, color: "bg-yellow-500" },
  High: { level: "High", threshold: 85, color: "bg-red-500" },
} as const;

const SG_TIMEZONE = "Asia/Singapore";

function getSingaporeDateTime() {
  const now = new Date();
  const date = now.toLocaleDateString("en-CA", { timeZone: SG_TIMEZONE });
  const timeStr = now.toLocaleTimeString("en-GB", {
    timeZone: SG_TIMEZONE,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const [hourStr, minuteStr] = timeStr.split(":");
  const hour = parseInt(hourStr, 10);
  const minute = Math.floor(parseInt(minuteStr, 10) / 15) * 15;
  const time = `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;

  return { date, time };
}

function getLevelFromPercentage(percentage: number) {
  if (percentage <= LEVELS.Low.threshold) return LEVELS.Low;
  if (percentage <= LEVELS.Medium.threshold) return LEVELS.Medium;
  return LEVELS.High;
}

export default function CrowdPrediction({
  gymName,
  disablePredict,
}: CrowdPredictionProps) {
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [crowdData, setCrowdData] = useState<CrowdLevel | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const { date, time } = getSingaporeDateTime();
    setSelectedDate(date);
    setSelectedTime(time);
  }, []);

  const generateTimeOptions = () => {
    const times = [];
    for (let hour = 0; hour <= 22; hour++) {
      for (let minute = 0; minute < 60; minute += 15) {
        times.push(
          `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`,
        );
      }
    }
    return times;
  };

  const timeOptions = generateTimeOptions();

  const getCrowdLevel = async (time: string): Promise<CrowdLevel> => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL;
    const params = new URLSearchParams({ timestamp: time });
    const response = await fetch(
      `${baseUrl}/api/predict/forecast?${params.toString()}`,
    );

    if (!response.ok) {
      throw new Error(
        `Failed to fetch crowd prediction: ${response.status} ${response.statusText}`,
      );
    }

    const data: CrowdLevelResponse = await response.json();
    return {
      gymSlug: data.gym_slug,
      gymName: data.gym_name,
      timestamp: data.timestamp,
      occupancy: data.occupancy,
      capacity: data.capacity,
      occupancyPercentage: data.occupancy_pct,
      modelVersion: data.model_version,
    };
  };

  const handlePredict = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const isoString = `${selectedDate}T${selectedTime}:00`;
      const data = await getCrowdLevel(isoString);
      setCrowdData(data);
    } catch (err) {
      setCrowdData(null);
      setError(
        err instanceof Error ? err.message : "Failed to fetch crowd prediction",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const occupancyPercentage = crowdData
    ? Math.round(crowdData.occupancyPercentage * 100)
    : 0;
  const levelInfo = crowdData
    ? getLevelFromPercentage(occupancyPercentage)
    : null;

  return (
    <div className="flex flex-col gap-6 rounded-2xl border-2 border-border bg-card p-8 shadow-lg transition-transform hover:shadow-xl">
      <h2 className="text-center text-2xl font-bold text-primary">{gymName}</h2>

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-foreground">Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-lg border border-border bg-background px-4 py-2 text-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-foreground">Time</label>
          <div className="relative">
            <select
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              className="w-full appearance-none rounded-lg border border-border bg-background px-4 py-2 pr-10 text-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {timeOptions.map((time) => (
                <option key={time} value={time}>
                  {time}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>
      </div>

      {isLoading && (
        <p className="text-center text-sm text-muted-foreground">
          Prediction in progress
          <span className="inline-flex w-5">
            <span className="animate-[pulse_1.4s_ease-in-out_infinite]">.</span>
            <span className="animate-[pulse_1.4s_ease-in-out_0.2s_infinite]">
              .
            </span>
            <span className="animate-[pulse_1.4s_ease-in-out_0.4s_infinite]">
              .
            </span>
          </span>
        </p>
      )}

      {error && <p className="text-center text-sm text-red-500">{error}</p>}

      {crowdData && levelInfo && !isLoading && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">
              Predicted Crowd Level
            </span>
            <span className="rounded-full bg-secondary px-3 py-1 text-sm font-bold text-secondary-foreground">
              {levelInfo.level}
            </span>
          </div>

          <div className="w-full gap-2">
            <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full ${levelInfo.color} transition-all duration-300`}
                style={{ width: `${Math.min(occupancyPercentage, 100)}%` }}
              />
            </div>
            <p className="text-right text-xs text-muted-foreground">
              {occupancyPercentage}% capacity
            </p>
          </div>
        </div>
      )}

      <div className="rounded-lg bg-secondary/10 p-4">
        <p className="text-center text-sm text-foreground">
          {selectedDate} at {selectedTime}
          {crowdData && (
            <>
              {" · "}
              {crowdData.occupancy}/{crowdData.capacity}
            </>
          )}
        </p>
      </div>

      <Button
        type="button"
        onClick={handlePredict}
        disabled={isLoading || disablePredict}
        className="w-full rounded-lg bg-primary px-4 py-3 font-bold text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Predict Crowd Level
      </Button>
    </div>
  );
}
