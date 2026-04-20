import time
import requests

# Flask API on the Pi
FLASK_LATEST_URL = "http://localhost:5050/api/latest"
FLASK_GPS_CURRENT_URL = "http://localhost:5050/api/gps/current"

# Firebase Realtime Database URL
FIREBASE_DB_URL = "https://vital-radar-default-rtdb.firebaseio.com"

def push_to_firebase(record):
    """
    Push one record to Firebase under /vitalradar/<timestamp_ms>.
    """
    ts = int(time.time() * 1000)
    url = f"{FIREBASE_DB_URL}/vitalradar/{ts}.json"
    print("[FIREBASE] PUT", url)
    try:
        r = requests.put(url, json=record, timeout=2.0)
        print("[FIREBASE] status", r.status_code, r.text[:80])
        r.raise_for_status()
    except Exception as e:
        print("[FIREBASE ERROR]", e)

def get_latest_from_flask():
    """
    Fetch latest window of detections from Flask backend.
    Returns list of records (may be empty).
    """
    try:
        r = requests.get(FLASK_LATEST_URL, timeout=2.0)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.ConnectionError:
        # Flask not ready yet, return empty list
        return []
    except Exception as e:
        print("[FLASK ERROR]", e)
        return []

    # Your /api/latest returns { records: [...], ... }
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("records"), list):
            return data["records"]
        if isinstance(data.get("data"), list):
            return data["data"]
    return []

def get_current_gps():
    """
    Fetch current GPS data from Flask backend.
    Returns GPS dict or None if unavailable.
    """
    try:
        r = requests.get(FLASK_GPS_CURRENT_URL, timeout=1.0)
        r.raise_for_status()
        data = r.json()
        if data.get("ok") and data.get("data"):
            return data["data"]
    except Exception as e:
        # GPS unavailable is not critical, just skip
        pass
    return None

def main():
    print("[*] Firebase bridge starting; polling Flask every 3s.")
    last_timestamp = None

    while True:
        records = get_latest_from_flask()
        if not records:
            time.sleep(3)
            continue

        # Take the last (latest) record
        latest = records[-1]
        ts = latest.get("timestamp") or latest.get("time")

        # Avoid writing duplicates if timestamp hasn't changed
        if ts is not None and ts == last_timestamp:
            time.sleep(3)
            continue

        # Try to get current GPS data and attach it
        gps_data = get_current_gps()
        if gps_data:
            latest["gps"] = gps_data

        print("[BRIDGE] New latest record:", ts, latest)
        push_to_firebase(latest)
        last_timestamp = ts
        time.sleep(3)

if __name__ == "__main__":
    main()
