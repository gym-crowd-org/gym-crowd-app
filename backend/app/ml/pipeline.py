import datetime
import os

import joblib
import pandas as pd
from app.api.services import upsert_prediction
from app.ml.weather import get_weather_data

from supabase import Client

FEATURE_COLS = [
    "name",
    "hour",
    "day_of_week",
    "is_weekend",
    "capacity",
    "temperature_2m",
    "rain",
]
TARGET_COL = "current"
MODEL_DIR = "models"
MODEL_VERSION = os.getenv("MODEL_VERSION")
MODEL_PATH = f"{MODEL_DIR}/gym_crowd_model_{MODEL_VERSION}.joblib"


def prepare_features(
    supabase: Client,
    timestamp: datetime,
    gym_id: str,
    gym_name: str,
    gym_capacity: int,
) -> pd.DataFrame:
    df = pd.DataFrame(
        [{"timestamp": timestamp, "name": gym_name, "capacity": gym_capacity}]
    )
    ts = pd.to_datetime(df["timestamp"])
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("Asia/Singapore")
    else:
        ts = ts.dt.tz_convert("Asia/Singapore")
    df["timestamp"] = ts
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["weather_hour"] = df["timestamp"].dt.floor("h")

    weather = get_weather_data(timestamp, supabase)
    forecast_at = pd.to_datetime(weather["forecast_at"])
    if forecast_at.dt.tz is None:
        forecast_at = forecast_at.dt.tz_localize("Asia/Singapore")
    else:
        forecast_at = forecast_at.dt.tz_convert("Asia/Singapore")
    # weather["weather_hour"] = forecast_at.dt.floor("h")
    weather["weather_hour"] = df["weather_hour"]
    weather = weather.drop(columns=["forecast_at"])
    return df.merge(weather, on="weather_hour", how="left")


def clamp_occupancy(value: float, capacity: int) -> int:
    """Round a raw model output into the DB's allowed range [0, capacity]."""
    return max(0, min(capacity, int(round(float(value)))))


def load_model():
    return joblib.load(MODEL_PATH)


def predict_slots(
    model,
    gym_name: str,
    gym_capacity: int,
    slots: list[datetime.datetime],
    weather: pd.DataFrame,
) -> list[int]:
    """Predict occupancy for many timestamps of one gym in a single model call.

    `weather` has columns forecast_at (tz-aware, hourly), temperature_2m, rain.
    Each slot uses the weather of its floored hour, as in training.
    """
    df = pd.DataFrame({"timestamp": pd.to_datetime(slots)})
    df["timestamp"] = df["timestamp"].dt.tz_convert("Asia/Singapore")
    df["name"] = gym_name
    df["capacity"] = gym_capacity
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["weather_hour"] = df["timestamp"].dt.floor("h")

    w = weather.copy()
    w["weather_hour"] = pd.to_datetime(w["forecast_at"]).dt.tz_convert(
        "Asia/Singapore"
    )
    df = df.merge(w[["weather_hour", "temperature_2m", "rain"]], on="weather_hour", how="left")
    missing = df["temperature_2m"].isna() | df["rain"].isna()
    if missing.any():
        raise ValueError(
            f"Missing weather for slots: {df.loc[missing, 'timestamp'].tolist()}"
        )

    predictions = model.predict(df[FEATURE_COLS])
    return [clamp_occupancy(p, gym_capacity) for p in predictions]


def predict_crowd(
    supabase: Client,
    timestamp: datetime,
    gym_id: str,
    gym_name: str,
    gym_capacity: int,
) -> dict:
    pipeline = joblib.load(MODEL_PATH)
    test_df = prepare_features(
        supabase, timestamp, gym_id, gym_name, gym_capacity
    )
    predictions = pipeline.predict(test_df[FEATURE_COLS])
    occupancy = clamp_occupancy(predictions[0], gym_capacity)

    rows = [
        {
            "gym_id": gym_id,
            "predicted_for": timestamp.isoformat(),
            "occupancy": occupancy,
            "capacity": gym_capacity,
            "model_version": MODEL_VERSION,
            "source": "on_demand",
        }
    ]

    upsert_prediction(supabase, rows)

    return {"occupancy": occupancy, "model_version": MODEL_VERSION}
