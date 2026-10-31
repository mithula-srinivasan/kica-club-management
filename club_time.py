from datetime import datetime
from zoneinfo import ZoneInfo

KUWAIT = ZoneInfo("Asia/Kuwait")


def kuwait_today():
    return datetime.now(KUWAIT).date()