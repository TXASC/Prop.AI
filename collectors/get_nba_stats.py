
import requests
import pandas as pd
import os
import logging
from config import RAW_DATA_DIR, LOGS_DIR

LOG_PATH = os.path.join(LOGS_DIR, "get_nba_stats.log")
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def get_player_gamelogs():
    import datetime
    from config import NBA_API_KEY
    headers = {
        "Ocp-Apim-Subscription-Key": NBA_API_KEY
    }
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    today = datetime.date.today()
    for i in range(1, 15):  # Try up to 14 days back
        game_date = today - datetime.timedelta(days=i)
        date_str = game_date.strftime("%Y-%m-%d")
        url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{date_str}"
        logging.info(f"Requesting NBA player stats for {date_str} from SportsData.io...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            logging.info(f"Status code: {response.status_code}")
            if response.status_code != 200:
                logging.warning(f"Failed to fetch stats: {response.status_code}")
                logging.warning(f"Response text: {response.text[:500]}")
                continue
            try:
                data = response.json()
            except Exception as e:
                logging.error(f"JSON decode error: {e}")
                logging.error(f"Raw response: {response.text[:500]}")
                continue
            logging.info(f"Fetched {len(data)} player game stats.")
            raw_json_path = os.path.join(RAW_DATA_DIR, f"nba_player_stats_raw_{date_str}.json")
            csv_path = os.path.join(RAW_DATA_DIR, f"nba_player_stats_{date_str}.csv")
            with open(raw_json_path, "w", encoding="utf-8") as f:
                import json
                json.dump(data, f, ensure_ascii=False, indent=2)
            if not data:
                logging.warning(f"No stats found for {date_str}.")
                continue
            try:
                df = pd.json_normalize(data)
                df.to_csv(csv_path, index=False)
                logging.info(f"CSV file created at {csv_path} with {len(df)} rows.")
                return
            except Exception as e:
                logging.error(f"Error saving CSV: {e}")
                continue
        except Exception as e:
            logging.error(f"Request or processing error: {e}")
            continue
    logging.warning("No NBA player stats found for the last 14 days.")

if __name__ == "__main__":
    get_player_gamelogs()
