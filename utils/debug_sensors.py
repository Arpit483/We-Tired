#!/usr/bin/env python3
"""
Debug script to check VitalRadar sensor data flow
"""

import requests
import json
import sqlite3
import time

def check_database():
    """Check if database has recent dual sensor data"""
    print("🗄️  Checking Database...")
    try:
        conn = sqlite3.connect("app/predictions.db")
        cursor = conn.cursor()
        
        # Check latest records
        cursor.execute("""
            SELECT id, timestamp, breathing, status, direction, 
                   left_detected, left_distance, left_votes,
                   right_detected, right_distance, right_votes
            FROM predictions 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        if rows:
            print(f"   ✅ Found {len(rows)} recent records")
            for row in rows:
                print(f"   📊 ID:{row[0]} | Status:{row[3]} | Left:{row[5]}({row[6]}cm) | Right:{row[8]}({row[9]}cm)")
        else:
            print("   ❌ No records found in database")
            
        conn.close()
        return len(rows) > 0
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def check_api():
    """Check if Flask API is responding with dual sensor data"""
    print("\n🌐 Checking API...")
    try:
        response = requests.get("http://localhost:5050/api/latest", timeout=5)
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            if records:
                latest = records[-1]
                print(f"   ✅ API responding with {len(records)} records")
                print(f"   📊 Latest: Status={latest.get('status')} | Left={latest.get('left_detected')} | Right={latest.get('right_detected')}")
                print(f"   📊 Distances: Left={latest.get('left_distance')}cm | Right={latest.get('right_distance')}cm")
                return True
            else:
                print("   ⚠️  API responding but no records")
                return False
        else:
            print(f"   ❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API connection error: {e}")
        return False

def check_processes():
    """Check if required processes are running"""
    print("\n🔍 Checking Processes...")
    import subprocess
    
    processes = [
        ("Deep Learning", "python.*deep_optimized.py"),
        ("Flask App", "python.*app.py")
    ]
    
    all_running = True
    for name, pattern in processes:
        try:
            result = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"   ✅ {name} running (PIDs: {', '.join(pids)})")
            else:
                print(f"   ❌ {name} not running")
                all_running = False
        except Exception as e:
            print(f"   ❌ Error checking {name}: {e}")
            all_running = False
    
    return all_running

def check_sensors():
    """Check if sensor devices exist"""
    print("\n🔌 Checking Sensors...")
    import os
    
    sensors = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
    all_connected = True
    
    for sensor in sensors:
        if os.path.exists(sensor):
            print(f"   ✅ {sensor} connected")
        else:
            print(f"   ❌ {sensor} not found")
            all_connected = False
    
    return all_connected

def main():
    print("🎯 VitalRadar Debug Check")
    print("=" * 40)
    
    # Check all components
    sensors_ok = check_sensors()
    processes_ok = check_processes()
    db_ok = check_database()
    api_ok = check_api()
    
    print("\n📋 Summary:")
    print("=" * 40)
    print(f"   Sensors Connected: {'✅' if sensors_ok else '❌'}")
    print(f"   Processes Running: {'✅' if processes_ok else '❌'}")
    print(f"   Database Has Data: {'✅' if db_ok else '❌'}")
    print(f"   API Responding: {'✅' if api_ok else '❌'}")
    
    if all([sensors_ok, processes_ok, db_ok, api_ok]):
        print("\n🎉 All systems working! Check website at http://localhost:5050")
    else:
        print("\n🔧 Issues found. Recommendations:")
        if not sensors_ok:
            print("   - Check sensor USB connections")
        if not processes_ok:
            print("   - Run: ./start_vitalradar.sh")
        if not db_ok:
            print("   - Check if deep_optimized.py is sending data")
        if not api_ok:
            print("   - Restart Flask app")

if __name__ == "__main__":
    main()