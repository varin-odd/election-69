from config import BACKUP_PATH, DATA_PATH, TS_FORMAT, BASE_URL, ODD_KEY, DEBUG, MASTER, FEED_DB_1_3, FEED_DB_DETAIL_4, FEED_RF
from datetime import datetime
import pandas as pd
import requests

HEADERS = {'Authorization': 'Bearer ' + ODD_KEY}

def M_to_csv(df, filename):
    df.to_csv(f'{BACKUP_PATH}M_{filename}_{datetime.now().strftime(TS_FORMAT)}.csv', index=False, encoding="utf-8-sig")
    df.to_csv(f'{DATA_PATH}M_{filename}.csv', index=False, encoding="utf-8-sig")
def M_elections():
    response = requests.get(f'{BASE_URL}/elections', headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            df = pd.DataFrame(data['data']['elections'])
            M_to_csv(df, 'ELECTIONS')
            return True
    raise Exception(f'feed.py: M_elections() failed')
def M_provinces():
    response = requests.get(f'{BASE_URL}/provinces', headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            df = pd.DataFrame(data['data']['provinces'])
            M_to_csv(df, 'PROVINCES')
            return True
    raise Exception(f'feed.py: M_provinces() failed')

def get_all_pages_partyLists(electionId):
    partyLists = []
    page = 1
    limit = 1000

    while True:
        url = f'{BASE_URL}/party-list/{electionId}?page={page}&limit={limit}'
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
           raise Exception(f'feed.py: M_party_list failed')
        data = response.json()
        if not data['success']:
           raise Exception(f'feed.py: M_party_list failed')

        # ดึงข้อมูลของหน้านั้น
        cd = data["data"]["partyLists"]
        partyLists.extend(cd)
        # อ่านข้อมูล pagination
        pagination = data["data"]["pagination"]
        total_pages = pagination["totalPages"]
        if DEBUG: print(f"Fetched page {page}/{total_pages}, items: {len(cd)}")

        if page >= total_pages:
            break
        page += 1

    return partyLists
def M_party_list(electionId):
    partyLists = get_all_pages_partyLists(electionId)
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

def F_to_csv(df, type, filename, mode='w'):
    backup = f'{BACKUP_PATH}F_{type[0].upper()}_{filename}_{datetime.now().strftime(TS_FORMAT)}.csv'
    data = f'{DATA_PATH}F_{type[0].upper()}_{filename}.csv'
    if mode == 'w':
        df.to_csv(backup, index=False, encoding="utf-8-sig")
        df.to_csv(data, index=False, encoding="utf-8-sig")
    elif mode == 'a':
        df.to_csv(backup, index=False, encoding="utf-8-sig", header=False, mode='a')
        df.to_csv(data, index=False, encoding="utf-8-sig", header=False, mode='a')
def F_DB_1_statistics(electionId, type, id, mode):
    response = requests.get(f'{BASE_URL}/elections/{electionId}/{type}/statistics', headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            #print(data['data'])
            df = pd.DataFrame([data['data']['statistics']])
            df['election_id'] = id
            df = df[["election_id",
                     "goodVotes", "totalVotes", "invalidVotes", "noVotes", "eligibleVoters", "voterTurnoutPercentage"]]
            F_to_csv(df, type, 'DB_1', mode)
            return True
    raise Exception(f'feed.py: F_DB_1_statistics failed')
def F_DB_2_3_national_summary(electionId, type):
    response = requests.get(f'{BASE_URL}/elections/{electionId}/{type}/national-summary', headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            data = data['data']
            df = pd.DataFrame({
                'totalConstituencySeats': [data['totalConstituencySeats']],
                'totalPartyListSeats': [data['totalPartyListSeats']],
                'totalSeats': [data['totalSeats']],
                'totalVotes': [data['totalVotes']]
            })
            F_to_csv(df, type, 'DB_2')

            parties = data['parties']
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
            F_to_csv(df, type, 'DB_3')
            return True
    raise Exception(f'feed.py: F_DB_2_3_national_summary(type="{type}") failed')

def get_all_pages_candidates(electionId, type):
    candidates = []
    page = 1
    limit = 1000

    while True:
        url = f'{BASE_URL}/elections/{electionId}/{type}/candidates?page={page}&limit={limit}'
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
           raise Exception(f'feed.py: F_DBD_4_candidates(type="{type}") failed')
        data = response.json()
        if not data['success']:
           raise Exception(f'feed.py: F_DBD_4_candidates(type="{type}") failed')

        # ดึงข้อมูลของหน้านั้น
        cd = data["data"]["candidates"]
        candidates.extend(cd)
        # อ่านข้อมูล pagination
        pagination = data["data"]["pagination"]
        total_pages = pagination["totalPages"]
        if DEBUG: print(f"Fetched page {page}/{total_pages}, items: {len(cd)}")

        if page >= total_pages:
            break
        page += 1

    return candidates
def F_DBD_4_candidates(electionId, type):
    candidates = get_all_pages_candidates(electionId, type)
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
    F_to_csv(df, type, 'DBD_4')
 
def F_RF_referendum(electionId, type):
    if type == "realtime":
        raise Exception(f'feed.py: F_RF_referendum(type="{type}") failed. "เจอปัญหาว่า realtime ไม่มีข้อมูล มีแต่ final"')

    response = requests.get(f'{BASE_URL}/elections/{electionId}/{type}/referendum', headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            data = data['data']['questions']
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
            F_to_csv(df, type, 'RF')
            return True
    raise Exception(f'feed.py: F_RF_referendum(type="{type}") failed')

if __name__ == '__main__':
    try:
        if MASTER:
            M_elections()
            M_provinces()

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

    except Exception as e:
        print(e)