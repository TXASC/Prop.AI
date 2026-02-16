import os
import json
import sqlite3

import logging
def populate_game_logs_from_json(json_path, db_path):
    encodings = ['utf-8', 'utf-8-sig', 'latin1']
    for enc in encodings:
        try:
            with open(json_path, 'r', encoding=enc) as f:
                data = json.load(f)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logging.error(f"Failed to load {json_path} with encoding {enc}: {e}")
            return
    else:
        logging.error(f"All encoding attempts failed for {json_path}")
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for entry in data:
        player_id = entry.get('PlayerID')
        name = entry.get('Name')
        team = entry.get('Team')
        game_date = entry.get('Day', '').split('T')[0]
        minutes = entry.get('Minutes', 0)
        points = entry.get('Points', 0)
        rebounds = entry.get('Rebounds', 0)
        assists = entry.get('Assists', 0)
        opponent = entry.get('Opponent', '')
        pra = points + rebounds + assists
        # Save player
        c.execute('''INSERT OR IGNORE INTO players (player_id, name, team) VALUES (?, ?, ?)''',
                  (player_id, name, team))
        # Save game log
        c.execute('''INSERT INTO game_logs (player_id, game_date, minutes, points, rebounds, assists)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (player_id, game_date, minutes, points, rebounds, assists))
    conn.commit()
    conn.close()
    print(f"Populated game_logs from {json_path}")

if __name__ == '__main__':
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'))
    for fname in os.listdir(raw_dir):
        if fname.startswith('nba_player_stats_raw_') and fname.endswith('.json'):
            json_path = os.path.join(raw_dir, fname)
            populate_game_logs_from_json(json_path, db_path)
