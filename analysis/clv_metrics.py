"""
clv_metrics.py

Provides CLV summary metrics for NBA prop bets.

Functions:
    compute_clv_summary(session):
        Computes CLV metrics from the clv_prop_snapshots table.
        Returns:
            dict with total bets, bets with closing lines, average CLV, CLV win rate, and EV bucket distribution (if EV exists).
"""
import pandas as pd
from database.clv_tracking import get_clv_db_connection

def compute_clv_summary(session=None):
    """
    Computes CLV summary metrics from the clv_prop_snapshots table.
    Args:
        session: (unused, for API compatibility)
    Returns:
        dict: summary metrics
    """
    conn = get_clv_db_connection()
    df = pd.read_sql_query("SELECT * FROM clv_prop_snapshots", conn)
    conn.close()
    total_bets = len(df)
    bets_with_closing = df['closing_line'].notnull().sum()
    avg_clv = df['clv'].mean() if bets_with_closing else None
    clv_win_rate = None
    if bets_with_closing:
        clv_win_rate = (df['clv'] > 0).mean()
    # EV bucket distribution
    ev_dist = None
    if 'expected_value' in df.columns:
        bins = [-float('inf'), 0, 0.05, 0.10, 0.20, float('inf')]
        labels = ['<=0', '0-5%', '5-10%', '10-20%', '>20%']
        df['ev_bucket'] = pd.cut(df['expected_value'].fillna(0), bins=bins, labels=labels)
        ev_dist = df['ev_bucket'].value_counts().to_dict()
    return {
        'total_bets': total_bets,
        'bets_with_closing_lines': bets_with_closing,
        'average_clv': avg_clv,
        'clv_win_rate': clv_win_rate,
        'ev_bucket_distribution': ev_dist
    }
