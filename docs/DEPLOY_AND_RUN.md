# Complete Guide: Deploy, Commit & Run on Raspberry Pi
## 🚀 Quick Start (One Command)
From your Mac, run this single command to deploy everything and commit:
```bash
cd "/Users/adityasunildolas/Downloads/Map1 copy"
./deploy_and_commit.sh 192.168.13.16 pi
```
This will:
1. ✅ Deploy all files to Raspberry Pi
2. ✅ Set up virtual environment
3. ✅ Install dependencies
4. ✅ Commit all changes with git
---
## 📋 Step-by-Step Instructions
### Step 1: Deploy Files to Raspberry Pi
From your Mac terminal:
```bash
cd "/Users/adityasunildolas/Downloads/Map1 copy"
./deploy_to_pi.sh 192.168.13.16 pi
```
**What this does:**
- Copies all Python files, app directory, scripts, and model files
- Sets up virtual environment on Pi
- Installs all Python dependencies
- Creates systemd services (optional)
**Expected output:**
```
==========================================
VitalRadar Deployment to Raspberry Pi
==========================================
[*] Testing SSH connection...
[✓] SSH connection successful
[*] Copying files...
[✓] Files copied
[*] Setting up environment...
[✓] Setup complete!
```
### Step 2: Commit Changes on Raspberry Pi
From your Mac terminal:
```bash
./commit_on_pi.sh 192.168.13.16 pi "Fix: Database errors, add DL confidence, improve terminal output"
```
**Or commit manually after SSH:**
```bash
# SSH into Pi
ssh raspberrypi
# Password: 21291645
# Navigate to project
cd /home/pi/VitalRadar
# Initialize git if needed
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
# Add all files
git add -A
# Check what will be committed
git status
# Commit
git commit -m "Fix: Database errors, add DL confidence, improve terminal output and map display"
# View commit
git log -1
```
### Step 3: Run the Application
**Option A: Using start.sh (Recommended)**
```bash
# SSH into Pi
ssh raspberrypi
# Password: 21291645
# Navigate to project
cd /home/pi/VitalRadar
# Start all services
./start.sh
```
**What starts:**
- Flask app (port 5050)
- Deep learning detection (`deep.py`)
**Expected output:**
```
==========================================
Starting VitalRadar System
==========================================
[*] Starting Flask application...
[✓] Flask started (PID: 12345)
[*] Waiting for Flask to be ready...
[✓] Flask is ready!
[*] Starting deep learning detection...
[✓] Deep learning started (PID: 12346)
==========================================
All services started!
==========================================
```
**Option B: Run Flask Only (For Testing)**
```bash
ssh raspberrypi
cd /home/pi/VitalRadar
source venv/bin/activate
python app.py
```
**Option C: Run Deep Learning Only (For Testing)**
```bash
ssh raspberrypi
cd /home/pi/VitalRadar
source venv/bin/activate
python deep.py
```
### Step 4: Verify Everything Works
**1. Check Flask is running:**
```bash
# On your Mac
curl http://192.168.13.16:5050/api/latest
```
Should return JSON (even if empty records), NOT 500 error.
**2. Check Dashboard:**
- Open browser: `http://192.168.13.16:5050`
- Dashboard should load
- Map should be visible
- No errors in browser console (F12)
**3. Check Deep Learning Output:**
```bash
# On Pi
cd /home/pi/VitalRadar
tail -f deep.log
```
Should see formatted table with detections.
**4. Check Logs:**
```bash
# On Pi
cd /home/pi/VitalRadar
tail -f flask.log    # Flask logs
tail -f deep.log     # Deep learning output
```
---
## 🔄 Complete Workflow (All-in-One)
### From Your Mac:
```bash
# 1. Navigate to project
cd "/Users/adityasunildolas/Downloads/Map1 copy"
# 2. Deploy and commit in one step
./deploy_and_commit.sh 192.168.13.16 pi
# 3. SSH into Pi
ssh raspberrypi
# Password: 21291645
# 4. Start application
cd /home/pi/VitalRadar
./start.sh
```
---
## 🛑 Stopping Services
**Stop all services:**
```bash
# On Pi
```
**Or stop individually:**
```bash
# Find process IDs
ps aux | grep python
# Kill specific process
kill <PID>
```
---
## 📊 Viewing Output
### Terminal Output (Deep Learning)
The deep learning script outputs a formatted table:
```
================================================================================================
LD2410 BREATHING DETECTION - CNN+LSTM + FFT
================================================================================================
  Frame     Dist      Freq       Pwr       Ent  FFT_Conf  DL_Conf    Votes      Detection       Time
------------------------------------------------------------------------------------------------
     0   125.50    0.250    85.30    4.20     0.750     0.820   18/32            NO   10:30:45
```
### Dashboard Output
- Open: `http://192.168.13.16:5050`
- See live detections
- Logs show FFT and DL confidence
---
## 🔧 Troubleshooting
### SSH Connection Issues
```bash
# Test connection
ssh raspberrypi
# If fails, try IP directly
ssh pi@192.168.13.16
# Check SSH config
cat ~/.ssh/config
```
### Deployment Fails
```bash
# Test SSH connection first
./test_ssh_connection.sh 192.168.13.16 pi
# Check if Pi is reachable
ping 192.168.13.16
```
### Flask Not Starting
```bash
# On Pi
cd /home/pi/VitalRadar
source venv/bin/activate
# Check if port is in use
sudo lsof -i :5050
# Kill existing process
pkill -f "python.*app.py"
# Start Flask manually
python app.py
```
### Database Errors
```bash
# On Pi
cd /home/pi/VitalRadar
chmod 664 app/predictions.db
chown pi:pi app/predictions.db
# Recreate database if needed
rm app/predictions.db
source venv/bin/activate
python3 -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"
```
### Deep Learning Not Running
```bash
# On Pi
cd /home/pi/VitalRadar
source venv/bin/activate
# Check if model file exists
ls -lh cnn_lstm_fast_final_model.pt
# Run deep learning manually
python deep.py
```
---
## 📝 Git Commands on Pi
### View Commits
```bash
cd /home/pi/VitalRadar
git log
git log --oneline
```
### View Changes
```bash
git status
git diff
```
### Create New Commit
```bash
git add -A
git commit -m "Your commit message"
```
---
## 🎯 Quick Reference
| Task | Command |
|------|---------|
| **Deploy** | `./deploy_to_pi.sh 192.168.13.16 pi` |
| **Commit** | `./commit_on_pi.sh 192.168.13.16 pi "message"` |
| **Deploy + Commit** | `./deploy_and_commit.sh 192.168.13.16 pi` |
| **SSH to Pi** | `ssh raspberrypi` |
| **Start App** | `cd /home/pi/VitalRadar && ./start.sh` |
| **View Logs** | `tail -f deep.log` |
| **Test API** | `curl http://192.168.13.16:5050/api/latest` |
| **Open Dashboard** | `http://192.168.13.16:5050` |
---
## ✅ Success Checklist
After deployment, verify:
- [ ] SSH connection works: `ssh raspberrypi`
- [ ] Files deployed: `ls /home/pi/VitalRadar`
- [ ] Flask starts: `./start.sh` shows all services started
- [ ] API works: `curl http://192.168.13.16:5050/api/latest` returns JSON
- [ ] Dashboard loads: `http://192.168.13.16:5050` opens without errors
- [ ] Deep learning runs: `tail -f deep.log` shows detection table
- [ ] Git commit: `git log` shows your commit
---
## 🚀 Next Steps
1. **Monitor logs** to see detections in real-time
2. **Check dashboard** to see map updates
4. **Test detection** by moving in front of sensor
5. **View terminal output** to see deep learning confidence scores
Everything is ready to deploy and run! 🎉
