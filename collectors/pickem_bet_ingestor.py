"""
Pick'em Bet Ingestor

Ingests pick'em entries from PrizePicks, Underdog, and DraftKings Pick 6,
stores them in the pickem_bets table, and logs all actions.

Functions:
    ingest_pickem_entries(platform=None, start_date=None, end_date=None)
"""

import logging
import json
from datetime import datetime
from database.clv_tracking import insert_pickem_bet
import os

LOG_PATH = "logs/pickem_ingestor.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def ingest_pickem_entries(platform=None, start_date=None, end_date=None):
    """
    Ingest pick'em entries from supported platforms and store in DB.
    Args:
        platform (str): Optional platform filter.
        start_date (str): Optional start date (YYYY-MM-DD).
        end_date (str): Optional end date (YYYY-MM-DD).
    """
    # Placeholder: Replace with real API or file ingestion logic
    sources = [
        ("PrizePicks", "data/raw/prizepicks_entries.json"),
        ("Underdog", "data/raw/underdog_entries.json"),
        ("DraftKings", "data/raw/draftkings_entries.json"),
    ]
    for plat, path in sources:
        if platform and plat.lower() != platform.lower():
            continue
        if not os.path.exists(path):
            logging.warning(f"Source not found: {path}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            for entry in entries:
                entry_id = entry.get("entry_id")
                user_id = entry.get("user_id")
                bet_type = entry.get("bet_type")
                legs_count = entry.get("legs_count")
                total_entry_amount = entry.get("total_entry_amount")
                potential_payout = entry.get("potential_payout")
                status = entry.get("status", "pending")
                bet_timestamp = entry.get("bet_timestamp", datetime.utcnow().isoformat())
                projected_lines = json.dumps(entry.get("projected_lines", {}))
                closing_lines = None
                resolved_timestamp = entry.get("resolved_timestamp")
                raw_data = json.dumps(entry)
                insert_pickem_bet(
                    plat, entry_id, user_id, bet_type, legs_count, total_entry_amount,
                    potential_payout, status, bet_timestamp, projected_lines, closing_lines,
                    resolved_timestamp, raw_data
                )
                logging.info(f"Ingested {plat} entry {entry_id} at {bet_timestamp}")
        except Exception as e:
            logging.error(f"Failed to ingest {plat} entries: {e}")
