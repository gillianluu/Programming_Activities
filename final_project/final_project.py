from dotenv import load_dotenv
import os
import base64
import requests
import json
import csv
from datetime import datetime

load_dotenv()

client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")

CSV_FILE = "tracks.csv"
RESULTS_FILE = "results.json"


# =========================
# GET TOKEN
# =========================
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data)
    return response.json()["access_token"]


# =========================
# GET TRACKS
# =========================
def get_tracks(token):
    headers = {"Authorization": "Bearer " + token}
    url = "https://api.spotify.com/v1/search"

    tracks = []
    limit = 10
    offset = 0

    while len(tracks) < 100:
        params = {
            "q": "pop",
            "type": "track",
            "limit": limit,
            "offset": offset
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if "tracks" not in data:
            print("Error:", data)
            break

        items = data["tracks"]["items"]

        if not items:
            break

        tracks.extend(items)
        offset += limit

    return tracks[:100]


# =========================
# SAVE TO CSV
# =========================
def save_to_csv(tracks):
    existing_ids = set()

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_ids.add(row["track_id"])

    file_exists = os.path.exists(CSV_FILE)

    new_rows = 0

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["date", "track_id", "track_name", "artist"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for track in tracks:
            track_id = track.get("id")
            track_name = track.get("name")

            artists = track.get("artists", [])
            artist_name = artists[0]["name"] if artists else ""

            if not track_id or track_id in existing_ids:
                continue

            writer.writerow({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "track_id": track_id,
                "track_name": track_name,
                "artist": artist_name
            })

            new_rows += 1

    return new_rows


# =========================
# LOAD CSV
# =========================
def load_csv():
    tracks = []

    if not os.path.exists(CSV_FILE):
        return tracks

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tracks.append(row)

    return tracks


# =========================
# ANALYSIS (ONLY MOST COMMON ARTIST)
# =========================
def find_most_common_artist(tracks, new_rows):
    if not tracks:
        return {"error": "No data"}

    counts = {}

    for track in tracks:
        artist = track.get("artist", track.get("artist_name", ""))

        if artist == "":
            continue

        counts[artist] = counts.get(artist, 0) + 1

    most_common = max(counts, key=counts.get)

    return {
        "date_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_rows_added": new_rows,
        "total_tracks": len(tracks),
        "most_common_artist": most_common,
        "count": counts[most_common]
    }


# =========================
# SAVE RESULTS
# =========================
def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)


# =========================
# MAIN
# =========================
def main():
    token = get_token()
    tracks = get_tracks(token)

    new_rows = save_to_csv(tracks)
    all_tracks = load_csv()

    results = find_most_common_artist(all_tracks, new_rows)
    save_results(results)

    print(f"{new_rows} new rows added")
    print("Most common artist:", results["most_common_artist"])


if __name__ == "__main__":
    main()