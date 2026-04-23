

---

## Features

| Feature | Detail |
|---|---|
| 🧠 **CNN+LSTM Inference** | Trained PyTorch model blended with FFT-based confidence scoring |
| 📡 **Dual Sensor Support** | Two LD2410 radar sensors running in parallel (`/dev/ttyUSB0`, `/dev/ttyUSB1`) |
| 🌐 **React Dashboard** | Real-time tactical UI served by Flask with Socket.IO live updates |
| 📊 **Live Telemetry** | Sensor distance, confidence, voting bars, breathing frequency, terminal log |
| 💾 **Detection History** | SQLite-backed history with REST endpoint and chart visualization |
| 🩺 **System Health** | CPU/RAM/temp monitoring with sensor port status |
| 🔁 **Auto-Reconnect** | WebSocket reconnects automatically; sensor threads restart on failure |
| 🍓 **Pi 4 Optimized** | Bounded thread/queue model, minimal memory footprint, FFT fallback if no GPU |

---

## Architecture

```
LD2410 USB0 ──┐
               ├── deep_optimized.py ──► POST /api/predict ──► Flask (app.py)
LD2410 USB1 ──┘       CNN+LSTM                                     │
                     + FFT scoring                          Socket.IO emit
                                                                   │
                                                        React Dashboard (port 5050)
                                                        ├── Dashboard (live sensors)
                                                        ├── BioMetrics (history chart)
                                                        └── System Health (CPU/temp)
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **PyTorch on Pi:** PyTorch is large (~800 MB). The system automatically falls back to FFT-only mode if `torch` is not installed. To use deep learning inference on Pi, install the CPU-only wheel:
> ```bash
> pip install torch==2.0.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
> ```

### 2. Build the frontend (first time only)

```bash
cd app/frontend
npm install
npm run build      # outputs to app/static/
cd ../..
```

### 3. Run the system

```bash
# Terminal 1 — Flask web server
python3 app.py

# Terminal 2 — Dual sensor detection engine
python3 deep_optimized.py
```

### 4. Access the dashboard

```
http://<your-pi-ip>:5050
```

---

## Frontend Development (Hot Reload)

During development, Vite proxies all `/api` and Socket.IO traffic to Flask automatically:

```bash
cd app/frontend
npm run dev        # → http://localhost:3000
```

Flask must be running on port `5050` alongside Vite for the proxy to work.

---

## Deployment on Raspberry Pi

### Automated (recommended)

```bash
chmod +x utils/deploy_to_pi.sh
./utils/deploy_to_pi.sh <PI_IP>
```

### Manual

```bash
# On Pi:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd app/frontend && npm install && npm run build && cd ../..

# Start
python3 app.py &
python3 deep_optimized.py
```

Or use the included management scripts:

```bash
./start_vitalradar.sh    # Start all services
./stop_vitalradar.sh     # Stop all services
./status_vitalradar.sh   # Check status
```

---

## Project Structure

```
vitalradar/
├── deep_optimized.py          # Dual-sensor detection engine (CNN+LSTM + FFT)
├── ld2410_runner.py           # Standalone single-sensor runner
├── check_deep_learning_output.py  # Diagnostic & restart tool
├── app.py                     # Flask entry point (port 5050)
├── app/
│   ├── __init__.py            # Flask app + SocketIO factory
│   ├── routes.py              # API endpoints + SSE streams
│   ├── svminterface.py        # Payload normaliser / DB writer
│   ├── svmmodel.py            # SVM fallback model
│   ├── frontend/              # React + Vite source
│   │   ├── src/
│   │   │   ├── App.jsx
│   │   │   ├── context/SensorContext.jsx   # Global state (useReducer)
│   │   │   ├── hooks/useSocket.js          # Socket.IO client
│   │   │   ├── hooks/useSystemHealth.js    # Polling /api/system
│   │   │   ├── pages/                      # Dashboard, History, SystemHealth, Landing
│   │   │   └── components/                 # SensorPanel, TerminalLog, Charts…
│   │   └── vite.config.js                  # Build → app/static/, dev proxy
│   └── static/                # Built React app (served by Flask)
├── cnn_lstm_fast_final_model.pt   # Trained PyTorch model
├── requirements.txt           # Pinned Python dependencies
├── start_vitalradar.sh
├── stop_vitalradar.sh
├── status_vitalradar.sh
├── utils/deploy_to_pi.sh
└── docs/                      # Deployment guides & troubleshooting
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict` | Receive sensor payload from `deep_optimized.py` |
| `GET`  | `/api/latest` | Latest detection result |
| `GET`  | `/api/history` | Last 500 detection records (SQLite) |
| `GET`  | `/api/system` | CPU, RAM, temp, sensor port status |
| `POST` | `/api/restart` | Restart `deep_optimized.py` (localhost only) |
| `POST` | `/api/stop` | Stop `deep_optimized.py` (localhost only) |
| `GET`  | `/stream/sensors` | SSE stream of sensor updates |
| `GET`  | `/stream/terminal` | SSE stream of terminal log lines |

**Socket.IO events:** `sensor_update`, `terminal_update`

---

## Configuration

All detection parameters are in `Config` at the top of `deep_optimized.py`:

```python
class Config:
    PORTS           = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
    BAUD            = 115200
    SAMPLE_WINDOW   = 64        # samples per inference window (10 Hz → 6.4 s)
    CONFIDENCE_THRESHOLD = 0.85
    VOTING_WINDOW   = 32
    VOTING_THRESHOLD = 18
    BREATH_FREQ_MIN = 0.15      # Hz
    BREATH_FREQ_MAX = 0.67      # Hz
    MODEL_PATH      = "cnn_lstm_fast_final_model.pt"
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Sensor not found | `ls /dev/ttyUSB*` — check cable, try `sudo usermod -a -G dialout $USER` |
| Dashboard shows "SYS_DISCONNECTED" | Flask not running or Socket.IO connection failed — check `python3 app.py` |
| PyTorch model fails to load | Run in FFT-only mode (remove `cnn_lstm_fast_final_model.pt` or let it fall back automatically) |
| `npm run build` fails | Run `npm install` first inside `app/frontend/` |
| API returns 404 in dev | Ensure Flask is running on port `5050` alongside Vite |

See `docs/TROUBLESHOOTING.md` and `docs/PI_DEPLOYMENT_GUIDE.md` for more.

---

## License

MIT License — see [LICENSE](LICENSE) for details.