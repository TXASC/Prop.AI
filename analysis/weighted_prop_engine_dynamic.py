
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import json
import logging
from datetime import date
from helpers.db_manager import get_recent_players_by_date
from config import OUTPUT_DIR, LOGS_DIR

HISTORICAL_ACCURACY_FILE = os.path.join(OUTPUT_DIR, "historical_accuracy.json")
MIN_EDGE = 0.05
DEFAULT_WEIGHTS = {
    "box_score": 0.25,
    "dfs": 0.25,
    "sharp_line": 0.25,
    "retail_line": 0.25
}
LOG_PATH = os.path.join(LOGS_DIR, "weighted_prop_engine.log")
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def load_accuracy():
    try:
        with open(HISTORICAL_ACCURACY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_WEIGHTS.copy()

def save_accuracy(accuracy_dict):
    with open(HISTORICAL_ACCURACY_FILE, "w") as f:
        json.dump(accuracy_dict, f, indent=2)

def compute_dynamic_weights(accuracy_dict):
    total = sum(accuracy_dict.values())
    if total == 0:
        return DEFAULT_WEIGHTS.copy()
    return {k: v/total for k, v in accuracy_dict.items()}

def update_accuracy(df_actual, df_pred, accuracy_dict):
    sources = ["box_score_proj", "dfs_proj", "sharp_line_implied", "retail_line_implied"]
    for src in sources:
        correct = ((df_pred[src] - df_actual["actual_stat"]).abs() < 0.05).sum()
        total = len(df_actual)
        accuracy_dict[src.split("_")[0]] = (accuracy_dict.get(src.split("_")[0], 0)*0.9) + (correct/total*0.1)
    return accuracy_dict

def weighted_prop_pipeline_dynamic():
    today = date.today()
    players = get_recent_players_by_date(7)  # Best practice: use last 7 days

    # Placeholder fetch functions (replace with real API calls)
    box_scores = pd.DataFrame([{'player_id': p[0], 'box_score_proj': 20.0} for p in players])
    dfs_proj = pd.DataFrame([{'player_id': p[0], 'dfs_proj': 19.5} for p in players])
    sharp_lines = pd.DataFrame([{'player_id': p[0], 'sharp_line_implied': 21.0, 'book_line': 21.0} for p in players])
    retail_lines = pd.DataFrame([{'player_id': p[0], 'retail_line_implied': 20.5} for p in players])

    df = pd.DataFrame([{'player_id': p[0], 'player_name': p[1], 'team': p[2]} for p in players])
    df = df.merge(box_scores, on="player_id", how="left")
    df = df.merge(dfs_proj, on="player_id", how="left")
    df = df.merge(sharp_lines, on="player_id", how="left")
    df = df.merge(retail_lines, on="player_id", how="left")

    historical_accuracy = load_accuracy()
    weights = compute_dynamic_weights(historical_accuracy)

    df["weighted_ev"] = (
        df["box_score_proj"] * weights["box_score"] +
        df["dfs_proj"] * weights["dfs"] +
        df["sharp_line_implied"] * weights["sharp_line"] +
        df["retail_line_implied"] * weights["retail_line"]
    )
    df["edge"] = df["weighted_ev"] - df["book_line"]
    df_filtered = df[df["edge"].abs() >= MIN_EDGE]

    from config import WEIGHTED_PROPS_CSV
    output_path = WEIGHTED_PROPS_CSV
    df_filtered.to_csv(output_path, index=False)
    logging.info(f"Generated {len(df_filtered)} props. CSV saved to {output_path}")

    # Debug printout
    print(f"[Weighted Prop Engine Dynamic] {len(df_filtered)} props processed for {today}.")
    print(df_filtered.nlargest(10, 'weighted_ev')[['player_name', 'stat', 'weighted_ev', 'edge']] if 'stat' in df_filtered.columns else df_filtered.nlargest(10, 'weighted_ev')[['player_name', 'weighted_ev', 'edge']])
    missing = df[df.isnull().any(axis=1)]
    if not missing.empty:
        print(f"Missing players/data flagged for review:\n{missing[['player_id', 'player_name']]}")
        logging.warning(f"Missing players/data: {missing[['player_id', 'player_name']].to_dict('records')}")

    # Post-game update (example, not run here)
    # df_actual = pd.DataFrame([...])
    # historical_accuracy = update_accuracy(df_actual, df_filtered, historical_accuracy)
    # save_accuracy(historical_accuracy)

    return df_filtered

if __name__ == "__main__":
    weighted_prop_pipeline_dynamic()
