import logging
import os
from providers.balldontlie_provider import BallDontLieProvider
from config import PLAYER_POOL_LOG


def build_today_player_pool(games):
    os.makedirs(os.path.dirname(PLAYER_POOL_LOG), exist_ok=True)
    pool_logger = logging.getLogger('player_pool')
    handler = logging.FileHandler(PLAYER_POOL_LOG)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    if not pool_logger.hasHandlers():
        pool_logger.addHandler(handler)
    pool_logger.setLevel(logging.INFO)

    provider = BallDontLieProvider()
    from database.db_manager import get_player_recent_stats
    player_minutes = {}
    player_games = {}
    team_players = {}
    for game in games:
        for team in [game['home_team'], game['away_team']]:
            recent_games = provider.get_recent_team_games(team)
            team_players[team] = set()
            for g in recent_games:
                box = provider.get_game_box_score(g['id'])
                for stat in box:
                    pid = stat.get('player_id')
                    pname = stat.get('player_name')
                    mins = stat.get('min', 0)
                    if mins > 0:
                        team_players[team].add(pid)
                        player_minutes.setdefault(pid, []).append(mins)
                        player_games.setdefault(pid, []).append(g['id'])
    # Always use DB for recent players, fallback if API fails
    from database.db_manager import get_recent_players_by_date
    player_pool = []
    skipped = []
    try:
        for team, pids in team_players.items():
            for pid in pids:
                avg_min = sum(player_minutes[pid]) / len(player_minutes[pid]) if player_minutes[pid] else 0
                games_played = len(player_games[pid])
                pname = None
                for g in games:
                    for t in [g['home_team'], g['away_team']]:
                        if t == team:
                            recent_games = provider.get_recent_team_games(team)
                            for game_obj in recent_games:
                                box = provider.get_game_box_score(game_obj['id'])
                                for stat in box:
                                    if stat.get('player_id') == pid:
                                        pname = stat.get('player_name')
                                        break
                if avg_min >= 12 and games_played >= 3:
                    player_pool.append({'player_id': pid, 'player_name': pname, 'team': team})
                else:
                    skipped.append({'player_id': pid, 'player_name': pname, 'team': team, 'reason': f"avg_min={avg_min}, games_played={games_played}"})
    except Exception as e:
        pool_logger.warning(f"API player pool failed, falling back to DB only: {e}")
    # Always add DB players (ensures pool even if API fails)
    db_players = get_recent_players_by_date(days=7)
    for pid, pname, team in db_players:
        player_pool.append({'player_id': pid, 'player_name': pname, 'team': team})
    pool_logger.info(f"Teams processed: {[g['home_team'] for g in games] + [g['away_team'] for g in games]}")
    pool_logger.info(f"Players detected: {len(player_pool)}")
    pool_logger.info(f"Players skipped: {len(skipped)}")
    for s in skipped:
        pool_logger.info(f"Skipped: {s}")
    return player_pool
