# provider_layer_fix.py
# Updated BallDontLie provider layer with correct API URL, retries, and logging

import requests
import logging
from datetime import datetime
import time

# Setup logging
logging.basicConfig(
    filename="logs/provider.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_URL = "https://balldontlie.io/api/v1"  # <- Correct URL, no www
GAMES_ENDPOINT = f"{BASE_URL}/games"

def fetch_todays_games(retries=3, delay=2):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    params = {"dates[]": today_str}

    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Fetching games for today: {today_str}")
            response = requests.get(GAMES_ENDPOINT, params=params)
            logging.info(f"Request URL: {response.url} | Status: {response.status_code}")
            logging.info(f"Raw response snippet: {response.text[:200]}")  # first 200 chars

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    logging.info(f"Found {len(data['data'])} games today")
                    return data["data"]
                else:
                    logging.warning(f"No games returned for today: {today_str}")
                    return []
            else:
                logging.warning(f"Attempt {attempt} failed: {response.status_code}, retrying in {delay}s")
                time.sleep(delay)

        except requests.RequestException as e:
            logging.error(f"Request exception: {e}, retrying in {delay}s")
            time.sleep(delay)

    logging.error(f"All attempts failed for endpoint games with params {params}")
    return []

if __name__ == "__main__":
    games = fetch_todays_games()
    print(games)
