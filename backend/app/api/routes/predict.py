from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.api.schemas import PredictForecastOut, PredictionPointOut, PredictNowOut
from app.api.services import (
    forecast_predictions,
    get_gym_by_slug,
    nearest_prediction,
    occupancy_pct,
)
from app.cache.redis_client import cache_get, cache_set
from app.config import get_settings
from app.db.client import get_supabase

router = APIRouter(prefix="/predict", tags=["predict"])


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
    hours: int = Query(default=24, ge=1, le=48),
    supabase: Client = Depends(get_supabase),
) -> PredictForecastOut:
    settings = get_settings()
    slug = gym or settings.default_gym_slug

    gym_row = get_gym_by_slug(supabase, slug)
    rows = forecast_predictions(supabase, gym_row["id"], hours=hours)
    points = [
        PredictionPointOut(
            predicted_for=row["predicted_for"],
            occupancy=row["occupancy"],
            capacity=row["capacity"],
            occupancy_pct=occupancy_pct(row["occupancy"], row["capacity"]),
            model_version=row["model_version"],
        )
        for row in rows
    ]
    return PredictForecastOut(
        gym_slug=gym_row["slug"],
        gym_name=gym_row["name"],
        hours=hours,
        points=points,
    )
