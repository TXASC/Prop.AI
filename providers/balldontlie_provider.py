
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import logging
import os

ET = ZoneInfo("America/New_York")

# Setup logging for provider
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/provider.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class BallDontLieProvider:
    BASE = "https://www.balldontlie.io/api/v1"
    API_KEY = os.environ.get("BALLDONTLIE_API_KEY", "0114434c-8ed4-42bf-b10a-132dfa3feb14")

    def fetch_with_retry(self, endpoint, params=None, retries=2, delay=2):
        headers = {"Authorization": self.API_KEY}
        for attempt in range(retries + 1):
            r = requests.get(f"{self.BASE}/{endpoint}", params=params, headers=headers)
            logging.info(f"Request URL: {r.url} | Status: {r.status_code}")
            logging.info(f"Raw response: {r.text}")
            if r.status_code == 200:
                return r.json()
            else:
                logging.warning(f"Attempt {attempt+1} failed: {r.status_code}, retrying in {delay}s")
                time.sleep(delay)
        logging.error(f"All attempts failed for endpoint {endpoint} with params {params}")
        return {"data": []}

    def get_recent_team_games(self, team_name):
        team_id = None
        try:
            teams = self.fetch_with_retry("teams")
            for t in teams.get("data", []):
                if t.get("full_name", "").lower() == team_name.lower():
                    team_id = t.get("id")
                    break
        except Exception as e:
            logging.error(f"Failed to fetch teams for {team_name}: {e}")
        if not team_id:
            logging.warning(f"Could not find team id for {team_name}")
            return []
        for attempt in range(3):
            try:
                games = self.fetch_with_retry("games", params={"team_ids[]": team_id, "per_page": 5})
                return games.get("data", [])
            except Exception as e:
                logging.error(f"Team games fetch failed for {team_name} (id {team_id}), attempt {attempt+1}: {e}")
        logging.warning(f"Could not fetch recent games for {team_name} after 3 attempts.")
        return []

    def get_game_box_score(self, game_id):
        from database.db_manager import save_player, save_game_log
        for attempt in range(3):
            try:
                stats = self.fetch_with_retry("stats", params={"game_ids[]": game_id, "per_page": 100})
                box = []
                for s in stats.get("data", []):
                    player_id = s.get('player_id')
                    player_name = f"{s.get('player', {}).get('first_name', '')} {s.get('player', {}).get('last_name', '')}"
                    team = s.get('team', {}).get('full_name', '')
                    mins = s.get('min', 0)
                    points = s.get('pts', 0)
                    rebounds = s.get('reb', 0)
                    assists = s.get('ast', 0)
                    game_date = s.get('game', {}).get('date', '')
                    box.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'min': mins
                    })
                    # Save player and game log to DB
                    save_player({'player_id': player_id, 'player_name': player_name, 'team': team})
                    save_game_log(player_id, {
                        'game_date': game_date,
                        'minutes': mins,
                        'points': points,
                        'rebounds': rebounds,
                        'assists': assists
                    })
                return box
            except Exception as e:
                logging.error(f"Box score fetch failed for game {game_id}, attempt {attempt+1}: {e}")
        logging.warning(f"Could not fetch box score for game {game_id} after 3 attempts.")
        return []
    def get_team_roster_by_name(self, team_name):
        """Fetch roster for a team by name, retry up to 3 times."""
        import logging
        team_id = None
        # Find team id
        try:
            teams = self.fetch_with_retry("teams")
            for t in teams.get("data", []):
                if t.get("full_name", "").lower() == team_name.lower():
                    team_id = t.get("id")
                    break
        except Exception as e:
            logging.error(f"Failed to fetch teams for {team_name}: {e}")
        if not team_id:
            logging.warning(f"Could not find team id for {team_name}")
            return []
        # Fetch players for team
        for attempt in range(3):
            try:
                players = self.fetch_with_retry("players", params={"team_ids[]": team_id, "per_page": 100})
                return players.get("data", [])
            except Exception as e:
                logging.error(f"Roster fetch failed for {team_name} (id {team_id}), attempt {attempt+1}: {e}")
        logging.warning(f"Could not fetch roster for {team_name} after 3 attempts.")
        return []

    def get_recent_player_stats(self, player_id):
        """Fetch last 5 games box scores for player, return averages."""
        import logging
        stats = self.fetch_with_retry("stats", params={"player_ids[]": player_id, "per_page": 5})
        games = stats.get("data", [])
        if not games:
            logging.warning(f"No recent stats for player {player_id}")
            return {"points": 0, "rebounds": 0, "assists": 0, "minutes": 0}
        pts, rebs, asts, mins = 0, 0, 0, 0
        for g in games:
            pts += g.get("pts", 0)
            rebs += g.get("reb", 0)
            asts += g.get("ast", 0)
            mins += g.get("min", 0) if g.get("min") else 0
        n = len(games)
        return {
            "points": round(pts/n, 2),
            "rebounds": round(rebs/n, 2),
            "assists": round(asts/n, 2),
            "minutes": round(mins/n, 2) if n else 0
        }
    BASE = "https://www.balldontlie.io/api/v1"
    # Use environment variable if set, else fallback to hardcoded key
    API_KEY = os.environ.get("BALLDONTLIE_API_KEY", "0114434c-8ed4-42bf-b10a-132dfa3feb14")

    def fetch_with_retry(self, endpoint, params=None, retries=2, delay=2):
        """Generic GET request with retry and Authorization header"""
        headers = {"Authorization": self.API_KEY}
        for attempt in range(retries + 1):
            r = requests.get(f"{self.BASE}/{endpoint}", params=params, headers=headers)
            logging.info(f"Request URL: {r.url} | Status: {r.status_code}")
            logging.info(f"Raw response: {r.text}")
            if r.status_code == 200:
                return r.json()
            else:
                logging.warning(f"Attempt {attempt+1} failed: {r.status_code}, retrying in {delay}s")
                time.sleep(delay)
        logging.error(f"All attempts failed for endpoint {endpoint} with params {params}")
        return {"data": []}  # safe fallback

    # Removed schedule/game-day fetching. Only stat utilities below.

    def get_player_game_logs(self, player_id, num_games=5):
        class BallDontLieProvider:
            BASE = "https://www.balldontlie.io/api/v1"
            API_KEY = os.environ.get("BALLDONTLIE_API_KEY", "0114434c-8ed4-42bf-b10a-132dfa3feb14")

            def fetch_with_retry(self, endpoint, params=None, retries=2, delay=2):
                """Generic GET request with retry and Authorization header"""
                headers = {"Authorization": self.API_KEY}
                for attempt in range(retries + 1):
                    r = requests.get(f"{self.BASE}/{endpoint}", params=params, headers=headers)
                    logging.info(f"Request URL: {r.url} | Status: {r.status_code}")
                    logging.info(f"Raw response: {r.text}")
                    if r.status_code == 200:
                        return r.json()
                    else:
                        logging.warning(f"Attempt {attempt+1} failed: {r.status_code}, retrying in {delay}s")
                        time.sleep(delay)
                logging.error(f"All attempts failed for endpoint {endpoint} with params {params}")
                return {"data": []}  # safe fallback

            def get_team_roster_by_name(self, team_name):
                """Fetch roster for a team by name, retry up to 3 times."""
                import logging
                team_id = None
                # Find team id
                try:
                    teams = self.fetch_with_retry("teams")
                    for t in teams.get("data", []):
                        if t.get("full_name", "").lower() == team_name.lower():
                            team_id = t.get("id")
                            break
                except Exception as e:
                    logging.error(f"Failed to fetch teams for {team_name}: {e}")
                if not team_id:
                    logging.warning(f"Could not find team id for {team_name}")
                    return []
                # Fetch players for team
                for attempt in range(3):
                    try:
                        players = self.fetch_with_retry("players", params={"team_ids[]": team_id, "per_page": 100})
                        return players.get("data", [])
                    except Exception as e:
                        logging.error(f"Roster fetch failed for {team_name} (id {team_id}), attempt {attempt+1}: {e}")
                logging.warning(f"Could not fetch roster for {team_name} after 3 attempts.")
                return []

            def get_recent_player_stats(self, player_id):
                """Fetch last 5 games box scores for player, return averages."""
                import logging
                stats = self.fetch_with_retry("stats", params={"player_ids[]": player_id, "per_page": 5})
                games = stats.get("data", [])
                if not games:
                    logging.warning(f"No recent stats for player {player_id}")
                    return {"points": 0, "rebounds": 0, "assists": 0, "minutes": 0}
                pts, rebs, asts, mins = 0, 0, 0, 0
                for g in games:
                    pts += g.get("pts", 0)
                    rebs += g.get("reb", 0)
                    asts += g.get("ast", 0)
                    mins += g.get("min", 0) if g.get("min") else 0
                n = len(games)
                return {
                    "points": round(pts/n, 2),
                    "rebounds": round(rebs/n, 2),
                    "assists": round(asts/n, 2),
                    "minutes": round(mins/n, 2) if n else 0
                }

            def get_recent_team_games(self, team_name):
                import logging
                team_id = None
                try:
                    teams = self.fetch_with_retry("teams")
                    for t in teams.get("data", []):
                        if t.get("full_name", "").lower() == team_name.lower():
                            team_id = t.get("id")
                            break
                except Exception as e:
                    logging.error(f"Failed to fetch teams for {team_name}: {e}")
                if not team_id:
                    logging.warning(f"Could not find team id for {team_name}")
                    return []
                for attempt in range(3):
                    try:
                        games = self.fetch_with_retry("games", params={"team_ids[]": team_id, "per_page": 5})
                        return games.get("data", [])
                    except Exception as e:
                        logging.error(f"Team games fetch failed for {team_name} (id {team_id}), attempt {attempt+1}: {e}")
                logging.warning(f"Could not fetch recent games for {team_name} after 3 attempts.")
                return []

            def get_game_box_score(self, game_id):
                import logging
                for attempt in range(3):
                    try:
                        stats = self.fetch_with_retry("stats", params={"game_ids[]": game_id, "per_page": 100})
                        box = []
                        for s in stats.get("data", []):
                            box.append({
                                'player_id': s.get('player_id'),
                                'player_name': f"{s.get('player', {}).get('first_name', '')} {s.get('player', {}).get('last_name', '')}",
                                'min': s.get('min', 0)
                            })
                        return box
                    except Exception as e:
                        logging.error(f"Box score fetch failed for game {game_id}, attempt {attempt+1}: {e}")
                logging.warning(f"Could not fetch box score for game {game_id} after 3 attempts.")
                return []
