import json
import urllib.request

import pandas as pd

weather_url = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude=1.3667&longitude=103.8"
    f"&start_date={start_date}&end_date={end_date}"
    "&hourly=temperature_2m,rain&timezone=Asia%2FSingapore"
)
with urllib.request.urlopen(weather_url) as response:
    weather_data = json.load(response)
    weather_df = pd.DataFrame(weather_data["hourly"])
