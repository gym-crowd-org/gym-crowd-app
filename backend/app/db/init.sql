CREATE TABLE gyms (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug          TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  capacity      INT  NOT NULL CHECK (capacity > 0),
  timezone      TEXT NOT NULL DEFAULT 'Asia/Singapore',
  is_active     BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE weather_forecasts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_key    TEXT NOT NULL,              -- e.g. 'sg-usc' or lat,lon hash
  forecast_at     TIMESTAMPTZ NOT NULL,
  temperature_2m  DOUBLE PRECISION NOT NULL,
  rain            DOUBLE PRECISION NOT NULL CHECK (rain >= 0),
  source          TEXT NOT NULL DEFAULT 'open-meteo',
  fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (location_key, forecast_at)
);

CREATE TABLE crowd_readings (             -- was crowd_actual
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id        UUID NOT NULL REFERENCES gyms(id),
  observed_at   TIMESTAMPTZ NOT NULL,
  occupancy     INT NOT NULL CHECK (occupancy >= 0),
  capacity      INT NOT NULL CHECK (capacity > 0),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gym_id, observed_at),
  CHECK (occupancy <= capacity)
);

CREATE TABLE crowd_predictions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id         UUID NOT NULL REFERENCES gyms(id),
  predicted_for  TIMESTAMPTZ NOT NULL,
  occupancy      INT NOT NULL CHECK (occupancy >= 0),
  capacity       INT NOT NULL CHECK (capacity > 0),
  model_version  TEXT NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gym_id, predicted_for, model_version),
  CHECK (occupancy <= capacity)
);

CREATE INDEX idx_crowd_readings_gym_time
  ON crowd_readings (gym_id, observed_at DESC);

CREATE INDEX idx_crowd_predictions_gym_time
  ON crowd_predictions (gym_id, predicted_for DESC);

CREATE INDEX idx_weather_forecasts_loc_time
  ON weather_forecasts (location_key, forecast_at DESC);