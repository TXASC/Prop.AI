
import sys
import importlib.util
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
bootstrap_path = repo_root / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", bootstrap_path)
bootstrap = importlib.util.module_from_spec(spec)
sys.modules["bootstrap"] = bootstrap
spec.loader.exec_module(bootstrap)
get_repo_root = bootstrap.get_repo_root
import config
import os
import json
import hashlib
import sqlite3
import requests
import datetime
import logging
import time
from typing import Optional, List

class OddsAdapter:
    def __init__(self, db_path, api_key, daily_credit_budget, default_ttl_minutes):
        self.db_path = db_path
        self.api_key = api_key
        self.daily_credit_budget = daily_credit_budget
        self.default_ttl_minutes = default_ttl_minutes
        self._ensure_tables()
        self.logger = logging.getLogger("OddsAdapter")
        if not self.logger.hasHandlers():
            logging.basicConfig(level=logging.INFO)

    def _ensure_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS odds_api_cache (
                    cache_key TEXT PRIMARY KEY,
                    fetched_at TEXT,
                    ttl_minutes INTEGER,
                    url TEXT,
                    params_json TEXT,
                    response_json TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS odds_credit_ledger (
                    date TEXT PRIMARY KEY,
                    credits_used INTEGER
                )
            """)
            conn.commit()

    def _get_today(self):
        return datetime.datetime.utcnow().strftime('%Y-%m-%d')

    def _get_credits_used(self):
        today = self._get_today()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT credits_used FROM odds_credit_ledger WHERE date=?", (today,))
            row = c.fetchone()
            return row[0] if row else 0

    def _increment_credits(self, used):
        today = self._get_today()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT credits_used FROM odds_credit_ledger WHERE date=?", (today,))
            row = c.fetchone()
            if row:
                c.execute("UPDATE odds_credit_ledger SET credits_used=credits_used+? WHERE date=?", (used, today))
            else:
                c.execute("INSERT INTO odds_credit_ledger (date, credits_used) VALUES (?, ?)", (today, used))
            conn.commit()

    def _make_cache_key(self, **params):
        # Deterministic hash of sorted params
        params_json = json.dumps(params, sort_keys=True)
        return hashlib.sha256(params_json.encode()).hexdigest()

    def get_odds(self, sport: str, regions: str, markets: str, odds_format: str="decimal", date_format: str="iso", bookmakers: Optional[str]=None, event_ids: Optional[List[str]]=None, ttl_minutes: Optional[int]=None) -> dict:
        ttl = ttl_minutes if ttl_minutes is not None else self.default_ttl_minutes
        params = {
            "sport": sport,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
            "dateFormat": date_format,
        }
        if bookmakers:
            params["bookmakers"] = bookmakers
        if event_ids:
            params["eventIds"] = ",".join(event_ids)
        cache_key = self._make_cache_key(**params)
        now = datetime.datetime.utcnow()
        # Check cache
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT fetched_at, ttl_minutes, response_json FROM odds_api_cache WHERE cache_key=?", (cache_key,))
            row = c.fetchone()
            if row:
                fetched_at = datetime.datetime.fromisoformat(row[0])
                cache_ttl = row[1]
                if (now - fetched_at).total_seconds() < cache_ttl * 60:
                    self.logger.info(f"CACHE_HIT: {params}")
                    print("CACHE_HIT")
                    return json.loads(row[2])
                else:
                    self.logger.info(f"CACHE_EXPIRED: {params}")
            else:
                self.logger.info(f"CACHE_MISS: {params}")
                print("CACHE_MISS")
        # Enforce credit budget
        credits_used = self._get_credits_used()
        if credits_used >= self.daily_credit_budget:
            msg = f"DAILY CREDIT BUDGET EXCEEDED: {credits_used} >= {self.daily_credit_budget}"
            self.logger.error(msg)
            raise RuntimeError(msg)
        # Build URL
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
        req_params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
            "dateFormat": date_format,
        }
        if bookmakers:
            req_params["bookmakers"] = bookmakers
        if event_ids:
            req_params["eventIds"] = ",".join(event_ids)
        # Retry logic
        from config import RETRY_ATTEMPTS, RETRY_DELAY
        attempts = RETRY_ATTEMPTS if 'RETRY_ATTEMPTS' in dir() else 3
        delay = RETRY_DELAY if 'RETRY_DELAY' in dir() else 2
        last_exc = None
        for attempt in range(attempts):
            try:
                response = requests.get(url, params=req_params, timeout=10)
                if response.status_code == 200:
                    break
                else:
                    last_exc = Exception(f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                last_exc = e
            time.sleep(delay)
        else:
            if last_exc is not None:
                raise last_exc
            else:
                raise Exception("Unknown error in OddsAdapter HTTP request retries.")
        # Track credits
        credits_this_call = 1
        for header in ["x-credits-used", "x-requests-used"]:
            if header in response.headers:
                try:
                    credits_this_call = int(response.headers[header])
                except Exception:
                    pass
        self._increment_credits(credits_this_call)
        self.logger.info(f"CREDITS_USED: {credits_this_call} (total today: {self._get_credits_used()})")
        # Store in cache
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO odds_api_cache (cache_key, fetched_at, ttl_minutes, url, params_json, response_json) VALUES (?, ?, ?, ?, ?, ?)",
                      (cache_key, now.isoformat(), ttl, url, json.dumps(req_params, sort_keys=True), response.text))
            conn.commit()
        return response.json()
