"""
Weighted NBA Prop Engine
-----------------------
Combines box score stats, DFS projections, and sportsbook lines using configurable weights.
Modular, robust, and ready for future AI/x-factor integration.
"""
import logging
import pandas as pd
from typing import Dict, List
from analysis.projection_engine import generate_player_projections
from analysis.player_pool import build_today_player_pool
from database.db_manager import get_player_recent_stats
from providers.odds_provider import fetch_nba_games_and_markets
from providers.balldontlie_provider import BallDontLieProvider

# Placeholder: Fetch DFS projections (replace with real API)
def fetch_dfs_projections(player_ids: List[int]) -> Dict[int, Dict[str, float]]:
    # Example: {player_id: {'points': 22.5, 'rebounds': 7.1, 'assists': 5.2}}
    return {pid: {'points': 20.0, 'rebounds': 6.0, 'assists': 4.0} for pid in player_ids}

# Placeholder: Fetch sportsbook lines (replace with real API)
def fetch_sportsbook_lines(player_ids: List[int]) -> Dict[int, Dict[str, float]]:
    # Example: {player_id: {'points': 21.5, 'rebounds': 6.5, 'assists': 4.5}}
    return {pid: {'points': 21.0, 'rebounds': 6.5, 'assists': 4.5} for pid in player_ids}

# Weighted EV computation
def compute_weighted_ev(box_score: Dict[str, float], dfs_proj: Dict[str, float], sportsbook_line: Dict[str, float], weights: Dict[str, float]) -> Dict[str, float]:
    return {
        stat: (
            weights['box_score'] * box_score.get(stat, 0.0) +
            weights['dfs'] * dfs_proj.get(stat, 0.0) +
            weights['sportsbook'] * sportsbook_line.get(stat, 0.0)
        )
        for stat in ['points', 'rebounds', 'assists']
    }

# Edge computation
def compute_edge(ev: Dict[str, float], book_line: Dict[str, float]) -> Dict[str, float]:
    return {stat: ev[stat] - book_line.get(stat, 0.0) for stat in ['points', 'rebounds', 'assists']}

# Main pipeline function
def weighted_prop_pipeline(games: List[Dict], weights: Dict[str, float], min_edge: float = 1.0) -> pd.DataFrame:
    logger = logging.getLogger('weighted_prop_engine')
    player_pool = build_today_player_pool(games)
    player_ids = [p['player_id'] for p in player_pool]

    # Fetch all data sources
    box_score_projs = {p['player_id']: {
        'points': p['projected_points'],
        'rebounds': p['projected_rebounds'],
        'assists': p['projected_assists']
    } for p in generate_player_projections(player_pool)}
    dfs_projs = fetch_dfs_projections(player_ids)
    sportsbook_lines = fetch_sportsbook_lines(player_ids)

    rows = []
    for player in player_pool:
        pid = player['player_id']
        pname = player['player_name']
        team = player['team']

        box_score = box_score_projs.get(pid, {})
        dfs_proj = dfs_projs.get(pid, {})
        book_line = sportsbook_lines.get(pid, {})

        ev = compute_weighted_ev(box_score, dfs_proj, book_line, weights)
        edge = compute_edge(ev, book_line)

        logger.info(f"Player: {pname} | Weights: {weights} | EV: {ev} | Edge: {edge}")

        for stat in ['points', 'rebounds', 'assists']:
            if abs(edge[stat]) >= min_edge:
                rows.append({
                    'date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                    'player_id': pid,
                    'player_name': pname,
                    'team': team,
                    'stat': stat,
                    'weighted_ev': ev[stat],
                    'book_line': book_line.get(stat, 0.0),
                    'edge': edge[stat],
                    'confidence': abs(edge[stat])
                })

    df = pd.DataFrame(rows)
    output_path = 'output/weighted_props.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"Filtered props saved to {output_path}")
    return df

# Example integration for daily_pipeline.py
if __name__ == '__main__':
    logging.basicConfig(filename='logs/weighted_prop_engine.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    games = fetch_nba_games_and_markets()
    weights = {'box_score': 0.4, 'dfs': 0.4, 'sportsbook': 0.2}  # Configurable
    min_edge = 1.5  # Configurable threshold
    weighted_prop_pipeline(games, weights, min_edge)
