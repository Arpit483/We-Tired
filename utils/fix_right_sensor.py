#!/usr/bin/env python3
"""
Fix script for right sensor data not appearing on website
"""

import requests
import json
import sqlite3
import time

def test_api_data():
    """Test what data the API is actually returning"""
    print("🔍 Testing API data...")
    try:
        response = requests.get("http://localhost:5050/api/latest")
        if response.status_code == 200:
            data = response.json()
            if data.get('records'):
                latest = data['records'][-1]
                print("📊 Latest API record:")
                print(f"   Status: {latest.get('status', 'N/A')}")
                print(f"   Direction: {latest.get('direction', 'N/A')}")
                print(f"   Left detected: {latest.get('left_detected', 'N/A')}")
                print(f"   Left distance: {latest.get('left_distance', 'N/A')}")
                print(f"   Right detected: {latest.get('right_detected', 'N/A')}")
                print(f"   Right distance: {latest.get('right_distance', 'N/A')}")
                
                # Check if right sensor data exists
                if latest.get('right_distance') is None or latest.get('right_distance') == 0:
                    print("❌ Right sensor data missing from API!")
                    return False
                else:
                    print("✅ Right sensor data found in API")
                    return True
            else:
                print("❌ No records in API response")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def check_database_schema():
    """Check if database has right sensor columns"""
    print("\n🗄️  Checking database schema...")
    try:
        conn = sqlite3.connect("app/predictions.db")
        cursor = conn.cursor()
        
        # Check if right sensor columns exist
        cursor.execute("PRAGMA table_info(predictions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['right_detected', 'right_distance', 'right_confidence', 'right_votes']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All right sensor columns exist")
            
            # Check if there's actual right sensor data
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE right_distance > 0")
            count = cursor.fetchone()[0]
            print(f"📊 Records with right sensor data: {count}")
            
            if count == 0:
                print("❌ No right sensor data in database!")
                return False
            else:
                print("✅ Right sensor data found in database")
                return True
                
        conn.close()
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def send_test_data():
    """Send test dual sensor data to API"""
    print("\n🧪 Sending test dual sensor data...")
    
    test_payload = {
        "breathing": False,
        "status": "not_detected",
        "direction": "none",
        "left_detected": False,
        "left_distance": 100.0,
        "left_confidence": 0.75,
        "left_votes": 5,
        "left_freq": 0.3,
        "left_power": 400.0,
        "right_detected": False,
        "right_distance": 200.0,
        "right_confidence": 0.80,
        "right_votes": 3,
        "right_freq": 0.4,
        "right_power": 500.0,
        "distance": 150.0,
        "freq": 0.35,
        "power": 450.0,
        "entropy": 0.775,
        "fft_conf": 0.75,
        "dl_conf": 0.80,
        "votes": 4,
        "voting_window": 32,
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        response = requests.post("http://localhost:5050/api/predict", json=test_payload)
        if response.status_code == 200:
            print("✅ Test data sent successfully")
            
            # Wait and check if it appears in API
            time.sleep(1)
            if test_api_data():
                print("✅ Test data confirmed in API")
                return True
            else:
                print("❌ Test data not appearing in API")
                return False
        else:
            print(f"❌ Failed to send test data: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test data send failed: {e}")
        return False

def main():
    print("🔧 Right Sensor Data Fix")
    print("=" * 40)
    
    # Step 1: Check database schema
    db_ok = check_database_schema()
    
    # Step 2: Test current API data
    api_ok = test_api_data()
    
    # Step 3: If no right sensor data, send test data
    if not api_ok:
        print("\n🧪 Attempting to fix with test data...")
        test_ok = send_test_data()
        if test_ok:
            print("✅ Right sensor data flow restored!")
        else:
            print("❌ Unable to restore right sensor data flow")
    
    print("\n📋 Recommendations:")
    if not db_ok:
        print("   1. Run database schema update")
        print("   2. Restart Flask app")
    if not api_ok:
        print("   3. Check if deep_optimized.py is running")
        print("   4. Verify both sensors are sending data")
        print("   5. Restart the entire system with ./start_vitalradar.sh")

if __name__ == "__main__":
    main()