#!/usr/bin/env python3
"""
LD2410 legacy single-sensor runner.
Posts distance buffer to Flask /api/predict, then reads latest state
from /api/latest to show the full prediction status.

MED-04 fix: /api/predict returns {"ok": true} — the actual prediction
result is fetched separately from /api/latest.
"""
import serial
import time
import requests
from collections import deque
import sys

PORT       = "/dev/ttyUSB0"
BAUD       = 115200
FLASK_BASE = "http://localhost:5050"
FLASK_URL  = f"{FLASK_BASE}/api/predict"
LATEST_URL = f"{FLASK_BASE}/api/latest"
BUFFER_SIZE = 64

distance_buffer = deque(maxlen=BUFFER_SIZE)


def send_to_flask(distances):
    """Post distance array then fetch the prediction from /api/latest."""
    payload = {"distance_series": list(distances)}
    try:
        r = requests.post(FLASK_URL, json=payload, timeout=2)
        if r.status_code == 200:
            post_resp = r.json()
            if post_resp.get("ok"):
                # MED-04: read the actual result from /api/latest, not from the POST response
                latest_r = requests.get(LATEST_URL, timeout=2)
                if latest_r.status_code == 200:
                    pred = latest_r.json()
                    breathing = pred.get("breathing", False)
                    distance  = pred.get("left_distance", pred.get("distance", 0.0))
                    votes     = pred.get("votes", 0)
                    status    = "[OK] DETECTED" if breathing else "[  ] NO SIGNAL"
                    print(
                        f"{status} | "
                        f"Dist:{float(distance) * 100:.1f}cm | "
                        f"Votes:{votes}"
                    )
                else:
                    print(f"[WARN] /api/latest returned HTTP {latest_r.status_code}")
            else:
                print(f"[ERROR] predict: {post_resp.get('error')}")
        else:
            data = {}
            try:
                data = r.json()
            except Exception:
                pass
            print(f"[HTTP {r.status_code}] {data.get('error', r.text[:80])}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Flask not running at {FLASK_BASE}")
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    print("[*] LD2410 Sensor Reader (legacy single-sensor)")
    print(f"[*] Port: {PORT} | Baud: {BAUD}")
    print(f"[*] Flask: {FLASK_URL}\n")

    while True:
        try:
            print("[*] Connecting to sensor...")
            ser = serial.Serial(PORT, BAUD, timeout=0.5)
            print("[+] Connected!\n")

            while True:
                try:
                    line = ser.readline().decode(errors="ignore").strip()
                    if not line or not line.startswith("distance:"):
                        continue
                    try:
                        dist = float(line.split(":")[1])
                    except (ValueError, IndexError):
                        continue

                    distance_buffer.append(dist)
                    print(f"[SENSOR] Distance: {dist:6.1f}cm | Buffer: {len(distance_buffer):2d}/64")

                    if len(distance_buffer) >= 64:
                        send_to_flask(distance_buffer)

                except KeyboardInterrupt:
                    print("\n[EXIT] Shutting down...")
                    ser.close()
                    sys.exit(0)
                except (ValueError, UnicodeDecodeError) as e:
                    print(f"[LINE ERROR] {e}")
                    continue

        except FileNotFoundError:
            print(f"[ERROR] Port {PORT} not found")
            print("[INFO] Check: ls /dev/ttyUSB* /dev/ttyACM*")
        except PermissionError:
            print(f"[ERROR] Permission denied on {PORT}")
            print("[FIX] Run: sudo usermod -a -G dialout $USER && newgrp dialout")
        except serial.serialutil.SerialException as e:
            print(f"[SERIAL ERROR] {e}")
        except KeyboardInterrupt:
            print("\n[EXIT] Shutting down...")
            sys.exit(0)

        print("[*] Retrying in 5 seconds...\n")
        time.sleep(5)


if __name__ == "__main__":
    main()
