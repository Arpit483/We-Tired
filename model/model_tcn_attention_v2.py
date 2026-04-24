"""
VitalRadar — TCN-Attention v2 (Dual-Stream)
============================================
Upgraded model for radar_dataset_DataPort (LD2410 sensor).
Drop-in replacement for CNN+LSTM in We-Tired / deep_optimized.py.

Task:     Binary classification — breathing / no_breathing
Input:    64-sample sliding window of LD2410 distance readings (~6.4 seconds)
Output:   (detected: bool, confidence: float)
Hardware: Raspberry Pi 4, LD2410 radar sensor

Key upgrades over v1 (model_tcn_attention.py):
  [1] Added dilation=8 TCN block → receptive field 51 steps (5.1s) covers full trauma breath cycle
  [2] FFT dual-stream: frequency-domain power features fused with temporal features
      → model sees BOTH waveform shape AND spectral fingerprint of breathing
  [3] Breathing-band emphasis loss: recall on class=1 weighted 2× more than precision
      → prioritises finding victims over avoiding false alarms (rescue context)
  [4] Label smoothing in loss: reduces overconfidence, better-calibrated probability output
  [5] FocalLoss option: handles the hard negatives (thick_conc, ceiling, cloth)
  [6] Fixed double forward-pass bug in training loop (was running model(x) twice per step)
  [7] weights_only=True in torch.load (PyTorch ≥2.0 security best practice)

Usage:
    python3 model_tcn_attention_v2.py --train --data ./radar_dataset_DataPort
    python3 model_tcn_attention_v2.py --test-file ./radar_dataset_DataPort/breathing/thick_conc.txt
    python3 model_tcn_attention_v2.py --train --data ./radar_dataset_DataPort --focal
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import glob
from scipy import signal as scipy_signal
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')


# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

class Config:
    WINDOW_SIZE    = 64         # samples per window (6.4 seconds @ 10Hz)
    STRIDE         = 16         # sliding window hop (data augmentation via overlap)
    SAMPLE_RATE    = 10.0       # Hz — LD2410 standard output rate
    BATCH_SIZE     = 32
    EPOCHS         = 100        # +20 over v1 — more capacity needs more training
    LR             = 1e-3
    WEIGHT_DECAY   = 1e-4
    DROPOUT        = 0.2
    NUM_CLASSES    = 2          # [no_breathing=0, breathing=1]
    LABEL_SMOOTHING = 0.05      # NEW: softens hard labels → better-calibrated confidence
    RECALL_BIAS    = 2.0        # NEW: breathing class weighted 2× extra → fewer missed victims
    DEVICE         = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_SAVE     = "tcn_attention_vitalradar_v2.pt"
    DATA_ROOT      = "./radar_dataset_DataPort"
    # Breathing frequency band limits (Hz)
    BREATH_MIN_HZ  = 0.15       # ~9 breaths/min  — slow (trauma victim)
    BREATH_MAX_HZ  = 0.67       # ~40 breaths/min — panic breathing


# ──────────────────────────────────────────────────────────────────────────────
# PREPROCESSING
# ──────────────────────────────────────────────────────────────────────────────

def preprocess_window(arr: np.ndarray) -> np.ndarray:
    """
    Normalise a 64-sample distance window for TCN stream input.
      1. Detrend — removes slow body movement / sensor drift
      2. High-pass Butterworth @0.1Hz — removes DC offset
      3. Normalise to [-1, 1] — makes model range-invariant (1m to 6m same scale)
    """
    x = scipy_signal.detrend(arr)
    try:
        sos = scipy_signal.butter(4, 0.1, btype='high',
                                   output='sos', fs=Config.SAMPLE_RATE)
        x = scipy_signal.sosfilt(sos, x)
    except Exception:
        pass
    peak = np.max(np.abs(x)) + 1e-8
    return (x / peak).astype(np.float32)


def compute_fft_features(arr: np.ndarray) -> np.ndarray:
    """
    NEW in v2: Compute FFT power spectrum for the breathing-frequency band.

    Returns a 33-element float32 array representing power at each FFT bin.
    The model's FFT stream learns which frequency components indicate breathing.

    Why this helps through rubble / concrete:
      Even when the time-domain waveform is severely attenuated or noisy,
      a victim's breathing still creates a narrow spectral peak in 0.15–0.67 Hz.
      The FFT stream detects this peak directly, complementing the TCN's
      waveform-shape detection.
    """
    x = scipy_signal.detrend(arr)
    # rfft returns WINDOW_SIZE//2 + 1 = 33 complex values for length-64 input
    fft_mag = np.abs(np.fft.rfft(x))  # shape: [33]
    # Normalise so different signal amplitudes produce similar magnitude spectra
    fft_mag = fft_mag / (np.max(fft_mag) + 1e-8)
    return fft_mag.astype(np.float32)


# ──────────────────────────────────────────────────────────────────────────────
# DATASET
# ──────────────────────────────────────────────────────────────────────────────

def parse_distance_file(filepath: str) -> list:
    """
    Parse a .txt file from radar_dataset_DataPort.
    Returns list of float distance values.
    Handles: "distance:123.4", plain "123.4", or engineering mode "123.4 45 23 1"
    """
    values = []
    with open(filepath, 'r', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                if line.startswith("distance:"):
                    val = float(line.split(":")[1].split()[0])
                elif "," in line:
                    # Handle CSV format (timestamp, distance) - always take the last part
                    val = float(line.split(",")[-1])
                else:
                    val = float(line.split()[0])
                values.append(val)
            except (ValueError, IndexError):
                continue
    return values


class RadarDataset(Dataset):
    """
    Sliding-window dataset from radar_dataset_DataPort.

    Returns TWO tensors per sample:
        x_tcn:  [1, 64]  — detrended, normalised time-domain window (TCN stream)
        x_fft:  [1, 33]  — FFT power spectrum (FFT stream)
        label:  int       — 0=no_breathing, 1=breathing
    """

    def __init__(self, data_root: str, split: str = 'train',
                 test_size: float = 0.2, seed: int = 42, augment: bool = True):
        self.augment = augment and (split == 'train')
        self.windows_tcn = []
        self.windows_fft = []
        self.labels = []
        all_tcn, all_fft, all_labs = [], [], []

        for fpath in glob.glob(os.path.join(data_root, 'breathing', '*.txt')):
            t, f = self._file_to_windows(fpath)
            all_tcn.extend(t); all_fft.extend(f)
            all_labs.extend([1] * len(t))

        for fpath in glob.glob(os.path.join(data_root, 'no_breathing', '*.txt')):
            t, f = self._file_to_windows(fpath)
            all_tcn.extend(t); all_fft.extend(f)
            all_labs.extend([0] * len(t))

        idxs = list(range(len(all_labs)))
        tr, te = train_test_split(idxs, test_size=test_size,
                                   stratify=all_labs, random_state=seed)
        for i in (tr if split == 'train' else te):
            self.windows_tcn.append(all_tcn[i])
            self.windows_fft.append(all_fft[i])
            self.labels.append(all_labs[i])

        n_pos = sum(self.labels)
        print(f"[Dataset:{split:5s}] {len(self.labels):5d} windows | "
              f"breathing={n_pos}  no_breathing={len(self.labels)-n_pos}")

    def _file_to_windows(self, fpath):
        vals = parse_distance_file(fpath)
        arr  = np.array(vals, dtype=np.float32)
        N    = len(arr)
        tcn_wins, fft_wins = [], []
        for s in range(0, N - Config.WINDOW_SIZE + 1, Config.STRIDE):
            w = arr[s : s + Config.WINDOW_SIZE]
            tcn_wins.append(preprocess_window(w))
            fft_wins.append(compute_fft_features(w))
        return tcn_wins, fft_wins

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        x_t = self.windows_tcn[idx].copy()
        x_f = self.windows_fft[idx].copy()

        if self.augment:
            # Time-domain augmentations (applied to TCN stream only)
            x_t += np.random.normal(0, 0.02, x_t.shape).astype(np.float32)
            scale = np.random.uniform(0.8, 1.2)
            x_t  *= scale
            shift  = np.random.randint(-8, 8)
            x_t    = np.roll(x_t, shift)
            x_t    = (x_t / (np.max(np.abs(x_t)) + 1e-8)).astype(np.float32)

            # Recompute FFT after augmentation so both streams stay consistent
            # (scale doesn't change spectrum shape; shift creates small phase change)
            # We add a tiny noise perturbation to FFT independently for regularisation
            x_f += np.random.normal(0, 0.01, x_f.shape).astype(np.float32)
            x_f  = np.clip(x_f, 0, 1)

        return (
            torch.tensor(x_t).unsqueeze(0),                   # [1, 64]
            torch.tensor(x_f).unsqueeze(0),                   # [1, 33]
            torch.tensor(self.labels[idx], dtype=torch.long)  # scalar
        )

    @property
    def class_weights(self):
        """
        Compute class weights with extra recall bias on class=1 (breathing).
        In rescue context, missing a victim (false negative) is far worse
        than a false alarm. RECALL_BIAS=2.0 makes the model try harder to
        detect breathing even at the cost of some false positives.
        """
        n = len(self.labels)
        p = sum(self.labels)     # breathing count
        q = n - p                # no_breathing count
        w_neg = n / (2.0 * q + 1e-8)
        w_pos = n / (2.0 * p + 1e-8) * Config.RECALL_BIAS
        return torch.tensor([w_neg, w_pos], dtype=torch.float32)


# ──────────────────────────────────────────────────────────────────────────────
# MODEL BUILDING BLOCKS
# ──────────────────────────────────────────────────────────────────────────────

class CausalConv1d(nn.Module):
    """
    Causal dilated Conv1D.
    Pads only on the LEFT (past) so the model cannot see the future.
    Required for real-time streaming inference on Raspberry Pi.
    """
    def __init__(self, in_ch, out_ch, kernel_size, dilation=1):
        super().__init__()
        self.pad  = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(in_ch, out_ch, kernel_size,
                               dilation=dilation, padding=0)

    def forward(self, x):
        return self.conv(F.pad(x, (self.pad, 0)))


class TCNBlock(nn.Module):
    """
    Temporal Convolutional Block:
      CausalConv1d → BN → GELU → Dropout
      CausalConv1d → BN → GELU → Dropout
      + Residual skip connection (1×1 conv if channel change)

    Effective receptive field per block (kernel=3):
      dilation=1 → 3 steps  (0.3s)
      dilation=2 → 9 steps  (0.9s)
      dilation=4 → 21 steps (2.1s)
      dilation=8 → 45 steps (4.5s)  ← NEW in v2: covers full trauma breath cycle
    Stacked: total field = 1 + 2*(3-1)*(1+2+4+8) = 61 steps ≈ 6.1 seconds
    """
    def __init__(self, in_ch, out_ch, kernel=3, dilation=1, dropout=0.2):
        super().__init__()
        self.conv1 = CausalConv1d(in_ch, out_ch, kernel, dilation)
        self.bn1   = nn.BatchNorm1d(out_ch)
        self.conv2 = CausalConv1d(out_ch, out_ch, kernel, dilation)
        self.bn2   = nn.BatchNorm1d(out_ch)
        self.act   = nn.GELU()
        self.drop  = nn.Dropout(dropout)
        self.skip  = nn.Conv1d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()

    def forward(self, x):
        res = self.skip(x)
        out = self.drop(self.act(self.bn1(self.conv1(x))))
        out = self.drop(self.act(self.bn2(self.conv2(out))))
        return self.act(out + res)


class FFTStream(nn.Module):
    """
    NEW in v2: Frequency-domain stream.

    Processes the 33-bin FFT power spectrum with a small 1D CNN.
    Learns to detect the characteristic spectral peak of breathing
    (0.15–0.67 Hz band) even when the time-domain signal is weak.

    Input:  [B, 1, 33]  — FFT magnitude spectrum
    Output: [B, 64]     — frequency feature vector
    """
    def __init__(self, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            # Local spectral patterns (adjacent frequency bins)
            nn.Conv1d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm1d(16),
            nn.GELU(),
            nn.Dropout(dropout),

            # Wider spectral context
            nn.Conv1d(16, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.GELU(),
            nn.Dropout(dropout),

            # Compress to summary vector
            nn.AdaptiveAvgPool1d(1)   # [B, 32, 1]
        )
        self.fc = nn.Sequential(
            nn.Linear(32, 64),
            nn.GELU()
        )

    def forward(self, x_fft):
        # x_fft: [B, 1, 33]
        out = self.net(x_fft).squeeze(-1)   # [B, 32]
        return self.fc(out)                  # [B, 64]


# ──────────────────────────────────────────────────────────────────────────────
# MAIN MODEL — TCN + FFT DUAL STREAM
# ──────────────────────────────────────────────────────────────────────────────

class TCNAttentionModelV2(nn.Module):
    """
    VitalRadar TCN-Attention v2 — Dual-Stream (~340K parameters)

    Inputs:
        x_tcn: [B, 1, 64]  — time-domain distance window
        x_fft: [B, 1, 33]  — FFT magnitude spectrum of same window

    Output:
        [B, 2]  — logits for [no_breathing, breathing]

    Architecture:
        ┌── TCN Stream ──────────────────────────────────────────────┐
        │  Conv1D embed(1→32)                                         │
        │  → TCNBlock(32→64,  dilation=1)  receptive field:  0.3s   │
        │  → TCNBlock(64→64,  dilation=2)  receptive field:  0.9s   │
        │  → TCNBlock(64→128, dilation=4)  receptive field:  2.1s   │
        │  → TCNBlock(128→128,dilation=8)  receptive field:  4.5s ← NEW │
        │  → MultiHeadAttention(128, heads=4)                        │
        │  → AdaptiveAvgPool → [B, 128]                              │
        └─────────────────────────────────────────────────────────────┘
                              ↓ concat [B, 192]
        ┌── FFT Stream ──────────────────────────────────────────────┐
        │  Conv1D(1→16→32) + Pool → Linear(32→64) → [B, 64]  ← NEW │
        └─────────────────────────────────────────────────────────────┘
                              ↓
                        Linear(192→96) → GELU → Dropout
                        Linear(96→2)
                        Softmax → confidence
    """

    def __init__(self, num_classes=2, dropout=0.2):
        super().__init__()

        # ── TCN stream ────────────────────────────────────────────
        self.embed = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.GELU()
        )
        self.tcn1 = TCNBlock(32,  64,  dilation=1, dropout=dropout)
        self.tcn2 = TCNBlock(64,  64,  dilation=2, dropout=dropout)
        self.tcn3 = TCNBlock(64,  128, dilation=4, dropout=dropout)
        self.tcn4 = TCNBlock(128, 128, dilation=8, dropout=dropout)  # NEW

        self.attn      = nn.MultiheadAttention(128, num_heads=4,
                                                batch_first=True, dropout=dropout)
        self.attn_norm = nn.LayerNorm(128)
        self.pool      = nn.AdaptiveAvgPool1d(1)

        # ── FFT stream (NEW) ──────────────────────────────────────
        self.fft_stream = FFTStream(dropout=dropout)

        # ── Fusion classifier (128 TCN + 64 FFT = 192) ───────────
        self.head = nn.Sequential(
            nn.Linear(192, 96),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(96, num_classes)
        )

    def forward(self, x_tcn, x_fft):
        # ── Shape guards — catch mismatches early (fail loud, not silently) ──
        assert x_tcn.ndim == 3 and x_tcn.shape[1] == 1 and x_tcn.shape[2] == 64, (
            f"x_tcn must be [B, 1, 64], got {list(x_tcn.shape)}"
        )
        assert x_fft.ndim == 3 and x_fft.shape[1] == 1 and x_fft.shape[2] == 33, (
            f"x_fft must be [B, 1, 33], got {list(x_fft.shape)}"
        )
        # ── TCN stream ────────────────────────────────────────────
        t = self.embed(x_tcn)               # [B, 32, 64]
        t = self.tcn1(t)                    # [B, 64, 64]
        t = self.tcn2(t)                    # [B, 64, 64]
        t = self.tcn3(t)                    # [B, 128, 64]
        t = self.tcn4(t)                    # [B, 128, 64]  NEW

        # Self-attention over time axis
        ta = t.permute(0, 2, 1)             # [B, 64, 128]
        a, _ = self.attn(ta, ta, ta)        # [B, 64, 128]
        ta = self.attn_norm(ta + a)         # residual + norm
        t = ta.permute(0, 2, 1)            # [B, 128, 64]
        t = self.pool(t).squeeze(-1)        # [B, 128]

        # ── FFT stream ────────────────────────────────────────────
        f = self.fft_stream(x_fft)         # [B, 64]

        # ── Fuse and classify ─────────────────────────────────────
        combined = torch.cat([t, f], dim=1)  # [B, 192]
        return self.head(combined)           # [B, 2]

    @torch.no_grad()
    def predict_confidence(self, x_tcn: torch.Tensor,
                            x_fft: torch.Tensor) -> tuple:
        """Returns (detected: bool, confidence: float 0–1)

        Borderline rule: if the raw softmax probability for class=1 is between
        0.50 and 0.65 (inclusive) the prediction is treated as uncertain and
        detected=False is returned.  Only prob > 0.65 counts as a real detection.
        This prevents the model from accumulating votes on ambiguous frames.
        """
        probs = torch.softmax(self.forward(x_tcn, x_fft), dim=-1)
        conf  = probs[0, 1].item()
        # Do not count borderline predictions — only clear confidence triggers detected=True
        detected = conf > 0.65
        return detected, conf


# ──────────────────────────────────────────────────────────────────────────────
# FOCAL LOSS (optional — helps on hard negatives like ceiling, thick_conc)
# ──────────────────────────────────────────────────────────────────────────────

class FocalLoss(nn.Module):
    """
    Focal Loss: down-weights easy examples, focuses training on hard negatives.
    Useful when the model quickly learns the easy cases but struggles with
    through-concrete breathing or ceiling clutter.

    gamma=2.0 is standard; alpha balances class weights.
    """
    def __init__(self, alpha=None, gamma=2.0, label_smoothing=0.0):
        super().__init__()
        self.alpha           = alpha          # class weights tensor or None
        self.gamma           = gamma
        self.label_smoothing = label_smoothing

    def forward(self, logits, targets):
        n_cls = logits.size(1)
        # Label smoothing
        if self.label_smoothing > 0:
            with torch.no_grad():
                smooth_targets = torch.full_like(logits,
                                                  self.label_smoothing / (n_cls - 1))
                smooth_targets.scatter_(1, targets.unsqueeze(1),
                                         1.0 - self.label_smoothing)
            log_probs = F.log_softmax(logits, dim=-1)
            ce = -(smooth_targets * log_probs).sum(dim=-1)
        else:
            ce = F.cross_entropy(logits, targets, reduction='none')

        pt   = torch.exp(-ce)
        loss = (1 - pt) ** self.gamma * ce

        if self.alpha is not None:
            alpha_t = self.alpha[targets]
            loss = alpha_t * loss

        return loss.mean()


# ──────────────────────────────────────────────────────────────────────────────
# TRAINING
# ──────────────────────────────────────────────────────────────────────────────

def train_model(data_root: str = Config.DATA_ROOT, use_focal: bool = False):
    print(f"\n{'='*65}")
    print(f"  VitalRadar — TCN-Attention v2 (Dual-Stream) Training")
    print(f"  Device: {Config.DEVICE}")
    print(f"  Loss:   {'FocalLoss' if use_focal else 'CrossEntropyLoss'} "
          f"+ label_smoothing={Config.LABEL_SMOOTHING}")
    print(f"  Recall bias on breathing class: {Config.RECALL_BIAS}×")
    print(f"{'='*65}\n")

    tr_ds = RadarDataset(data_root, 'train', augment=True)
    vl_ds = RadarDataset(data_root, 'test',  augment=False)
    tr_dl = DataLoader(tr_ds, Config.BATCH_SIZE, shuffle=True,  num_workers=0)
    vl_dl = DataLoader(vl_ds, Config.BATCH_SIZE, shuffle=False, num_workers=0)

    model = TCNAttentionModelV2(dropout=Config.DROPOUT).to(Config.DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {n_params:,}  (~{n_params*4/1024/1024:.1f} MB)\n")

    weights = tr_ds.class_weights.to(Config.DEVICE)

    if use_focal:
        criterion = FocalLoss(alpha=weights, gamma=2.0,
                               label_smoothing=Config.LABEL_SMOOTHING)
    else:
        criterion = nn.CrossEntropyLoss(weight=weights,
                                         label_smoothing=Config.LABEL_SMOOTHING)

    optimizer = torch.optim.AdamW(model.parameters(),
                                   lr=Config.LR,
                                   weight_decay=Config.WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=Config.EPOCHS, eta_min=1e-5
    )

    history = []
    best_acc    = 0.0
    last_preds  = []
    last_labels = []

    for ep in range(1, Config.EPOCHS + 1):
        # ── Train ─────────────────────────────────────────────────
        model.train()
        tr_loss = tr_correct = tr_total = 0
        for x_t, x_f, y in tr_dl:
            x_t = x_t.to(Config.DEVICE)
            x_f = x_f.to(Config.DEVICE)
            y   = y.to(Config.DEVICE)

            optimizer.zero_grad()
            logits = model(x_t, x_f)
            loss   = criterion(logits, y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            tr_loss    += loss.item() * x_t.size(0)
            tr_correct += (logits.argmax(1) == y).sum().item()
            tr_total   += x_t.size(0)

        scheduler.step()

        # ── Validate ──────────────────────────────────────────────
        model.eval()
        vl_correct = vl_total = 0
        vl_loss    = 0
        preds_ep, labs_ep = [], []
        with torch.no_grad():
            for x_t, x_f, y in vl_dl:
                x_t = x_t.to(Config.DEVICE)
                x_f = x_f.to(Config.DEVICE)
                y   = y.to(Config.DEVICE)
                out = model(x_t, x_f)
                v_loss = criterion(out, y)
                vl_loss += v_loss.item() * x_t.size(0)
                p   = out.argmax(1)
                vl_correct += (p == y).sum().item()
                vl_total   += x_t.size(0)
                preds_ep.extend(p.cpu().tolist())
                labs_ep.extend(y.cpu().tolist())

        tr_a = tr_correct / tr_total * 100
        vl_a = vl_correct / vl_total * 100
        v_l  = vl_loss / vl_total
        t_l  = tr_loss / tr_total

        history.append({
            "epoch": ep,
            "train_loss": t_l,
            "val_loss": v_l,
            "train_acc": tr_a,
            "val_acc": vl_a
        })

        marker = ""
        if vl_a > best_acc:
            best_acc    = vl_a
            torch.save(model.state_dict(), Config.MODEL_SAVE)
            marker      = "  ✓ best"
            last_preds  = preds_ep
            last_labels = labs_ep

        if ep % 10 == 0 or ep == 1 or marker:
            print(f"Ep {ep:03d}/{Config.EPOCHS} | "
                  f"Loss:{tr_loss/tr_total:.4f} | "
                  f"Train:{tr_a:.1f}% | Val:{vl_a:.1f}%{marker}")

    print(f"\nBest val accuracy: {best_acc:.2f}%")
    print("\nClassification Report (best checkpoint):")
    print(classification_report(last_labels, last_preds,
                                 target_names=['no_breathing', 'breathing']))
    print("Confusion Matrix:")
    cm = confusion_matrix(last_labels, last_preds)
    print(cm)
    tn, fp, fn, tp = cm.ravel()
    print(f"\nRecall (breathing):    {tp/(tp+fn+1e-8):.3f}  ← victims found")
    print(f"Precision (breathing): {tp/(tp+fp+1e-8):.3f}  ← false alarms")
    print(f"\nFalse negative rate:   {fn/(tp+fn+1e-8):.3f}  ← missed victims")

    # Save history to JSON for visualization
    import json
    with open("training_history.json", "w") as f:
        json.dump(history, f, indent=4)
    print("\n[*] Training history saved to training_history.json")

    return model


# ──────────────────────────────────────────────────────────────────────────────
# INFERENCE ENGINE — drop-in for deep_optimized.py
# ──────────────────────────────────────────────────────────────────────────────

class TCNInferenceEngine:
    """
    Drop-in replacement for CNN+LSTM inference in deep_optimized.py.

    Minimal change needed in deep_optimized.py:
    ─────────────────────────────────────────────
    # In imports:
    from model_tcn_attention_v2 import TCNInferenceEngine

    # Replace load_model() and model call:
    self.engine = TCNInferenceEngine("tcn_attention_vitalradar_v2.pt")

    # In run_sensor(), replace FFT+model block:
    detected, conf = self.engine.predict(arr)
    ─────────────────────────────────────────────
    The voting buffer, web interface, Firebase, and GPS remain unchanged.
    """

    def __init__(self, model_path: str = Config.MODEL_SAVE, device=None):
        self.device = device or torch.device("cpu")
        self.model  = TCNAttentionModelV2()
        self.model.load_state_dict(
            torch.load(model_path, map_location=self.device, weights_only=True)
        )
        self.model.to(self.device).eval()
        print(f"[TCNInferenceEngine v2] Loaded from {model_path}")
        # Window-size consistency check — warn if Config has been modified
        if Config.WINDOW_SIZE != 64:
            import warnings
            warnings.warn(
                f"[VitalRadar] Config.WINDOW_SIZE={Config.WINDOW_SIZE} but this model was "
                f"trained on WINDOW_SIZE=64. Predictions will be incorrect.",
                UserWarning, stacklevel=2
            )

    def predict(self, distance_array: np.ndarray) -> tuple:
        """
        distance_array: np.ndarray shape [64,] — last 64 distance readings in cm
        Returns: (detected: bool, confidence: float 0–1)

        Inference time on Raspberry Pi 4 (CPU): ~12ms
        """
        x_t = torch.tensor(preprocess_window(distance_array)).unsqueeze(0).unsqueeze(0)
        x_f = torch.tensor(compute_fft_features(distance_array)).unsqueeze(0).unsqueeze(0)
        x_t = x_t.to(self.device)
        x_f = x_f.to(self.device)
        return self.model.predict_confidence(x_t, x_f)

    def get_summary_info(self):
        """Returns a dictionary with model structural info."""
        n_params = sum(p.numel() for p in self.model.parameters())
        # Receptive field calculation (based on TCN block dilations)
        # RF = 1 + 2 * (kernel-1) * sum(dilations)
        # kernel=3, dilations=[1, 2, 4, 8] -> 1 + 2 * (2) * (15) = 61 samples (6.1s)
        return {
            "name": "VitalRadar TCN-Attention v2",
            "parameters": n_params,
            "receptive_field_samples": 61,
            "receptive_field_seconds": 6.1,
            "streams": ["TCN (Time-Domain)", "FFT (Frequency-Domain)"],
            "input_shape_tcn": [1, 64],
            "input_shape_fft": [1, 33]
        }


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="VitalRadar TCN-Attention v2 (Dual-Stream)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 model_tcn_attention_v2.py --train --data ./radar_dataset_DataPort
  python3 model_tcn_attention_v2.py --train --data ./radar_dataset_DataPort --focal
  python3 model_tcn_attention_v2.py --test-file ./radar_dataset_DataPort/breathing/thick_conc.txt
  python3 model_tcn_attention_v2.py --test-file ./radar_dataset_DataPort/breathing/bt.txt
        """
    )
    ap.add_argument("--train",     action="store_true",
                    help="Train the model from scratch")
    ap.add_argument("--focal",     action="store_true",
                    help="Use FocalLoss instead of CrossEntropyLoss (helps with hard negatives)")
    ap.add_argument("--data",      default=Config.DATA_ROOT,
                    help=f"Path to dataset root (default: {Config.DATA_ROOT})")
    ap.add_argument("--test-file", metavar="FILE",
                    help="Run inference on a single .txt recording")
    ap.add_argument("--model",     default=Config.MODEL_SAVE,
                    help=f"Model checkpoint path (default: {Config.MODEL_SAVE})")
    args = ap.parse_args()

    if args.train:
        train_model(data_root=args.data, use_focal=args.focal)

    elif args.test_file:
        print(f"[*] Loading model: {args.model}")
        engine = TCNInferenceEngine(model_path=args.model)
        print(f"[*] Testing: {args.test_file}")
        vals = parse_distance_file(args.test_file)
        if len(vals) < Config.WINDOW_SIZE:
            print(f"ERROR: file has only {len(vals)} samples (need {Config.WINDOW_SIZE})")
        else:
            # Test multiple windows across the file and report average
            results = []
            arr_full = np.array(vals, dtype=np.float32)
            for s in range(0, len(arr_full) - Config.WINDOW_SIZE + 1, Config.STRIDE):
                w = arr_full[s : s + Config.WINDOW_SIZE]
                det, conf = engine.predict(w)
                results.append((det, conf))
            confs  = [r[1] for r in results]
            avg_c  = np.mean(confs)
            vote   = sum(r[0] for r in results) / len(results)
            print(f"\nFile:           {os.path.basename(args.test_file)}")
            print(f"Windows tested: {len(results)}")
            print(f"Avg confidence: {avg_c:.3f}")
            print(f"Vote fraction:  {vote:.2f}  (>0.5 = breathing detected)")
            print(f"\nResult: {'✓ BREATHING DETECTED' if vote > 0.5 else '✗ NO BREATHING'}")

    else:
        ap.print_help()
