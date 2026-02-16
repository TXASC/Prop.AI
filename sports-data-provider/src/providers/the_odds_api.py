import requests

class TheOddsAPI:
    BASE_URL = "https://api.theoddsapi.com/v4/sports"

    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_nba_games_and_markets(self):
        url = f"{self.BASE_URL}/basketball/nba/schedules"
        params = {
            'api_key': self.api_key
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()