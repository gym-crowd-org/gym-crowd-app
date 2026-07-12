from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from postgrest.exceptions import APIError

from supabase import Client


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


def nearest_prediction(
    supabase: Client,
    gym_id: UUID | str,
    around: datetime | None = None,
) -> dict[str, Any] | None:
    """Return the prediction closest to `around` (defaults to now), preferring future."""
    around = around or datetime.now(timezone.utc)
    upcoming = _run(
        supabase.table("crowd_predictions")
        .select("predicted_for, occupancy, capacity, model_version")
        .eq("gym_id", str(gym_id))
        .gte("predicted_for", around.isoformat())
        .order("predicted_for", desc=False)
        .limit(1)
    )
    if upcoming.data:
        return upcoming.data[0]

    past = _run(
        supabase.table("crowd_predictions")
        .select("predicted_for, occupancy, capacity, model_version")
        .eq("gym_id", str(gym_id))
        .lt("predicted_for", around.isoformat())
        .order("predicted_for", desc=True)
        .limit(1)
    )
    return past.data[0] if past.data else None


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
