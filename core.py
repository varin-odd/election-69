from config import BACKUP_PATH, DATA_PATH, TS_FORMAT
from datetime import datetime
import glob, os, shutil

# To-do: เพิ่ม all history files

M_FEEDS = ["M_ELECTIONS", "M_PROVINCES", "M_PARTY_LIST", "M_CANDIDATES"]
F_FEEDS = ["F_R_DB_1", "F_R_DB_2", "F_R_DB_3", "F_R_DBD_4",
           "F_F_DB_1", "F_F_DB_2", "F_F_DB_3", "F_F_DBD_4"]
S_FEEDS = ["F_F_RF"] # Special FEED ที่มีแค่ Final ไม่มี Realtime

def extract_datetime(filename, prefix):
    # เอาเฉพาะชื่อไฟล์ ไม่เอา path
    basename = os.path.basename(filename)
    # ตัด prefix และ .csv ออก
    dt_str = basename.replace(f"{prefix}_", "").replace(".csv", "")
    # แปลงเป็น datetime
    return datetime.strptime(dt_str, TS_FORMAT)

def get_latest_csv_files():
    for prefix in M_FEEDS + F_FEEDS + S_FEEDS:
        pattern = os.path.join(BACKUP_PATH, prefix + "_*.csv")
        files = glob.glob(pattern)

        # บางครั้ง M_CANDIDATES อาจจะไม่มีไฟล์
        if not files:
            continue
        latest_file = max(files, key=lambda f: extract_datetime(f, prefix))
        shutil.copy(latest_file, DATA_PATH + f"{prefix}.csv")
        #print(latest_file)

def get_realtime_or_final_files(type):
    for prefix in F_FEEDS:
        if prefix[2] == type[0].upper():
            shutil.move(DATA_PATH + f"{prefix}.csv", DATA_PATH + f"F_{prefix[4:]}.csv")
        else:
            os.remove(DATA_PATH + f"{prefix}.csv")
    for prefix in S_FEEDS:
        shutil.move(DATA_PATH + f"{prefix}.csv", DATA_PATH + f"F_{prefix[4:]}.csv")

if __name__ == "__main__":
    get_latest_csv_files()
    get_realtime_or_final_files("R")