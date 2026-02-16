import os
import pandas as pd
from datetime import datetime
from analysis.player_pool import build_today_player_pool
from analysis.projection_engine import generate_player_projections
from providers.odds_provider import fetch_nba_games_and_markets

today = datetime.now().strftime('%Y-%m-%d')
games = fetch_nba_games_and_markets()
player_pool = build_today_player_pool(games)
projections = generate_player_projections(player_pool)

# Record predictions for all players in tonight's games
rows = []
for proj in projections:
    rows.append({
        'date': today,
        'player_id': proj['player_id'],
        'player_name': proj['player_name'],
        'team': proj['team'],
        'projected_points': proj['projected_points'],
        'projected_rebounds': proj['projected_rebounds'],
        'projected_assists': proj['projected_assists']
    })

os.makedirs('output', exist_ok=True)
pd.DataFrame(rows).to_csv(f'output/simulation_{today}.csv', index=False)
print(f"Simulation complete. Predictions saved to output/simulation_{today}.csv")
