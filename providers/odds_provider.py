


import sys
import importlib.util
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
bootstrap_path = repo_root / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", bootstrap_path)
bootstrap = importlib.util.module_from_spec(spec)
sys.modules["bootstrap"] = bootstrap
spec.loader.exec_module(bootstrap)
get_repo_root = bootstrap.get_repo_root
import config
from providers.odds_adapter import OddsAdapter

# Instantiate the OddsAdapter singleton
_odds_adapter = OddsAdapter(
    db_path=config.DB_PATH,
    api_key=config.ODDS_API_KEY,
    daily_credit_budget=config.ODDS_DAILY_CREDIT_BUDGET,
    default_ttl_minutes=config.ODDS_DEFAULT_TTL_MINUTES
)

def fetch_nba_games_and_markets():
    # Use the adapter for NBA odds
    import os
    fast_mode = os.environ.get("FAST_MODE", "0") == "1"
    markets = "h2h" if fast_mode else "h2h,spreads,totals"
    odds = _odds_adapter.get_odds(
        sport="basketball_nba",
        regions="us",
        markets=markets,
        odds_format="american",
        date_format="iso"
    )
    clean_games = []
    for game in odds:
        clean_games.append({
            'game_id': game.get('id'),
            'home_team': game.get('home_team'),
            'away_team': game.get('away_team'),
            'commence_time': game.get('commence_time'),
            'bookmakers': game.get('bookmakers', [])
        })
    return clean_games
