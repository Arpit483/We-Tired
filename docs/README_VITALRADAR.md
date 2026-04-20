# VitalRadar Dual Sensor Detection System

🎯 **Real-time breathing detection using dual LD2410 sensors with web interface**

## 🚀 Quick Start

### Start the entire system:
```bash
cd "/home/pi/done 3"
./start_vitalradar.sh
```

### Check system status:
```bash
./status_vitalradar.sh
```

### Stop all services:
```bash
./stop_vitalradar.sh
```

## 🌐 Access Points

- **Web Interface**: http://localhost:5050
- **API Endpoint**: http://localhost:5050/api/latest
- **GPS Data**: http://localhost:5050/api/gps/latest

## 📊 System Components

### 1. **Dual Sensor Detection** (`deep_optimized.py`)
- **Left Sensor**: /dev/ttyUSB0 (Sensor 1)
- **Right Sensor**: /dev/ttyUSB1 (Sensor 2)
- **Detection Logic**:
  - Both sensors detect → **GREEN "DETECTED"**
  - Neither sensor detects → **RED "NOT DETECTED"**
  - One sensor detects → **YELLOW "HIGH CHANCE"**

### 2. **Web Interface** (`app.py`)
- Real-time dual sensor data display
- Interactive map with detection locations
- Direction guidance (Move Left/Right/Centered)
- Auto-zoom to detection locations

### 3. **GPS Tracking** (`neo6m_runner.py`)
- Real-time location tracking
- Detection location mapping
- GPS data logging

### 4. **Firebase Sync** (`firebase_bridge.py`)
- Cloud data synchronization
- Remote monitoring capability

## 📱 Web Interface Features

### Status Display
- **Main Status**: Large indicator showing overall detection status
- **Left Sensor**: Individual status, distance, votes
- **Right Sensor**: Individual status, distance, votes
- **Direction Guidance**: Movement instructions based on sensor data
- **Average Distance**: Combined sensor reading
- **Overall Confidence**: Calculated from both sensors

### Interactive Map
- **Auto-zoom**: Automatically zooms to detection locations
- **Color-coded markers**:
  - 🟢 Green: Confirmed detection (both sensors)
  - 🟡 Yellow: High chance detection (one sensor)
- **Detailed popups**: Sensor data, time, location info

## 🔧 Technical Details

### Sensor Configuration
```python
PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]  # Left, Right sensors
CONFIDENCE_THRESHOLD = 0.85
VOTING_WINDOW = 32
VOTING_THRESHOLD = 18
```

### Detection Logic (Preserved 100%)
- Your original breathing detection algorithm is completely intact
- Web integration is non-intrusive and doesn't affect detection
- All feature extraction and scoring functions unchanged

### Database Schema
- Dual sensor fields: `left_*` and `right_*` columns
- Status tracking: `status`, `direction` fields
- GPS integration: `latitude`, `longitude` fields
- Legacy compatibility: `sensor1_*`, `sensor2_*` aliases

## 📋 Log Files

- `deep_learning.log` - Dual sensor detection output
- `flask_web.log` - Web interface logs
- `gps_tracking.log` - GPS data logs
- `firebase_sync.log` - Cloud sync logs

## 🛠️ Troubleshooting

### Check if sensors are connected:
```bash
ls -la /dev/ttyUSB*
```

### Monitor real-time sensor output:
```bash
tail -f deep_learning.log
```

### Test API manually:
```bash
curl http://localhost:5050/api/latest
```

### Restart individual services:
```bash
# Stop all first
./stop_vitalradar.sh

# Start individual components
source venv/bin/activate
python3 deep_optimized.py &  # Dual sensor detection
python app.py &              # Web interface
python3 neo6m_runner.py &    # GPS tracking
python3 firebase_bridge.py & # Firebase sync
```

## 🎯 System Status Indicators

### Deep Learning Output
```
[S1] F:01234  D:67.0  Freq:0.312  Pow:468.9  Conf:0.700  Votes:0/32  ⚫ NO
[S2] F:01180  D:215.0  Freq:0.469  Pow:1009.7  Conf:0.700  Votes:0/32  ⚫ NO
```

### Web Interface Status
- **Status**: not_detected | high_chance | detected
- **Direction**: none | move_left | move_right | center
- **Individual Sensors**: Distance, votes, confidence per sensor

## ✨ Features

- ✅ **Dual sensor detection** with individual monitoring
- ✅ **Real-time web interface** with 2-second updates
- ✅ **Direction guidance** based on sensor positions
- ✅ **GPS integration** with location mapping
- ✅ **Auto-zoom map** to detection locations
- ✅ **Firebase cloud sync** for remote monitoring
- ✅ **Comprehensive logging** for debugging
- ✅ **Easy startup/shutdown** scripts
- ✅ **Status monitoring** tools

## 🔄 Auto-refresh

The web interface automatically refreshes every 2 seconds to show real-time data from both sensors.

---

**🎯 VitalRadar - Advanced Dual Sensor Person Detection System**