import logging
from providers.balldontlie_provider import BallDontLieProvider

def generate_player_projections(player_pool, implied_scores=None):
    provider = BallDontLieProvider()
    from database.db_manager import get_player_recent_stats, save_game_log
    projections = []
    for player in player_pool:
        rows = get_player_recent_stats(player['player_id'], last_n=5)
        if len(rows) < 3:
            # Fallback: call API and store
            stats = provider.get_recent_player_stats(player['player_id'])
            avg_minutes = stats['minutes']
            points = stats['points']
            rebounds = stats['rebounds']
            assists = stats['assists']
        else:
            avg_minutes = sum([r[0] for r in rows]) / len(rows)
            points = sum([r[1] for r in rows]) / len(rows)
            rebounds = sum([r[2] for r in rows]) / len(rows)
            assists = sum([r[3] for r in rows]) / len(rows)
        if avg_minutes < 10:
            logging.warning(f"Skipped player {player['player_name']} (avg_minutes={avg_minutes})")
            continue
        per_minute = {
            'points': points / avg_minutes if avg_minutes else 0,
            'rebounds': rebounds / avg_minutes if avg_minutes else 0,
            'assists': assists / avg_minutes if avg_minutes else 0
        }
        proj = {
            'player_id': player['player_id'],
            'player_name': player['player_name'],
            'team': player['team'],
            'projected_points': round(per_minute['points'] * avg_minutes, 2),
            'projected_rebounds': round(per_minute['rebounds'] * avg_minutes, 2),
            'projected_assists': round(per_minute['assists'] * avg_minutes, 2)
        }
        projections.append(proj)
    logging.info(f"Generated projections for {len(projections)} players.")
    return projections
