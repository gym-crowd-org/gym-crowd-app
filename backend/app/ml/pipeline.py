import datetime
import json
import urllib.request

import joblib
import pandas as pd

gym_id_to_name = {"usc-gym": "University Town - Fitness gym"}
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
MODEL_PATH = f"{MODEL_DIR}/gym_crowd_model.joblib"


def prepare_features(
    timestamp: datetime, gym_id: str, weather_df: pd.DataFrame
) -> pd.DataFrame:
    df = pd.DataFrame(
        [{"timestamp": timestamp, "name": gym_id_to_name[gym_id], "capacity": 110}]
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

    weather = weather_df.copy()
    forecast_at = pd.to_datetime(weather["forecast_at"])
    if forecast_at.dt.tz is None:
        forecast_at = forecast_at.dt.tz_localize("Asia/Singapore")
    else:
        forecast_at = forecast_at.dt.tz_convert("Asia/Singapore")
    # weather["weather_hour"] = forecast_at.dt.floor("h")
    weather["weather_hour"] = df["hour"]
    weather = weather.drop(columns=["forecast_at"])
    return df.merge(weather, on="weather_hour", how="left")


def predict_crowd(timestamp: datetime, gym_id: str, weather_df: pd.DataFrame) -> int:
    pipeline = joblib.load(f"{MODEL_DIR}/gym_crowd_model.joblib")
    test_df = prepare_features(timestamp, gym_id, weather_df)
    predictions = pipeline.predict(test_df[FEATURE_COLS])
    test_df["predicted"] = predictions
    return test_df["predicted"].iloc[0]
