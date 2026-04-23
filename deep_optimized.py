"""
LD2410 BREATHING DETECTION — DUAL SENSOR VERSION
=================================================
Supports:
- Sensor 1 → /dev/ttyUSB0
- Sensor 2 → /dev/ttyUSB1
Runs two independent detection loops in parallel.
"""

import serial
import numpy as np
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    class DummyNN:
        class Module:
            pass
    nn = DummyNN()
    torch = None
import collections
import time
import threading
from scipy import signal
from scipy.fftpack import fft, fftfreq
import warnings
import requests
import json

warnings.filterwarnings('ignore')

# ── TCN-Attention v2 engine ──────────────────────────────
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(
    _os.path.abspath(__file__)), 'model'))
try:
    from model_tcn_attention_v2 import TCNInferenceEngine
    HAS_TCN = True
except Exception as _e:
    print(f"[!] TCNInferenceEngine import failed: {_e}")
    HAS_TCN = False
    TCNInferenceEngine = None

# =====================================================================================
# CONFIGURATION
# =====================================================================================
class Config:
    PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]   # <--- TWO SENSORS HERE
    BAUD = 115200
    TIMEOUT = 0.5
    MODEL_PATH = _os.path.join("model", "tcn_attention_vitalradar_v2.pt")
    SAMPLE_WINDOW = 64
    BREATH_FREQ_MIN = 0.15
    BREATH_FREQ_MAX = 0.67
    CONFIDENCE_THRESHOLD = 0.85
    VOTING_WINDOW = 32
    VOTING_THRESHOLD = 18
    SAMPLE_PERIOD = 0.1
    VERBOSE = True
    SHOW_FEATURES = True

# =====================================================================================
# MODEL DEFINITION (same as your original)
# =====================================================================================
class FastCNNLSTMModel(nn.Module):
    def __init__(self, num_classes=2, dropout_rate=0.2):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2)
        
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2)
        
        self.dropout_conv = nn.Dropout(dropout_rate)
        self.lstm_input_size = 32 * 16
        self.lstm = nn.LSTM(input_size=self.lstm_input_size,
                           hidden_size=128,
                           num_layers=1,
                           batch_first=True)
        
        self.fc1 = nn.Linear(128, 64)
        self.relu_fc = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x):
        x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x = self.dropout_conv(x)
        
        b, c, h, w = x.size()
        x = x.permute(0, 3, 1, 2).reshape(b, w, -1)
        
        lstm_out, _ = self.lstm(x)
        x = lstm_out[:, -1, :]
        
        x = self.relu_fc(self.fc1(x))
        x = self.dropout_fc(x)
        x = self.fc2(x)
        return x

# =====================================================================================
# FEATURE EXTRACTION — SAME AS ORIGINAL
# =====================================================================================
def extract_breathing_features(dist_array):
    features = {}
    detrended = signal.detrend(dist_array)
    
    try:
        sos = signal.butter(4, 0.15, btype='high', output='sos', fs=10)
        filtered = signal.sosfilt(sos, detrended)
    except:
        filtered = detrended
    
    N = len(filtered)
    dt = Config.SAMPLE_PERIOD
    freqs = fftfreq(N, dt)[:N//2]
    fft_vals = np.abs(fft(filtered))[:N//2]
    
    mask = (freqs >= Config.BREATH_FREQ_MIN) & (freqs <= Config.BREATH_FREQ_MAX)
    if np.any(mask):
        bf = freqs[mask]
        bp = fft_vals[mask]
        idx = np.argmax(bp)
        features["peak_freq"] = bf[idx]
        features["peak_power"] = bp[idx]
    else:
        features["peak_freq"] = 0
        features["peak_power"] = 0
    
    features["rms_power"] = np.sqrt(np.mean(filtered**2))
    features["variance"] = np.var(filtered)
    features["peak_to_peak"] = np.max(filtered) - np.min(filtered)
    
    ps = fft_vals**2
    ps = ps[ps > 0]
    ps /= np.sum(ps) + 1e-10
    features["spectral_entropy"] = -np.sum(ps * np.log2(ps + 1e-10))
    
    zc = np.sum(np.abs(np.diff(np.sign(filtered)))) / 2
    features["zero_crossing_rate"] = zc / len(filtered)
    
    return features

def score_breathing_features(f):
    s = 0
    if Config.BREATH_FREQ_MIN <= f["peak_freq"] <= Config.BREATH_FREQ_MAX:
        s += 0.3
    if f["peak_power"] > 75:
        s += 0.2
    if f["spectral_entropy"] < 5:
        s += 0.2
    if 5 < f["variance"] < 200:
        s += 0.15
    if 2 < f["peak_to_peak"] < 150:
        s += 0.15
    return s

# =====================================================================================
# MODEL LOADING
# =====================================================================================
def load_model(path, device):
    try:
        if not HAS_TORCH:
            raise ImportError("PyTorch is not installed, falling back to FFT.")
        print(f"[+] Loading model: {path}")
        model = FastCNNLSTMModel()
        model.load_state_dict(torch.load(path, map_location=device))
        model.to(device)
        model.eval()
        return model
    except:
        print("[!] Model load failed. Using FFT-only.")
        return None

# =====================================================================================
# WEB INTEGRATION (MINIMAL - DOES NOT CHANGE YOUR LOGIC)
# =====================================================================================
sensor_states = {1: {}, 2: {}}
web_lock = threading.Lock()

import queue
web_queue = queue.Queue(maxsize=100)

def web_worker():
    while True:
        try:
            payload = web_queue.get()
            requests.post("http://localhost:5050/api/predict", json=payload, timeout=0.5)
        except Exception:
            pass

threading.Thread(target=web_worker, daemon=True).start()

def send_to_web(sensor_id, distance, detected, confidence, votes, freq, power):
    """Send data to web interface - does not affect your detection logic"""
    try:
        with web_lock:
            sensor_states[sensor_id] = {
                "detected": detected,
                "distance": distance,
                "confidence": confidence,
                "votes": votes,
                "freq": freq,
                "power": power
            }
            
            # Determine overall status
            s1 = sensor_states.get(1, {})
            s2 = sensor_states.get(2, {})
            
            s1_detected = s1.get("detected", False)
            s2_detected = s2.get("detected", False)
            
            if s1_detected and s2_detected:
                status = "detected"
                direction = "center"
            elif not s1_detected and not s2_detected:
                status = "not_detected"
                direction = "none"
            elif s1_detected and not s2_detected:
                status = "high_chance"
                direction = "move_right"
            else:
                status = "high_chance"
                direction = "move_left"
            
            payload = {
                "breathing": status == "detected",
                "status": status,
                "direction": direction,
                "left_detected": s1_detected,
                "left_distance": s1.get("distance", 0),
                "left_confidence": s1.get("confidence", 0),
                "left_votes": s1.get("votes", 0),
                "left_freq": s1.get("freq", 0),
                "left_power": s1.get("power", 0),
                "right_detected": s2_detected,
                "right_distance": s2.get("distance", 0),
                "right_confidence": s2.get("confidence", 0),
                "right_votes": s2.get("votes", 0),
                "right_freq": s2.get("freq", 0),
                "right_power": s2.get("power", 0),
                "sensor1_detected": s1_detected,
                "sensor1_distance": s1.get("distance", 0),
                "sensor1_confidence": s1.get("confidence", 0),
                "sensor1_votes": s1.get("votes", 0),
                "sensor2_detected": s2_detected,
                "sensor2_distance": s2.get("distance", 0),
                "sensor2_confidence": s2.get("confidence", 0),
                "sensor2_votes": s2.get("votes", 0),
                
                # Required fields for Flask API
                "distance": (s1.get("distance", 0) + s2.get("distance", 0)) / 2,
                "freq": (s1.get("freq", 0) + s2.get("freq", 0)) / 2,
                "power": (s1.get("power", 0) + s2.get("power", 0)) / 2,
                "entropy": (s1.get("confidence", 0) + s2.get("confidence", 0)) / 2,
                "fft_conf": s1.get("confidence", 0),
                "dl_conf": s2.get("confidence", 0),
                "votes": (s1.get("votes", 0) + s2.get("votes", 0)) / 2,
                "voting_window": Config.VOTING_WINDOW,
                "timestamp": int(time.time() * 1000)
            }
            
            # Send to Flask API (non-blocking)
            try:
                web_queue.put_nowait(payload)
            except queue.Full:
                pass
            
    except:
        pass  # Don't let web integration affect your detection

# =====================================================================================
# THREAD WORKER FOR EACH SENSOR (YOUR EXACT ORIGINAL CODE)
# =====================================================================================
import queue

terminal_queue = queue.Queue(maxsize=1000)

def terminal_worker():
    while True:
        try:
            msg = terminal_queue.get()
            requests.post("http://localhost:5050/api/terminal", json={"line": msg}, timeout=0.5)
        except:
            pass

threading.Thread(target=terminal_worker, daemon=True).start()

def tee_print(*args, **kwargs):
    import sys
    msg = " ".join(map(str, args))
    print(*args, **kwargs)
    sys.stdout.flush()
    try:
        terminal_queue.put_nowait(msg)
    except queue.Full:
        pass

def run_sensor(sensor_id, port, tcn_engine, device):
    prefix = f"[S{sensor_id}]"
    tee_print(f"{prefix} Opening {port} ...")
    
    try:
        ser = serial.Serial(port, Config.BAUD, timeout=Config.TIMEOUT)
    except Exception as e:
        tee_print(f"{prefix} Failed to open port {port}: {e}")
        return
    
    tee_print(f"{prefix} Connected to {port}")
    
    dist_buf = collections.deque(maxlen=Config.SAMPLE_WINDOW)
    vote_buf = collections.deque(maxlen=Config.VOTING_WINDOW)
    line_buffer = ""
    frame = 0
    
    try:
        while True:
            try:
                byte = ser.read(1)
                if not byte:
                    continue
                
                char = byte.decode("utf-8", errors="ignore")
                line_buffer += char
                
                if "\n" in line_buffer:
                    parts = line_buffer.split("\n")
                    line_buffer = parts[-1]
                    
                    for line in parts[:-1]:
                        line = line.strip()
                        if not line or not line.startswith("distance:"):
                            continue
                        
                        distance = float(line.split(":")[1])
                        dist_buf.append(distance)
                        
                        if len(dist_buf) < Config.SAMPLE_WINDOW:
                            continue
                        
                        arr = np.array(dist_buf, dtype=np.float32)

                        # LEGACY FILTER: commented out — replaced by TCN-Attention v2
                        # feats = extract_breathing_features(arr)
                        # fft_conf = score_breathing_features(feats)
                        # if model is not None and HAS_TORCH:
                        #     arr_t = torch.tensor(arr, dtype=torch.float32).to(device)
                        #     x_input = arr_t.unsqueeze(0).unsqueeze(0).unsqueeze(0).expand(1, 1, 64, 64)
                        #     with torch.no_grad():
                        #         out = model(x_input)
                        #         prob = torch.softmax(out, dim=1)[0, 1].item()
                        #     ml_conf = prob
                        # else:
                        #     ml_conf = fft_conf
                        # conf = max(fft_conf, ml_conf)

                        # ── TCN-Attention v2 inference ─────────────────────────────
                        if tcn_engine is not None:
                            try:
                                _detected_tcn, conf = tcn_engine.predict(arr)
                            except Exception as _e:
                                tee_print(f"{prefix} TCN predict error: {_e}")
                                conf = 0.0
                        else:
                            # Fallback: FFT-only if engine failed to load
                            feats = extract_breathing_features(arr)
                            conf  = score_breathing_features(feats)

                        # feats is only needed for tee_print freq/power — recompute lightly
                        # if engine ran we still need peak_freq and peak_power for the log line
                        _feats_log = extract_breathing_features(arr)

                        vote_buf.append(1 if conf > Config.CONFIDENCE_THRESHOLD else 0)
                        votes = sum(vote_buf)
                        detected = votes >= Config.VOTING_THRESHOLD
                        
                        status = "🟢 BREATHING" if detected else "⚫ NO"
                        tee_print(f"{prefix} F:{frame:05d}  D:{distance:6.1f}  "
                              f"Freq:{_feats_log['peak_freq']:.3f}  Pow:{_feats_log['peak_power']:.1f}  "
                              f"Conf:{conf:.3f}  Votes:{votes}/{Config.VOTING_WINDOW}  {status}")
                        
                        # Send to web (does not affect detection logic)
                        send_to_web(sensor_id, distance, detected, conf, votes,
                                   _feats_log['peak_freq'], _feats_log['peak_power'])
                        
                        frame += 1
                        
            except Exception as e:
                tee_print(f"{prefix} Error: {e}")
                time.sleep(0.2)
    finally:
        ser.close()
        tee_print(f"{prefix} Closed port {port}")

# =====================================================================================
# MAIN (YOUR EXACT ORIGINAL CODE)
# =====================================================================================
def main():
    device = torch.device("cpu") if HAS_TORCH else "cpu"

    # LEGACY: old CNN+LSTM loader — kept for reference
    # model = load_model(Config.MODEL_PATH, device)

    # Load TCN-Attention v2 engine (shared across both sensor threads)
    if HAS_TCN:
        try:
            tcn_engine = TCNInferenceEngine(Config.MODEL_PATH)
            print("[+] TCNInferenceEngine v2 loaded successfully.")
        except Exception as e:
            print(f"[!] TCN engine load failed: {e}. Will use FFT-only.")
            tcn_engine = None
    else:
        tcn_engine = None
    model = None   # old model no longer used
    
    tee_print("\n=== STARTING TWO LD2410 SENSORS ===\n")
    
    threads = []
    for i, port in enumerate(Config.PORTS, start=1):
        t = threading.Thread(target=run_sensor, args=(i, port, tcn_engine, device))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tee_print("\n=== SHUTTING DOWN ===")

if __name__ == "__main__":
    main()