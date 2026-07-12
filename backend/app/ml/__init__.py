"""ML inference helpers.

Predictions are precomputed by jobs and stored in `crowd_predictions`.
Live `joblib` inference can be added here later when `models/` has a trained artifact.
"""

from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "gym_crowd_model.joblib"


def model_available() -> bool:
    return MODEL_PATH.exists()


def predict_occupancy(*_args, **_kwargs) -> int:
    raise NotImplementedError(
        "Live model inference is not wired yet. "
        "Serve precomputed rows from crowd_predictions, or place gym_crowd_model.joblib in backend/models/."
    )
