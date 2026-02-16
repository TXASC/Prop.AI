

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
from providers.odds_provider import fetch_nba_games_and_markets

def get_nba_props():
    # Use the refactored provider to get NBA odds
    games = fetch_nba_games_and_markets()
    if not games:
        print("No NBA odds data found.")
        return
    import pandas as pd
    rows = []
    for game in games:
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                rows.append({
                    "game_id": game.get('game_id'),
                    "home_team": game.get('home_team'),
                    "away_team": game.get('away_team'),
                    "commence_time": game.get('commence_time'),
                    "bookmaker": bookmaker.get('key'),
                    "market": market.get('key'),
                    "outcomes": market.get('outcomes')
                })
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv("data/raw/nba_odds_adapter_output.csv", index=False)
        print(f"Saved {len(df)} odds rows to data/raw/nba_odds_adapter_output.csv")
    else:
        print("No odds rows found.")

if __name__ == "__main__":
    get_nba_props()
