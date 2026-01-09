from flask import Flask, render_template, request, jsonify
from config import DATA_PATH
import csv
import os

app = Flask(__name__)


def parse_int(value):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0


def format_int(value):
    return f"{parse_int(value):,}"


def load_party_list_stats(election_id):
    path = os.path.join(DATA_PATH, "F_DB_1.csv")
    with open(path, encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("election_id") == election_id:
                turnout = row.get("voterTurnoutPercentage", "0")
                try:
                    turnout_value = float(turnout)
                except ValueError:
                    turnout_value = 0.0
                return {
                    "turnout_percent": f"{turnout_value:.1f}",
                    "good_votes": format_int(row.get("goodVotes")),
                    "total_votes": format_int(row.get("totalVotes")),
                    "invalid_votes": format_int(row.get("invalidVotes")),
                    "no_votes": format_int(row.get("noVotes")),
                    "eligible_voters": format_int(row.get("eligibleVoters")),
                }
    return {
        "turnout_percent": "0.0",
        "good_votes": "0",
        "total_votes": "0",
        "invalid_votes": "0",
        "no_votes": "0",
        "eligible_voters": "0",
    }


def load_top_parties():
    path = os.path.join(DATA_PATH, "F_DB_3.csv")
    parties = []
    with open(path, encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["totalSeats"] = parse_int(row.get("totalSeats"))
            if row["totalSeats"] > 0:
                parties.append(row)
    parties.sort(key=lambda item: item["totalSeats"], reverse=True)
    cleaned = []
    for item in parties:
        cleaned.append(
            {
                "partyName": item.get("partyName", ""),
                "partyCode": item.get("partyCode", ""),
                "partyColor": item.get("partyColor", "#888888"),
                "totalSeats": item["totalSeats"],
            }
        )
    return cleaned


def load_rank1_candidates(party_code):
    path = os.path.join(DATA_PATH, "F_DBD_4.csv")
    results = []
    with open(path, encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("partyCode") != str(party_code):
                continue
            if parse_int(row.get("rank")) != 1:
                continue
            results.append(
                {
                    "provinceName": row.get("provinceName", ""),
                    "areaNumber": parse_int(row.get("areaNumber")),
                    "name": row.get("name", ""),
                    "totalVotes": format_int(row.get("totalVotes")),
                }
            )
    results.sort(key=lambda item: (item["provinceName"], item["areaNumber"]))
    return results


@app.route("/")
def index():
    page = parse_int(request.args.get("page", 1))
    page = max(page, 1)
    per_page = 5

    stats_party_list = load_party_list_stats("p")
    stats_constituency = load_party_list_stats("c")

    parties = load_top_parties()
    total_parties = len(parties)
    total_pages = max((total_parties + per_page - 1) // per_page, 1)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    paged_parties = parties[start:end]

    return render_template(
        "index.html",
        stats_party_list=stats_party_list,
        stats_constituency=stats_constituency,
        parties=paged_parties,
        page=page,
        total_pages=total_pages,
    )


@app.route("/party/<party_code>")
def party_candidates(party_code):
    candidates = load_rank1_candidates(party_code)
    return jsonify({"partyCode": party_code, "candidates": candidates})


if __name__ == "__main__":
    app.run(debug=True)
