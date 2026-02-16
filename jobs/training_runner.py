
import sys
import os
import importlib.util
import logging
import sqlite3
import uuid
import datetime
from pathlib import Path
import argparse
import traceback

# Ensure project root is in sys.path for config import
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

# === Helper 1: Bootstrap repo root ===
def bootstrap_repo_root():
    repo_root = Path(__file__).resolve().parents[1]
    bootstrap_path = repo_root / "scripts" / "bootstrap.py"
    spec = importlib.util.spec_from_file_location("bootstrap", bootstrap_path)
    if spec and spec.loader:
        bootstrap = importlib.util.module_from_spec(spec)
        sys.modules["bootstrap"] = bootstrap
        spec.loader.exec_module(bootstrap)
        return repo_root
    else:
        raise ImportError(f"Could not import bootstrap from {bootstrap_path}")

# === Helper 2: Ensure .venv interpreter ===
def ensure_venv():
    if ".venv" not in str(sys.executable).lower():
        raise RuntimeError(f"Training runner must be executed with .venv Python. Current interpreter: {sys.executable}")

# === Helper 3: Setup logging ===
def setup_logging(log_path):
    logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# === Helper 4: Get DB connection ===
def get_db_conn():
    return sqlite3.connect(config.DB_PATH)

# === Helper 5: Init runs table ===
def init_runs_table():
    with get_db_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS training_runs (
                run_id TEXT PRIMARY KEY,
                started_utc TEXT,
                finished_utc TEXT,
                mode TEXT,
                reason TEXT,
                status TEXT,
                notes TEXT
            )
            """
        )
        conn.commit()

# === Helper 6: Record run ===
def record_run(run_id, started_utc, finished_utc, mode, reason, status, notes):
    with get_db_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO training_runs (run_id, started_utc, finished_utc, mode, reason, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, started_utc, finished_utc, mode, reason, status, notes)
        )
        conn.commit()

# === Helper 7: Read last run for cooldown ===
def read_last_run_for_cooldown(mode, reason):
    with get_db_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT run_id, started_utc, finished_utc, status, reason FROM training_runs
            WHERE mode=? AND status='SUCCESS' AND reason=?
            ORDER BY started_utc DESC LIMIT 1
            """,
            (mode, reason)
        )
        return c.fetchone()

# === Helper 8: Write FAST artifact ===
def write_fast_artifact(out_path, status, run_id, reason, mode, notes):
    import json
    out = {
        "status": status,
        "run_id": run_id,
        "reason": reason,
        "mode": mode,
        "timestamp_utc": datetime.datetime.utcnow().isoformat(),
        "notes": notes
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

# === Main ===
def main():
    repo_root = bootstrap_repo_root()
    ensure_venv()
    logs_dir = getattr(config, 'LOGS_DIR', str(repo_root / 'logs'))
    output_dir = getattr(config, 'OUTPUT_DIR', str(repo_root / 'output'))
    log_path = os.path.join(logs_dir, "training_runner.log")
    setup_logging(log_path)
    init_runs_table()

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='train', choices=['train', 'backtest', 'smoke'])
    parser.add_argument('--fast', action='store_true')
    parser.add_argument('--reason', default='scheduled_daily_fast')
    args = parser.parse_args()

    COOLDOWN_MINUTES = getattr(config, 'COOLDOWN_MINUTES', 45)
    budget_flag_path = os.path.join(output_dir, "budget_stop.flag")
    fast_artifact_path = os.path.join(output_dir, "fast_top_edges.json")

    run_id = str(uuid.uuid4())
    started_utc = datetime.datetime.utcnow().isoformat()
    mode = args.mode
    reason = args.reason
    status = "SUCCESS"
    notes = ""

    # Budget kill-switch
    if os.path.exists(budget_flag_path):
        status = "BUDGET_STOP"
        notes = "Budget stop flag present."
        write_fast_artifact(fast_artifact_path, status, run_id, reason, mode, notes)
        record_run(run_id, started_utc, started_utc, mode, reason, status, notes)
        logging.warning(notes)
        print(notes)
        return

    # Cooldown gate
    last_run = read_last_run_for_cooldown(mode, reason)
    if last_run:
        last_finished = last_run[2]
        if last_finished:
            last_dt = datetime.datetime.fromisoformat(last_finished)
            now_dt = datetime.datetime.utcnow()
            delta = (now_dt - last_dt).total_seconds() / 60.0
            if delta < COOLDOWN_MINUTES:
                status = "COOLDOWN_SKIP"
                notes = f"Cooldown: last run {delta:.1f} min ago. Skipping."
                write_fast_artifact(fast_artifact_path, status, run_id, reason, mode, notes)
                record_run(run_id, started_utc, started_utc, mode, reason, status, notes)
                logging.info(notes)
                print(notes)
                return

    # Run pipeline
    try:
        if args.fast:
            os.environ["FAST_MODE"] = "1"
            import daily_pipeline
            if hasattr(daily_pipeline, 'run_daily_pipeline'):
                daily_pipeline.run_daily_pipeline(reason=reason)
                notes = 'FAST: ran daily_pipeline.run_daily_pipeline with FAST_MODE'
            else:
                raise ImportError('No run_daily_pipeline in daily_pipeline')
        else:
            import daily_pipeline
            if hasattr(daily_pipeline, 'run_daily_pipeline'):
                daily_pipeline.run_daily_pipeline(reason=reason)
                notes = 'ran daily_pipeline.run_daily_pipeline'
            else:
                raise ImportError('No run_daily_pipeline in daily_pipeline')
    except Exception as exc:
        status = 'FAIL'
        notes = f'Exception: {exc}\n{traceback.format_exc()}'
        logging.error(notes)
    finished_utc = datetime.datetime.utcnow().isoformat()
    write_fast_artifact(fast_artifact_path, status, run_id, reason, mode, notes)
    record_run(run_id, started_utc, finished_utc, mode, reason, status, notes)
    logging.info(f"Run {run_id} finished with status {status}. Notes: {notes}")
    print(f"Run {run_id} finished with status {status}. Notes: {notes}")

if __name__ == "__main__":
    main()
