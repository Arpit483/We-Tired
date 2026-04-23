#!/usr/bin/env python3
import serial
import time
import requests
from collections import deque
import sys

PORT = "/dev/ttyUSB0"
BAUD = 115200
FLASK_URL = "http://localhost:5050/api/predict"
BUFFER_SIZE = 64

distance_buffer = deque(maxlen=BUFFER_SIZE)

def send_to_flask(distances):
    """Send distance array to Flask"""
    payload = {"distance_series": list(distances)}
    try:
        r = requests.post(FLASK_URL, json=payload, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                pred = data.get("prediction", {})
                status = "✓ DETECTED" if pred.get("breathing") else "✗ NO SIGNAL"
                print(f"[OK] {status} | Dist:{pred.get('distance'):.1f}cm | Votes:{pred.get('votes')}")
            else:
                print(f"[ERROR] {data.get('error')}")
        else:
            print(f"[HTTP {r.status_code}]")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Flask not running at http://localhost:5050")
    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    print("[*] LD2410 Sensor Reader")
    print(f"[*] Port: {PORT} | Baud: {BAUD}")
    print(f"[*] Flask: {FLASK_URL}\n")
    
    while True:
        try:
            print("[*] Connecting to sensor...")
            ser = serial.Serial(PORT, BAUD, timeout=0.5)
            print("[✓] Connected!\n")
            
            while True:
                try:
                    line = ser.readline().decode(errors="ignore").strip()
                    
                    if not line:
                        continue
                    
                    if not line.startswith("distance:"):
                        continue
                    
                    try:
                        dist = float(line.split(":")[1])
                    except ValueError:
                        continue
                    
                    distance_buffer.append(dist)
                    print(f"[SENSOR] Distance: {dist:6.1f}cm | Buffer: {len(distance_buffer):2d}/64")
                    
                    # Send when buffer full
                    if len(distance_buffer) >= 64:
                        send_to_flask(distance_buffer)
                
                except KeyboardInterrupt:
                    print("\n[EXIT] Shutting down...")
                    ser.close()
                    sys.exit(0)
                except Exception as e:
                    print(f"[LINE ERROR] {e}")
                    continue
        
        except FileNotFoundError:
            print(f"[ERROR] Port {PORT} not found")
            print("[INFO] Check: ls /dev/ttyUSB* /dev/ttyACM*")
        except PermissionError:
            print(f"[ERROR] Permission denied on {PORT}")
            print("[FIX] Run: sudo usermod -a -G dialout $USER && newgrp dialout")
        except Exception as e:
            print(f"[ERROR] {e}")
        
        print("[*] Retrying in 5 seconds...\n")
        time.sleep(5)

if __name__ == "__main__":
    main()
