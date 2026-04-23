import numpy as np
import joblib
import os
from scipy.stats import skew, kurtosis
from scipy.fftpack import fft

MODEL_PATH = os.path.join(os.path.dirname(__file__), "svm_model_optimized.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "svm_scaler.pkl")

clf = None
scaler = None



def load_model():
    global clf, scaler
    try:
        loaded = joblib.load(MODEL_PATH)
        
        if isinstance(loaded, dict):
            clf = loaded.get('model')
            scaler = loaded.get('scaler')
        elif isinstance(loaded, (list, tuple)) and len(loaded) == 2:
            scaler, clf = loaded
        else:
            clf = loaded
            scaler = None
        
        print(f"[✓] SVM model loaded successfully")
        return True
    except Exception as e:
        print(f"[✗] Model load failed: {e}")
        return False

def extract_features(dist_array):
    """Extract 33 features from distance array"""
    x = np.array(dist_array, dtype=float)
    
    if len(x) == 0:
        return np.zeros(33)
    
    # 1. Statistical (10)
    mean_val = np.mean(x)
    std_val = np.std(x)
    min_val = np.min(x)
    max_val = np.max(x)
    median_val = np.median(x)
    skewness = skew(x) if len(x) > 1 else 0
    kurt_val = kurtosis(x) if len(x) > 1 else 0
    p25 = np.percentile(x, 25)
    p75 = np.percentile(x, 75)
    iqr = p75 - p25
    
    # 2. Energy (6)
    energy_total = np.sum(x**2)
    win = 16
    if len(x) > win:
        energies = np.array([np.sum(x[i:i+win]**2) for i in range(len(x)-win)])
    else:
        energies = np.array([energy_total])
    
    mean_energy = np.mean(energies)
    std_energy = np.std(energies)
    max_energy = np.max(energies)
    p75_energy = np.percentile(energies, 75)
    p90_energy = np.percentile(energies, 90)
    
    # 3. Temporal (2)
    diff = np.diff(x) if len(x) > 1 else np.array([0])
    mean_var_time = np.mean(diff**2)
    std_var_time = np.std(diff**2)
    
    # 4. FFT (4)
    fft_vals = np.abs(fft(x))[:len(x)//2] if len(x) > 1 else np.array([0])
    fft_energy = np.sum(fft_vals**2)
    fft_max = np.max(fft_vals) if len(fft_vals) > 0 else 0
    fft_mean = np.mean(fft_vals) if len(fft_vals) > 0 else 0
    fft_std = np.std(fft_vals) if len(fft_vals) > 0 else 0
    
    # 5. Range (3)
    peak = np.max(x)
    second_peak = np.partition(x, -2)[-2] if len(x) > 1 else peak
    peak_ratio = peak / (second_peak + 1e-6)
    
    # 6. Local patch (4)
    idx = np.argmax(x)
    local = x[max(0, idx-3):min(len(x), idx+4)]
    local_mean = np.mean(local) if len(local) > 0 else 0
    local_std = np.std(local) if len(local) > 0 else 0
    local_energy = np.sum(local**2) if len(local) > 0 else 0
    local_max = np.max(local) if len(local) > 0 else 0
    
    # 7. Texture (2)
    hist, _ = np.histogram(x, bins=20)
    hist = hist / (np.sum(hist) + 1e-6)
    entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0])) if np.any(hist > 0) else 0
    contrast = np.mean(np.abs(diff)) if len(diff) > 0 else 0
    
    # Extra (2)
    smoothness = np.mean(np.abs(np.diff(diff))) if len(diff) > 1 else 0
    amp_range = max_val - min_val
    
    return np.array([
        mean_val, std_val, min_val, max_val, median_val, skewness, kurt_val,
        p25, p75, iqr,
        energy_total, mean_energy, std_energy, max_energy,
        p75_energy, p90_energy,
        mean_var_time, std_var_time,
        peak, second_peak, peak_ratio,
        fft_energy, fft_max, fft_mean, fft_std,
        local_mean, local_std, local_energy, local_max,
        entropy, contrast,
        smoothness, amp_range
    ], dtype=float)

def predict(feature_dict):
    """SVM path is disabled. The TCN-Attention v2 engine is used for all inference."""
    return {"error": "SVM disabled; using deep learning path only", "ok": False}

# MED-01: load_model() is intentionally NOT called at import time.
# The SVM pkl files are absent and calling it would generate noisy failure
# messages on every server startup. Call load_model() manually if you ever
# need to re-enable SVM inference.
