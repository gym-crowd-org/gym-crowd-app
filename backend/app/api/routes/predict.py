from datetime import datetime
from zoneinfo import ZoneInfo

from app.api.schemas import PredictForecastOut, PredictNowOut
from app.api.services import get_gym_by_slug, nearest_prediction, occupancy_pct
from app.cache.redis_client import cache_get, cache_set
from app.config import get_settings
from app.db.client import get_supabase
from app.ml.pipeline import predict_crowd
from fastapi import APIRouter, Depends, HTTPException, Query

from supabase import Client

router = APIRouter(prefix="/predict", tags=["predict"])

SG_TZ = ZoneInfo("Asia/Singapore")


def _parse_timestamp_as_singapore(timestamp: str) -> datetime:
    try:
        ts = datetime.fromisoformat(timestamp)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp. Timestamp must be in ISO format (YYYY-MM-DDTHH:MM:SS.sss+00:00).",
        )
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=SG_TZ)
    return ts


@router.get("/now", response_model=PredictNowOut)
def get_predict_now(
    gym: str | None = Query(default=None, description="Gym slug, e.g. usc-gym"),
    supabase: Client = Depends(get_supabase),
) -> PredictNowOut:
    settings = get_settings()
    slug = gym or settings.default_gym_slug
    cache_key = f"predict:now:{slug}"

    cached = cache_get(cache_key)
    if cached is not None:
        return PredictNowOut.model_validate(cached)

    gym_row = get_gym_by_slug(supabase, slug)
    pred = nearest_prediction(supabase, gym_row["id"])
    if pred is None:
        raise HTTPException(status_code=404, detail=f"No predictions for {slug}")

    payload = PredictNowOut(
        gym_slug=gym_row["slug"],
        gym_name=gym_row["name"],
        predicted_for=pred["predicted_for"],
        occupancy=pred["occupancy"],
        capacity=pred["capacity"],
        occupancy_pct=occupancy_pct(pred["occupancy"], pred["capacity"]),
        model_version=pred["model_version"],
    )
    cache_set(cache_key, payload.model_dump(mode="json"))
    return payload


@router.get("/forecast", response_model=PredictForecastOut)
def get_predict_forecast(
    gym: str | None = Query(default=None, description="Gym slug, e.g. usc-gym"),
    timestamp: str | None = Query(default=None, description="Timestamp to predict"),
    supabase: Client = Depends(get_supabase),
) -> PredictForecastOut:
    settings = get_settings()
    slug = gym or settings.default_gym_slug
    gym_row = get_gym_by_slug(supabase, slug)

    # Parse timestamp to Singapore timezone
    if timestamp is not None:
        timestamp = _parse_timestamp_as_singapore(timestamp)
    else:
        raise HTTPException(
            status_code=400,
            detail="Timestamp is required. Timestamp must be in ISO format (YYYY-MM-DDTHH:MM:SS.sss+00:00).",
        )

    # Query predictions within 10 minutes of timestamp from DB
    pred = nearest_prediction(supabase, gym_row["id"], timestamp)
    if pred is None:
        # call the ML pipeline to predict the crowd
        pred = predict_crowd(supabase, timestamp, gym_row["id"], gym_row["name"])

    payload = PredictForecastOut(
        gym_slug=gym_row["slug"],
        gym_name=gym_row["name"],
        timestamp=timestamp,
        occupancy=pred["occupancy"],
        capacity=gym_row["capacity"],
        occupancy_pct=occupancy_pct(pred["occupancy"], gym_row["capacity"]),
        model_version=pred["model_version"],
    )
    return payload
