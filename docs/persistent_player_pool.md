# Persistent Player Pool Logic

## Overview
This project uses a local SQLite database to cache player and game logs, enabling robust prop generation even during API outages. The player pool is built nightly using both recent box scores and database records.

## How It Works
- **Box Score Detection:** The pipeline fetches recent box scores for each team, identifying active rotation players based on minutes played.
- **Database Integration:** Players who played in the last 7 days (from the local DB) are included in the pool, even if API data is missing.
- **Projection Engine:** Player projections use local DB stats, falling back to API only if DB has fewer than 3 games for a player.
- **Logging:** All player pool operations are logged to `logs/player_pool.log`.

## Benefits
- **Reduced API Dependence:** Props and parlays are generated nightly, even if external APIs are unreliable.
- **Stable Prop Counts:** As the database grows, prop counts stabilize and projections improve.
- **Persistent Player Pool:** Ensures robust prop generation and historical tracking.

## Key Files
- `database/db_manager.py`: Manages DB schema and CRUD operations.
- `analysis/player_pool.py`: Builds player pool using box scores and DB records.
- `analysis/projection_engine.py`: Generates projections using DB stats.
- `daily_pipeline.py`: Orchestrates the nightly workflow.

## Monitoring
- Check `logs/player_pool.log` for player pool status.
- Review `data/processed/today_props_ai.csv` for nightly props.

## Next Steps
- Run pipeline nightly to grow DB and stabilize prop counts.
- Monitor logs and output for improvements.
