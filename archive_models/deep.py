"""
LD2410 Breathing Detection - Deep Learning Inference (Option A)
Uses FastCNNLSTMModel trained on BS matrices (256 x 1099)
"""

import serial
import collections
import time

import numpy as np
from scipy import signal
from scipy.fftpack import fft, fftfreq

import torch
import torch.nn as nn
import requests

FLASK_URL = "http://localhost:5050/api/predict"

# ============================================================================
# CONFIG
# ============================================================================

class Config:
    # Serial
    PORT = "/dev/ttyUSB0"
    BAUD = 115200
    TIMEOUT = 0.5

    # Model
    MODEL_PATH = "cnn_lstm_fast_final_model.pt"

    # Detection parameters (same idea as your earlier script)
    SAMPLE_WINDOW = 64              # distance samples for FFT / feature scoring
    SAMPLE_PERIOD = 0.1             # 10 Hz
    BREATH_FREQ_MIN = 0.15          # Hz
    BREATH_FREQ_MAX = 0.67          # Hz
    CONFIDENCE_THRESHOLD = 0.85
    VOTING_WINDOW = 32
    VOTING_THRESHOLD = 18

    VERBOSE = True


# ============================================================================
# FAST CNN+LSTM MODEL (SAME AS TRAINING)
# ============================================================================

class FastCNNLSTMModel(nn.Module):
    def __init__(self, num_classes=2, dropout_rate=0.2):
        super(FastCNNLSTMModel, self).__init__()

        self.conv1 = nn.Conv2d(1, 16, kernel_size=(3, 3), stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))

        self.conv2 = nn.Conv2d(16, 32, kernel_size=(3, 3), stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))

        self.dropout_conv = nn.Dropout(dropout_rate)

        self.lstm_input_size = 32 * 64  # 2048
        self.lstm = nn.LSTM(
            input_size=self.lstm_input_size,
            hidden_size=128,
            num_layers=1,
            batch_first=True,
            dropout=0
        )

        self.fc1 = nn.Linear(128, 64)
        self.relu_fc = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x):
        # x: (B, 1, 256, 1099)
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu1(x)
        x = self.pool1(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu2(x)
        x = self.pool2(x)
        x = self.dropout_conv(x)

        # (B, 32, 64, 274) -> (B, 274, 2048)
        B, C, H, W = x.size()
        x = x.permute(0, 3, 1, 2).contiguous().view(B, W, -1)

        lstm_out, _ = self.lstm(x)
        x = lstm_out[:, -1, :]  # (B, 128)

        x = self.fc1(x)
        x = self.relu_fc(x)
        x = self.dropout_fc(x)
        x = self.fc2(x)
        return x


# ============================================================================
# FEATURE EXTRACTION (1D distance, FFT)
# ============================================================================

def extract_breathing_features(dist_array):
    detrended = signal.detrend(dist_array)

    try:
        sos = signal.butter(4, 0.15, btype='high', fs=10, output='sos')
        filtered = signal.sosfilt(sos, detrended)
    except Exception:
        filtered = detrended

    N = len(filtered)
    dt = Config.SAMPLE_PERIOD
    freqs = fftfreq(N, dt)[:N // 2]
    fft_vals = np.abs(fft(filtered))[:N // 2]

    mask = (freqs >= Config.BREATH_FREQ_MIN) & (freqs <= Config.BREATH_FREQ_MAX)

    if np.any(mask):
        bf = freqs[mask]
        bp = fft_vals[mask]
        peak_idx = np.argmax(bp)
        peak_freq = bf[peak_idx]
        peak_power = bp[peak_idx]
    else:
        peak_freq = 0.0
        peak_power = 0.0

    rms_power = np.sqrt(np.mean(filtered ** 2))
    variance = np.var(filtered)
    peak_to_peak = np.max(filtered) - np.min(filtered)

    power_spectrum = np.abs(fft_vals) ** 2
    power_spectrum /= (power_spectrum.sum() + 1e-10)
    ps = power_spectrum[power_spectrum > 0]
    if len(ps) > 0:
        spectral_entropy = -np.sum(ps * np.log2(ps + 1e-10))
    else:
        spectral_entropy = 0.0

    zero_crossings = np.sum(np.abs(np.diff(np.sign(filtered)))) / 2
    zcr = zero_crossings / len(filtered)

    return {
        "peak_freq": peak_freq,
        "peak_power": peak_power,
        "rms_power": rms_power,
        "variance": variance,
        "peak_to_peak": peak_to_peak,
        "spectral_entropy": spectral_entropy,
        "zero_crossing_rate": zcr,
    }


def score_breathing_features(f):
    score = 0.0
    if Config.BREATH_FREQ_MIN <= f["peak_freq"] <= Config.BREATH_FREQ_MAX:
        score += 0.3
    if f["peak_power"] > 75:
        score += 0.2
    if f["spectral_entropy"] < 5.0:
        score += 0.2
    if 5 < f["variance"] < 200:
        score += 0.15
    if 2 < f["peak_to_peak"] < 150:
        score += 0.15
    return score


# ============================================================================
# CNN+LSTM INFERENCE (2D BS matrix)
# ============================================================================

def predict_breathing_from_bs(model, bs_matrix, device):
    """
    bs_matrix: np.ndarray (256, 1099)
    returns: breathing probability [0,1] or None
    """
    if model is None:
        return None

    try:
        if bs_matrix.shape == (1099, 256):
            bs_matrix = bs_matrix.T
        if bs_matrix.shape != (256, 1099):
            return None

        norm = (bs_matrix - bs_matrix.mean()) / (bs_matrix.std() + 1e-8)
        x = torch.from_numpy(norm).float().unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            return probs[0, 1].item()

    except Exception as e:
        if Config.VERBOSE:
            print(f"[!] DL inference error: {e}")
        return None


# ============================================================================
# PLACEHOLDER: ACQUIRE BS MATRIX FROM LD2410
# ============================================================================

def get_current_bs_matrix():
    """
    TODO: Implement this using your LD2410 raw data + range-FFT / processing.
    Must return np.ndarray of shape (256, 1099) or None if not ready.
    """
    return None  # replace with real implementation



def report_to_backend(distance, feats, fft_conf, dl_conf, votes, detection):
    """
    Send ONE decision to Flask backend; does NOT change detection logic.
    """
    payload = {
        "breathing": bool(detection),                 # your final decision
        "freq": float(feats["peak_freq"]),
        "power": float(feats["peak_power"]),
        "entropy": float(feats["spectral_entropy"]),
        "distance": float(distance),
        "fft_conf": float(fft_conf),
        "dl_conf": float(dl_conf),
        "votes": int(votes),
        "voting_window": int(Config.VOTING_WINDOW),
    }
    
    # Existing Flask backend (with retry logic)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            requests.post(FLASK_URL, json=payload, timeout=1.0)
            break  # Success, exit retry loop
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                if Config.VERBOSE:
                    print(f"[API] Connection refused, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(0.5)
            else:
                if Config.VERBOSE:
                    print("[API ERROR] Connection refused - Flask may not be running")
        except Exception as e:
            if Config.VERBOSE:
                print(f"[API ERROR] {e}")
            break


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    device = torch.device("cpu")

    # Load model
    print(f"[*] Loading model: {Config.MODEL_PATH}")
    try:
        model = FastCNNLSTMModel(num_classes=2, dropout_rate=0.2)
        model.load_state_dict(torch.load(Config.MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()
        print("[✓] Model loaded successfully")
        print(f"[*] Model device: {device}")
        print(f"[*] Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    except Exception as e:
        print(f"[✗] Model load failed: {e}")
        print("[!] Continuing with FFT-only mode (DL confidence = FFT confidence)")
        model = None

    # Serial for distance stream (for FFT features and logging)
    print(f"[*] Opening serial {Config.PORT} @ {Config.BAUD}")
    ser = serial.Serial(Config.PORT, Config.BAUD, timeout=Config.TIMEOUT)
    time.sleep(1)
    print("[✓] Serial connected\n")

    distance_buffer = collections.deque(maxlen=Config.SAMPLE_WINDOW)
    vote_buffer = collections.deque(maxlen=Config.VOTING_WINDOW)
    inference_times = collections.deque(maxlen=100)
    frame_count = 0
    line_buffer = ""

    print("\n" + "=" * 160)
    print("LD2410 BREATHING DETECTION - CNN+LSTM + FFT")
    print("=" * 160)
    print(f"{'Frame':>6} {'Dist':>8} {'Freq':>8} {'Pwr':>8} {'Ent':>8} "
          f"{'FFT_Conf':>9} {'DL_Conf':>9} {'Votes':>8} {'Detection':>14} {'Time':>10}")
    print("-" * 160)
    print("[*] Starting detection loop...")
    print("[*] Deep Learning Model: CNN+LSTM")
    print("[*] Detection Threshold: {:.2f} | Voting Window: {}".format(
        Config.CONFIDENCE_THRESHOLD, Config.VOTING_WINDOW))
    print("-" * 160 + "\n")

    try:
        while True:
            chunk = ser.read(1)
            if not chunk:
                continue

            ch = chunk.decode("utf-8", errors="ignore")
            line_buffer += ch

            if "\n" in line_buffer:
                lines = line_buffer.split("\n")
                line_buffer = lines[-1]

                for line in lines[:-1]:
                    line = line.strip()
                    if not line:
                        continue

                    if not line.startswith("distance:"):
                        continue

                    try:
                        distance = float(line.split(":")[1].strip())
                    except ValueError:
                        continue

                    distance_buffer.append(distance)

                    if len(distance_buffer) < Config.SAMPLE_WINDOW:
                        continue

                    dist_array = np.array(distance_buffer, dtype=np.float32)

                    inf_start = time.time()
                    feats = extract_breathing_features(dist_array)
                    fft_conf = score_breathing_features(feats)

                    # Deep model on BS matrix
                    bs_matrix = get_current_bs_matrix()
                    dl_conf = fft_conf  # Default to FFT confidence
                    if model is not None and bs_matrix is not None:
                        prob = predict_breathing_from_bs(model, bs_matrix, device)
                        if prob is not None:
                            dl_conf = prob
                    elif model is None:
                        # Model not loaded, use FFT only
                        dl_conf = fft_conf

                    inf_time = time.time() - inf_start
                    inference_times.append(inf_time)

                    # Voting
                    voting_conf = max(fft_conf, dl_conf)
                    vote_buffer.append(1 if voting_conf > Config.CONFIDENCE_THRESHOLD else 0)
                    votes = sum(vote_buffer)

                    detection = votes >= Config.VOTING_THRESHOLD
                    status = "BREATHING" if detection else "NO"

                    avg_ms = np.mean(inference_times) * 1000.0
                    time_str = time.strftime("%H:%M:%S")

                    # Format votes as "XX/YY" aligned to 8 characters
                    votes_str = f"{votes:2d}/{Config.VOTING_WINDOW}"
                    print(f"{frame_count:6d} {distance:8.2f} {feats['peak_freq']:8.3f} "
                          f"{feats['peak_power']:8.1f} {feats['spectral_entropy']:8.2f} "
                          f"{fft_conf:9.3f} {dl_conf:9.3f} "
                          f"{votes_str:>8} {status:>14} {time_str:>10}")
                    
                    # Log detection with details
                    if detection and Config.VERBOSE:
                        print(f"[DETECTION] Frame {frame_count}: {status} | "
                              f"Distance: {distance:.2f}cm | "
                              f"FFT: {fft_conf:.3f} | DL: {dl_conf:.3f} | "
                              f"Votes: {votes}/{Config.VOTING_WINDOW}")
                    
                    report_to_backend(distance, feats, fft_conf, dl_conf, votes, detection)

                    frame_count += 1

    except KeyboardInterrupt:
        print("\n\n[*] Stopped by user")
        print(f"[*] Total frames processed: {frame_count}")
        if inference_times:
            avg_inf = np.mean(inference_times) * 1000.0
            print(f"[*] Average inference time: {avg_inf:.2f}ms")
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ser.close()
        print("[✓] Serial closed")
        print("[✓] Deep learning detection stopped")


if __name__ == "__main__":
    main()
