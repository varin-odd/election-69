from config import BACKUP_PATH, DATA_PATH, TS_FORMAT, BASE_URL, ODD_KEY, DEBUG, MASTER, FEED_DB_1_3, FEED_DB_DETAIL_4, FEED_RF
from datetime import datetime
import pandas as pd
import os, requests, util

HEADERS = {'Authorization': 'Bearer ' + ODD_KEY}

def lastUpdate_or_lastUpdated(data):
    if 'lastUpdate' in data:
        return data['lastUpdate']
    elif 'lastUpdated' in data:
        return data['lastUpdated']
    else:
        return "<lastUpdate_not_found>"
def lastUpdate_to_csv(feedname, lastUpdate):
    lastUpdate = util.convert_utc_to_bangkok(lastUpdate)

    csv_path = f'{DATA_PATH}LAST_UPDATE.csv'
    # โหลดไฟล์เดิม (ถ้าไม่มีให้สร้าง df เปล่า)
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        df = pd.read_csv(csv_path, dtype={"feedname": "string", "lastUpdate": "string"})
    else:
        df = pd.DataFrame(columns=["feedname", "lastUpdate"])

    # ทำให้ feedname เป็น key แล้ว upsert
    df = df.set_index("feedname")
    df.loc[feedname, "lastUpdate"] = lastUpdate
    df = df.reset_index()

    # เขียนกลับ
    df.to_csv(csv_path, index=False, encoding="utf-8")
def error_log(method, exception):
    print(f'ERROR feed.py {method}(): {exception}')

def get_all_pages(url, function_name, key_name):
    items = []
    page = 1
    limit = 1000
    lastUpdate = None

    while True:
        paged_url = f'{url}?page={page}&limit={limit}'
        response = requests.get(paged_url, headers=HEADERS)

        if response.status_code != 200:
           raise Exception(f'feed.py: {function_name} failed')
        data = response.json()
        if not data['success']:
           raise Exception(f'feed.py: {function_name} failed')

        # ดึงข้อมูลของหน้านั้น
        cd = data["data"][key_name]
        items.extend(cd)
        lastUpdate = lastUpdate_or_lastUpdated(data["data"])

        # อ่านข้อมูล pagination
        pagination = data["data"]["pagination"]
        total_pages = pagination["totalPages"]
        if DEBUG: print(f"Fetched page {page}/{total_pages}, items: {len(cd)}")

        if page >= total_pages:
            break
        page += 1

    return items, lastUpdate

def M_to_csv(df, filename):
    df.to_csv(f'{BACKUP_PATH}M_{filename}_{datetime.now().strftime(TS_FORMAT)}.csv', index=False, encoding="utf-8-sig")
    df.to_csv(f'{DATA_PATH}M_{filename}.csv', index=False, encoding="utf-8-sig")
def M_elections():
    try:
        response = requests.get(f'{BASE_URL}/elections', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                df = pd.DataFrame(data['data']['elections'])
                M_to_csv(df, 'ELECTIONS')
                return True
        raise Exception(f"Read '{BASE_URL}/elections' failed.")
    except Exception as e: error_log("M_elections", e)
def M_provinces():
    try:
        response = requests.get(f'{BASE_URL}/provinces', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                df = pd.DataFrame(data['data']['provinces'])
                M_to_csv(df, 'PROVINCES')
                return True
        raise Exception(f"Read '{BASE_URL}/provinces' failed.")
    except Exception as e: error_log("M_provinces", e)

# Many pages
def M_party_list(electionId):
    try:
        partyLists, lastUpdate = get_all_pages(f'{BASE_URL}/party-list/{electionId}', 'M_party_list', 'partyLists')
        df = pd.DataFrame(partyLists)
        df_p = pd.json_normalize(df["party"])
        df = df.join(df_p.add_prefix("party"))
        df = df.rename(columns=
            {
                "partyid": "partyId",
                "partycode": "partyCode",
                "partyname": "partyName",
                "partycolor": "partyColor"
            })
        df = df[["id", "number", "title", "firstName", "lastName", "name", "photoUrl", "pmCandidateRank",
                "partyId", "partyCode", "partyName", "partyabbreviation", "partyColor"]]
        M_to_csv(df, 'PARTY_LIST')
    except Exception as e: error_log("M_party_list", e)

# น่าจะไม่ได้ใช้
def M_candidates():
    try:
        candidates, lastUpdate = get_all_pages(f'{BASE_URL}/candidates', 'M_candidates', 'candidates')
        df = pd.DataFrame(candidates)
        df_p = pd.json_normalize(df["party"])
        df = df.join(df_p.add_prefix("party"))
        df = df.rename(columns=
            {
                "partyid": "partyId",
                "partycode": "partyCode",
                "partyname": "partyName",
                "partycolor": "partyColor"
            })
        df_p = pd.json_normalize(df["province"])
        df = df.join(df_p.add_prefix("province"))
        df = df.rename(columns=
            {
                "provinceid": "provinceId",
                "provincecode": "provinceCode",
                "provincename": "provinceName",
                "provinceregion": "provinceRegion"
            })
        df_p = pd.json_normalize(df["electionArea"])
        df = df.join(df_p.add_prefix("electionArea"))
        df = df.rename(columns=
            {
                "electionAreaid": "electionAreaId",
                "electionAreaname": "electionAreaName",
                "electionAreaareaNumber": "electionAreaAreaNumber",
            })
        df = df[["id", "electionId", "electionAreaId", "number", "title", "firstName", "lastName", "name", "photoUrl",
                "partyId", "partyCode", "partyName", "partyColor",
                "provinceId", "provinceCode", "provinceName", "provinceRegion",
                "electionAreaId", "electionAreaName", "electionAreaAreaNumber"]]
        M_to_csv(df, 'CANDIDATES')
    except Exception as e: print(e)

def F_to_csv(df, type, lastUpdate, filename, mode='w'):
    backup = f'{BACKUP_PATH}F_{type[0].upper()}_{filename}_{datetime.now().strftime(TS_FORMAT)}.csv'
    data = f'{DATA_PATH}F_{type[0].upper()}_{filename}.csv'
    if mode == 'w':
        df.to_csv(backup, index=False, encoding="utf-8-sig")
        df.to_csv(data, index=False, encoding="utf-8-sig")
    elif mode == 'a':
        df.to_csv(backup, index=False, encoding="utf-8-sig", header=False, mode='a')
        df.to_csv(data, index=False, encoding="utf-8-sig", header=False, mode='a')
    
    lastUpdate_to_csv(f'F_{type[0].upper()}_{filename}', lastUpdate)
def F_DB_1_statistics(electionId, type, id, mode):
    try:
        response = requests.get(f'{BASE_URL}/elections/{electionId}/{type}/statistics', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                lastUpdate = lastUpdate_or_lastUpdated(data['data'])
                df = pd.DataFrame([data['data']['statistics']])
                df['election_id'] = id
                df = df[["election_id",
                        "goodVotes", "totalVotes", "invalidVotes", "noVotes", "eligibleVoters", "voterTurnoutPercentage"]]
                F_to_csv(df, type, lastUpdate, 'DB_1', mode)
                return True
        raise Exception(f"Read '{BASE_URL}/elections/{electionId}/{type}/statistics' failed.")
    except Exception as e: error_log("F_DB_1_statistics", e)
def F_DB_2_3_national_summary(electionId, type):
    try:
        response = requests.get(f'{BASE_URL}/elections/{electionId}/{type}/national-summary', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                data = data['data']
                lastUpdate = lastUpdate_or_lastUpdated(data)
                df = pd.DataFrame({
                    'totalConstituencySeats': [data['totalConstituencySeats']],
                    'totalPartyListSeats': [data['totalPartyListSeats']],
                    'totalSeats': [data['totalSeats']],
                    'totalVotes': [data['totalVotes']]
                })
                F_to_csv(df, type, lastUpdate, 'DB_2')

                parties = data['parties']
                if len(parties) == 0:
                    raise Exception(f'data["parties"] ไม่มีค่า. ไม่ save file "F_{type[0].upper()}_DB_3.csv"')
                df = pd.DataFrame(parties)
                df_p = pd.json_normalize(df["party"])
                df = df.join(df_p.add_prefix("party"))
                df = df.rename(columns=
                    {
                        "partyid": "partyId",
                        "partycode": "partyCode",
                        "partyname": "partyName",
                        "partycolor": "partyColor"
                    })
                df = df[["partyId", "partyCode", "partyName", "partyColor",
                        "totalVotes", "constituencySeats", "partyListSeats", "totalSeats", "percentage"]]
                F_to_csv(df, type, lastUpdate, 'DB_3')
                return True
        raise Exception(f"Read '{BASE_URL}/elections/{electionId}/{type}/national-summary' failed.")
    except Exception as e: error_log("F_DB_2_3_national_summary", e)

# Many pages
def F_DBD_4_candidates(electionId, type):
    try:
        candidates, lastUpdate = get_all_pages(f'{BASE_URL}/elections/{electionId}/{type}/candidates', 'F_DBD_4_candidates(type="{type}")', 'candidates')
        df = pd.DataFrame(candidates)
        df_p = pd.json_normalize(df["party"])
        df = df.join(df_p.add_prefix("party"))
        df = df.rename(columns=
            {
                "partyid": "partyId",
                "partycode": "partyCode",
                "partyname": "partyName",
                "partycolor": "partyColor"
            })
        df = df[["id", "number", "name", "provinceCode", "provinceName", "areaNumber",
                "partyId", "partyCode", "partyName", "partyColor",
                "totalVotes", "rank", "percentage"]]
        F_to_csv(df, type, lastUpdate, 'DBD_4')
    except Exception as e: error_log("F_DBD_4_candidates", e)
 
def F_RF_referendum(electionId, type):
    try:
        if type == "realtime":
            raise Exception(f'(type="{type}") failed. "เจอปัญหาว่า realtime ไม่มีข้อมูล มีแต่ final"')

        response = requests.get(f'{BASE_URL}/elections/{electionId}/{type}/referendum', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                lastUpdate = lastUpdate_or_lastUpdated(data['data'])
                data = data['data']['questions']
                if len(data) == 0:
                    raise Exception(f'data["data"]["questions"] ไม่มีค่า. ไม่ save file "F_{type[0].upper()}_RF.csv"')
                rows = []
                for q in data:
                    base = {
                        "questionNumber": q["questionNumber"],
                        "questionText": q["questionText"],
                        "goodVotes": q["goodVotes"],
                        "totalVotes": q["totalVotes"],
                        "invalidVotes": q["invalidVotes"],
                        "noVotes": q["noVotes"],
                    }

                    for opt in q["options"]:
                        prefix = opt["optionCode"]  # agree / disagree
                        base[f"{prefix}OptionNumber"] = opt["optionNumber"]
                        base[f"{prefix}TotalVotes"] = opt["totalVotes"]
                        base[f"{prefix}Percentage"] = opt["percentage"]
                        base[f"{prefix}Rank"] = opt["rank"]

                    rows.append(base)
                df = pd.DataFrame(rows)
                df = df[["questionNumber", "questionText", "goodVotes", "totalVotes", "invalidVotes", "noVotes",
                        "agreeOptionNumber", "agreeTotalVotes", "agreePercentage", "agreeRank",
                        "disagreeOptionNumber", "disagreeTotalVotes", "disagreePercentage", "disagreeRank"]]
                F_to_csv(df, type, lastUpdate, 'RF')
                return True
        raise Exception(f"Read '{BASE_URL}/elections/{electionId}/{type}/referendum' failed.")
    except Exception as e: error_log("F_RF_referendum", e)

def main():
    if MASTER:
        M_elections()
        M_provinces()
        # น่าจะไม่ได้ใช้
        # M_candidates() # มี photoUrl ด้วยแต่พวก party list ไม่มีรายชื่ออยู่ในนี้

    df = pd.read_csv(DATA_PATH + 'M_ELECTIONS.csv')
    mp_party_list_id = (df.loc[df["type"] == "mp_party_list", "id"].squeeze())
    mp_constituency_id = (df.loc[df["type"] == "mp_constituency", "id"].squeeze())
    referendum_id = (df.loc[df["type"] == "referendum", "id"].squeeze())

    if MASTER:
        # ส.ส. บัญชีรายชื่อ
        M_party_list(mp_party_list_id)

    if FEED_DB_1_3:
        # อาสาสมัคร
        F_DB_1_statistics(mp_party_list_id, 'realtime', 'p', mode='w') #ขาด 1 value "คะแนนนับแล้ว" คำนวนอย่างไร
        F_DB_1_statistics(mp_constituency_id, 'realtime', 'c', mode='a') #ขาด 1 value "คะแนนนับแล้ว" คำนวนอย่างไร
        F_DB_2_3_national_summary(mp_party_list_id, 'realtime')
        # กกต.
        F_DB_1_statistics(mp_party_list_id, 'final', 'p', mode='w') #ขาด 1 value "คะแนนนับแล้ว" คำนวนอย่างไร
        F_DB_1_statistics(mp_constituency_id, 'final', 'c', mode='a') #ขาด 1 value "คะแนนนับแล้ว" คำนวนอย่างไร
        F_DB_2_3_national_summary(mp_party_list_id, 'final')
    
    if FEED_DB_DETAIL_4:
        F_DBD_4_candidates(mp_constituency_id, 'realtime') # อาสาสมัคร
        F_DBD_4_candidates(mp_constituency_id, 'final') # กกต.

    if FEED_RF:
        # Referundum มีแค่ final ไม่มี realtime
        F_RF_referendum(referendum_id, 'final')

if __name__ == '__main__':
    main()