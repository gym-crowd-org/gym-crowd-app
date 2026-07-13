from datetime import datetime

from app.ml.pipeline import predict_crowd
from app.ml.weather import get_weather_data

timestamp = datetime.now()
weather_df = get_weather_data(timestamp)
print(
    f"Predicted crowd for {timestamp}: {predict_crowd(timestamp, 'usc-gym', weather_df)}"
)
