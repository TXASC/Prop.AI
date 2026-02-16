import subprocess
import time
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "logs" / "training_runner.log"
FAST_JSON_PATH = REPO_ROOT / "output" / "fast_top_edges.json"
DB_PATH = REPO_ROOT / "database" / "prop_ai.db"
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
PS_FAST_RUNNER = REPO_ROOT / "scripts" / "run_training_mode_fast.ps1"

results = []
credits = []

for i in range(2):
    print(f"\n--- FAST RUN {i+1} ---")
    # Run the FAST mode runner
    subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass", "-File", str(PS_FAST_RUNNER)
    ], check=True)
    # Wait 20 seconds between runs
    if i == 0:
        time.sleep(20)
    # Print last 25 lines of log
    print("\nLast 25 lines of training_runner.log:")
    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(LOG_PATH, "r", encoding="latin-1", errors="replace") as f:
            lines = f.readlines()
    for line in lines[-25:]:
        print(line.strip())
    # Print contents of fast_top_edges.json
    print("\nContents of fast_top_edges.json:")
    with open(FAST_JSON_PATH, "r", encoding="utf-8") as f:
        fast_json = json.load(f)
        print(json.dumps(fast_json, indent=2))
        results.append(fast_json["status"])
    # Parse credits_used_today from DB
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT credits_used FROM odds_credit_ledger ORDER BY date DESC LIMIT 1")
        row = c.fetchone()
        credits.append(row[0] if row else None)

# Assertions
print("\n--- VERIFICATION ---")
run1_status = results[0]
run2_status = results[1]
print(f"Run 1 status: {run1_status}")
print(f"Run 2 status: {run2_status}")
assert run1_status in {"NO_GAMES","NO_EDGES","OK","BUDGET_STOP"}, f"Run 1 status invalid: {run1_status}"
assert run2_status == "COOLDOWN_SKIP", f"Run 2 status invalid: {run2_status}"
print(f"Credits after run 1: {credits[0]}")
print(f"Credits after run 2: {credits[1]}")
assert credits[1] == credits[0], "Credits increased on cooldown skip!"
print("\nPASS: FAST mode cooldown and cost-control verified.")
