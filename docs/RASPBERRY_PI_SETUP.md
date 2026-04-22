# Raspberry Pi Setup & Deployment Guide
## Quick Start: Deploy, Commit, and Run
### Option 1: Deploy from Your Computer (Recommended)
From your local machine (Mac/PC), deploy the changes to Raspberry Pi:
```bash
# Navigate to project directory
cd "/Users/adityasunildolas/Downloads/Map1 copy"
# Deploy all files to Raspberry Pi
./deploy_to_pi.sh raspberrypi.local pi
# Or if your Pi has a different IP/username:
./deploy_to_pi.sh 192.168.13.16 pi
```
This will:
- Copy all files to `/home/pi/VitalRadar` on the Pi
- Set up virtual environment
- Install dependencies
- Create systemd services (optional)
### Option 2: Manual Setup on Raspberry Pi
If you prefer to work directly on the Pi:
```bash
# 1. SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Password: 21291645
# 2. Navigate to project directory
cd /home/pi/VitalRadar
# 3. If files need to be updated, copy them manually or use git pull
# (If you have a remote repository set up)
```
---
## Committing Changes on Raspberry Pi
### Method 1: Commit from Your Computer (Easiest)
From your local machine, commit changes directly on the Pi:
```bash
# Commit with default message
./commit_on_pi.sh raspberrypi.local pi
# Commit with custom message
./commit_on_pi.sh raspberrypi.local pi "Fix: Database connection errors and 500 status codes"
```
### Method 2: Commit Manually on Raspberry Pi
SSH into the Pi and commit manually:
```bash
# 1. SSH into Raspberry Pi
ssh pi@raspberrypi.local
# 2. Navigate to project
cd /home/pi/VitalRadar
# 3. Initialize git (if not already done)
if [ ! -d ".git" ]; then
    git init
    cat > .gitignore << 'EOF'
*.log
*.db
__pycache__/
*.pyc
venv/
.pids
*.pkl
*.pt
!cnn_lstm_fast_final_model.pt
EOF
fi
# 4. Add all files
git add -A
# 5. Check what will be committed
git status
# 6. Commit with message
git commit -m "Fix: Database connection errors and 500 status codes on Raspberry Pi"
# 7. View commit
git log -1
```
### Suggested Commit Messages
- `"Fix: Database connection errors and 500 status codes on Raspberry Pi"`
- `"Add: SQLite timeout configuration and error handling"`
- `"Fix: /api/latest endpoint returning 500 errors"`
- `"Improve: Error handling and logging for database operations"`
---
## Running the Application on Raspberry Pi
### Method 1: Using start.sh Script (Recommended)
```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Navigate to project
cd /home/pi/VitalRadar
# Activate virtual environment and start all services
./start.sh
```
This will start:
- Flask app (port 5050)
- Deep learning detection
**To stop all services:**
```bash
```
### Method 2: Run Flask Only (For Testing)
```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Navigate to project
cd /home/pi/VitalRadar
# Activate virtual environment
source venv/bin/activate
# Run Flask app
python app.py
```
The app will be available at:
- `http://localhost:5050` (on Pi)
- `http://192.168.13.16:5050` (from other devices on network)
### Method 3: Using systemd Services (Auto-start on Boot)
If you want the services to start automatically on boot:
```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Start all services
sudo systemctl start vitalradar
sudo systemctl start vitalradar-deep
# Enable auto-start on boot
# Check status
sudo systemctl status vitalradar
# View logs
sudo journalctl -u vitalradar -f
```
**To stop services:**
```bash
```
**To disable auto-start:**
```bash
```
---
## Verifying the Fix
After deploying and starting the application:
1. **Check Flask is running:**
   ```bash
   curl http://localhost:5050/api/latest
   ```
2. **Check from browser:**
   - Open: `http://192.168.13.16:5050`
   - The dashboard should load without errors
   - Check browser console (F12) for any errors
3. **Check logs:**
   ```bash
   # On Raspberry Pi
   cd /home/pi/VitalRadar
   tail -f flask.log
   ```
4. **Test API endpoint:**
   ```bash
   # Should return JSON with empty records if database is new
   curl http://localhost:5050/api/latest
   ```
---
## Troubleshooting
### Flask Not Starting
```bash
# Check if port 5050 is in use
sudo lsof -i :5050
# Kill existing process
pkill -f "python.*app.py"
# Check Flask logs
tail -f /home/pi/VitalRadar/flask.log
```
### Database Permission Issues
```bash
# Fix database permissions
cd /home/pi/VitalRadar
chmod 664 app/predictions.db
chown pi:pi app/predictions.db
```
### Virtual Environment Issues
```bash
# Recreate virtual environment
cd /home/pi/VitalRadar
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
### Check Database
```bash
# On Raspberry Pi
cd /home/pi/VitalRadar
source venv/bin/activate
python3 -c "from app import create_app; from app.models import db, Prediction; app = create_app(); app.app_context().push(); print(f'Records: {Prediction.query.count()}')"
```
---
## Quick Reference
### Deploy Changes
```bash
./deploy_to_pi.sh raspberrypi.local pi
```
### Commit on Pi
```bash
./commit_on_pi.sh raspberrypi.local pi "Your commit message"
```
### SSH into Pi
```bash
ssh pi@raspberrypi.local
# Password: 21291645
```
### Start Application
```bash
cd /home/pi/VitalRadar
./start.sh
```
### View Logs
```bash
cd /home/pi/VitalRadar
tail -f flask.log
tail -f deep.log
```
### Stop All Services
```bash
```
---
## Network Access
- **Local access:** `http://localhost:5050` (on Pi)
- **Network access:** `http://192.168.13.16:5050` (from other devices)
- **Find Pi IP:** `hostname -I` (run on Pi)
Make sure firewall allows port 5050:
```bash
sudo ufw allow 5050
```
