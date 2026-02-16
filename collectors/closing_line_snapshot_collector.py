"""
Closing Line Snapshot Collector

Collects current NBA prop odds from The Odds API and stores timestamped snapshots
for forward CLV tracking.

Functions:
    collect_current_prop_odds()
"""

import logging
from datetime import datetime
from database.clv_tracking import insert_closing_line_snapshot
from providers.odds_provider import fetch_nba_games_and_markets

LOG_PATH = "logs/closing_line_capture.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def collect_current_prop_odds():
    """
    Fetches current NBA player prop odds and stores timestamped snapshots.
    Logs all actions. Fails gracefully if API unavailable.
    """
    try:
        games = fetch_nba_games_and_markets()
        now = datetime.utcnow().isoformat()
        for game in games:
            game_id = game.get("game_id")
            game_date = game.get("commence_time", "")[:10]
            for market in game.get("markets", []):
                if market.get("key", "").startswith("player_"):
                    for outcome in market.get("outcomes", []):
                        player_name = outcome.get("player")
                        stat_type = market.get("key").replace("player_", "").upper()
                        sportsbook = outcome.get("book", "unknown")
                        line = outcome.get("line")
                        odds = outcome.get("odds")
                        insert_closing_line_snapshot(
                            game_date, game_id, player_name, stat_type, sportsbook, line, odds, now
                        )
        logging.info(f"Collected odds snapshot for {len(games)} games at {now}")
    except Exception as e:
        logging.error(f"Failed to collect odds snapshot: {e}")
