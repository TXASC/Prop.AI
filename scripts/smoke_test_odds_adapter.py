
import sys
import importlib.util
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
bootstrap_path = repo_root / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", bootstrap_path)
if spec and spec.loader:
    bootstrap = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap"] = bootstrap
    spec.loader.exec_module(bootstrap)
    get_repo_root = bootstrap.get_repo_root
else:
    raise ImportError(f"Could not import bootstrap from {bootstrap_path}")
import config
from providers.odds_adapter import OddsAdapter

adapter = OddsAdapter(
    db_path=config.DB_PATH,
    api_key=config.ODDS_API_KEY,
    daily_credit_budget=config.ODDS_DAILY_CREDIT_BUDGET,
    default_ttl_minutes=config.ODDS_DEFAULT_TTL_MINUTES
)

def print_ledger():
    import sqlite3, datetime
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    with sqlite3.connect(config.DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT credits_used FROM odds_credit_ledger WHERE date=?", (today,))
        row = c.fetchone()
        print(f"Ledger for {today}: {row[0] if row else 0} credits used")

if __name__ == "__main__":
    print("First call (should be MISS):")
    adapter.get_odds(
        sport="basketball_nba",
        regions="us",
        markets="h2h,spreads,totals",
        odds_format="american",
        date_format="iso"
    )
    print_ledger()
    print("\nSecond call (should be HIT):")
    adapter.get_odds(
        sport="basketball_nba",
        regions="us",
        markets="h2h,spreads,totals",
        odds_format="american",
        date_format="iso"
    )
    print_ledger()
