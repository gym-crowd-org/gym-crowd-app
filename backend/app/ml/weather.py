from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import openmeteo_requests
import pandas as pd
import requests_cache
from app.api.schemas import WeatherForecastOut
from app.api.services import nearest_weather_forecast
from app.db.client import get_supabase
from retry_requests import retry

supabase = get_supabase()
LOCATION_KEY = "nus-singapore"
LATITUDE = 1.3667
LONGITUDE = 103.8
SG_TZ = ZoneInfo("Asia/Singapore")


def get_weather_data(
    timestamp: datetime,
) -> pd.DataFrame:
    """Get weather data from supabase or open-meteo."""

    weather_data: WeatherForecastOut | None = nearest_weather_forecast(
        supabase, LOCATION_KEY, timestamp
    )
    if weather_data is None:
        # fallback to open-meteo
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        start_date = timestamp.date().isoformat()
        end_date = (timestamp.date() + timedelta(days=1)).isoformat()
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "hourly": ["temperature_2m", "rain"],
            "timezone": "Asia/Singapore",
            "start_date": start_date,
            "end_date": end_date,
        }
        # weather_api returns a list of location responses
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_rain = hourly.Variables(1).ValuesAsNumpy()

        hourly_data = {
            "forecast_at": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            ).tz_convert(response.Timezone().decode())
        }
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["rain"] = hourly_rain

        df = pd.DataFrame(hourly_data)
        fetched_at = datetime.now(SG_TZ).isoformat()
        rows = [
            {
                "location_key": LOCATION_KEY,
                "forecast_at": ts.isoformat(),
                "temperature_2m": float(temp),
                "rain": float(rain),
                "source": "open-meteo",
                "fetched_at": fetched_at,
            }
            for ts, temp, rain in zip(
                df["forecast_at"], df["temperature_2m"], df["rain"]
            )
        ]

        supabase.table("weather_forecasts").upsert(
            rows,
            on_conflict="location_key,forecast_at",
        ).execute()

        weather_data = nearest_weather_forecast(supabase, LOCATION_KEY, timestamp)
        if weather_data is None:
            raise ValueError("No weather data found")

    return pd.DataFrame([dict(weather_data)])
