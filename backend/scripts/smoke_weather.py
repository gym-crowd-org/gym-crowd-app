from datetime import datetime

from app.ml.weather import get_weather_data

print(get_weather_data(datetime.now()))
