from datetime import datetime
import requests
import json

# Set today's date in the correct format

today = datetime.now().strftime("%Y-%m-%d")
url = "https://balldontlie.io/api/v1/games"
params = {"dates[]": today}

print(f"Fetching NBA games for today: {today}")
r = requests.get(url, params=params)

print(f"Status Code: {r.status_code}")

try:
    data = r.json()
    print("Raw API Response:")
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error parsing JSON: {e}")
