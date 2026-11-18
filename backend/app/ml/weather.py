from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import openmeteo_requests
import pandas as pd
import requests_cache
from app.api.schemas import WeatherForecastOut
from app.api.services import nearest_weather_forecast
from retry_requests import retry

from supabase import Client

LOCATION_KEY = "nus-singapore"
LATITUDE = 1.3667
LONGITUDE = 103.8
SG_TZ = ZoneInfo("Asia/Singapore")


def get_weather_data(timestamp: datetime, supabase: Client) -> pd.DataFrame:
    """Get weather data from supabase or open-meteo."""

    weather_data: WeatherForecastOut | None = nearest_weather_forecast(
        supabase, LOCATION_KEY, timestamp
    )
    if weather_data is None:
        # fallback to open-meteo
        start_date = timestamp.date()
        fetch_and_store_forecast(supabase, start_date, start_date + timedelta(days=1))

        weather_data = nearest_weather_forecast(supabase, LOCATION_KEY, timestamp)
        if weather_data is None:
            raise ValueError("No weather data found")

    return pd.DataFrame([dict(weather_data)])


def fetch_and_store_forecast(
    supabase: Client, start_date: date, end_date: date
) -> list[dict]:
    """Fetch the hourly Open-Meteo forecast for [start_date, end_date] (SGT) and
    upsert it into weather_forecasts. Returns the stored rows."""
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # The order of variables in hourly is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ["temperature_2m", "rain"],
        "timezone": "Asia/Singapore",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    # weather_api returns a list of location responses
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()

    forecast_at = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    ).tz_convert(response.Timezone().decode())

    fetched_at = datetime.now(SG_TZ).isoformat()
    rows = [
        {
            "location_key": LOCATION_KEY,
            "forecast_at": ts.isoformat(),
            "temperature_2m": float(temp),
            "rain": max(float(rain), 0.0),
            "source": "open-meteo",
            "fetched_at": fetched_at,
        }
        for ts, temp, rain in zip(forecast_at, hourly_temperature_2m, hourly_rain)
    ]

    supabase.table("weather_forecasts").upsert(
        rows,
        on_conflict="location_key,forecast_at",
    ).execute()
    return rows
