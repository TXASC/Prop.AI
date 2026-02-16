import pandas as pd
from datetime import datetime
import os

def back_to_back():
    # For MVP, simulate fatigue by minutes played
    input_path = "data/processed/clean_player_stats.csv"
    output_path = "data/processed/fatigue_flags.csv"
    if not os.path.exists(input_path):
        print(f"Missing input file: {input_path}")
        return
    df = pd.read_csv(input_path)
    # Assume heavy minutes = fatigue risk
    df["fatigue_flag"] = df["MIN"].apply(lambda x: 1 if x > 34 else 0)
    df.to_csv(output_path, index=False)
    print(f"Fatigue flags saved to {output_path}")

if __name__ == "__main__":
    back_to_back()
