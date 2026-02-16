import sys
from pathlib import Path

if ".venv" not in str(sys.executable).lower():
    raise RuntimeError(
        f"Weekly digest must be executed with .venv Python. "
        f"Current interpreter: {sys.executable}"
    )
import sys
import importlib.util
from pathlib import Path
import sqlite3
import datetime
import json
import os

def bootstrap_repo():
    repo_root = Path(__file__).resolve().parents[1]
    bootstrap_path = repo_root / "scripts" / "bootstrap.py"
    spec = importlib.util.spec_from_file_location("bootstrap", bootstrap_path)
    if spec and spec.loader:
        bootstrap = importlib.util.module_from_spec(spec)
        sys.modules["bootstrap"] = bootstrap
        spec.loader.exec_module(bootstrap)
        return repo_root, bootstrap.get_repo_root
    else:
        raise ImportError(f"Could not import bootstrap from {bootstrap_path}")

repo_root, get_repo_root = bootstrap_repo()
import config

def get_job_runs(db_path):
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT started_at, status, mode, reason, notes FROM job_runs WHERE started_at >= ? ORDER BY started_at DESC
        """, (since,))
        return c.fetchall()

def get_credits_by_day(db_path):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT date, credits_used FROM odds_credit_ledger ORDER BY date DESC LIMIT 7")
        return c.fetchall()

def get_latest_odds_cache(db_path):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT MAX(fetched_at) FROM odds_api_cache")
        row = c.fetchone()
        return row[0] if row else None

def get_latest_file_timestamp(path):
    if os.path.exists(path):
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
    return None

def get_top_picks(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                picks = json.load(f)
                if isinstance(picks, list):
                    return picks[:10]
                elif isinstance(picks, dict) and 'picks' in picks:
                    return picks['picks'][:10]
            except Exception:
                return []
    return []

def find_budget_stops(log_path):
    if not os.path.exists(log_path):
        return []
    stops = []
    with open(log_path, 'r') as f:
        for line in f:
            if 'daily budget' in line.lower():
                stops.append(line.strip())
    return stops[-10:]

def main():
    db_path = config.DB_PATH
    output_path = repo_root / 'output' / 'weekly_digest.md'
    log_path = repo_root / 'logs' / 'training_runner.log'
    backtest_path = repo_root / 'output' / 'backtest_report_current_season.csv'
    picks_path = repo_root / 'output' / 'daily_picks.json'

    runs = get_job_runs(db_path)
    credits = get_credits_by_day(db_path)
    latest_odds = get_latest_odds_cache(db_path)
    latest_backtest = get_latest_file_timestamp(backtest_path)
    top_picks = get_top_picks(picks_path)
    budget_stops = find_budget_stops(log_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# Weekly Digest\n\n')
        f.write('## Run Summary (last 7 days)\n')
        f.write(f'- Total runs: {len(runs)}\n')
        f.write(f'- Success: {sum(1 for r in runs if r[1]=="SUCCESS")}\n')
        f.write(f'- Fail: {sum(1 for r in runs if r[1]=="FAIL")}\n')
        f.write('\n')
        f.write('## Credits Used by Day\n')
        for date, credits_used in credits:
            f.write(f'- {date}: {credits_used} credits\n')
        f.write('\n')
        f.write(f'## Latest Odds Cache Timestamp\n- {latest_odds}\n\n')
        f.write(f'## Latest Backtest File Timestamp\n- {latest_backtest}\n\n')
        f.write('## Top 10 Most Recent Picks\n')
        for pick in top_picks:
            f.write(f'- {pick}\n')
        f.write('\n')
        f.write('## Budget Stop Events (last 10)\n')
        for stop in budget_stops:
            f.write(f'- {stop}\n')
    print(f"Weekly digest written to {output_path}")

if __name__ == "__main__":
    main()
