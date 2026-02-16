import logging
from datetime import datetime
from providers.odds_provider import fetch_nba_games_and_markets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
Fetch NBA games for today's date using OddsAPI provider.
Returns: List of games for today.
"""
def fetch_games_for_today():
    games = fetch_nba_games_and_markets()
    from datetime import datetime, timedelta
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    filtered_games = []
    for game in games:
        # commence_time is ISO format, e.g. '2026-02-13T00:43:00Z'
        game_date = datetime.fromisoformat(game['commence_time'].replace('Z', ''))
        # Include games starting today or before noon tomorrow (covers late-night games)
        if today <= game_date.date() <= tomorrow:
            filtered_games.append(game)
    logger.info(f"Fetched {len(filtered_games)} NBA games for {today} from OddsAPI.")
    return filtered_games

if __name__ == "__main__":
    games_today = fetch_games_for_today()
    logger.info(f"Total games retrieved: {len(games_today)}")
