from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.api.schemas import HistoryOut, HistoryPointOut
from app.api.services import (
    get_gym_by_slug,
    history_predictions,
    history_readings,
)
from app.config import get_settings
from app.db.client import get_supabase

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryOut)
def get_history(
    gym: str | None = Query(default=None, description="Gym slug, e.g. usc-gym"),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    supabase: Client = Depends(get_supabase),
) -> HistoryOut:
    settings = get_settings()
    slug = gym or settings.default_gym_slug

    now = datetime.now(timezone.utc)
    end = to_ts or now
    start = from_ts or (end - timedelta(hours=24))

    gym_row = get_gym_by_slug(supabase, slug)
    readings = history_readings(supabase, gym_row["id"], start, end)
    preds = history_predictions(supabase, gym_row["id"], start, end)

    by_time: dict[str, HistoryPointOut] = {}

    for row in readings:
        key = row["observed_at"]
        by_time[key] = HistoryPointOut(
            at=row["observed_at"],
            actual=row["occupancy"],
            predicted=None,
            capacity=row["capacity"],
        )

    for row in preds:
        key = row["predicted_for"]
        existing = by_time.get(key)
        if existing is None:
            by_time[key] = HistoryPointOut(
                at=row["predicted_for"],
                actual=None,
                predicted=row["occupancy"],
                capacity=row["capacity"],
            )
        else:
            by_time[key] = existing.model_copy(update={"predicted": row["occupancy"]})

    points = sorted(by_time.values(), key=lambda p: p.at)
    return HistoryOut(
        gym_slug=gym_row["slug"],
        gym_name=gym_row["name"],
        from_ts=start,
        to_ts=end,
        points=points,
    )
