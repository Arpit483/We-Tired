#!/usr/bin/env python3
"""
Wait for Flask to be ready before starting other services
"""
import time
import requests
import sys

FLASK_URL = "http://localhost:5050/api/latest"
MAX_WAIT = 30  # Maximum seconds to wait
RETRY_INTERVAL = 1  # Seconds between retries

def wait_for_flask():
    print(f"[*] Waiting for Flask to be ready at {FLASK_URL}...")
    
    for i in range(MAX_WAIT):
        try:
            response = requests.get(FLASK_URL, timeout=2)
            if response.status_code == 200:
                print("[✓] Flask is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            pass
        
        if i % 5 == 0:
            print(f"[*] Still waiting... ({i}/{MAX_WAIT}s)")
        time.sleep(RETRY_INTERVAL)
    
    print(f"[ERROR] Flask did not become ready within {MAX_WAIT} seconds")
    return False

if __name__ == "__main__":
    if wait_for_flask():
        sys.exit(0)
    else:
        sys.exit(1)

