from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.api.schemas import HistoryOut, HistoryPointOut
from app.api.services import (
    get_gym_by_slug,
    history_predictions,
    history_readings,
    latest_reading,
    occupancy_pct,
)
from app.cache.redis_client import cache_get, cache_set
from app.config import get_settings
from app.db.client import get_supabase
from app.ml.pipeline import MODEL_VERSION

router = APIRouter(prefix="/history", tags=["history"])

SG_TZ = ZoneInfo("Asia/Singapore")
CACHE_TTL_SECONDS = 300


def _point(at: str, occupancy: int, capacity: int) -> HistoryPointOut:
    return HistoryPointOut(
        at=at,
        occupancy=occupancy,
        capacity=capacity,
        occupancy_pct=occupancy_pct(occupancy, capacity),
    )


@router.get("", response_model=HistoryOut)
def get_history(
    gym: str | None = Query(default=None, description="Gym slug, e.g. usc-gym"),
    day: date | None = Query(
        default=None, alias="date", description="SGT day (YYYY-MM-DD); default today"
    ),
    supabase: Client = Depends(get_supabase),
) -> HistoryOut:
    settings = get_settings()
    slug = gym or settings.default_gym_slug
    day = day or datetime.now(SG_TZ).date()

    cache_key = f"history:{slug}:{day.isoformat()}:{MODEL_VERSION}"
    cached = cache_get(cache_key)
    if cached is not None:
        return HistoryOut.model_validate(cached)

    gym_row = get_gym_by_slug(supabase, slug)
    opens = datetime.combine(day, time.fromisoformat(gym_row["opens_at"]), tzinfo=SG_TZ)
    closes = datetime.combine(day, time.fromisoformat(gym_row["closes_at"]), tzinfo=SG_TZ)

    readings = history_readings(supabase, gym_row["id"], opens, closes)
    preds = (
        history_predictions(supabase, gym_row["id"], opens, closes, MODEL_VERSION)
        if MODEL_VERSION
        else []
    )
    latest = latest_reading(supabase, gym_row["id"])

    payload = HistoryOut(
        gym_slug=gym_row["slug"],
        gym_name=gym_row["name"],
        date=day,
        opens_at=opens,
        closes_at=closes,
        capacity=gym_row["capacity"],
        model_version=MODEL_VERSION,
        last_reading_at=latest["observed_at"] if latest else None,
        actual=[_point(r["observed_at"], r["occupancy"], r["capacity"]) for r in readings],
        predicted=[_point(r["predicted_for"], r["occupancy"], r["capacity"]) for r in preds],
    )
    cache_set(cache_key, payload.model_dump(mode="json"), ttl_seconds=CACHE_TTL_SECONDS)
    return payload
