#!/usr/bin/env python3
"""
Debug script to compare database content vs API output
"""

import sqlite3
import requests
import json
import os

def check_database_directly():
    """Query database directly to see actual right sensor data"""
    print("🗄️  Direct Database Query:")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect("app/predictions.db")
        cursor = conn.cursor()
        
        # Get latest 3 records with all right sensor data
        cursor.execute("""
            SELECT id, timestamp, status, direction,
                   left_detected, left_distance, left_votes,
                   right_detected, right_distance, right_votes
            FROM predictions 
            WHERE right_distance > 0
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        
        rows = cursor.fetchall()
        print(f"Found {len(rows)} records with right_distance > 0:")
        
        for row in rows:
            print(f"  ID: {row[0]}")
            print(f"    Status: {row[2]} | Direction: {row[3]}")
            print(f"    Left: detected={row[4]}, distance={row[5]}, votes={row[6]}")
            print(f"    Right: detected={row[7]}, distance={row[8]}, votes={row[9]}")
            print()
        
        # Also check the very latest record regardless of right_distance
        cursor.execute("""
            SELECT id, timestamp, status, direction,
                   left_detected, left_distance, left_votes,
                   right_detected, right_distance, right_votes
            FROM predictions 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        latest = cursor.fetchone()
        if latest:
            print("Latest record (regardless of right_distance):")
            print(f"  ID: {latest[0]}")
            print(f"    Status: {latest[2]} | Direction: {latest[3]}")
            print(f"    Left: detected={latest[4]}, distance={latest[5]}, votes={latest[6]}")
            print(f"    Right: detected={latest[7]}, distance={latest[8]}, votes={latest[9]}")
        
        conn.close()
        return rows
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return []

def check_flask_api():
    """Check what Flask API returns"""
    print("\n🌐 Flask API Response:")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:5050/api/latest")
        if response.status_code == 200:
            data = response.json()
            if data.get('records'):
                latest = data['records'][-1]
                print("Latest API record:")
                print(f"  ID: {latest.get('id')}")
                print(f"    Status: {latest.get('status')} | Direction: {latest.get('direction')}")
                print(f"    Left: detected={latest.get('left_detected')}, distance={latest.get('left_distance')}, votes={latest.get('left_votes')}")
                print(f"    Right: detected={latest.get('right_detected')}, distance={latest.get('right_distance')}, votes={latest.get('right_votes')}")
                return latest
            else:
                print("❌ No records in API response")
                return None
        else:
            print(f"❌ API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

def test_flask_model_directly():
    """Test Flask model conversion directly"""
    print("\n🔧 Testing Flask Model Conversion:")
    print("-" * 40)
    
    try:
        # Import Flask app context
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import create_app
        from app.models import Prediction
        
        app = create_app()
        with app.app_context():
            # Get latest prediction using Flask ORM
            latest_pred = Prediction.query.order_by(Prediction.timestamp.desc()).first()
            
            if latest_pred:
                print("Flask ORM result:")
                print(f"  ID: {latest_pred.id}")
                print(f"  Raw right_distance: {latest_pred.right_distance}")
                print(f"  Raw right_detected: {latest_pred.right_detected}")
                print(f"  Raw right_votes: {latest_pred.right_votes}")
                
                # Test as_dict conversion
                dict_result = latest_pred.as_dict()
                print(f"\n  as_dict() right_distance: {dict_result.get('right_distance')}")
                print(f"  as_dict() right_detected: {dict_result.get('right_detected')}")
                print(f"  as_dict() right_votes: {dict_result.get('right_votes')}")
                
                return dict_result
            else:
                print("❌ No predictions found via Flask ORM")
                return None
                
    except Exception as e:
        print(f"❌ Flask model test failed: {e}")
        return None

def main():
    print("🔍 Database vs API Debug")
    print("=" * 50)
    
    # Step 1: Check database directly
    db_records = check_database_directly()
    
    # Step 2: Check Flask API
    api_record = check_flask_api()
    
    # Step 3: Test Flask model directly
    flask_record = test_flask_model_directly()
    
    print("\n📋 Analysis:")
    print("=" * 50)
    
    if db_records and api_record:
        db_latest = db_records[0] if db_records else None
        if db_latest and api_record:
            db_right_dist = db_latest[8]  # right_distance from DB
            api_right_dist = api_record.get('right_distance')
            
            print(f"Database right_distance: {db_right_dist}")
            print(f"API right_distance: {api_right_dist}")
            
            if db_right_dist != api_right_dist:
                print("❌ MISMATCH: Database has right sensor data but API doesn't!")
                print("   Issue is in Flask app data retrieval/conversion")
            else:
                print("✅ Database and API match")
    
    if flask_record:
        print(f"Flask ORM right_distance: {flask_record.get('right_distance')}")

if __name__ == "__main__":
    main()