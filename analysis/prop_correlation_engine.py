"""
Prop Correlation Engine

Computes rolling Pearson correlations between NBA player/team props for parlay optimization.

Functions:
    compute_rolling_correlations(window=20)
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from database.clv_tracking import upsert_prop_correlation, get_clv_db_connection

LOG_PATH = "logs/prop_correlation.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def compute_rolling_correlations(window=20):
    """
    Compute rolling Pearson correlations between relevant NBA props.
    Stores results in prop_correlations table.
    Args:
        window (int): Number of games to use for rolling calculation.
    """
    try:
        conn = get_clv_db_connection()
        # Example: Pull last N games for all players from pickem_bets and game logs
        # Placeholder: Replace with real queries and joins as needed
        df_bets = pd.read_sql_query(
            f"""SELECT * FROM pickem_bets WHERE bet_timestamp >=
            (SELECT MAX(bet_timestamp) FROM pickem_bets) LIMIT {window}""", conn)
        # Example: Load historical game logs (assume data/processed/clean_player_stats.csv)
        df_stats = pd.read_csv('data/processed/clean_player_stats.csv')
        # Merge and compute correlations
        # Example: player points ↔ player usage
        for player_id in df_stats['player_id'].unique():
            sub = df_stats[df_stats['player_id'] == player_id].sort_values('game_date').tail(window)
            if len(sub) < 5:
                continue
            if 'PTS' in sub.columns and 'USG%' in sub.columns:
                corr = sub['PTS'].corr(sub['USG%'])
                if pd.notnull(corr):
                    upsert_prop_correlation(player_id, None, 'PTS', 'USG%', float(corr), len(sub), datetime.utcnow().isoformat())
                    logging.info(f"Updated correlation: {player_id} PTS↔USG% ({len(sub)} games) = {corr:.3f}")
        # Example: player assists ↔ teammate points
        for team in df_stats['team_id'].unique():
            team_players = df_stats[df_stats['team_id'] == team]['player_id'].unique()
            for p1 in team_players:
                for p2 in team_players:
                    if p1 == p2:
                        continue
                    sub1 = df_stats[(df_stats['player_id'] == p1) & (df_stats['team_id'] == team)].sort_values('game_date').tail(window)
                    sub2 = df_stats[(df_stats['player_id'] == p2) & (df_stats['team_id'] == team)].sort_values('game_date').tail(window)
                    if len(sub1) < 5 or len(sub2) < 5:
                        continue
                    merged = pd.merge(sub1[['game_date', 'AST']], sub2[['game_date', 'PTS']], on='game_date')
                    if len(merged) < 5:
                        continue
                    corr = merged['AST'].corr(merged['PTS'])
                    if pd.notnull(corr):
                        upsert_prop_correlation(p1, p2, 'AST', 'PTS', float(corr), len(merged), datetime.utcnow().isoformat())
                        logging.info(f"Updated correlation: {p1} AST↔{p2} PTS ({len(merged)} games) = {corr:.3f}")
        # Add more: minutes↔rebounds/blocks, team pace↔individual stats, player points↔team total points
        # ... (implement as above, using available columns)
        conn.close()
    except Exception as e:
        logging.error(f"Correlation computation failed: {e}")
