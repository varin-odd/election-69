from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ODD_KEY = os.getenv("ODD_KEY")

BACKUP_PATH = os.getenv("BACKUP_PATH")
DATA_PATH = os.getenv("DATA_PATH")
TS_FORMAT = os.getenv("TS_FORMAT")

DEBUG = os.getenv("DEBUG") == "true"
MASTER = os.getenv("MASTER") == "true"
FEED_DB_1_3 = os.getenv("FEED_DB_1_3") == "true"
FEED_DB_DETAIL_4 = os.getenv("FEED_DB_DETAIL_4") == "true"
FEED_RF = os.getenv("FEED_RF") == "true"

REALTIME_OR_FINAL = os.getenv("REALTIME_OR_FINAL")