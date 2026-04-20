#!/usr/bin/env python3
"""
Neo-6M GPS Module Runner
Reads GPS data from Neo-6M module via UART (GPIO pins) and sends to Flask API.
For Raspberry Pi, Neo-6M typically connects via UART (GPIO 14/15) or USB-to-Serial.
"""
import serial
import time
import requests
import sys
import re

# For Raspberry Pi, Neo-6M can be connected via:
# - USB-to-Serial adapter: /dev/ttyUSB0, /dev/ttyUSB1, etc.
# - GPIO UART: /dev/ttyAMA0 (Pi 3/4) or /dev/ttyS0 (Pi Zero)
PORT = "/dev/ttyUSB1"  # Change to your GPS module port
# Common ports: /dev/ttyUSB1, /dev/ttyACM0, /dev/ttyAMA0, /dev/ttyS0
BAUD = 9600  # Neo-6M default baud rate
FLASK_URL = "http://localhost:5050/api/gps"
UPDATE_INTERVAL = 5  # Send GPS data every N seconds

def parse_nmea_sentence(nmea_line):
    """
    Parse NMEA sentence (GPRMC or GPGGA) and extract GPS data.
    Returns dict with GPS data or None if invalid.
    """
    if not nmea_line.startswith('$'):
        return None
    
    # Parse GPRMC sentence (Recommended Minimum Specific GPS/Transit Data)
    if nmea_line.startswith('$GPRMC'):
        try:
            parts = nmea_line.split(',')
            if len(parts) < 12 or parts[2] == '':  # No valid fix
                return None
            
            # Extract data
            time_str = parts[1]
            status = parts[2]  # A=active, V=void
            if status != 'A':
                return None
            
            lat_raw = parts[3]
            lat_dir = parts[4]
            lon_raw = parts[5]
            lon_dir = parts[6]
            speed_knots = parts[7]
            date_str = parts[9]
            
            # Convert latitude
            lat_deg = float(lat_raw[:2])
            lat_min = float(lat_raw[2:])
            latitude = lat_deg + (lat_min / 60.0)
            if lat_dir == 'S':
                latitude = -latitude
            
            # Convert longitude
            lon_deg = float(lon_raw[:3])
            lon_min = float(lon_raw[3:])
            longitude = lon_deg + (lon_min / 60.0)
            if lon_dir == 'W':
                longitude = -longitude
            
            # Convert speed from knots to km/h
            speed_kmh = float(speed_knots) * 1.852 if speed_knots else 0.0
            
            return {
                'latitude': latitude,
                'longitude': longitude,
                'speed': speed_kmh,
                'satellites': 0,  # Not in GPRMC
                'fix_quality': 1,
                'altitude': 0.0,  # Not in GPRMC
                'raw_nmea': nmea_line.strip()
            }
        except (ValueError, IndexError) as e:
            return None
    
    # Parse GPGGA sentence (Global Positioning System Fix Data)
    elif nmea_line.startswith('$GPGGA'):
        try:
            parts = nmea_line.split(',')
            if len(parts) < 15 or parts[6] == '0':  # No fix
                return None
            
            time_str = parts[1]
            latitude_raw = parts[2]
            lat_dir = parts[3]
            longitude_raw = parts[4]
            lon_dir = parts[5]
            fix_quality = int(parts[6])
            satellites = int(parts[7]) if parts[7] else 0
            altitude = float(parts[9]) if parts[9] else 0.0
            
            # Convert latitude
            lat_deg = float(latitude_raw[:2])
            lat_min = float(latitude_raw[2:])
            latitude = lat_deg + (lat_min / 60.0)
            if lat_dir == 'S':
                latitude = -latitude
            
            # Convert longitude
            lon_deg = float(longitude_raw[:3])
            lon_min = float(longitude_raw[3:])
            longitude = lon_deg + (lon_min / 60.0)
            if lon_dir == 'W':
                longitude = -longitude
            
            return {
                'latitude': latitude,
                'longitude': longitude,
                'speed': 0.0,  # Not in GPGGA
                'satellites': satellites,
                'fix_quality': fix_quality,
                'altitude': altitude,
                'raw_nmea': nmea_line.strip()
            }
        except (ValueError, IndexError) as e:
            return None
    
    return None

def send_to_flask(gps_data):
    """Send GPS data to Flask API with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(FLASK_URL, json=gps_data, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    print(f"[OK] GPS: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f} | "
                          f"Alt: {gps_data['altitude']:.1f}m | Speed: {gps_data['speed']:.1f}km/h | "
                          f"Sats: {gps_data['satellites']}")
                    return
                else:
                    print(f"[ERROR] {data.get('error')}")
                    return
            else:
                print(f"[HTTP {r.status_code}] {r.text[:100]}")
                return
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print("[ERROR] Flask not running at http://localhost:5050 - will retry on next GPS update")
        except Exception as e:
            print(f"[ERROR] {e}")
            return

def main():
    print("[*] Neo-6M GPS Module Reader")
    print(f"[*] Port: {PORT} | Baud: {BAUD}")
    print(f"[*] Flask: {FLASK_URL}")
    print(f"[*] Update interval: {UPDATE_INTERVAL}s\n")
    
    last_send_time = 0
    
    while True:
        try:
            print("[*] Connecting to GPS module...")
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print("[✓] Connected! Waiting for GPS fix...\n")
            
            while True:
                try:
                    line = ser.readline().decode(errors="ignore").strip()
                    
                    if not line:
                        continue
                    
                    # Parse NMEA sentence
                    gps_data = parse_nmea_sentence(line)
                    
                    if gps_data is None:
                        continue
                    
                    # Print raw data
                    print(f"[GPS] Lat: {gps_data['latitude']:.6f}, "
                          f"Lon: {gps_data['longitude']:.6f}, "
                          f"Sats: {gps_data['satellites']}, "
                          f"Fix: {gps_data['fix_quality']}")
                    
                    # Send to Flask at intervals
                    current_time = time.time()
                    if current_time - last_send_time >= UPDATE_INTERVAL:
                        send_to_flask(gps_data)
                        last_send_time = current_time
                
                except KeyboardInterrupt:
                    print("\n[EXIT] Shutting down...")
                    ser.close()
                    sys.exit(0)
                except Exception as e:
                    print(f"[LINE ERROR] {e}")
                    continue
        
        except FileNotFoundError:
            print(f"[ERROR] Port {PORT} not found")
            print("[INFO] Check available ports: ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA* /dev/ttyS*")
            print("[INFO] Common GPS ports: /dev/ttyUSB1, /dev/ttyACM0, /dev/ttyAMA0, /dev/ttyS0")
        except PermissionError:
            print(f"[ERROR] Permission denied on {PORT}")
            print("[FIX] Run: sudo usermod -a -G dialout $USER && newgrp dialout")
        except Exception as e:
            print(f"[ERROR] {e}")
        
        print("[*] Retrying in 5 seconds...\n")
        time.sleep(5)

if __name__ == "__main__":
    main()
