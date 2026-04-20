#!/usr/bin/env python3
"""
Test script to manually send dual sensor data and verify website display
"""

import requests
import json
import time

def send_dual_sensor_data():
    """Send realistic dual sensor data to test the pipeline"""
    
    # Test case 1: Both sensors not detecting
    payload1 = {
        "breathing": False,
        "status": "not_detected",
        "direction": "none",
        "left_detected": False,
        "left_distance": 85.5,
        "left_confidence": 0.65,
        "left_votes": 2,
        "left_freq": 0.312,
        "left_power": 425.3,
        "right_detected": False,
        "right_distance": 195.2,
        "right_confidence": 0.70,
        "right_votes": 1,
        "right_freq": 0.469,
        "right_power": 580.7,
        "distance": 140.35,
        "freq": 0.3905,
        "power": 503.0,
        "entropy": 0.675,
        "fft_conf": 0.65,
        "dl_conf": 0.70,
        "votes": 1.5,
        "voting_window": 32
    }
    
    # Test case 2: Left sensor detecting (high chance)
    payload2 = {
        "breathing": False,
        "status": "high_chance",
        "direction": "move_right",
        "left_detected": True,
        "left_distance": 75.0,
        "left_confidence": 0.90,
        "left_votes": 20,
        "left_freq": 0.25,
        "left_power": 650.0,
        "right_detected": False,
        "right_distance": 220.0,
        "right_confidence": 0.60,
        "right_votes": 5,
        "right_freq": 0.45,
        "right_power": 400.0,
        "distance": 147.5,
        "freq": 0.35,
        "power": 525.0,
        "entropy": 0.75,
        "fft_conf": 0.90,
        "dl_conf": 0.60,
        "votes": 12.5,
        "voting_window": 32
    }
    
    # Test case 3: Both sensors detecting
    payload3 = {
        "breathing": True,
        "status": "detected",
        "direction": "center",
        "left_detected": True,
        "left_distance": 80.0,
        "left_confidence": 0.95,
        "left_votes": 25,
        "left_freq": 0.22,
        "left_power": 750.0,
        "right_detected": True,
        "right_distance": 185.0,
        "right_confidence": 0.88,
        "right_votes": 22,
        "right_freq": 0.24,
        "right_power": 680.0,
        "distance": 132.5,
        "freq": 0.23,
        "power": 715.0,
        "entropy": 0.915,
        "fft_conf": 0.95,
        "dl_conf": 0.88,
        "votes": 23.5,
        "voting_window": 32
    }
    
    test_cases = [
        ("Not Detected", payload1),
        ("High Chance (Left)", payload2),
        ("Detected (Both)", payload3)
    ]
    
    print("🧪 Testing Dual Sensor Data Pipeline")
    print("=" * 50)
    
    for name, payload in test_cases:
        print(f"\n📡 Sending: {name}")
        print(f"   Left: {payload['left_detected']} ({payload['left_distance']}cm)")
        print(f"   Right: {payload['right_detected']} ({payload['right_distance']}cm)")
        print(f"   Status: {payload['status']}")
        
        try:
            response = requests.post("http://localhost:5050/api/predict", json=payload)
            if response.status_code == 200:
                print(f"   ✅ Sent successfully")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(2)  # Wait between sends
    
    print(f"\n🌐 Check website: http://localhost:5050")
    print("   You should see the test data with both sensors!")

if __name__ == "__main__":
    send_dual_sensor_data()