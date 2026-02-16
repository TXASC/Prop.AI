# CLV table initialization (called from pipeline)
def initialize_clv_tracking():
    from database.clv_tracking import initialize_clv_table
    initialize_clv_table()

import sqlite3
import os
from config import DB_PATH

def get_recent_players_by_date(days=7):
    import datetime
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    c.execute('''SELECT DISTINCT player_id, name, team FROM players WHERE player_id IN (SELECT player_id FROM game_logs WHERE game_date >= ?)''', (seven_days_ago,))
    players = c.fetchall()
    conn.close()
    return players

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
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
    c.execute('''CREATE TABLE IF NOT EXISTS dfs_projections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        projection_date TEXT,
        points REAL,
        assists REAL,
        rebounds REAL,
        pra REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS historical_odds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        odds_date TEXT,
        prop_type TEXT,
        line REAL,
        sportsbook TEXT
    )''')
    conn.commit()
    conn.close()

def save_player(player):
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO players (player_id, name, team) VALUES (?, ?, ?)''',
              (player['player_id'], player['player_name'], player['team']))
    conn.commit()
    conn.close()

def save_game_log(player_id, stats):
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO game_logs (player_id, game_date, minutes, points, rebounds, assists)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (player_id, stats['game_date'], stats['minutes'], stats['points'], stats['rebounds'], stats['assists']))
    conn.commit()
    conn.close()

def get_player_recent_stats(player_id, last_n=10):
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT minutes, points, rebounds, assists FROM game_logs WHERE player_id=? ORDER BY game_date DESC LIMIT ?''',
              (player_id, last_n))
    rows = c.fetchall()
    conn.close()
    return rows

# Robust JSON import with UTF-8 handling
def import_json_to_table(json_path, table_name, mapping_func):
    import json
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for record in data:
        values = mapping_func(record)
        placeholders = ','.join(['?'] * len(values))
        c.execute(f'INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})', values)
    conn.commit()
    conn.close()
