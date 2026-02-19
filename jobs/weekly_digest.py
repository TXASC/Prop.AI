"""
weekly_digest.py

Goal:
- Generate output/weekly_digest.md as an artifact every run.
- Never fail the workflow if the SQLite DB is missing expected tables.
- If job_runs exists, summarize last 7 days.
- If job_runs does NOT exist, emit a clear note and still generate the digest.

This is intentionally defensive to prevent break/fix loops in CI.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "prop_ai.db"
OUTPUT_DIR = REPO_ROOT / "output"
OUTPUT_PATH = OUTPUT_DIR / "weekly_digest.md"

FAST_EDGES_PATH = OUTPUT_DIR / "fast_top_edges.json"
TODAY_PROPS_AI_PATH = REPO_ROOT / "data" / "processed" / "today_props_ai.csv"


def utc_now_iso() -> str:
    # Keep existing behavior; deprecation warnings are non-fatal.
    return _dt.datetime.utcnow().isoformat()


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    return cur.fetchone() is not None


def safe_connect(db_path: Path) -> sqlite3.Connection:
    # Allow creating an empty DB file if missing; digest should still succeed.
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))


def get_job_runs_last_7_days(db_path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Returns (runs, warning_message). Never raises.
    If job_runs does not exist, returns empty list and a warning string.
    """
    since_iso = (_dt.datetime.utcnow() - _dt.timedelta(days=7)).isoformat()

    try:
        conn = safe_connect(db_path)
        try:
            if not table_exists(conn, "job_runs"):
                return [], (
                    f"SQLite table `job_runs` not found in {db_path}. "
                    "Weekly run summary section skipped (digest still generated)."
                )

            cur = conn.cursor()

            # Try a safe, common-column query first.
            # If schema differs, fallback to SELECT *.
            try:
                cur.execute(
                    """
                    SELECT
                        run_id,
                        date,
                        reason,
                        status,
                        credits_used_today,
                        notes,
                        started_utc,
                        finished_utc
                    FROM job_runs
                    WHERE started_utc >= ?
                    ORDER BY started_utc DESC
                    """,
                    (since_iso,),
                )
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                cur.execute("SELECT * FROM job_runs ORDER BY rowid DESC LIMIT 200")
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()

            runs: List[Dict[str, Any]] = []
            for r in rows:
                runs.append({cols[i]: r[i] for i in range(len(cols))})
            return runs, None
        finally:
            conn.close()
    except Exception as e:
        # Last-resort: do not fail CI
        return [], f"Failed reading DB {db_path}: {type(e).__name__}: {e}"


def read_fast_edges_summary() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Reads output/fast_top_edges.json if present.
    Returns (payload, warning). Never raises.
    """
    if not FAST_EDGES_PATH.exists():
        return None, f"Missing {FAST_EDGES_PATH} (no fast edges summary available)."

    try:
        payload = json.loads(FAST_EDGES_PATH.read_text(encoding="utf-8"))
        return payload, None
    except Exception as e:
        return None, f"Failed reading {FAST_EDGES_PATH}: {type(e).__name__}: {e}"


def format_runs_section(runs: List[Dict[str, Any]], warning: Optional[str]) -> str:
    lines: List[str] = []
    lines.append("## Last 7 Days — Run Summary\n")

    if warning:
        lines.append(f"> ⚠️ {warning}\n")

    if not runs:
        lines.append("- No runs available to summarize.\n")
        return "\n".join(lines)

    statuses = [str(r.get("status", "")).upper() for r in runs]
    total = len(runs)
    success = sum(1 for s in statuses if "SUCCESS" in s or s == "OK")
    fail = total - success

    lines.append(f"- Runs found: **{total}**")
    lines.append(f"- Success: **{success}**")
    lines.append(f"- Fail/Other: **{fail}**\n")

    lines.append("### Most Recent Runs (up to 10)\n")
    lines.append("| started_utc | status | reason | run_id | credits_used_today |")
    lines.append("|---|---|---|---|---|")

    for r in runs[:10]:
        started = str(r.get("started_utc", r.get("timestamp_utc", r.get("date", ""))))
        status = str(r.get("status", ""))
        reason = str(r.get("reason", ""))
        run_id = str(r.get("run_id", r.get("id", "")))
        credits = str(r.get("credits_used_today", r.get("credits", "")))
        lines.append(f"| {started} | {status} | {reason} | {run_id} | {credits} |")

    lines.append("")
    return "\n".join(lines)


def format_fast_edges_section(edges_payload: Optional[Dict[str, Any]], warning: Optional[str]) -> str:
    lines: List[str] = []
    lines.append("## Latest FAST Edges Snapshot\n")

    if warning:
        lines.append(f"> ⚠️ {warning}\n")

    if not edges_payload:
        lines.append("- No fast edges payload available.\n")
        return "\n".join(lines)

    status = edges_payload.get("status")
    date = edges_payload.get("date")
    run_id = edges_payload.get("run_id")
    credits = edges_payload.get("credits_used_today")
    edges = edges_payload.get("edges") or []

    lines.append(f"- status: **{status}**")
    lines.append(f"- date: **{date}**")
    lines.append(f"- run_id: **{run_id}**")
    lines.append(f"- credits_used_today: **{credits}**")
    lines.append(f"- edges_count: **{len(edges)}**\n")

    if edges:
        lines.append("### Top Edges (up to 5)\n")
        for i, e in enumerate(edges[:5], start=1):
            try:
                compact = json.dumps(e, ensure_ascii=False)
            except Exception:
                compact = str(e)
            lines.append(f"{i}. `{compact}`")
        lines.append("")
    else:
        lines.append("- No edges listed in payload.\n")

    return "\n".join(lines)


def format_files_section() -> str:
    lines: List[str] = []
    lines.append("## Artifacts & Paths\n")
    lines.append(f"- Weekly digest: `{OUTPUT_PATH}`")
    lines.append(f"- FAST edges: `{FAST_EDGES_PATH}`")
    lines.append(f"- AI props CSV: `{TODAY_PROPS_AI_PATH}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ensure_output_dir()

    db_path = Path(os.environ.get("PROP_AI_DB_PATH", str(DEFAULT_DB_PATH))).resolve()

    runs, runs_warning = get_job_runs_last_7_days(db_path)
    edges_payload, edges_warning = read_fast_edges_summary()

    md_lines: List[str] = []
    md_lines.append("# Prop.AI — Weekly Digest\n")
    md_lines.append(f"- generated_utc: `{utc_now_iso()}`")
    md_lines.append(f"- db_path: `{db_path}`\n")

    md_lines.append(format_runs_section(runs, runs_warning))
    md_lines.append(format_fast_edges_section(edges_payload, edges_warning))
    md_lines.append(format_files_section())

    OUTPUT_PATH.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")

    # Always succeed; digest generation should never fail the pipeline.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

