def initialize_suggested_parlays_table():
    """
    Create the suggested_parlays table for storing generated parlay suggestions.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS suggested_parlays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        generated_date TEXT,
        legs TEXT,
        predicted_hit_probability REAL,
        projected_payout REAL,
        notes TEXT,
        status TEXT
    );
    """)
    conn.commit()
    conn.close()

def insert_suggested_parlay(platform, generated_date, legs, predicted_hit_probability, projected_payout, notes, status):
    """
    Insert a suggested parlay row.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO suggested_parlays (
        platform, generated_date, legs, predicted_hit_probability, projected_payout, notes, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (platform, generated_date, legs, predicted_hit_probability, projected_payout, notes, status))
    conn.commit()
    conn.close()
def initialize_prop_correlations_table():
    """
    Create the prop_correlations table for storing rolling correlations.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS prop_correlations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player1_id TEXT,
        player2_id TEXT,
        stat1 TEXT,
        stat2 TEXT,
        correlation_coefficient REAL,
        sample_size INTEGER,
        last_updated TEXT
    );
    """)
    conn.commit()
    conn.close()

def upsert_prop_correlation(player1_id, player2_id, stat1, stat2, corr, sample_size, last_updated):
    """
    Insert or update a prop correlation row.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO prop_correlations
        (player1_id, player2_id, stat1, stat2, correlation_coefficient, sample_size, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(player1_id, player2_id, stat1, stat2)
    DO UPDATE SET
        correlation_coefficient=excluded.correlation_coefficient,
        sample_size=excluded.sample_size,
        last_updated=excluded.last_updated
    """, (player1_id, player2_id, stat1, stat2, corr, sample_size, last_updated))
    conn.commit()
    conn.close()
def initialize_pickem_bets_table():
    """
    Create the pickem_bets table for storing pick'em entries.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS pickem_bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        entry_id TEXT UNIQUE NOT NULL,
        user_id TEXT,
        bet_type TEXT,
        legs_count INTEGER,
        total_entry_amount REAL,
        potential_payout REAL,
        status TEXT,
        bet_timestamp TEXT,
        projected_lines TEXT,
        closing_lines TEXT,
        resolved_timestamp TEXT,
        raw_data TEXT
    );
    """)
    conn.commit()
    conn.close()

def insert_pickem_bet(
    platform, entry_id, user_id, bet_type, legs_count, total_entry_amount,
    potential_payout, status, bet_timestamp, projected_lines, closing_lines,
    resolved_timestamp, raw_data
):
    """
    Insert a pick'em bet entry. Ignores duplicates based on entry_id.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
        INSERT OR IGNORE INTO pickem_bets (
            platform, entry_id, user_id, bet_type, legs_count, total_entry_amount,
            potential_payout, status, bet_timestamp, projected_lines, closing_lines,
            resolved_timestamp, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            platform, entry_id, user_id, bet_type, legs_count, total_entry_amount,
            potential_payout, status, bet_timestamp, projected_lines, closing_lines,
            resolved_timestamp, raw_data
        ))
        conn.commit()
    finally:
        conn.close()
def initialize_closing_line_snapshot_table():
    """
    Create table for timestamped odds snapshots if not exists.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS closing_line_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_date TEXT,
        game_id TEXT,
        player_name TEXT,
        stat_type TEXT,
        sportsbook TEXT,
        line REAL,
        odds REAL,
        timestamp_collected TEXT
    );
    """
    )
    conn.commit()
    conn.close()

def insert_closing_line_snapshot(game_date, game_id, player_name, stat_type, sportsbook, line, odds, timestamp_collected):
    """
    Insert a new odds snapshot row.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO closing_line_snapshots (
        game_date, game_id, player_name, stat_type, sportsbook, line, odds, timestamp_collected
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (game_date, game_id, player_name, stat_type, sportsbook, line, odds, timestamp_collected))
    conn.commit()
    conn.close()

def get_latest_snapshot_before(game_id, player_name, stat_type, sportsbook, game_start_time):
    """
    Get the latest odds snapshot before game start.
    """
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    SELECT line, odds FROM closing_line_snapshots
    WHERE game_id=? AND player_name=? AND stat_type=? AND sportsbook=?
      AND timestamp_collected <= ?
    ORDER BY timestamp_collected DESC LIMIT 1
    """, (game_id, player_name, stat_type, sportsbook, game_start_time))
    row = c.fetchone()
    conn.close()
    if row:
        return {'closing_line': row[0], 'closing_odds': row[1]}
    return None
import os
import sqlite3
from datetime import datetime

CLV_DB_PATH = os.path.join(os.path.dirname(__file__), "clv_tracking.db")
CLV_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "clv_tracking.log")

def get_clv_db_connection():
    conn = sqlite3.connect(CLV_DB_PATH)
    return conn

def initialize_clv_table():
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS clv_prop_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        player_name TEXT NOT NULL,
        stat_type TEXT NOT NULL,
        sportsbook TEXT NOT NULL,
        line_at_pick REAL NOT NULL,
        odds_at_pick REAL NOT NULL,
        timestamp_at_pick TEXT NOT NULL,
        projected_value REAL,
        expected_value REAL,
        closing_line REAL,
        closing_odds REAL,
        result TEXT,
        clv REAL
    );
    """)
    conn.commit()
    conn.close()
    log_clv_action("Initialized clv_prop_snapshots table.")

def insert_clv_snapshot(
    date, player_name, stat_type, sportsbook, line_at_pick, odds_at_pick,
    timestamp_at_pick, projected_value, expected_value,
    closing_line=None, closing_odds=None, result=None, clv=None
):
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO clv_prop_snapshots (
        date, player_name, stat_type, sportsbook, line_at_pick, odds_at_pick,
        timestamp_at_pick, projected_value, expected_value,
        closing_line, closing_odds, result, clv
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        date, player_name, stat_type, sportsbook, line_at_pick, odds_at_pick,
        timestamp_at_pick, projected_value, expected_value,
        closing_line, closing_odds, result, clv
    ))
    conn.commit()
    conn.close()
    log_clv_action(f"Inserted CLV snapshot for {player_name} {stat_type} on {date}.")

def log_clv_action(message):
    os.makedirs(os.path.dirname(CLV_LOG_PATH), exist_ok=True)
    with open(CLV_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {message}\n")
