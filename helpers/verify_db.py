import os
import sqlite3

def verify_db_tables(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check players table
    c.execute('SELECT COUNT(*) FROM players')
    player_count = c.fetchone()[0]
    # Check game_logs table
    c.execute('SELECT COUNT(*) FROM game_logs')
    log_count = c.fetchone()[0]
    # Check distinct seasons
    c.execute('SELECT MIN(game_date), MAX(game_date) FROM game_logs')
    min_date, max_date = c.fetchone()
    conn.close()
    print(f"Players table: {player_count} records")
    print(f"Game logs table: {log_count} records")
    print(f"Game logs date range: {min_date} to {max_date}")
    return player_count, log_count, min_date, max_date

if __name__ == '__main__':
    db_path = os.path.join(os.path.dirname(__file__), 'player_history.db')
    verify_db_tables(db_path)
