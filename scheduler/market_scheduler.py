import schedule
import time
import logging
from datetime import datetime
import pytz
import os
from daily_pipeline import run_daily_pipeline

# Scheduler run times (local time)
MORNING_SCAN = "10:30"
MIDDAY_NEWS_SCAN = "14:15"
FINAL_INJURY_SCAN = "18:15"

LOG_PATH = os.path.join("logs", "scheduler.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def schedule_pipeline():
    schedule.every().day.at(MORNING_SCAN).do(run_daily_pipeline, reason="morning_scan")
    schedule.every().day.at(MIDDAY_NEWS_SCAN).do(run_daily_pipeline, reason="midday_news_scan")
    schedule.every().day.at(FINAL_INJURY_SCAN).do(run_daily_pipeline, reason="final_injury_scan")
    logging.info("Market scheduler started. Scheduled runs: %s, %s, %s", MORNING_SCAN, MIDDAY_NEWS_SCAN, FINAL_INJURY_SCAN)
    print("Market scheduler active...")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    schedule_pipeline()
