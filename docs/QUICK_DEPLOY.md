# Quick Deploy & Run Guide

## 🚀 One-Command Deploy & Commit

From your computer, deploy all changes and commit on Raspberry Pi:

```bash
cd "/Users/adityasunildolas/Downloads/Map1 copy"
./deploy_and_commit.sh raspberrypi.local pi
```

Or with custom IP:
```bash
./deploy_and_commit.sh 192.168.13.16 pi
```

---

## 📝 Just Commit (if files already on Pi)

```bash
./commit_on_pi.sh raspberrypi.local pi "Fix: Database errors and 500 status codes"
```

---

## ▶️ Run on Raspberry Pi

### SSH into Pi:
```bash
ssh pi@raspberrypi.local
# Password: 21291645
```

### Start Application:
```bash
cd /home/pi/VitalRadar
./start.sh
```

### Or just Flask (for testing):
```bash
cd /home/pi/VitalRadar
source venv/bin/activate
python app.py
```

---

## ✅ Verify It Works

1. **Check API:**
   ```bash
   curl http://localhost:5050/api/latest
   ```
   Should return JSON (even if empty records), NOT 500 error.

2. **Open Browser:**
   - `http://192.168.13.16:5050`
   - Dashboard should load without errors

3. **Check Logs:**
   ```bash
   cd /home/pi/VitalRadar
   tail -f flask.log
   ```

---

## 🛑 Stop Services

```bash
pkill -f 'python.*(app|deep|neo6m|firebase)'
```

---

## 📋 What Was Fixed

- ✅ SQLite timeout configuration for Raspberry Pi
- ✅ Better error handling in `/api/latest` endpoint
- ✅ Graceful handling of empty database
- ✅ Comprehensive logging for debugging
- ✅ Database connection checks before queries

The `/api/latest` endpoint will now return valid JSON even if:
- Database is empty
- Database has connection issues
- Queries fail

No more 500 errors! 🎉

