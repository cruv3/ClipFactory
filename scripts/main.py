import time
from datetime import datetime
import json
import os

VIDEO_INTERVAL_HOURS = 6
REPORT_HOUR = 8
HISTORY_FILE = "../video_history.json"

def main_loop():
    