import os
from datetime import datetime
from database.clv_tracking import get_clv_db_connection, log_clv_action

def update_closing_lines_for_unsettled_props():
    """
    Updates closing_line and closing_odds for unsettled props using latest snapshot before game start.
    Computes CLV. Logs all updates to logs/clv_tracking.log.
    """
    import logging
    from database.clv_tracking import get_latest_snapshot_before
    BATCH_SIZE = 20
    conn = get_clv_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, player_name, stat_type, date, line_at_pick, sportsbook, game_id
        FROM clv_prop_snapshots
        WHERE closing_line IS NULL OR closing_odds IS NULL
    """)
    rows = c.fetchall()
    if not rows:
        log_clv_action("No unsettled props found for CLV update.")
        conn.close()
        return

    updates = []
    for row in rows:
        prop_id, player_name, stat_type, date, line_at_pick, sportsbook, game_id = row
        # Assume game start time is available as commence_time in ISO format in a games table
        c2 = conn.cursor()
        c2.execute("SELECT commence_time FROM games WHERE game_id=?", (game_id,))
        game_row = c2.fetchone()
        if not game_row:
            log_clv_action(f"No game start time for {game_id} ({player_name} {stat_type})")
            continue
        game_start_time = game_row[0]
        now = datetime.utcnow().isoformat()
        if now > game_start_time:
            closing = get_latest_snapshot_before(game_id, player_name, stat_type, sportsbook, game_start_time)
            if closing and closing.get('closing_line') is not None:
                closing_line = closing['closing_line']
                closing_odds = closing.get('closing_odds')
                clv = closing_line - line_at_pick if closing_line is not None and line_at_pick is not None else None
                updates.append((closing_line, closing_odds, clv, prop_id))
                log_clv_action(f"Set closing line for {player_name} {stat_type} {date} (id={prop_id}): line={closing_line}, odds={closing_odds}, clv={clv}")
            else:
                log_clv_action(f"No closing snapshot for {player_name} {stat_type} {date} (id={prop_id})")
    if updates:
        c.executemany("""
            UPDATE clv_prop_snapshots
            SET closing_line=?, closing_odds=?, clv=?
            WHERE id=?
        """, updates)
        conn.commit()
    conn.close()
