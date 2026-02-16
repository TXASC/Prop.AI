from typing import List, Dict, Any
import requests

class BallDontLieProvider:
    BASE_URL = "https://www.balldontlie.io/api/v1"

    def get_player_game_logs(self, player_id: int) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.BASE_URL}/stats?player_ids[]={player_id}")
        response.raise_for_status()
        return response.json().get('data', [])

    def get_team_roster(self, team_name: str) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.BASE_URL}/teams")
        response.raise_for_status()
        teams = response.json().get('data', [])
        team_id = next((team['id'] for team in teams if team['full_name'] == team_name), None)
        
        if team_id is None:
            return []

        response = requests.get(f"{self.BASE_URL}/players?team_ids[]={team_id}")
        response.raise_for_status()
        return response.json().get('data', [])

    def get_recent_games(self, team_id: int) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.BASE_URL}/games?team_ids[]={team_id}&start_date=2026-02-01&end_date=2026-02-12")
        response.raise_for_status()
        return response.json().get('data', [])