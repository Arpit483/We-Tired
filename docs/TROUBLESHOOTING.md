# Troubleshooting Connection Refused Errors
## Common Causes and Solutions
### 1. Flask Not Running
**Symptoms:** `Connection refused` when accessing `http://localhost:5050`
**Solution:**
```bash
# Check if Flask is running
ps aux | grep "python.*app.py"
# Check if port 5050 is in use
sudo lsof -i :5050
# Start Flask manually
cd /home/pi/VitalRadar
source venv/bin/activate
python app.py
```
### 2. Services Starting Before Flask is Ready
**Solution:**
- The updated `start.sh` now waits for Flask to be ready
- If issues persist, manually start Flask first, then other services:
```bash
# Terminal 1: Start Flask
python app.py
# Terminal 2: Start other services (after Flask is ready)
python deep.py &
```
### 3. Port Already in Use
**Symptoms:** `Address already in use` error
**Solution:**
```bash
# Find process using port 5050
sudo lsof -i :5050
# Kill the process
sudo kill -9 <PID>
# Or kill all Python processes
pkill -f "python.*app.py"
```
### 4. Firewall Blocking Connections
**Symptoms:** Can't access from other devices on network
**Solution:**
```bash
# Allow port 5050 through firewall
sudo ufw allow 5050
# Or disable firewall temporarily (for testing)
sudo ufw disable
```
### 5. Wrong Host Configuration
**Symptoms:** Services can't connect to Flask
**Check:**
- Flask should run on `0.0.0.0:5050` (all interfaces)
- Other services use `localhost:5050` (same machine)
**Verify in `app.py`:**
```python
app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
```
### 6. Database Lock Issues
**Symptoms:** Flask starts but API calls fail
**Solution:**
```bash
# Check database permissions
ls -la app/predictions.db
# Fix permissions if needed
chmod 664 app/predictions.db
chown pi:pi app/predictions.db
```
## Diagnostic Commands
### Check All Services
```bash
# Check if all processes are running
# Check logs
```
### Test Flask API
```bash
# Test from command line
curl http://localhost:5050/api/latest
```
### Check Network Connectivity
```bash
# Test if Flask is responding
netstat -tuln | grep 5050
# Test from another machine
curl http://<pi-ip>:5050/api/latest
```
## Step-by-Step Recovery
1. **Stop all services:**
   ```bash
   ```
2. **Check for port conflicts:**
   ```bash
   sudo lsof -i :5050
   ```
3. **Start Flask first:**
   ```bash
   cd /home/pi/VitalRadar
   source venv/bin/activate
   python app.py > flask.log 2>&1 &
   ```
4. **Wait for Flask to be ready:**
   ```bash
   python wait_for_flask.py
   ```
5. **Start other services:**
   ```bash
   python deep.py > deep.log 2>&1 &
   ```
6. **Verify all services:**
   ```bash
   ps aux | grep python
   curl http://localhost:5050/api/latest
   ```
## Quick Fix Script
```bash
#!/bin/bash
# Quick fix for connection issues
cd /home/pi/VitalRadar
source venv/bin/activate
# Kill all existing processes
sleep 2
# Start Flask
python app.py > flask.log 2>&1 &
sleep 5
# Wait for Flask
python wait_for_flask.py
# Start other services
python deep.py > deep.log 2>&1 &
echo "All services started. Check logs if issues persist."
```
