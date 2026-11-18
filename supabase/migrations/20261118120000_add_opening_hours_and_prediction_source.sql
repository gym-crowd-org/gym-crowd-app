-- Opening hours per gym (local time in gyms.timezone)
ALTER TABLE gyms
  ADD COLUMN opens_at  TIME NOT NULL DEFAULT '07:00',
  ADD COLUMN closes_at TIME NOT NULL DEFAULT '22:00',
  ADD CONSTRAINT gyms_opening_hours_check CHECK (opens_at < closes_at);

-- Where a prediction came from:
--   daily_batch: precomputed by the daily forecast job before the day starts
--   on_demand:   computed when a user asked /predict/forecast for a timestamp
ALTER TABLE crowd_predictions
  ADD COLUMN source TEXT NOT NULL DEFAULT 'on_demand'
    CHECK (source IN ('daily_batch', 'on_demand'));

-- Existing rows were all written by /predict/forecast, so 'on_demand' (the default) is correct.

ALTER TABLE crowd_predictions
  DROP CONSTRAINT crowd_predictions_gym_id_predicted_for_model_version_key;

ALTER TABLE crowd_predictions
  ADD CONSTRAINT crowd_predictions_gym_slot_version_source_key
    UNIQUE (gym_id, predicted_for, model_version, source);
