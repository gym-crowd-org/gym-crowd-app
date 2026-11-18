"""Daily forecast: predict every 30-min slot of one SGT day, before it starts.

Weather is fetched once from Open-Meteo, stored in weather_forecasts, and the
same rows feed every prediction, so we keep a record of what the forecast used.
Rows are written with source='daily_batch'; the insights chart reads only those.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from app.api.services import list_gyms, upsert_prediction
from app.ml.pipeline import MODEL_VERSION, load_model, predict_slots
from app.ml.weather import fetch_and_store_forecast

from supabase import Client

log = logging.getLogger(__name__)

SG_TZ = ZoneInfo("Asia/Singapore")
SLOT_MINUTES = 30


def day_slots(day: date, opens_at: time, closes_at: time) -> list[datetime]:
    """Slots from opening to closing inclusive, e.g. 07:00, 07:30, ..., 22:00."""
    start = datetime.combine(day, opens_at, tzinfo=SG_TZ)
    end = datetime.combine(day, closes_at, tzinfo=SG_TZ)
    slots = []
    t = start
    while t <= end:
        slots.append(t)
        t += timedelta(minutes=SLOT_MINUTES)
    return slots


def run_daily_forecast(supabase: Client, day: date) -> dict[str, int]:
    if not MODEL_VERSION:
        raise RuntimeError("MODEL_VERSION is not set")

    weather = pd.DataFrame(fetch_and_store_forecast(supabase, day, day))
    model = load_model()

    stats: dict[str, int] = {}
    for gym in list_gyms(supabase):
        slots = day_slots(
            day,
            time.fromisoformat(gym["opens_at"]),
            time.fromisoformat(gym["closes_at"]),
        )
        occupancies = predict_slots(model, gym["name"], gym["capacity"], slots, weather)
        upsert_prediction(
            supabase,
            [
                {
                    "gym_id": gym["id"],
                    "predicted_for": slot.isoformat(),
                    "occupancy": occ,
                    "capacity": gym["capacity"],
                    "model_version": MODEL_VERSION,
                    "source": "daily_batch",
                }
                for slot, occ in zip(slots, occupancies)
            ],
        )
        stats[gym["slug"]] = len(slots)

    log.info("forecast for %s done (model %s): %s", day, MODEL_VERSION, stats)
    return stats
