# Fix Database Schema and Verify Deep Learning Output

## Problem
The database on the Raspberry Pi has an outdated schema missing the `fft_conf` and `dl_conf` columns. This causes errors like:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: predictions.fft_conf
```

## Solution

### Step 1: Fix Database Schema on Raspberry Pi

Run the database fix script from your local machine:

```bash
./fix_database_on_pi.sh 192.168.13.16 pi
```

This script will:
- Backup the old database (if it exists)
- Delete the old database file
- Allow Flask to recreate it with the correct schema

### Step 2: Deploy Updated Code

Deploy the latest code to the Raspberry Pi:

```bash
./deploy_to_pi.sh 192.168.13.16 pi
```

### Step 3: Restart Services on Raspberry Pi

SSH into the Raspberry Pi and restart the services:

```bash
ssh pi@192.168.13.16
cd ~/Map1\ copy  # or wherever your project is
./start.sh
```

### Step 4: Verify Everything Works

#### A. Check Terminal Output (Deep Learning)

The terminal running `deep.py` should show output like:

```
================================================================================
LD2410 BREATHING DETECTION - CNN+LSTM + FFT
================================================================================
  Frame     Dist     Freq      Pwr      Ent  FFT_Conf  DL_Conf   Votes    Detection         Time
--------------------------------------------------------------------------------
      0   150.25    0.350    125.3     4.25     0.850     0.920   18/32        BREATHING   14:30:15
      1   150.30    0.352    126.1     4.23     0.855     0.925   19/32        BREATHING   14:30:16
```

**Key columns:**
- **Frame**: Frame number
- **Dist**: Distance in cm
- **Freq**: Peak breathing frequency (Hz)
- **Pwr**: Peak power
- **Ent**: Spectral entropy
- **FFT_Conf**: FFT-based confidence score (0.0-1.0)
- **DL_Conf**: Deep learning confidence score (0.0-1.0)
- **Votes**: Voting count (e.g., "18/32" means 18 out of 32 votes)
- **Detection**: "BREATHING" or "NO"
- **Time**: Current time (HH:MM:SS)

#### B. Check Map Display

1. Open the dashboard: `http://192.168.13.16:5050` (or `http://localhost:5050` if accessing locally)

2. The map should show **yellow markers** for each person detection with GPS coordinates

3. Click on a marker to see a popup with:
   - Time
   - Distance
   - Votes
   - **FFT Confidence**: The FFT-based confidence score
   - **DL Confidence**: The deep learning model confidence score
   - Latitude and Longitude

#### C. Check Detection Logs

In the dashboard, the "Detections Log" panel should show:
- Timestamp
- Distance and Votes
- **FFT: X.XXX • DL: X.XXX** (confidence scores)
- Detection reason

#### D. Check Flask Logs

On the Raspberry Pi, check for errors:

```bash
tail -f flask.log
```

You should see successful API calls like:
```
INFO:app.routes:Prediction saved: 123
```

If you see database errors, the schema fix didn't work. Try:
1. Stop all services: `pkill -f 'python.*(app|deep|neo6m|firebase)'`
2. Delete the database manually: `rm app/predictions.db`
3. Restart: `./start.sh`

## Expected Behavior

### Terminal Output (deep.py)
- Shows real-time detection with FFT_Conf and DL_Conf values
- Updates every frame (approximately every 0.1 seconds)
- Shows GPS coordinates when a person is detected
- Format matches the header exactly

### Map Display
- Yellow markers appear when breathing is detected AND GPS coordinates are available
- Markers show FFT and DL confidence in the popup
- Map automatically zooms to show all detection markers

### Dashboard
- Live detection status updates every 2 seconds
- Shows latest FFT and DL confidence values
- Detection count increments when breathing is detected
- Timeline shows chronological detection events

## Troubleshooting

### Database still has errors after fix
1. Make sure Flask is stopped before deleting the database
2. Delete the database: `rm app/predictions.db`
3. Restart Flask: `./start.sh`
4. Flask will automatically create a new database with the correct schema

### No GPS coordinates on map
- Check that `neo6m_runner.py` is running: `ps aux | grep neo6m`
- Check GPS logs: `tail -f gps.log`
- GPS needs a clear view of the sky to get a fix

### Deep learning output not showing
- Check that `deep.py` is running: `ps aux | grep deep`
- Check deep learning logs: `tail -f deep.log`
- Verify the model file exists: `ls -lh cnn_lstm_fast_final_model.pt`

### Map not updating
- Check browser console for JavaScript errors (F12)
- Verify Flask API is responding: `curl http://localhost:5050/api/latest`
- Check that records have GPS coordinates in the database

## Quick Verification Commands

```bash
# On Raspberry Pi, check if services are running
ps aux | grep -E '(app.py|deep.py|neo6m|firebase)'

# Check Flask API
curl http://localhost:5050/api/latest | jq '.records[0] | {fft_conf, dl_conf, breathing, latitude, longitude}'

# Check database schema
sqlite3 app/predictions.db ".schema predictions" | grep -E '(fft_conf|dl_conf)'

# View latest detections
sqlite3 app/predictions.db "SELECT id, breathing, fft_conf, dl_conf, latitude, longitude FROM predictions ORDER BY timestamp DESC LIMIT 5;"
```

## Success Criteria

✅ Terminal shows FFT_Conf and DL_Conf columns  
✅ Map displays yellow markers with GPS coordinates  
✅ Map popups show FFT Confidence and DL Confidence  
✅ Dashboard logs show FFT and DL confidence values  
✅ No database errors in flask.log  
✅ Detections are saved with GPS coordinates when available  

