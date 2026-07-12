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
    hours: int
    points: list[PredictionPointOut]


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
