from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from app.api.schemas import WeatherForecastOut
from fastapi import HTTPException
from postgrest.exceptions import APIError

from supabase import Client

SG_TZ = ZoneInfo("Asia/Singapore")


def _as_singapore(value: datetime | str) -> datetime:
    """Interpret naive timestamps as Asia/Singapore; convert aware ones to SG."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=SG_TZ)
    return value.astimezone(SG_TZ)


def _run(query: Any) -> Any:
    try:
        return query.execute()
    except APIError as exc:
        code = (exc.code or "") if hasattr(exc, "code") else ""
        message = str(getattr(exc, "message", None) or exc)
        if code in {"42501", "PGRST301"} or "permission denied" in message.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase permission denied. Add SUPABASE_SERVICE_ROLE_KEY to backend/.env "
                    "or grant SELECT on public tables to anon."
                ),
            ) from exc
        raise HTTPException(
            status_code=502, detail=f"Supabase error: {message}"
        ) from exc


def get_gym_by_slug(supabase: Client, slug: str) -> dict[str, Any]:
    result = _run(
        supabase.table("gyms")
        .select("id, slug, name, capacity, timezone, is_active")
        .eq("slug", slug)
        .eq("is_active", True)
        .limit(1)
    )
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Gym not found: {slug}")
    return result.data[0]


def list_gyms(supabase: Client) -> list[dict[str, Any]]:
    result = _run(
        supabase.table("gyms")
        .select("id, slug, name, capacity, timezone, is_active")
        .eq("is_active", True)
        .order("name")
    )
    return result.data or []


def latest_reading(supabase: Client, gym_id: UUID | str) -> dict[str, Any] | None:
    result = _run(
        supabase.table("crowd_readings")
        .select("observed_at, occupancy, capacity")
        .eq("gym_id", str(gym_id))
        .order("observed_at", desc=True)
        .limit(1)
    )
    return result.data[0] if result.data else None


def delay(row: dict[str, Any], attribute: str, around: datetime) -> timedelta:
    return abs(_as_singapore(row[attribute]) - around)


def nearest_prediction(
    supabase: Client,
    gym_id: UUID | str,
    around: datetime | None = None,
    max_delay: timedelta = timedelta(minutes=10),
) -> dict[str, Any] | None:
    """Return the prediction closest to `around` (defaults to now), preferring future."""
    around = _as_singapore(around or datetime.now(SG_TZ))
    window_start = around - max_delay
    window_end = around + max_delay
    result = _run(
        supabase.table("crowd_predictions")
        .select("predicted_for, occupancy, capacity, model_version")
        .eq("gym_id", str(gym_id))
        .gte("predicted_for", window_start.isoformat())
        .lte("predicted_for", window_end.isoformat())
    )
    rows = result.data or []
    if not rows:
        return None

    return min(rows, key=lambda row: delay(row, "predicted_for", around))


def nearest_weather_forecast(
    supabase: Client,
    location_key: str,
    around: datetime | None = None,
    max_delay: timedelta = timedelta(minutes=30),
) -> WeatherForecastOut | None:
    """Return the weather forecast closest to `around` with |delay| <= max_delay.

    Both `around` and stored `forecast_at` are treated as Asia/Singapore.
    Naive datetimes are assumed to already be Singapore local time.
    """
    around = _as_singapore(around or datetime.now(SG_TZ))
    window_start = around - max_delay
    window_end = around + max_delay

    result = _run(
        supabase.table("weather_forecasts")
        .select("forecast_at, temperature_2m, rain, source, fetched_at, created_at")
        .eq("location_key", location_key)
        .gte("forecast_at", window_start.isoformat())
        .lte("forecast_at", window_end.isoformat())
    )
    rows = result.data or []
    if not rows:
        return None

    return min(rows, key=lambda row: delay(row, "forecast_at", around))


def forecast_predictions(
    supabase: Client,
    gym_id: UUID | str,
    hours: int,
    start: datetime | None = None,
) -> list[dict[str, Any]]:
    start = start or datetime.now(timezone.utc)
    end = start + timedelta(hours=hours)
    result = _run(
        supabase.table("crowd_predictions")
        .select("predicted_for, occupancy, capacity, model_version")
        .eq("gym_id", str(gym_id))
        .gte("predicted_for", start.isoformat())
        .lte("predicted_for", end.isoformat())
        .order("predicted_for", desc=False)
    )
    return result.data or []


def history_readings(
    supabase: Client,
    gym_id: UUID | str,
    from_ts: datetime,
    to_ts: datetime,
) -> list[dict[str, Any]]:
    result = _run(
        supabase.table("crowd_readings")
        .select("observed_at, occupancy, capacity")
        .eq("gym_id", str(gym_id))
        .gte("observed_at", from_ts.isoformat())
        .lte("observed_at", to_ts.isoformat())
        .order("observed_at", desc=False)
    )
    return result.data or []


def history_predictions(
    supabase: Client,
    gym_id: UUID | str,
    from_ts: datetime,
    to_ts: datetime,
) -> list[dict[str, Any]]:
    result = _run(
        supabase.table("crowd_predictions")
        .select("predicted_for, occupancy, capacity, model_version")
        .eq("gym_id", str(gym_id))
        .gte("predicted_for", from_ts.isoformat())
        .lte("predicted_for", to_ts.isoformat())
        .order("predicted_for", desc=False)
    )
    return result.data or []


def occupancy_pct(occupancy: int, capacity: int) -> float:
    if capacity <= 0:
        return 0.0
    return round(occupancy / capacity, 4)


def upsert_prediction(supabase: Client, rows: dict[str, Any]):
    _run(
        supabase.table("crowd_predictions").upsert(
            rows,
            on_conflict="gym_id,predicted_for,model_version",
        )
    )
