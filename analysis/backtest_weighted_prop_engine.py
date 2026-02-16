"""
NBA Prop Betting Pipeline Backtest Script
-----------------------------------------
Evaluates the accuracy and performance of the dynamic weighted prop engine for Points, Rebounds, Assists (PRA) over the current NBA season.

Requirements:
- Uses historical box scores from local DB, DFS projections, sportsbook lines from TheOddsAPI.
- Modular functions for data fetching, player pool building, EV calculation, result comparison, and report generation.
- Logs skipped/missing players/props for transparency.
- Outputs: output/backtest_report_current_season.csv, optional top 10 props per day.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta

# Ensure helpers and analysis modules are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'helpers')))

from helpers.db_manager import get_recent_players_by_date, get_player_recent_stats
from analysis.player_pool import build_today_player_pool
from analysis.weighted_prop_engine_dynamic import compute_dynamic_weights, load_accuracy

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename="logs/backtest_weighted_prop_engine.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# --- CONFIG ---
OUTPUT_CSV = "output/backtest_report_current_season.csv"
TOP10_CSV = "output/backtest_top10_props_per_day.csv"
MIN_EDGE = 0.05
SEASON_START = "2025-10-25"  # Example: NBA season start
SEASON_END = datetime.now().strftime("%Y-%m-%d")

# --- Helper Functions ---

def fetch_historical_games(start_date, end_date):
    """
    Fetches all game dates between start and end from local DB.
    """
    db_path = os.path.join(os.path.dirname(__file__), '..', 'helpers', 'player_history.db')
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT DISTINCT game_date FROM game_logs WHERE game_date BETWEEN ? AND ? ORDER BY game_date ASC", (start_date, end_date))
    dates = [row[0] for row in c.fetchall()]
    conn.close()
    return dates

def fetch_actual_stats(player_id, game_date):
    """
    Fetches actual box score stats for a player on a given date.
    """
    db_path = os.path.join(os.path.dirname(__file__), '..', 'helpers', 'player_history.db')
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT points, rebounds, assists FROM game_logs WHERE player_id=? AND game_date=? LIMIT 1", (player_id, game_date))
    row = c.fetchone()
    conn.close()
    if row:
        return {'points': row[0], 'rebounds': row[1], 'assists': row[2]}
    else:
        return None

def fetch_dfs_projection(player_id, game_date):
    """
    Placeholder: Fetch DFS projection for a player on a given date.
    Replace with real DFS API or historical data.
    """
    # Example: Return average of last 5 games as proxy
    stats = get_player_recent_stats(player_id, last_n=5)
    if stats:
        return {
            'points': sum([r[1] for r in stats]) / len(stats),
            'rebounds': sum([r[2] for r in stats]) / len(stats),
            'assists': sum([r[3] for r in stats]) / len(stats)
        }
    return {'points': None, 'rebounds': None, 'assists': None}

def fetch_sportsbook_line(player_id, game_date):
    """
    Placeholder: Fetch sportsbook line for a player on a given date.
    Replace with real OddsAPI or historical data.
    """
    # Example: Use actual stat as proxy (for demo)
    actual = fetch_actual_stats(player_id, game_date)
    if actual:
        return {k: actual[k] for k in ['points', 'rebounds', 'assists']}
    return {'points': None, 'rebounds': None, 'assists': None}

def build_player_pool(game_date):
    """
    Builds player pool for a given game date using player_pool.py and db_manager.py.
    """
    players = get_recent_players_by_date(7, ref_date=game_date)
    pool = [{'player_id': p[0], 'player_name': p[1], 'team': p[2]} for p in players]
    return pool

def compute_weighted_ev(box_score, dfs_proj, sportsbook_line, weights):
    """
    Computes weighted expected value for each stat.
    """
    ev = {}
    for stat in ['points', 'rebounds', 'assists']:
        ev[stat] = (
            weights['box_score'] * (box_score.get(stat) or 0) +
            weights['dfs'] * (dfs_proj.get(stat) or 0) +
            weights['sharp_line'] * (sportsbook_line.get(stat) or 0) +
            weights['retail_line'] * (sportsbook_line.get(stat) or 0)
        )
    return ev

def compare_prediction(ev, actual):
    """
    Compares prediction to actual stat, returns accuracy and MAE.
    """
    result = {}
    for stat in ['points', 'rebounds', 'assists']:
        pred = ev.get(stat)
        act = actual.get(stat)
        if pred is not None and act is not None:
            mae = abs(pred - act)
            accuracy = 1 if abs(pred - act) <= 0.05 * act else 0
        else:
            mae = None
            accuracy = None
        result[stat] = {'mae': mae, 'accuracy': accuracy}
    return result

def run_backtest():
    """
    Main backtest loop for the current NBA season.
    """
    historical_accuracy = load_accuracy()
    weights = compute_dynamic_weights(historical_accuracy)
    game_dates = fetch_historical_games(SEASON_START, SEASON_END)
    all_rows = []
    top10_rows = []

    for game_date in game_dates:
        player_pool = build_player_pool(game_date)
        day_rows = []
        for player in player_pool:
            pid = player['player_id']
            pname = player['player_name']
            team = player['team']

            box_score = fetch_actual_stats(pid, game_date)
            dfs_proj = fetch_dfs_projection(pid, game_date)
            sportsbook_line = fetch_sportsbook_line(pid, game_date)

            if not box_score or not dfs_proj or not sportsbook_line:
                logging.warning(f"Missing data for player {pname} ({pid}) on {game_date}")
                continue

            ev = compute_weighted_ev(box_score, dfs_proj, sportsbook_line, weights)
            comparison = compare_prediction(ev, box_score)

            for stat in ['points', 'rebounds', 'assists']:
                edge_flag = 1 if ev[stat] - sportsbook_line[stat] >= MIN_EDGE else 0
                row = {
                    'date': game_date,
                    'player_id': pid,
                    'player_name': pname,
                    'team': team,
                    'prop': stat,
                    'predicted_ev': ev[stat],
                    'actual_stat': box_score[stat],
                    'accuracy': comparison[stat]['accuracy'],
                    'mae': comparison[stat]['mae'],
                    'edge_flag': edge_flag
                }
                day_rows.append(row)
        # Top 10 props by EV for the day
        if day_rows:
            df_day = pd.DataFrame(day_rows)
            top10 = df_day.nlargest(10, 'predicted_ev')
            top10_rows.extend(top10.to_dict('records'))
        all_rows.extend(day_rows)

    # Save detailed CSV
    df_all = pd.DataFrame(all_rows)
    df_all.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Backtest report saved to {OUTPUT_CSV}")

    # Save top 10 props per day
    if top10_rows:
        df_top10 = pd.DataFrame(top10_rows)
        df_top10.to_csv(TOP10_CSV, index=False)
        logging.info(f"Top 10 props per day saved to {TOP10_CSV}")

    # Print summary stats
    for stat in ['points', 'rebounds', 'assists']:
        stat_df = df_all[df_all['prop'] == stat]
        if not stat_df.empty:
            accuracy = stat_df['accuracy'].mean()
            mae = stat_df['mae'].mean()
            edge_success = stat_df[stat_df['edge_flag'] == 1]['accuracy'].mean()
            print(f"{stat.title()} - Accuracy: {accuracy:.2%}, MAE: {mae:.2f}, Edge Success Rate: {edge_success:.2%}")

    print(f"Backtest complete. See {OUTPUT_CSV} and {TOP10_CSV} for details.")

if __name__ == '__main__':
    run_backtest()
