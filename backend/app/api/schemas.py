import datetime as dt
from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, Field


class GymOut(BaseModel):
    id: UUID
    slug: str
    name: str
    capacity: int
    timezone: str
    is_active: bool
    opens_at: time
    closes_at: time


class WeatherForecastCreate(BaseModel):
    location_key: str
    forecast_at: datetime
    temperature_2m: float
    rain: float = Field(ge=0)
    source: str = "open-meteo"
    fetched_at: datetime | None = None


class WeatherForecastOut(BaseModel):
    id: UUID
    location_key: str
    forecast_at: datetime
    temperature_2m: float
    rain: float
    source: str
    fetched_at: datetime
    created_at: datetime


class WeatherForecastListOut(BaseModel):
    location_key: str
    points: list[WeatherForecastOut]


class OccupancyLatestOut(BaseModel):
    gym_slug: str
    gym_name: str
    observed_at: datetime
    occupancy: int
    capacity: int
    occupancy_pct: float = Field(description="occupancy / capacity")


class PredictionPointOut(BaseModel):
    predicted_for: datetime
    occupancy: int
    capacity: int
    occupancy_pct: float
    model_version: str


class PredictNowOut(BaseModel):
    gym_slug: str
    gym_name: str
    predicted_for: datetime
    occupancy: int
    capacity: int
    occupancy_pct: float
    model_version: str


class PredictForecastOut(BaseModel):
    gym_slug: str
    gym_name: str
    timestamp: datetime
    occupancy: int
    capacity: int
    occupancy_pct: float
    model_version: str


class HistoryPointOut(BaseModel):
    at: datetime
    occupancy: int
    capacity: int
    occupancy_pct: float = Field(description="occupancy / capacity")


class HistoryOut(BaseModel):
    gym_slug: str
    gym_name: str
    date: dt.date = Field(description="Day in Asia/Singapore")
    opens_at: datetime
    closes_at: datetime
    capacity: int
    model_version: str | None
    last_reading_at: datetime | None = Field(
        description="Latest reading for this gym on any day (for staleness checks)"
    )
    actual: list[HistoryPointOut]
    predicted: list[HistoryPointOut] = Field(
        description="Daily-batch forecast for the current MODEL_VERSION"
    )
