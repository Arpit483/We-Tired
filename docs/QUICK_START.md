# Quick Start Guide

## Deploy to Raspberry Pi (Same Network)

```bash
# 1. Find your Pi's IP (or use raspberrypi.local)
ping raspberrypi.local

# 2. Deploy
./deploy_to_pi.sh raspberrypi.local pi

# 3. SSH and start
ssh pi@raspberrypi.local
# Password: 21291645
cd /home/pi/VitalRadar
./start.sh

# 4. Access dashboard
# Open browser: http://raspberrypi.local:5050
```

## Manual Setup (if deployment script fails)

```bash
# On Raspberry Pi
cd ~
mkdir -p VitalRadar
cd VitalRadar

# Copy files manually or use scp
# Then:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x *.py start.sh
./start.sh
```

## GPS Port Configuration

Edit `neo6m_runner.py` and change:
```python
PORT = "/dev/ttyUSB1"  # Change to your GPS port
```

Common ports:
- USB adapter: `/dev/ttyUSB1`, `/dev/ttyACM0`
- GPIO UART: `/dev/ttyAMA0`, `/dev/ttyS0`

## Check Status

```bash
# View logs
tail -f flask.log deep.log gps.log firebase.log

# Check processes
ps aux | grep python

# Check Flask
curl http://localhost:5050/api/latest
```

## Stop Services

```bash
pkill -f 'python.*(app|deep|neo6m|firebase)'
```

