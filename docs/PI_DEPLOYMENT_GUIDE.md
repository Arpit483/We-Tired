# Raspberry Pi 4 Deployment Guide
## Quick Deployment Commands
### 1. Find Your Pi's IP Address
```bash
# On your Pi (via monitor/keyboard or existing SSH):
hostname -I
# Or scan your network:
nmap -sn 192.168.1.0/24 | grep -B2 "Raspberry Pi"
```
### 2. Deploy Code to Pi
#### Option A: Use the automated script
```bash
# Make script executable
chmod +x deploy_to_pi.sh
# Deploy (replace with your Pi's IP)
./deploy_to_pi.sh 192.168.1.100
```
#### Option B: Manual deployment
```bash
# Copy all files
scp -r . pi@192.168.1.100:/home/pi/vitalradar
# Connect and setup
ssh pi@192.168.1.100
cd /home/pi/vitalradar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Start services
python3 app.py &
python3 deep_optimized.py
```
### 3. Access Your System
- **Web Interface**: `http://192.168.1.100:5050` (replace with your Pi's IP)
- **Terminal Output**: Will appear simultaneously on both Pi terminal and web interface
## Real-time Performance Requirements
The system is optimized for **simultaneous display** (< 100ms latency):
- **WebSocket streaming** for instant terminal output
- **Optimized for Pi 4** memory and CPU constraints
- **No buffering delays** - output appears immediately
- **Preserved formatting** - exact terminal appearance on web
## Monitoring Commands
```bash
# Check if services are running
ssh pi@192.168.1.100 'ps aux | grep python3'
# View real-time logs
ssh pi@192.168.1.100 'tail -f /home/pi/vitalradar/flask.log'
ssh pi@192.168.1.100 'tail -f /home/pi/vitalradar/deep.log'
# Check system resources
ssh pi@192.168.1.100 'htop'
# Check network connections
ssh pi@192.168.1.100 'sudo netstat -tulpn | grep :5050'
```
## Troubleshooting
### If deployment fails:
1. **Check Pi connectivity**: `ping 192.168.1.100`
2. **Verify SSH access**: `ssh pi@192.168.1.100`
3. **Check available space**: `ssh pi@192.168.1.100 'df -h'`
### If web interface doesn't load:
1. **Check Flask is running**: `ssh pi@192.168.1.100 'ps aux | grep app.py'`
2. **Check port 5050**: `ssh pi@192.168.1.100 'sudo netstat -tulpn | grep :5050'`
3. **View Flask logs**: `ssh pi@192.168.1.100 'tail -f /home/pi/vitalradar/flask.log'`
### If terminal output isn't simultaneous:
1. **Check WebSocket connection** in browser developer tools
2. **Verify deep_optimized.py is running**: `ssh pi@192.168.1.100 'ps aux | grep deep_optimized.py'`
3. **Check for serial port issues**: `ssh pi@192.168.1.100 'ls -la /dev/ttyUSB*'`
## File Structure on Pi
```
/home/pi/vitalradar/
├── deep_optimized.py       # Deep learning detection system
├── app.py                  # Flask web server
├── app/                    # Web application
│   ├── routes.py          # API endpoints + WebSocket
│   ├── models.py          # Database models
│   └── templates/index.html # Web interface
├── requirements.txt        # Python dependencies
├── flask.log              # Web server logs
├── deep.log               # Detection system logs
└── venv/                  # Python virtual environment
```