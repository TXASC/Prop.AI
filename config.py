import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Date logic
TODAY = datetime.now().strftime('%Y-%m-%d')

# File paths
NBA_STATS_FILE = os.path.join(RAW_DATA_DIR, f'nba_player_stats_{TODAY}.csv')
NBA_STATS_JSON = os.path.join(RAW_DATA_DIR, f'nba_player_stats_raw_{TODAY}.json')
INJURIES_FILE = os.path.join(RAW_DATA_DIR, 'injuries.csv')
TODAY_PROPS_FILE = os.path.join(PROCESSED_DATA_DIR, 'today_props.csv')
WEIGHTED_PROPS_CSV = os.path.join(OUTPUT_DIR, 'weighted_props.csv')
PLAYER_POOL_LOG = os.path.join(OUTPUT_DIR, 'player_pool.log')
BACKTEST_REPORT = os.path.join(OUTPUT_DIR, 'backtest_report_current_season.csv')
BACKTEST_TOP10 = os.path.join(OUTPUT_DIR, 'backtest_top10_props_per_day.csv')

# Database
DB_PATH = os.getenv('DB_PATH', os.path.join(BASE_DIR, 'database', 'prop_ai.db'))

# API Keys (from .env)
NBA_API_KEY = os.getenv('NBA_API_KEY', '')
ODDS_API_KEY = os.getenv('ODDS_API_KEY', '')


# Other config
RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', 3))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 5))  # seconds

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_DAILY_CREDIT_BUDGET = int(os.getenv("ODDS_DAILY_CREDIT_BUDGET", "200"))
ODDS_DEFAULT_TTL_MINUTES = int(os.getenv("ODDS_DEFAULT_TTL_MINUTES", "20"))
NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL', 'your_email@example.com')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.example.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'app_password_or_token')
NOTIFY_SLACK_WEBHOOK = os.getenv('NOTIFY_SLACK_WEBHOOK', '')
USE_SLACK_NOTIFICATION = os.getenv('USE_SLACK_NOTIFICATION', 'False').lower() == 'true'
USE_EMAIL_NOTIFICATION = os.getenv('USE_EMAIL_NOTIFICATION', 'True').lower() == 'true'
