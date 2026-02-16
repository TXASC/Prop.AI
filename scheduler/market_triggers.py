import os
import json
import logging
from datetime import datetime
from providers.get_injuries import get_latest_injuries
from providers.odds_provider import fetch_nba_games_and_markets
import threading
import time
from collectors.closing_line_snapshot_collector import collect_current_prop_odds

CACHE_DIR = os.path.join("cache")
INJURY_SNAPSHOT = os.path.join(CACHE_DIR, "injury_snapshot.json")
ODDS_SNAPSHOT = os.path.join(CACHE_DIR, "odds_snapshot.json")
GAMES_SNAPSHOT = os.path.join(CACHE_DIR, "games_snapshot.json")
LOG_PATH = os.path.join("logs", "scheduler.log")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SNAPSHOT_INTERVAL_MINUTES = 10
CLOSING_WINDOW_HOURS = 3

def check_injury_news():
    try:
        latest = get_latest_injuries()
        if os.path.exists(INJURY_SNAPSHOT):
            with open(INJURY_SNAPSHOT, 'r') as f:
                prev = json.load(f)
        else:
            prev = {}
        changed = False
        for player, status in latest.items():
            if prev.get(player) != status:
                changed = True
                break
        if changed:
            logging.info("Injury news changed: rerun pipeline.")
        with open(INJURY_SNAPSHOT, 'w') as f:
            json.dump(latest, f)
        return changed
    except Exception as e:
        logging.error(f"Injury news check failed: {e}")
        return False

def check_line_movement():
    try:
        odds = fetch_nba_games_and_markets()
        if os.path.exists(ODDS_SNAPSHOT):
            with open(ODDS_SNAPSHOT, 'r') as f:
                prev = json.load(f)
        else:
            prev = {}
        changed = False
        for game in odds:
            gid = game.get('game_id')
            for bm in game.get('bookmakers', []):
                for market in bm.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        key = f"{gid}_{market['key']}_{outcome['name']}"
                        prev_line = prev.get(key, {}).get('line')
                        curr_line = outcome.get('line')
                        if prev_line is not None and curr_line is not None:
                            if abs(curr_line - prev_line) >= 0.75:
                                changed = True
                                break
        if changed:
            logging.info("Line movement detected: rerun pipeline.")
        # Save snapshot
        flat = {}
        for game in odds:
            gid = game.get('game_id')
            for bm in game.get('bookmakers', []):
                for market in bm.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        key = f"{gid}_{market['key']}_{outcome['name']}"
                        flat[key] = {'line': outcome.get('line')}
        with open(ODDS_SNAPSHOT, 'w') as f:
            json.dump(flat, f)
        return changed
    except Exception as e:
        logging.error(f"Line movement check failed: {e}")
        return False

def check_new_games_added():
    try:
        odds = fetch_nba_games_and_markets()
        today_games = set(g['game_id'] for g in odds)
        if os.path.exists(GAMES_SNAPSHOT):
            with open(GAMES_SNAPSHOT, 'r') as f:
                prev_games = set(json.load(f))
        else:
            prev_games = set()
        new_games = today_games - prev_games
        with open(GAMES_SNAPSHOT, 'w') as f:
            json.dump(list(today_games), f)
        if new_games:
            logging.info(f"New games added: {new_games}")
        return bool(new_games)
    except Exception as e:
        logging.error(f"New games check failed: {e}")
        return False

def run_periodic_odds_snapshot():
    """
    Periodically collect odds snapshots for games starting soon.
    """
    while True:
        try:
            now = datetime.utcnow()
            games = fetch_nba_games_and_markets()
            soon_games = [
                g for g in games
                if "commence_time" in g and
                0 <= (datetime.fromisoformat(g["commence_time"]) - now).total_seconds() / 3600 <= CLOSING_WINDOW_HOURS
            ]
            if soon_games:
                collect_current_prop_odds()
            else:
                logging.info("No games within closing window for odds snapshot.")
        except Exception as e:
            logging.error(f"Periodic odds snapshot error: {e}")
        time.sleep(SNAPSHOT_INTERVAL_MINUTES * 60)

# To enable, call run_periodic_odds_snapshot() in a separate thread or process.
# Example:
# threading.Thread(target=run_periodic_odds_snapshot, daemon=True).start()
