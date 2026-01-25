from config import BACKUP_PATH, DATA_PATH, TS_FORMAT, REALTIME_OR_FINAL, DEBUG
from datetime import datetime
import pandas as pd
import glob, os, shutil

# To-do: เพิ่ม all history files

M_FEEDS = ["M_ELECTIONS", "M_PROVINCES", "M_PARTY_LIST", "M_CANDIDATES"]
F_FEEDS = ["F_R_DB_1", "F_R_DB_2", "F_R_DB_3", "F_R_DBD_4",
           "F_F_DB_1", "F_F_DB_2", "F_F_DB_3", "F_F_DBD_4"]
S_FEEDS = ["F_F_RF"] # Special FEED ที่มีแค่ Final ไม่มี Realtime
LAST_UPDATE = f'{DATA_PATH}LAST_UPDATE.csv'

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

def lastUpdate_to_csv(df, feedname, lastUpdate):
    # ทำให้ feedname เป็น key แล้ว upsert
    df = df.set_index("feedname")
    df.loc[feedname, "lastUpdate"] = lastUpdate
    df = df.reset_index()

    # เขียนกลับ
    df.to_csv(LAST_UPDATE, index=False, encoding="utf-8")
    return df

def error_log(type, fromFile, toFile, exception):
    print(f'ERROR core.py get_realtime_or_final_files("{type}"): File "{fromFile}" --> "{toFile}": {exception}')
def get_realtime_or_final_files(type):
    df = pd.read_csv(LAST_UPDATE)
    for prefix in F_FEEDS:
        fromFile = f"{prefix}.csv"
        toFile = f"F_{prefix[4:]}.csv"
        if prefix[2] == type[0].upper():
            try:
                shutil.move(DATA_PATH + fromFile, DATA_PATH + toFile)
                lastUpdate = df.loc[df['feedname'] == prefix, 'lastUpdate'].iloc[0]
                if DEBUG: print("move: " + DATA_PATH + fromFile + ", " + DATA_PATH + toFile + ", " + lastUpdate)
                df = lastUpdate_to_csv(df, toFile[:-4], lastUpdate)
            except Exception as e:
                error_log(type, fromFile, toFile, e)
                if not os.path.exists(DATA_PATH + toFile):
                    shutil.copy(f'zero_data/{toFile}', DATA_PATH + toFile)
                    print(f'Copied {toFile} from "zero_data"')
        else:
            try:
                os.remove(DATA_PATH + fromFile)
                if DEBUG: print("remove: " + DATA_PATH + fromFile)
            except Exception as e: error_log(type, fromFile, "REMOVE", e)
    for prefix in S_FEEDS:
        fromFile = f"{prefix}.csv"
        toFile = f"F_{prefix[4:]}.csv"
        try:
            shutil.move(DATA_PATH + fromFile, DATA_PATH + toFile)
            lastUpdate = df.loc[df['feedname'] == prefix, 'lastUpdate'].iloc[0]
            if DEBUG: print("move: " + DATA_PATH + fromFile + ", " + DATA_PATH + toFile + ", " + lastUpdate)
            df = lastUpdate_to_csv(df, toFile[:-4], lastUpdate)
        except Exception as e:
            error_log(type, fromFile, toFile, e)
            if not os.path.exists(DATA_PATH + toFile):
                shutil.copy(f'zero_data/{toFile}', DATA_PATH + toFile)
                print(f'Copied {toFile} from "zero_data"')

def main():
    get_latest_csv_files()
    get_realtime_or_final_files(REALTIME_OR_FINAL)

if __name__ == "__main__":
    main()