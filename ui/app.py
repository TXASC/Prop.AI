"""
NBA Pick'em Analytics Streamlit UI
Premium, color-coded, interactive dashboard for suggested parlays, CLV, and correlation insights.
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

# =========================
# COLOR PALETTE & STYLES
# =========================
COLOR_HIGH = '#2ecc40'   # Green
COLOR_MED = '#ffeb3b'    # Yellow
COLOR_LOW = '#ff4136'    # Red
COLOR_BG = '#f7f7f7'
COLOR_HEADER = '#1e90ff'
ICON_RECOMMENDED = '⭐'

st.set_page_config(page_title="NBA Pick'em Analytics", layout="wide", page_icon="🏀")
st.markdown(f"""
    <style>
        .high-row {{ background-color: {COLOR_HIGH}33; }}
        .med-row {{ background-color: {COLOR_MED}33; }}
        .low-row {{ background-color: {COLOR_LOW}33; }}
        .header {{ color: {COLOR_HEADER}; font-size: 2em; font-weight: bold; }}
        .stat-badge {{ font-size: 1.2em; padding: 0.2em 0.6em; border-radius: 8px; background: {COLOR_HEADER}22; }}
    </style>
""", unsafe_allow_html=True)

# =========================
# LOGGING
# =========================
def log_ui_action(action):
    """Log UI actions to logs/ui.log."""
    log_path = os.path.join(os.path.dirname(__file__), '../logs/ui.log')
    with open(log_path, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] {action}\n")

# =========================
# DATABASE HELPERS
# =========================
def get_db_connection():
    """Return SQLite connection, fallback if DB missing."""
    db_path = os.path.join(os.path.dirname(__file__), '../database/prop_ai.db')
    if not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path)

def fetch_table(table_name):
    """Fetch table as DataFrame, fallback to empty."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# =========================
# HEADER & QUICK STATS
# =========================
def render_header():
    """Render project header and quick stats."""
    st.markdown('<div class="header">NBA Pick\'em Analytics Dashboard 🏀</div>', unsafe_allow_html=True)
    last_run = get_last_pipeline_run()
    st.write(f"Last pipeline run: {last_run}")
    quick_stats = get_quick_stats()
    st.markdown(f"<span class='stat-badge'>Total Parlays: {quick_stats['parlays']}</span> "
                f"<span class='stat-badge'>Total Bets: {quick_stats['bets']}</span> "
                f"<span class='stat-badge'>Total CLV: {quick_stats['clv']:.2f}</span>", unsafe_allow_html=True)

# =========================
# FILTERS
# =========================
def render_filters():
    """Render interactive filters for platform, max legs, CLV threshold."""
    platforms = ['PrizePicks', 'Underdog', 'DraftKings']
    platform = st.selectbox('Platform', platforms)
    max_legs = st.slider('Max Legs', 2, 6, 5)
    clv_threshold = st.slider('CLV Threshold', -10.0, 50.0, 0.0)
    log_ui_action(f"Filter: platform={platform}, max_legs={max_legs}, clv_threshold={clv_threshold}")
    return platform, max_legs, clv_threshold

# =========================
# SUGGESTED PARLAYS TABLE
# =========================
def render_suggested_parlays(platform, max_legs, clv_threshold):
    """Display suggested parlays with color-coding and expandable details."""
    df = fetch_table('suggested_parlays')
    if df.empty:
        st.info("No suggested parlays available.")
        return
    df = df[df['platform'] == platform]
    df = df[df['legs'] <= max_legs]
    df = df[df['CLV'] >= clv_threshold]
    if df.empty:
        st.warning("No parlays match your filters.")
        return
    for idx, row in df.iterrows():
        color = COLOR_HIGH if row['joint_probability'] >= 0.7 and row['CLV'] >= 10 else \
                COLOR_MED if row['joint_probability'] >= 0.5 and row['CLV'] >= 0 else COLOR_LOW
        icon = ICON_RECOMMENDED if row['joint_probability'] >= 0.7 and row['CLV'] >= 10 else ''
        with st.expander(f"{icon} {row['platform']} | {row['legs']} legs | Payout: ${row['projected_payout']} | Prob: {row['joint_probability']:.2f} | CLV: {row['CLV']:.2f}", expanded=False):
            st.markdown(f"<div style='background:{color}33;padding:8px;border-radius:8px;'>"
                        f"<b>Notes:</b> {row.get('notes','')}", unsafe_allow_html=True)
            if 'legs_detail' in row:
                for leg in row['legs_detail']:
                    st.write(f"- {leg['player']} ({leg['prop']}): Line {leg['line']}, Projection {leg['projection']}")

# =========================
# CLV SUMMARY PANEL
# =========================
def render_clv_summary():
    """Show CLV summary, bets, ROI, and chart."""
    df = fetch_table('clv_prop_snapshots')
    if df.empty:
        st.info("No CLV data available.")
        return
    total_clv = df['clv'].sum()
    total_bets = len(df)
    roi = total_clv / total_bets if total_bets else 0
    st.subheader("CLV Summary")
    st.write(f"Total CLV: {total_clv:.2f}")
    st.write(f"Total Bets: {total_bets}")
    st.write(f"ROI Estimate: {roi:.2f}")
    # Chart
    clv_over_time = df.groupby('date')['clv'].sum().reset_index()
    fig, ax = plt.subplots()
    ax.plot(clv_over_time['date'], clv_over_time['clv'], color=COLOR_HEADER)
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative CLV')
    ax.set_title('CLV Over Time')
    st.pyplot(fig)

# =========================
# CORRELATION INSIGHTS
# =========================
def render_correlation_insights():
    """Show top positive correlations affecting parlays."""
    df = fetch_table('prop_correlations')
    if df.empty:
        st.info("No correlation data available.")
        return
    st.subheader("Correlation Insights")
    top_corrs = df.sort_values('corr', ascending=False).head(10)
    with st.expander("Top Positive Correlations", expanded=False):
        for idx, row in top_corrs.iterrows():
            st.write(f"{row['player1_id']} ({row['stat1']}) ↔ {row['player2_id']} ({row['stat2']}): Corr = {row['corr']:.2f}, Sample = {row['sample_size']}")

# =========================
# QUICK STATS & UTILS
# =========================
def get_last_pipeline_run():
    """Get last pipeline run timestamp from logs."""
    log_path = os.path.join(os.path.dirname(__file__), '../logs/pipeline.log')
    if not os.path.exists(log_path):
        return 'Never'
    with open(log_path, 'r') as f:
        lines = f.readlines()
        for line in reversed(lines):
            if 'Starting Daily NBA Player Prop Pipeline' in line:
                return line.split(' ')[0]
    return 'Unknown'

def get_quick_stats():
    """Return quick stats for header."""
    df_parlays = fetch_table('suggested_parlays')
    df_bets = fetch_table('pickem_bets')
    df_clv = fetch_table('clv_prop_snapshots')
    return {
        'parlays': len(df_parlays),
        'bets': len(df_bets),
        'clv': df_clv['clv'].sum() if not df_clv.empty else 0.0
    }

# =========================
# MAIN APP
# =========================
def main():
    """Main Streamlit app entry point."""
    render_header()
    st.sidebar.title("Filters")
    platform, max_legs, clv_threshold = render_filters()
    st.sidebar.button("Refresh", on_click=lambda: log_ui_action("Refresh pressed"))
    st.sidebar.checkbox("Show Historical Bets", value=False)
    st.markdown("---")
    render_suggested_parlays(platform, max_legs, clv_threshold)
    st.markdown("---")
    render_clv_summary()
    st.markdown("---")
    render_correlation_insights()

if __name__ == '__main__':
    main()
