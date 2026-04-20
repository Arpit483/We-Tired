# VitalRadar - Raspberry Pi Deployment Guide

Complete running code for Raspberry Pi with GPS integration, map visualization, and Firebase sync.

## Features

- ✅ Deep learning model for person detection (using `deep.py` logic)
- ✅ Neo-6M GPS module integration via GPIO/UART
- ✅ Interactive map with yellow dots for detected persons
- ✅ Lat/Long display on hover
- ✅ Firebase Realtime Database integration
- ✅ Original aesthetics preserved
- ✅ SSH deployment script

## Hardware Requirements

- Raspberry Pi (3/4/Zero)
- LD2410 radar sensor (connected to `/dev/ttyUSB0`)
- Neo-6M GPS module (connected via UART or USB-to-Serial)
- Internet connection for Firebase

## GPS Module Connection

The Neo-6M GPS module can be connected in two ways:

### Option 1: USB-to-Serial Adapter
- Connect GPS module to USB-to-Serial adapter
- Usually appears as `/dev/ttyUSB1` or `/dev/ttyACM0`
- Update `PORT` in `neo6m_runner.py` if needed

### Option 2: GPIO UART (Raspberry Pi 3/4)
- Connect GPS TX to GPIO 15 (RXD)
- Connect GPS RX to GPIO 14 (TXD)
- Enable UART: `sudo raspi-config` → Interface Options → Serial Port → Enable
- Usually appears as `/dev/ttyAMA0` or `/dev/ttyS0`
- Update `PORT` in `neo6m_runner.py` accordingly

## Deployment Steps

### 1. Find Raspberry Pi IP Address

On your local machine (same network):
```bash
# Option 1: Use hostname (if mDNS works)
ping raspberrypi.local

# Option 2: Find IP on network
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry Pi"
```

### 2. Deploy to Raspberry Pi

From your local machine:
```bash
# Make deployment script executable
chmod +x deploy_to_pi.sh

# Deploy (replace with your Pi's IP)
./deploy_to_pi.sh 192.168.1.100 pi

# Or use hostname
./deploy_to_pi.sh raspberrypi.local pi
```

The script will:
- Copy all files to `/home/pi/VitalRadar`
- Create virtual environment
- Install all dependencies
- Set up systemd services for auto-start
- Make scripts executable

### 3. Configure GPS Port (if needed)

SSH into Raspberry Pi:
```bash
ssh pi@192.168.1.100
# Password: 21291645
```

Check available serial ports:
```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA* /dev/ttyS*
```

Edit GPS port in `neo6m_runner.py`:
```bash
cd /home/pi/VitalRadar
nano neo6m_runner.py
# Change PORT = "/dev/ttyUSB1" to your GPS port
```

### 4. Start Services

**Option A: Manual Start**
```bash
cd /home/pi/VitalRadar
./start.sh
```

**Option B: Systemd Services**
```bash
# Start all services
sudo systemctl start vitalradar vitalradar-deep vitalradar-gps vitalradar-firebase

# Enable auto-start on boot
sudo systemctl enable vitalradar vitalradar-deep vitalradar-gps vitalradar-firebase

# Check status
sudo systemctl status vitalradar
```

### 5. Access Dashboard

Open in browser:
```
http://192.168.1.100:5050
```
(Replace with your Pi's IP address)

## File Structure

```
VitalRadar/
├── app.py                 # Flask main application
├── deep.py                # Deep learning detection (uses CNN+LSTM model)
├── neo6m_runner.py        # GPS module reader
├── firebase_bridge.py     # Firebase sync
├── ld2410_runner.py       # LD2410 sensor reader (optional)
├── start.sh               # Start all services
├── deploy_to_pi.sh        # Deployment script
├── requirements.txt       # Python dependencies
├── cnn_lstm_fast_final_model.pt  # Trained model
└── app/
    ├── __init__.py
    ├── routes.py          # API endpoints
    ├── models.py          # Database models
    ├── templates/
    │   └── index.html     # Dashboard with map
    └── static/
        └── js/
            └── dashboard.js
```

## How It Works

1. **Deep Learning Detection** (`deep.py`):
   - Reads distance data from LD2410 sensor
   - Uses CNN+LSTM model for breathing detection
   - When person detected, fetches GPS coordinates
   - Sends data to Flask API and Firebase

2. **GPS Module** (`neo6m_runner.py`):
   - Continuously reads NMEA sentences from Neo-6M
   - Parses GPRMC/GPGGA sentences
   - Sends GPS data to Flask API every 5 seconds

3. **Flask API** (`app.py`):
   - Stores predictions and GPS data in SQLite database
   - Serves dashboard at port 5050
   - Provides REST API endpoints

4. **Firebase Bridge** (`firebase_bridge.py`):
   - Syncs latest detections to Firebase Realtime Database
   - Updates every 3 seconds

5. **Dashboard** (`app/templates/index.html`):
   - Shows live detection status
   - Displays map with yellow dots for detected persons
   - Shows lat/long on hover
   - Original aesthetics preserved

## Troubleshooting

### GPS Not Working
```bash
# Check if GPS module is detected
ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA*

# Check GPS logs
tail -f /home/pi/VitalRadar/gps.log

# Test GPS manually
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB1', 9600); print(s.readline())"
```

### Flask Not Starting
```bash
# Check if port 5050 is in use
sudo lsof -i :5050

# Check Flask logs
tail -f /home/pi/VitalRadar/flask.log
```

### Permission Errors
```bash
# Add user to dialout group (for serial ports)
sudo usermod -a -G dialout $USER
newgrp dialout
```

### Model File Missing
Make sure `cnn_lstm_fast_final_model.pt` is in the deployment directory.

## Stopping Services

```bash
# Manual stop
pkill -f 'python.*(app|deep|neo6m|firebase)'

# Systemd stop
sudo systemctl stop vitalradar vitalradar-deep vitalradar-gps vitalradar-firebase
```

## Network Configuration

- Default Flask port: `5050`
- Make sure firewall allows port 5050:
  ```bash
  sudo ufw allow 5050
  ```

## Firebase Configuration

Firebase URL is hardcoded in:
- `deep.py`: `FIREBASE_DB_URL = "https://vital-radar-default-rtdb.firebaseio.com"`
- `firebase_bridge.py`: Same URL

Update these if using a different Firebase project.

## Support

For issues:
1. Check logs in `/home/pi/VitalRadar/*.log`
2. Verify hardware connections
3. Check network connectivity
4. Ensure all dependencies are installed

