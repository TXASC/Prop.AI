"""
closing_lines_provider.py

Provides closing line and odds data for NBA props. Structured for future real API integration.

Functions:
    get_closing_line(date, player_name, stat_type, sportsbook=None):
        Retrieve the closing line and odds for a given prop. Currently uses a MOCK implementation.
        - Attempts to read from available historical odds/props data in the project.
        - Returns None if data is unavailable, with clear logging.
        - Does NOT break runtime if data is missing.

Future:
    Replace MOCK with real sportsbook API integration.
"""
import logging
import os
import pandas as pd
from datetime import datetime

# Setup logger
LOG_PATH = os.path.join('logs', 'clv_tracking.log')
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def get_closing_line(date, player_name, stat_type, sportsbook=None):
    """
    Retrieve the closing line and odds for a given prop.
    MOCK implementation: Reads from available historical odds/props data or returns None.

    Args:
        date (str): Date in 'YYYY-MM-DD' format
        player_name (str): Player's full name
        stat_type (str): Stat type (e.g., 'PTS', 'REB')
        sportsbook (str, optional): Sportsbook name

    Returns:
        dict or None: {'closing_line': float, 'closing_odds': float/int} or None if unavailable
    """
    # MOCK: Try to read from data/processed/today_props_ai.csv or data/raw/today_props.csv
    possible_files = [
        os.path.join('data', 'processed', 'today_props_ai.csv'),
        os.path.join('data', 'raw', 'today_props.csv')
    ]
    for file in possible_files:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                # Try to match by date, player, stat_type
                mask = (
                    (df.get('date', date) == date) &
                    (df.get('player', player_name) == player_name) &
                    (df.get('stat_type', stat_type) == stat_type)
                )
                if sportsbook:
                    mask &= (df.get('sportsbook', sportsbook) == sportsbook)
                row = df[mask]
                if not row.empty:
                    closing_line = row.iloc[0].get('line')
                    closing_odds = row.iloc[0].get('odds', None)
                    return {'closing_line': closing_line, 'closing_odds': closing_odds}
            except Exception as e:
                logging.warning(f"Error reading {file}: {e}")
    logging.info(f"No closing line found for {date}, {player_name}, {stat_type}, {sportsbook}")
    return None
