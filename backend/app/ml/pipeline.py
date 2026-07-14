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
CAPACITY = 110


def prepare_features(
    supabase: Client, timestamp: datetime, gym_id: str, gym_name: str
) -> pd.DataFrame:
    df = pd.DataFrame(
        [{"timestamp": timestamp, "name": gym_name, "capacity": CAPACITY}]
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


def predict_crowd(
    supabase: Client, timestamp: datetime, gym_id: str, gym_name: str
) -> dict:
    pipeline = joblib.load(MODEL_PATH)
    test_df = prepare_features(supabase, timestamp, gym_id, gym_name)
    predictions = pipeline.predict(test_df[FEATURE_COLS])
    occupancy = int(round(float(predictions[0])))

    rows = [
        {
            "gym_id": gym_id,
            "predicted_for": timestamp.isoformat(),
            "occupancy": occupancy,
            "capacity": CAPACITY,
            "model_version": MODEL_VERSION,
        }
    ]

    upsert_prediction(supabase, rows)

    return {"occupancy": occupancy, "model_version": MODEL_VERSION}
