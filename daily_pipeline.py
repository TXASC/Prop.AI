import os
import pandas as pd
import logging
from datetime import datetime
try:
    import pytz
except ImportError:
    pytz = None
from config import LOGS_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR
from fetch_games import fetch_games_for_today
from analysis.implied_totals import calculate_implied_scores
from providers.balldontlie_provider import BallDontLieProvider
from analysis.statistical_engine import compute_ev
from analysis.ai_layer import ai_adjustments
from analysis.parlay_optimizer_topN import top_n_3_pick_parlays
from analysis.weighted_prop_engine_dynamic import weighted_prop_pipeline_dynamic

def run_daily_pipeline(reason="manual"):
    os.makedirs(LOGS_DIR, exist_ok=True)
    logging.basicConfig(filename=os.path.join(LOGS_DIR, "pipeline.log"), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.info(f"=== Starting Daily NBA Player Prop Pipeline - Reason: {reason} ===")
    from database.db_manager import initialize_database, initialize_clv_tracking
    initialize_database()
    initialize_clv_tracking()

    # Step 0: Ingest pick'em entries
    from collectors.pickem_bet_ingestor import ingest_pickem_entries
    try:
        ingest_pickem_entries()
    except Exception as e:
        logging.error(f"Pick'em ingestion failed: {e}")

    # Step 1: Fetch games (OddsAPI)
    games = fetch_games_for_today()
    if not games:
        logging.warning("No games today — pipeline stops.")
        print("No games today — pipeline stops.")
        return
    logging.info(f"Found {len(games)} games today.")
    print(f"Found {len(games)} games today.")

    # Step 2: Compute implied team scores
    implied_scores = []
    for game in games:
        try:
            scores = calculate_implied_scores(game)
            implied_scores.append({**game, **scores})
        except Exception as e:
            logging.error(f"Implied score error for game {game.get('game_id')}: {e}")
            continue

    # Step 3: Build player pool
    from analysis.player_pool import build_today_player_pool
    player_pool = build_today_player_pool(implied_scores)

    # Step 4: Generate player projections
    from analysis.projection_engine import generate_player_projections
    projections = generate_player_projections(player_pool)

    # Step 5: Generate props from projections
    from analysis.prop_generator import generate_props_from_projections
    df_props = generate_props_from_projections(projections)

    # Step 4: Run EV calculation
    try:
        df_ev = compute_ev(df_props)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        ev_path = os.path.join(PROCESSED_DATA_DIR, "today_props_ev.csv")
        df_ev.to_csv(ev_path, index=False)
        logging.info(f"Saved {len(df_ev)} positive EV props to {ev_path}")
        print(f"Saved {len(df_ev)} positive EV props to {ev_path}")
    except Exception as e:
        logging.error(f"EV calculation error: {e}")
        df_ev = df_props

    # --- CLV Tracking Integration ---
    try:
        from database.clv_tracking import insert_clv_snapshot, log_clv_action
        from helpers.clv_utils import update_closing_lines_for_unsettled_props
        from analysis.clv_metrics import compute_clv_summary
        for _, row in df_ev.iterrows():
            # Use UTC if pytz is available, else local time
            if pytz:
                ts = datetime.now(pytz.utc).isoformat()
            else:
                ts = datetime.utcnow().isoformat()
            insert_clv_snapshot(
                date=row.get("date", datetime.now().strftime("%Y-%m-%d")),
                player_name=row["PLAYER_NAME"],
                stat_type="PRA",  # or row.get("STAT_TYPE", "PRA") if available
                sportsbook="unknown",  # Placeholder, update as needed
                line_at_pick=row.get("prop_line"),
                odds_at_pick=None,  # Placeholder, update as needed
                timestamp_at_pick=ts,
                projected_value=row.get("projected_PRA"),
                expected_value=row.get("edge"),
                closing_line=None,
                closing_odds=None,
                result=None,
                clv=None
            )
        # Step: Update closing lines for unsettled props
        update_closing_lines_for_unsettled_props()
        # Step: Compute and log CLV summary
        clv_summary = compute_clv_summary(None)
        log_clv_action(f"CLV Summary: {clv_summary}")
        logging.info(f"CLV Summary: {clv_summary}")
        print(f"CLV Summary: {clv_summary}")
    except Exception as e:
        from database.clv_tracking import log_clv_action
        log_clv_action(f"Error in CLV pipeline: {e}")

    # Step: Compute prop correlations
    try:
        from analysis.prop_correlation_engine import compute_rolling_correlations
        compute_rolling_correlations()
    except Exception as e:
        logging.error(f"Correlation engine failed: {e}")

    # Step: Generate parlay suggestions
    try:
        from analysis.parlay_suggester import generate_suggested_parlays
        generate_suggested_parlays()
    except Exception as e:
        logging.error(f"Parlay suggestion failed: {e}")

    # Step 5: Run AI reasoning
    injuries_df = pd.DataFrame(columns=["player", "status", "details"])
    media_df = {}
    try:
        df_ai = ai_adjustments(df_ev, injuries_df=injuries_df, media_df=media_df)
        ai_path = os.path.join(PROCESSED_DATA_DIR, "today_props_ai.csv")
        df_ai.to_csv(ai_path, index=False)
        logging.info(f"Saved AI-adjusted props to {ai_path}")
        print(f"Saved AI-adjusted props to {ai_path}")
    except Exception as e:
        logging.error(f"AI reasoning error: {e}")
        df_ai = df_ev

    # Step 6: Run dynamic weighted prop engine
    try:
        df_weighted = weighted_prop_pipeline_dynamic()
        logging.info(f"Weighted prop engine output: {len(df_weighted)} props saved to weighted_props.csv")
        print(f"Weighted prop engine output: {len(df_weighted)} props saved to weighted_props.csv")
    except Exception as e:
        logging.error(f"Weighted prop engine error: {e}")

    # Step 7: Generate top 3 parlays
    try:
        top_parlays = top_n_3_pick_parlays(df_ai, n=3)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        for i, parlay_df in enumerate(top_parlays, start=1):
            filename = os.path.join(OUTPUT_DIR, f"today_top_parlay_{i}.csv")
            parlay_df.to_csv(filename, index=False)
            logging.info(f"Saved parlay #{i} to {filename}")
            print(f"Saved parlay #{i} to {filename}")
            print(parlay_df[["PLAYER_NAME", "TEAM_ABBREVIATION", "adjusted_EV", "confidence"]])
    except Exception as e:
        logging.error(f"Parlay generation error: {e}")

    logging.info("=== Pipeline Complete ===")
    print("=== Pipeline Complete ===")

    # --- Notification Integration ---
    from helpers.notification_utils import send_email_notification, send_slack_notification, build_notification_summary

    from config import USE_EMAIL_NOTIFICATION, USE_SLACK_NOTIFICATION


    today = datetime.now().strftime("%Y-%m-%d")
    eval_report_path = os.path.join(OUTPUT_DIR, f"daily_eval_{today}.csv")
    summary = build_notification_summary(eval_report_path)
    subject = f"Prop AI Nightly Report {today}"

    if USE_EMAIL_NOTIFICATION:
        send_email_notification(subject, summary, eval_report_path)
    if USE_SLACK_NOTIFICATION:
        slack_msg = f"*Prop AI Nightly Report {today}*\n{summary}\nReport: {eval_report_path}"
        send_slack_notification(slack_msg)

if __name__ == "__main__":
    run_daily_pipeline(reason="manual")
