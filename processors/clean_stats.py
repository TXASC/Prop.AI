
import pandas as pd
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR


def clean_stats():
    import glob
    import os
    # Find the latest stats CSV file
    files = glob.glob(os.path.join(RAW_DATA_DIR, "nba_player_stats_*.csv"))
    if not files:
        print("No raw stats CSV found.")
        return
    latest_file = max(files, key=os.path.getctime)
    df = pd.read_csv(latest_file)

    # Map SportsData.io columns to expected names
    col_map = {
        'Name': 'PLAYER_NAME',
        'Team': 'TEAM_ABBREVIATION',
        'Minutes': 'MIN',
        'Points': 'PTS',
        'Rebounds': 'REB',
        'Assists': 'AST',
    }
    # Some columns may be missing, so check and rename only those present
    for src, dst in col_map.items():
        if src in df.columns:
            df.rename(columns={src: dst}, inplace=True)

    # Use only available columns
    needed = ['PLAYER_NAME','TEAM_ABBREVIATION','MIN','PTS','REB','AST']
    missing = [c for c in needed if c not in df.columns]
    if missing:
        print(f"Missing columns in raw data: {missing}")
        return
    df = df[needed]
    df['PRA'] = df['PTS'] + df['REB'] + df['AST']
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    output_path = os.path.join(PROCESSED_DATA_DIR, "clean_player_stats.csv")
    df.to_csv(output_path, index=False)

if __name__ == "__main__":
    clean_stats()
