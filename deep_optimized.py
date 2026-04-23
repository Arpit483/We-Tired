"""
LD2410 BREATHING DETECTION — DUAL SENSOR VERSION
=================================================
Supports:
- Sensor 1 → /dev/ttyUSB0
- Sensor 2 → /dev/ttyUSB1
Runs two independent detection loops in parallel.
"""

import serial
import serial.serialutil  # explicit so we can catch SerialException
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
import queue
import logging
import os
import sys

warnings.filterwarnings('ignore')

# Set up module-level logger (replaces bare print for errors)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger("deep_optimized")

# ── TCN-Attention v2 engine ──────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model'))
try:
    from model_tcn_attention_v2 import TCNInferenceEngine
    HAS_TCN = True
except Exception as _e:
    logger.warning("[!] TCNInferenceEngine import failed: %s", _e)
    HAS_TCN = False
    TCNInferenceEngine = None

# =====================================================================================
# CONFIGURATION
# =====================================================================================
class Config:
    PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
    BAUD = 115200
    TIMEOUT = 0.5
    MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model', 'tcn_attention_vitalradar_v2.pt')
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
# MODEL DEFINITION (kept for reference — no longer used for inference)
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
                            hidden_size=128, num_layers=1, batch_first=True)
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
        return self.fc2(x)


# =====================================================================================
# FEATURE EXTRACTION
# =====================================================================================
def extract_breathing_features(dist_array):
    features = {}
    detrended = signal.detrend(dist_array)
    try:
        sos = signal.butter(4, 0.15, btype='high', output='sos', fs=10)
        filtered = signal.sosfilt(sos, detrended)
    except ValueError:
        filtered = detrended

    N = len(filtered)
    dt = Config.SAMPLE_PERIOD
    freqs = fftfreq(N, dt)[:N // 2]
    fft_vals = np.abs(fft(filtered))[:N // 2]

    mask = (freqs >= Config.BREATH_FREQ_MIN) & (freqs <= Config.BREATH_FREQ_MAX)
    if np.any(mask):
        bf = freqs[mask]
        bp = fft_vals[mask]
        idx = np.argmax(bp)
        features["peak_freq"] = bf[idx]
        features["peak_power"] = bp[idx]
    else:
        features["peak_freq"] = 0.0
        features["peak_power"] = 0.0

    features["rms_power"] = np.sqrt(np.mean(filtered ** 2))
    features["variance"] = np.var(filtered)
    features["peak_to_peak"] = float(np.max(filtered) - np.min(filtered))

    ps = fft_vals ** 2
    ps = ps[ps > 0]
    ps /= np.sum(ps) + 1e-10
    features["spectral_entropy"] = float(-np.sum(ps * np.log2(ps + 1e-10)))

    zc = np.sum(np.abs(np.diff(np.sign(filtered)))) / 2
    features["zero_crossing_rate"] = zc / len(filtered)
    return features


def score_breathing_features(f):
    s = 0.0
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
# LEGACY MODEL LOADER (unused in inference — kept for reference)
# =====================================================================================
def load_model(path, device):
    try:
        if not HAS_TORCH:
            raise ImportError("PyTorch not installed.")
        logger.info("[+] Loading legacy CNN+LSTM model: %s", path)
        model = FastCNNLSTMModel()
        model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
        model.to(device)
        model.eval()
        return model
    except Exception as exc:
        logger.warning("[!] Legacy model load failed (%s). FFT-only mode.", exc)
        return None


# =====================================================================================
# SCAN MODE LOGIC
# =====================================================================================
_scan_active   = threading.Event()   # set = scan running
_scan_stop     = threading.Event()   # set = stop requested  
_scan_results  = []                  # collects per-frame results during scan
_scan_lock     = threading.Lock()

def start_scan(duration=10.0):
    """Clear results, arm scan window, auto-stop after duration seconds."""
    _scan_stop.clear()
    with _scan_lock:
        _scan_results.clear()
    _scan_active.set()
    
    def _scan_timer():
        end_time = time.time() + duration
        while time.time() < end_time:
            if _scan_stop.is_set():
                break
            time.sleep(0.1)
        _scan_active.clear()
        
    threading.Thread(target=_scan_timer, daemon=True).start()

def stop_scan():
    """Immediately end scan and return aggregated result dict."""
    _scan_stop.set()
    _scan_active.clear()
    with _scan_lock:
        total_frames = len(_scan_results)
        if total_frames == 0:
            return {
                "human_present": False,
                "confidence": 0.0,
                "sensor1_votes": 0,
                "sensor2_votes": 0,
                "total_frames": 0,
                "scan_duration": 0.0
            }
        
        s1_votes = sum(1 for r in _scan_results if r["sensor_id"] == 1 and r["detected"])
        s2_votes = sum(1 for r in _scan_results if r["sensor_id"] == 2 and r["detected"])
        avg_conf = sum(r["confidence"] for r in _scan_results) / total_frames
        
        start_t = _scan_results[0]["timestamp"]
        end_t = _scan_results[-1]["timestamp"]
        dur = end_t - start_t

        s1_frames = sum(1 for r in _scan_results if r["sensor_id"] == 1)
        s2_frames = sum(1 for r in _scan_results if r["sensor_id"] == 2)
        
        # Decision rule: human_present = True if >50% of frames across either sensor report detected=True AND avg confidence > 0.6
        s1_present = (s1_votes > s1_frames * 0.5) if s1_frames > 0 else False
        s2_present = (s2_votes > s2_frames * 0.5) if s2_frames > 0 else False
        
        human_present = (s1_present or s2_present) and avg_conf > 0.6

        return {
            "human_present": bool(human_present),
            "confidence": float(avg_conf),
            "sensor1_votes": s1_votes,
            "sensor2_votes": s2_votes,
            "total_frames": total_frames,
            "scan_duration": round(dur, 2)
        }


# =====================================================================================
# WEB INTEGRATION
# =====================================================================================
sensor_states = {1: {}, 2: {}}
web_lock = threading.Lock()
# MED-07: tcn_lock removed — PyTorch CPU forward passes are thread-safe for read-only
# inference on the same model. Each call operates on independent tensors.

web_queue = queue.Queue(maxsize=100)


def web_worker():
    """Background thread: drain web_queue and POST to Flask."""
    while True:
        try:
            payload = web_queue.get()
            requests.post("http://localhost:5050/api/predict", json=payload, timeout=0.5)
        except requests.exceptions.RequestException:
            pass  # Flask may not be up yet; silently retry
        except Exception as exc:
            logger.warning("web_worker unexpected error: %s", exc)


threading.Thread(target=web_worker, daemon=True).start()


def send_to_web(sensor_id, distance, detected, confidence, votes, freq, power):
    """Assemble combined payload and enqueue it for the web_worker."""
    # HIGH-01: only catch errors we expect here; let SystemExit/KeyboardInterrupt propagate
    try:
        with web_lock:
            sensor_states[sensor_id] = {
                "detected": detected,
                "distance": distance,
                "confidence": confidence,
                "votes": votes,
                "freq": freq,
                "power": power,
            }
            s1 = sensor_states.get(1, {})
            s2 = sensor_states.get(2, {})
            s1_detected = s1.get("detected", False)
            s2_detected = s2.get("detected", False)

            if s1_detected and s2_detected:
                status, direction = "detected", "center"
            elif not s1_detected and not s2_detected:
                status, direction = "not_detected", "none"
            elif s1_detected:
                status, direction = "high_chance", "move_right"
            else:
                status, direction = "high_chance", "move_left"

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
                "distance": (s1.get("distance", 0) + s2.get("distance", 0)) / 2,
                "freq": (s1.get("freq", 0) + s2.get("freq", 0)) / 2,
                "power": (s1.get("power", 0) + s2.get("power", 0)) / 2,
                "entropy": (s1.get("confidence", 0) + s2.get("confidence", 0)) / 2,
                "fft_conf": s1.get("confidence", 0),
                "dl_conf": s2.get("confidence", 0),
                "votes": (s1.get("votes", 0) + s2.get("votes", 0)) / 2,
                "voting_window": Config.VOTING_WINDOW,
                "timestamp": int(time.time() * 1000),
            }

        try:
            web_queue.put_nowait(payload)
        except queue.Full:
            pass

    except (ValueError, TypeError, KeyError) as exc:
        # HIGH-01: log data-level errors but don't crash the detection loop
        logger.warning("send_to_web data error (s%s): %s", sensor_id, exc)


# =====================================================================================
# TERMINAL RELAY
# =====================================================================================
terminal_queue = queue.Queue(maxsize=1000)


def terminal_worker():
    while True:
        try:
            msg = terminal_queue.get()
            requests.post(
                "http://localhost:5050/api/terminal",
                json={"line": msg},
                timeout=0.5,
            )
        except requests.exceptions.RequestException:
            pass
        except Exception as exc:
            logger.warning("terminal_worker error: %s", exc)


threading.Thread(target=terminal_worker, daemon=True).start()


def tee_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(*args, **kwargs)
    sys.stdout.flush()
    try:
        terminal_queue.put_nowait(msg)
    except queue.Full:
        pass


# =====================================================================================
# SENSOR LOOP
# =====================================================================================
def run_sensor(sensor_id, port, tcn_engine, device):
    """
    Read distance frames from one LD2410 sensor and run TCN inference.

    HIGH-01: exception handling is now targeted:
      - serial.SerialException  → recoverable hardware errors
      - ValueError / UnicodeDecodeError → malformed sensor line
      - SystemExit / KeyboardInterrupt → always propagated (not caught)
    """
    prefix = f"[S{sensor_id}]"
    tee_print(f"{prefix} Opening {port} ...")

    try:
        ser = serial.Serial(port, Config.BAUD, timeout=Config.TIMEOUT)
    except (serial.serialutil.SerialException, OSError) as e:
        tee_print(f"{prefix} Failed to open port {port}: {e}")
        return

    tee_print(f"{prefix} Connected to {port}")

    dist_buf  = collections.deque(maxlen=Config.SAMPLE_WINDOW)
    vote_buf  = collections.deque(maxlen=Config.VOTING_WINDOW)
    line_buf  = ""
    frame     = 0

    try:
        while True:
            # HIGH-01: catch only recoverable serial / parse errors inside the loop
            try:
                byte = ser.read(1)
                if not byte:
                    continue

                char = byte.decode("utf-8", errors="ignore")
                line_buf += char

                if "\n" not in line_buf:
                    continue

                parts   = line_buf.split("\n")
                line_buf = parts[-1]

                for raw_line in parts[:-1]:
                    raw_line = raw_line.strip()
                    if not raw_line or not raw_line.startswith("distance:"):
                        continue

                    try:
                        distance = float(raw_line.split(":")[1])
                    except (ValueError, IndexError):
                        continue

                    dist_buf.append(distance)
                    if len(dist_buf) < Config.SAMPLE_WINDOW:
                        continue

                    arr = np.array(dist_buf, dtype=np.float32)

                    # MED-03: compute features once, reuse for both logging and fallback
                    feats = extract_breathing_features(arr)

                    # ── TCN-Attention v2 inference (MED-07: no tcn_lock needed) ──
                    if tcn_engine is not None:
                        try:
                            _detected_tcn, conf = tcn_engine.predict(arr)
                        except Exception as tcn_err:
                            logger.error("%s TCN predict error: %s", prefix, tcn_err)
                            conf = score_breathing_features(feats)  # fallback
                    else:
                        conf = score_breathing_features(feats)

                    if Config.VERBOSE:
                        freq_str = f"{feats['peak_freq']:.3f}"
                        pow_str  = f"{feats['peak_power']:.1f}"
                    else:
                        freq_str = pow_str = "-"

                    vote_buf.append(1 if conf > Config.CONFIDENCE_THRESHOLD else 0)
                    votes    = sum(vote_buf)
                    detected = votes >= Config.VOTING_THRESHOLD

                    status = "BREATHING" if detected else "NO"
                    tee_print(
                        f"{prefix} F:{frame:05d}  D:{distance:6.1f}  "
                        f"Freq:{freq_str}  Pow:{pow_str}  "
                        f"Conf:{conf:.3f}  Votes:{votes}/{Config.VOTING_WINDOW}  {status}"
                    )

                    freq_val = feats["peak_freq"] if Config.VERBOSE else 0.0
                    pow_val  = feats["peak_power"] if Config.VERBOSE else 0.0
                    send_to_web(sensor_id, distance, detected, conf, votes, freq_val, pow_val)
                    
                    if _scan_active.is_set():
                        with _scan_lock:
                            _scan_results.append({
                                "sensor_id": sensor_id,
                                "detected": detected,
                                "confidence": float(conf),
                                "timestamp": time.time()
                            })
                            
                    frame += 1

            except (serial.serialutil.SerialException, OSError) as hw_err:
                logger.error("%s Serial error: %s — retrying in 0.5s", prefix, hw_err)
                time.sleep(0.5)
            except (ValueError, UnicodeDecodeError) as parse_err:
                logger.warning("%s Parse error: %s", prefix, parse_err)
                # continue without sleeping; next byte will arrive shortly

    finally:
        ser.close()
        tee_print(f"{prefix} Closed port {port}")


# =====================================================================================
# MAIN
# =====================================================================================
def main():
    # CRIT-02: check model file existence before starting threads
    model_path = os.path.abspath(Config.MODEL_PATH)
    if HAS_TCN and not os.path.isfile(model_path):
        logger.critical(
            "[CRIT-02] Model file not found: %s\n"
            "  → Run 'python model/download_weights.py' or copy the .pt file manually.\n"
            "  → FATAL: Cannot run without model.",
            model_path,
        )
        sys.exit(1)
    elif HAS_TCN:
        try:
            tcn_engine = TCNInferenceEngine(model_path)
            logger.info("[+] TCNInferenceEngine v2 loaded: %s", model_path)
        except Exception as e:
            logger.critical("[CRIT-02] TCN engine load failed: %s — FATAL.", e)
            sys.exit(1)
    else:
        tcn_engine = None

    device = torch.device("cpu") if HAS_TORCH else "cpu"

    tee_print("\n=== STARTING TWO LD2410 SENSORS ===\n")

    threads = []
    for i, port in enumerate(Config.PORTS, start=1):
        t = threading.Thread(target=run_sensor, args=(i, port, tcn_engine, device), daemon=True)
        t.start()
        threads.append(t)

    # Keep main alive; propagate KeyboardInterrupt cleanly
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tee_print("\n=== SHUTTING DOWN ===")


if __name__ == "__main__":
    main()