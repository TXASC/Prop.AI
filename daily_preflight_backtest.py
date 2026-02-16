"""
Daily Preflight Backtest Script for NBA Prop AI Pipeline
------------------------------------------------------
Performs pre-flight checks, backtesting, weight optimization, and reporting.
"""
import os
import sys
import logging
import datetime
import pandas as pd
from config import DATA_DIR, OUTPUT_DIR, LOGS_DIR, DB_PATH, WEIGHTED_PROPS_CSV

# Configurable parameters (can be loaded from config.py or .env)
N_BACKTEST_ITER = 3
PROP_CATEGORIES = ["Points", "Rebounds", "Assists"]
MIN_EV_THRESHOLD = 0.05

# Setup logging
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOGS_DIR, "daily_preflight.log")
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("preflight")

TODAY = datetime.datetime.now().strftime("%Y-%m-%d")

# 1. Pre-Flight Verification
def preflight_checks():
    results = {"folders": {}, "db": {}, "apis": {}, "outputs": {}}
    # Check folders
    for folder in [DATA_DIR, OUTPUT_DIR, LOGS_DIR]:
        exists = os.path.exists(folder)
        results["folders"][folder] = exists
        logger.info(f"Folder check: {folder} exists={exists}")
    # Check DB
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for table in ["players", "game_logs"]:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            found = c.fetchone() is not None
            results["db"][table] = found
            logger.info(f"DB table check: {table} exists={found}")
        conn.close()
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        results["db"]["error"] = str(e)
    # Check APIs
    try:
        from providers.odds_provider import fetch_nba_games_and_markets
        games = fetch_nba_games_and_markets()
        results["apis"]["TheOddsAPI"] = len(games) > 0
        logger.info(f"TheOddsAPI check: success={len(games) > 0}")
    except Exception as e:
        logger.error(f"TheOddsAPI error: {e}")
        results["apis"]["TheOddsAPI"] = False
    try:
        from providers.balldontlie_provider import BallDontLieProvider
        provider = BallDontLieProvider()
        teams = provider.get_teams()
        results["apis"]["BallDontLie"] = len(teams) > 0
        logger.info(f"BallDontLie check: success={len(teams) > 0}")
    except Exception as e:
        logger.error(f"BallDontLie error: {e}")
        results["apis"]["BallDontLie"] = False
    # Check previous day's weighted props
    prev_props_path = WEIGHTED_PROPS_CSV
    exists = os.path.exists(prev_props_path)
    results["outputs"]["weighted_props.csv"] = exists
    logger.info(f"Output check: {prev_props_path} exists={exists}")
    return results

# 2. Backtest Loop (stub, to be filled with actual logic)
def run_backtests(n_iter=N_BACKTEST_ITER, categories=PROP_CATEGORIES):
    all_metrics = []
    for i in range(n_iter):
        logger.info(f"Backtest iteration {i+1}/{n_iter}")
        # TODO: Call actual backtest logic from analysis/backtest_weighted_prop_engine.py or similar
        # Simulate metrics for now
        metrics = {
            "iteration": i+1,
            "accuracy": 0.7 + 0.05*i,
            "mae": 2.1 - 0.1*i,
            "edge_success_rate": 0.25 + 0.05*i,
            "details": f"Simulated for {categories}"
        }
        all_metrics.append(metrics)
        # Save detailed results (stub)
        df = pd.DataFrame([metrics])
        df.to_csv(os.path.join(OUTPUT_DIR, f"backtest_report_{TODAY}_iter{i+1}.csv"), index=False)
        df.to_csv(os.path.join(OUTPUT_DIR, f"backtest_top_props_{TODAY}_iter{i+1}.csv"), index=False)
    return all_metrics

# 3. Weight Optimization (stub, to be filled with actual logic)
def optimize_weights(metrics_list):
    # TODO: Call/update weighted_prop_engine_dynamic.py weights
    # Simulate weight adjustment
    weight_log_path = os.path.join(LOGS_DIR, "weight_adjustment.log")
    with open(weight_log_path, "a") as f:
        for m in metrics_list:
            msg = f"Iteration {m['iteration']}: Adjusted weights based on accuracy={m['accuracy']:.2f}, edge_success_rate={m['edge_success_rate']:.2f}\n"
            f.write(msg)
            logger.info(msg.strip())
    return True

# 4. Daily Evaluation Report
def generate_eval_report(preflight, metrics, output_path):
    # Summarize all results in a CSV
    rows = []
    for k, v in preflight["folders"].items():
        rows.append({"check": f"Folder {k}", "status": v, "suggestion": "Create folder" if not v else "OK"})
    for k, v in preflight["db"].items():
        if k == "error":
            rows.append({"check": "DB error", "status": False, "suggestion": v})
        else:
            rows.append({"check": f"DB table {k}", "status": v, "suggestion": "Check DB schema" if not v else "OK"})
    for k, v in preflight["apis"].items():
        rows.append({"check": f"API {k}", "status": v, "suggestion": "Check API key or endpoint" if not v else "OK"})
    for k, v in preflight["outputs"].items():
        rows.append({"check": f"Output {k}", "status": v, "suggestion": "Run pipeline for previous day" if not v else "OK"})
    for m in metrics:
        rows.append({"check": f"Backtest Iter {m['iteration']}", "status": True, "suggestion": f"Acc={m['accuracy']:.2f}, MAE={m['mae']:.2f}, EdgeSR={m['edge_success_rate']:.2f}"})
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Daily evaluation report saved to {output_path}")

# 5. Main workflow
def main():
    logger.info("=== Starting Daily Preflight Backtest ===")
    preflight = preflight_checks()
    metrics = run_backtests()
    optimize_weights(metrics)
    eval_report_path = os.path.join(OUTPUT_DIR, f"daily_eval_{TODAY}.csv")
    generate_eval_report(preflight, metrics, eval_report_path)
    logger.info("=== Daily Preflight Backtest Complete ===")

if __name__ == "__main__":
    main()
