# Deep Learning Output & Map Display Guide

## ✅ What Was Fixed/Enhanced

### 1. **Database Model Updates**
- Added `fft_conf` (FFT confidence) column to store FFT-based confidence scores
- Added `dl_conf` (Deep Learning confidence) column to store CNN+LSTM model confidence
- Both values are now stored and returned in API responses

### 2. **Enhanced Terminal Output**
- Clear header with detection parameters
- Real-time timestamp for each frame
- GPS coordinates displayed when person is detected
- Detailed detection logs with all metrics
- Better error handling and model loading messages

### 3. **Map Visualization**
- Map shows yellow markers for all detections with GPS coordinates
- Popup displays:
  - Deep Learning confidence
  - FFT confidence
  - Distance, votes, and GPS coordinates
- Tooltip shows DL confidence and coordinates on hover

### 4. **API Integration**
- Deep learning confidence (`dl_conf`) is stored in database
- FFT confidence (`fft_conf`) is stored in database
- Both are included in `/api/latest` response
- Dashboard displays both confidence scores

## 📊 Terminal Output Format

When running `deep.py`, you'll see:

```
================================================================================================
LD2410 BREATHING DETECTION - CNN+LSTM + FFT
================================================================================================
  Frame     Dist      Freq       Pwr       Ent  FFT_Conf  DL_Conf    Votes      Detection       Time
------------------------------------------------------------------------------------------------
[*] Starting detection loop...
[*] Deep Learning Model: CNN+LSTM
[*] Detection Threshold: 0.85 | Voting Window: 32
[*] GPS enabled: Will attach coordinates on detection
------------------------------------------------------------------------------------------------

     0   125.50    0.250    85.30    4.20     0.750     0.820   18/32            NO   10:30:45
     1   125.80    0.255    86.10    4.15     0.760     0.835   19/32            NO   10:30:46
    14   133.50    0.320    99.50    3.50     1.000     0.998   32/32      BREATHING   10:30:59 | GPS: 37.774929, -122.419418
[DETECTION] Frame 14: BREATHING | Distance: 133.50cm | FFT: 1.000 | DL: 0.998 | Votes: 32/32 | GPS: 37.774929, -122.419418
```

## 🗺️ Map Display

### What Shows on Map:
- **Yellow markers** for each detection with GPS coordinates
- **Popup on click** shows:
  - Person Detected (Deep Learning)
  - Time, Distance, Votes
  - FFT Confidence
  - DL Confidence (Deep Learning)
  - GPS coordinates

### When Markers Appear:
- `breathing == true` (person detected)
- GPS coordinates are available (`latitude` and `longitude` not null)
- Automatically updates every 2 seconds

## 🔍 Verification Steps

### 1. Check Terminal Output
```bash
# On Raspberry Pi
cd /home/pi/VitalRadar
source venv/bin/activate
python deep.py
```

**Expected:**
- Model loads successfully
- Table header appears
- Real-time detection data streams
- GPS coordinates show when person detected

### 2. Check Database
```bash
# On Raspberry Pi
cd /home/pi/VitalRadar
source venv/bin/activate
python3 -c "
from app import create_app
from app.models import db, Prediction
app = create_app()
with app.app_context():
    latest = Prediction.query.order_by(Prediction.timestamp.desc()).first()
    if latest:
        print(f'Latest: breathing={latest.breathing}, dl_conf={latest.dl_conf}, fft_conf={latest.fft_conf}')
        print(f'GPS: {latest.latitude}, {latest.longitude}')
    else:
        print('No records yet')
"
```

### 3. Check API Response
```bash
# Test API endpoint
curl http://localhost:5050/api/latest | python -m json.tool
```

**Expected JSON:**
```json
{
  "total_detections": 10,
  "breathing_count": 3,
  "avg_votes": 25,
  "max_distance": 150.5,
  "records": [
    {
      "id": 1,
      "timestamp": "2025-12-10T10:30:59",
      "breathing": true,
      "freq": 0.320,
      "power": 99.5,
      "entropy": 3.5,
      "distance": 133.5,
      "votes": 32,
      "fft_conf": 1.000,
      "dl_conf": 0.998,
      "latitude": 37.774929,
      "longitude": -122.419418
    }
  ]
}
```

### 4. Check Dashboard
1. Open browser: `http://192.168.13.16:5050`
2. Check "Detections Log" - should show FFT and DL confidence
3. Check map - yellow markers should appear for detections with GPS
4. Click markers - popup should show DL confidence

## 🚀 Running Everything

### Start All Services:
```bash
cd /home/pi/VitalRadar
./start.sh
```

This starts:
- Flask app (port 5050)
- Deep learning detection (`deep.py`)
- GPS module (`neo6m_runner.py`)
- Firebase bridge

### View Logs:
```bash
# Terminal output from deep learning
tail -f deep.log

# Flask logs
tail -f flask.log

# GPS logs
tail -f gps.log
```

## 📋 Output Fields Explained

| Field | Description | Range |
|-------|-------------|-------|
| **Frame** | Sequential detection frame number | 0+ |
| **Dist** | Distance from sensor (cm) | 0-600 |
| **Freq** | Peak breathing frequency (Hz) | 0.15-0.67 |
| **Pwr** | Peak power in frequency domain | 0+ |
| **Ent** | Spectral entropy | 0-10 |
| **FFT_Conf** | FFT-based confidence | 0.0-1.0 |
| **DL_Conf** | Deep Learning (CNN+LSTM) confidence | 0.0-1.0 |
| **Votes** | Positive votes in window | 0-32 |
| **Detection** | Status: "BREATHING" or "NO" | - |
| **Time** | Current time (HH:MM:SS) | - |
| **GPS** | Coordinates (if detected) | lat, lon |

## 🎯 Key Features

1. **Dual Confidence Scores**: Both FFT and Deep Learning confidence are tracked
2. **GPS Integration**: Coordinates automatically attached when person detected
3. **Real-time Map**: Live updates every 2 seconds with detection markers
4. **Detailed Logging**: Terminal shows all metrics in formatted table
5. **Error Handling**: Graceful fallback if model doesn't load

## 🔧 Troubleshooting

**No DL confidence?**
- Check if model file exists: `cnn_lstm_fast_final_model.pt`
- Script will use FFT-only mode if model fails to load
- Check terminal for model loading messages

**No GPS on map?**
- Ensure `neo6m_runner.py` is running
- Check GPS module connection
- Verify `/api/gps/current` returns data

**No terminal output?**
- Check serial port: `/dev/ttyUSB0` (or correct port)
- Verify sensor is sending data
- Check `deep.log` for errors

**Map not updating?**
- Check browser console (F12) for errors
- Verify `/api/latest` returns records with GPS
- Ensure Flask is running on port 5050

