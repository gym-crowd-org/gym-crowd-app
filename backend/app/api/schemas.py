from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GymOut(BaseModel):
    id: UUID
    slug: str
    name: str
    capacity: int
    timezone: str
    is_active: bool


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
    actual: int | None = None
    predicted: int | None = None
    capacity: int


class HistoryOut(BaseModel):
    gym_slug: str
    gym_name: str
    from_ts: datetime
    to_ts: datetime
    points: list[HistoryPointOut]
