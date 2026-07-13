from datetime import datetime

from app.db.client import get_supabase
from app.ml.weather import get_weather_data

from supabase import Client

supabase: Client = get_supabase()
print(get_weather_data(datetime.now(), supabase))
