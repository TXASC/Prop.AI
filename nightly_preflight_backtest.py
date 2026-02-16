"""
Nightly Preflight Backtest Script for NBA Prop AI Pipeline
--------------------------------------------------------
Extends daily_preflight_backtest.py with nightly scheduling and full automation.
"""
import os
import sys
import logging
import datetime
import argparse
import time

from config import DATA_DIR, OUTPUT_DIR, LOGS_DIR, DB_PATH, WEIGHTED_PROPS_CSV, \
    USE_EMAIL_NOTIFICATION, USE_SLACK_NOTIFICATION

# Notification helpers
from helpers.notification_utils import (
    send_email_notification, send_slack_notification, build_notification_summary
)

# Import daily preflight logic

import importlib.util
DAILY_PREFLIGHT_PATH = os.path.join(os.path.dirname(__file__), "daily_preflight_backtest.py")
spec = importlib.util.spec_from_file_location("daily_preflight_backtest", DAILY_PREFLIGHT_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load daily_preflight_backtest.py from {DAILY_PREFLIGHT_PATH}")
daily_preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily_preflight)

# Configurable parameters (can be loaded from config.py or .env)
N_BACKTEST_ITER = getattr(daily_preflight, 'N_BACKTEST_ITER', 3)
PROP_CATEGORIES = getattr(daily_preflight, 'PROP_CATEGORIES', ["Points", "Rebounds", "Assists"])
MIN_EV_THRESHOLD = getattr(daily_preflight, 'MIN_EV_THRESHOLD', 0.05)
RUN_TIME = getattr(daily_preflight, 'RUN_TIME', "03:00")  # Default 3:00 AM

# Setup logging
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOGS_DIR, "nightly_preflight.log")
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nightly_preflight")


try:
    import schedule
except ImportError:
    logger.error("schedule module not found. Please install with 'pip install schedule'.")
    print("schedule module not found. Please install with 'pip install schedule'.")
    sys.exit(1)

def run_nightly():
    logger.info("=== Nightly Preflight Backtest START ===")
    notification_log_path = os.path.join(LOGS_DIR, "notifications.log")
    try:
        preflight = daily_preflight.preflight_checks()
        metrics = daily_preflight.run_backtests(N_BACKTEST_ITER, PROP_CATEGORIES)
        daily_preflight.optimize_weights(metrics)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        eval_report_path = os.path.join(OUTPUT_DIR, f"daily_eval_{today}.csv")
        daily_preflight.generate_eval_report(preflight, metrics, eval_report_path)
        logger.info("Nightly preflight completed successfully.")

        # --- Notification logic ---
        summary = build_notification_summary(eval_report_path)
        subject = f"NBA Prop AI Nightly Report {today}"
        email_success = slack_success = None
        if USE_EMAIL_NOTIFICATION:
            email_success = send_email_notification(subject, summary, eval_report_path, logger)
        if USE_SLACK_NOTIFICATION:
            slack_msg = f"*NBA Prop AI Nightly Report {today}*\n{summary}\nReport: {eval_report_path}"
            slack_success = send_slack_notification(slack_msg, logger)
        # Log notification results
        with open(notification_log_path, "a") as notif_log:
            notif_log.write(f"{datetime.datetime.now()} | Email sent: {email_success} | Slack sent: {slack_success}\n")
    except Exception as e:
        logger.error(f"Nightly preflight error: {e}")
        # Attempt to send failure notification
        try:
            fail_subject = f"NBA Prop AI Nightly Run FAILED {datetime.datetime.now().strftime('%Y-%m-%d')}"
            fail_msg = f"Nightly run failed with error: {e}"
            if USE_EMAIL_NOTIFICATION:
                send_email_notification(fail_subject, fail_msg, None, logger)
            if USE_SLACK_NOTIFICATION:
                send_slack_notification(fail_msg, logger)
            with open(notification_log_path, "a") as notif_log:
                notif_log.write(f"{datetime.datetime.now()} | FAILURE notification sent.\n")
        except Exception as notif_e:
            logger.error(f"Notification failure: {notif_e}")
    logger.info("=== Nightly Preflight Backtest END ===")

def main():
    parser = argparse.ArgumentParser(description="Nightly Preflight Backtest for NBA Prop AI Pipeline")
    parser.add_argument('--manual', action='store_true', help='Run immediately (manual mode)')
    parser.add_argument('--time', type=str, default=RUN_TIME, help='Scheduled run time in HH:MM (24h)')
    args = parser.parse_args()

    if args.manual:
        logger.info("Manual run mode activated.")
        run_nightly()
        return

    # Nightly scheduling
    logger.info(f"Scheduling nightly preflight at {args.time}.")
    schedule.every().day.at(args.time).do(run_nightly)
    logger.info(f"Next scheduled run: {args.time} (local time)")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
