import sqlite3
import os
import datetime

def initialize_database():
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY,
        name TEXT,
        team TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        game_date TEXT,
        minutes REAL,
        points REAL,
        rebounds REAL,
        assists REAL
    )''')
    conn.commit()
    conn.close()

def save_player(player):
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO players (player_id, name, team) VALUES (?, ?, ?)''',
              (player['player_id'], player['player_name'], player['team']))
    conn.commit()
    conn.close()

def save_game_log(player_id, stats):
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT INTO game_logs (player_id, game_date, minutes, points, rebounds, assists)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (player_id, stats['game_date'], stats['minutes'], stats['points'], stats['rebounds'], stats['assists']))
    conn.commit()
    conn.close()

def get_player_recent_stats(player_id, last_n=10):
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''SELECT minutes, points, rebounds, assists FROM game_logs WHERE player_id=? ORDER BY game_date DESC LIMIT ?''',
              (player_id, last_n))
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_players_by_date(days=7, ref_date=None):
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if ref_date is None:
        ref_date = datetime.datetime.now()
    else:
        ref_date = datetime.datetime.strptime(str(ref_date), '%Y-%m-%d')
    cutoff = (ref_date - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    c.execute('''SELECT DISTINCT player_id, name, team FROM players WHERE player_id IN (SELECT player_id FROM game_logs WHERE game_date >= ?)''', (cutoff,))
    players = c.fetchall()
    conn.close()
    return players
