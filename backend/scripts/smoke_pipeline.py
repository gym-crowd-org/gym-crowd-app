from datetime import datetime

from app.api.services import get_gym_by_slug
from app.db.client import get_supabase
from app.ml.pipeline import predict_crowd

timestamp = datetime.now()
supabase = get_supabase()
gym_row = get_gym_by_slug(supabase, "usc-gym")
pred = predict_crowd(
    supabase, timestamp, gym_row["id"], gym_row["name"], gym_row["capacity"]
)
print(f"Predicted crowd for {timestamp}: {pred}")
