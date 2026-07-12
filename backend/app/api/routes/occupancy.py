from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.api.schemas import OccupancyLatestOut
from app.api.services import get_gym_by_slug, latest_reading, occupancy_pct
from app.cache.redis_client import cache_get, cache_set
from app.config import get_settings
from app.db.client import get_supabase

router = APIRouter(prefix="/occupancy", tags=["occupancy"])


@router.get("/latest", response_model=OccupancyLatestOut)
def get_occupancy_latest(
    gym: str | None = Query(default=None, description="Gym slug, e.g. usc-gym"),
    supabase: Client = Depends(get_supabase),
) -> OccupancyLatestOut:
    settings = get_settings()
    slug = gym or settings.default_gym_slug
    cache_key = f"occupancy:latest:{slug}"

    cached = cache_get(cache_key)
    if cached is not None:
        return OccupancyLatestOut.model_validate(cached)

    gym_row = get_gym_by_slug(supabase, slug)
    reading = latest_reading(supabase, gym_row["id"])
    if reading is None:
        raise HTTPException(status_code=404, detail=f"No occupancy readings for {slug}")

    payload = OccupancyLatestOut(
        gym_slug=gym_row["slug"],
        gym_name=gym_row["name"],
        observed_at=reading["observed_at"],
        occupancy=reading["occupancy"],
        capacity=reading["capacity"],
        occupancy_pct=occupancy_pct(reading["occupancy"], reading["capacity"]),
    )
    cache_set(cache_key, payload.model_dump(mode="json"), ttl_seconds=60)
    return payload
