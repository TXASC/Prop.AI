
# SPORTS BETTING AI — ARCHITECTURE STATE
Date: 2026-02-16
Status: Hands-Off Training Mode (Stabilized)

------------------------------------------------------------
1. PROJECT PURPOSE
------------------------------------------------------------

Primary Function:
- NBA player prop data ingestion
- Odds normalization
- EV calculation
- Backtesting & simulation
- Automated daily FAST-mode training runs

Current Mode:
- Backend-only
- No live betting integration
- No UI dependency for core logic
- Production-safe FAST training mode active

------------------------------------------------------------
2. CORE ENTRYPOINTS
------------------------------------------------------------

Primary Job Runner:
- jobs/training_runner.py

FAST Mode Runner:
- run_training_mode_fast.ps1

Standard Mode Runner:
- run_training_mode.ps1

Pipeline Entry:
- daily_pipeline.py

Smoke Test:
- scripts/smoke_test_odds_adapter.py

------------------------------------------------------------
3. DATA LAYER
------------------------------------------------------------

Primary Database:
- SQLite
- Path: database/prop_ai.db

Key Tables:
- (List key tables after DB inspection)

Caching Layer:
- providers/odds_adapter.py
- SQLite-based cache
- TTL enforcement
- Daily credit budget enforcement

Output Artifacts:
- output/fast_top_edges.json
- output/weekly_digest.md
- logs/training_runner.log

------------------------------------------------------------
4. ODDS PROVIDER STRUCTURE
------------------------------------------------------------

Single Choke-Point:
- providers/odds_adapter.py

Responsibilities:
- TheOdds API calls
- Cache lookup
- TTL enforcement
- Daily credit tracking
- Credit kill-switch
- Budget stop flag creation

Direct HTTP Calls Outside Adapter:
- (Confirm after inspection — expected: NONE)

Markets Used in FAST Mode:
- h2h only

------------------------------------------------------------
5. TRAINING MODE SAFETY CONTROLS
------------------------------------------------------------

Cooldown Gate:
- Prevents duplicate runs within window
- Writes COOLDOWN_SKIP artifact

Credit Kill-Switch:
- Stops execution if daily credit budget exceeded
- Writes budget_stop.flag

FAST Mode Behavior:
- Ingestion
- EV computation
- Minimal market scope
- No deep backtesting

------------------------------------------------------------
6. SCHEDULING
------------------------------------------------------------

Scheduled Tasks:
- schedule_tasks.ps1
- unschedule_tasks.ps1

Current Frequency:
- Daily FAST
- Weekly digest

Manual One-Click:
- run_training_mode_fast.ps1

------------------------------------------------------------
7. KNOWN RISKS (AS OF TODAY)
------------------------------------------------------------

[ ] Multiple legacy folders (sports_betting_platform vs root scripts)
[ ] Duplicate pipelines
[ ] CSV outputs still exist alongside DB
[ ] No REST API wrapper yet
[ ] No monitoring endpoint
[ ] No centralized metrics dashboard

------------------------------------------------------------
8. WHAT IS FROZEN (DO NOT MODIFY WITHOUT PLAN)
------------------------------------------------------------

- providers/odds_adapter.py
- FAST mode logic
- Credit controls
- Cooldown logic
- Training runner structure

------------------------------------------------------------
9. NEXT 3 MILESTONES (PLANNED — NOT IMPLEMENTED)
------------------------------------------------------------

Milestone 1: REST API Wrapper
- Add FastAPI layer
- /health endpoint
- /metrics endpoint
- Wrap training trigger

Milestone 2: Data Layer Hardening
- Remove CSV fallbacks
- Ensure DB is single source of truth
- Centralize DB access

Milestone 3: Monitoring & Autonomy
- Add run metrics table
- Add failure notifications
- Add credit dashboard endpoint

------------------------------------------------------------
10. CURRENT MATURITY SCORE (TO BE FILLED LATER)
------------------------------------------------------------

Architecture Stability: __ /10
Cost Control: __ /10
Autonomy Level: __ /10
Refactor Risk: __ /10

------------------------------------------------------------
END OF SNAPSHOT
------------------------------------------------------------

Return confirmation: "ARCHITECTURE_STATE created successfully."
