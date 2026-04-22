# VitalRadar - Raspberry Pi Deployment Guide
## Features
- ✅ Deep learning model for person detection (using `deep.py` logic)
- ✅ Interactive map with yellow dots for detected persons
- ✅ Lat/Long display on hover
- ✅ Original aesthetics preserved
- ✅ SSH deployment script
## Hardware Requirements
- Raspberry Pi (3/4/Zero)
- LD2410 radar sensor (connected to `/dev/ttyUSB0`)
### Option 1: USB-to-Serial Adapter
- Usually appears as `/dev/ttyUSB1` or `/dev/ttyACM0`
### Option 2: GPIO UART (Raspberry Pi 3/4)
- Enable UART: `sudo raspi-config` → Interface Options → Serial Port → Enable
- Usually appears as `/dev/ttyAMA0` or `/dev/ttyS0`
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
SSH into Raspberry Pi:
```bash
ssh pi@192.168.1.100
# Password: 21291645
```
Check available serial ports:
```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA* /dev/ttyS*
```
```bash
cd /home/pi/VitalRadar
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
# Enable auto-start on boot
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
   - Continuously reads NMEA sentences from Neo-6M
   - Parses GPRMC/GPGGA sentences
3. **Flask API** (`app.py`):
   - Serves dashboard at port 5050
   - Provides REST API endpoints
   - Updates every 3 seconds
5. **Dashboard** (`app/templates/index.html`):
   - Shows live detection status
   - Displays map with yellow dots for detected persons
   - Shows lat/long on hover
   - Original aesthetics preserved
## Troubleshooting
```bash
ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA*
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
# Systemd stop
```
## Network Configuration
- Default Flask port: `5050`
- Make sure firewall allows port 5050:
  ```bash
  sudo ufw allow 5050
  ```
## Support
For issues:
1. Check logs in `/home/pi/VitalRadar/*.log`
2. Verify hardware connections
3. Check network connectivity
4. Ensure all dependencies are installed
