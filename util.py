from datetime import datetime
from zoneinfo import ZoneInfo

def convert_utc_to_bangkok(dt_str):
    # แปลงเป็น datetime
    dt_utc = datetime.fromisoformat(dt_str)
    # แปลง timezone เป็น Bangkok
    dt_bkk = dt_utc.astimezone(ZoneInfo("Asia/Bangkok"))
    # แปลงรูปแบบ
    result = dt_bkk.strftime("%Y-%m-%d %H:%M:%S")
    return result