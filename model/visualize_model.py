# -*- coding: utf-8 -*-
"""
VitalRadar — Complete Visualization & Export Tool
==================================================
Generates high-quality PNG images for:
  1. Training History (Loss + Accuracy curves)
  2. Model Architecture diagram
  3. Signal Breakdown (Raw / Preprocessed / FFT)
  4. Dataset Statistics
  5. Model Specs card

Run:  python visualize_model.py
All images saved to ./visualizations/
"""

import os, sys, json, warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')          # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
warnings.filterwarnings('ignore')

OUT_DIR = os.path.join(os.path.dirname(__file__), "visualizations")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Colour palette ─────────────────────────────────────────────────────────────
BG      = "#0d1117"
PANEL   = "#161b22"
BORDER  = "#30363d"
CYAN    = "#00ffcc"
ORANGE  = "#ff9900"
BLUE    = "#00ccff"
PURPLE  = "#bf00ff"
GREEN   = "#39d353"
RED     = "#ff4757"
WHITE   = "#e6edf3"
GREY    = "#8b949e"

def _fig(w=16, h=9, title=None):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    if title:
        fig.suptitle(title, fontsize=18, fontweight='bold',
                     color=CYAN, y=0.97, fontfamily='monospace')
    return fig

def _ax(ax, xlabel=None, ylabel=None, title=None):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.tick_params(colors=GREY, labelsize=9)
    ax.xaxis.label.set_color(GREY)
    ax.yaxis.label.set_color(GREY)
    if xlabel: ax.set_xlabel(xlabel, color=GREY)
    if ylabel: ax.set_ylabel(ylabel, color=GREY)
    if title:  ax.set_title(title, color=WHITE, fontsize=11, pad=8)
    ax.grid(color=BORDER, linewidth=0.6, alpha=0.7)
    return ax

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight',
                facecolor=BG, edgecolor='none')
    plt.close(fig)
    print(f"  ✓  Saved: {path}")
    return path


# ══════════════════════════════════════════════════════════════════════════════
# 1. TRAINING HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def plot_training_history(history_path="training_history.json"):
    print("\n[1/5] Training History …")
    if not os.path.exists(history_path):
        print("      SKIP — training_history.json not found"); return

    with open(history_path) as f:
        h = json.load(f)

    epochs  = [e['epoch']     for e in h]
    t_loss  = [e['train_loss'] for e in h]
    v_loss  = [e['val_loss']   for e in h]
    t_acc   = [e['train_acc']  for e in h]
    v_acc   = [e['val_acc']    for e in h]

    best_ep  = epochs[v_acc.index(max(v_acc))]
    best_acc = max(v_acc)
    best_vloss = min(v_loss)

    fig = _fig(18, 10, "VitalRadar TCN-Attention v2 — Training Progress")
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35,
                            left=0.07, right=0.97, top=0.90, bottom=0.08)

    # ── Loss ──────────────────────────────────────────────────────────────────
    ax1 = _ax(fig.add_subplot(gs[0, :2]), "Epoch", "Loss",
              "Training vs Validation Loss")
    ax1.plot(epochs, t_loss, color=ORANGE, lw=2, label="Train Loss")
    ax1.plot(epochs, v_loss, color=BLUE,   lw=2, label="Val Loss")
    ax1.fill_between(epochs, t_loss, v_loss, alpha=0.08, color=CYAN)
    ax1.axvline(best_ep, color=GREEN, lw=1.2, ls='--', alpha=0.7,
                label=f"Best epoch {best_ep}")
    ax1.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=WHITE)

    # ── Accuracy ──────────────────────────────────────────────────────────────
    ax2 = _ax(fig.add_subplot(gs[1, :2]), "Epoch", "Accuracy (%)",
              "Training vs Validation Accuracy")
    ax2.plot(epochs, t_acc, color=ORANGE, lw=2, label="Train Acc")
    ax2.plot(epochs, v_acc, color=CYAN,   lw=2, label="Val Acc")
    ax2.fill_between(epochs, t_acc, v_acc, alpha=0.08, color=PURPLE)
    ax2.axhline(best_acc, color=GREEN, lw=1, ls=':', alpha=0.6,
                label=f"Best val {best_acc:.1f}%")
    ax2.set_ylim(55, 102)
    ax2.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=WHITE)

    # ── Stats card ────────────────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[:, 2])
    ax3.set_facecolor(PANEL)
    for sp in ax3.spines.values(): sp.set_edgecolor(BORDER)
    ax3.axis('off')

    stats = [
        ("Total Epochs",        f"{len(epochs)}"),
        ("Best Val Accuracy",   f"{best_acc:.2f}%"),
        ("Best Val Loss",       f"{best_vloss:.4f}"),
        ("Best Epoch",          f"{best_ep}"),
        ("Final Train Acc",     f"{t_acc[-1]:.2f}%"),
        ("Final Val Acc",       f"{v_acc[-1]:.2f}%"),
        ("Final Train Loss",    f"{t_loss[-1]:.4f}"),
        ("Final Val Loss",      f"{v_loss[-1]:.4f}"),
        ("Train/Val Gap",       f"{t_acc[-1]-v_acc[-1]:.2f}%"),
    ]
    ax3.text(0.5, 0.97, "[Summary Stats]", transform=ax3.transAxes,
             ha='center', va='top', fontsize=13, color=CYAN, fontweight='bold')
    for i, (k, v) in enumerate(stats):
        y = 0.87 - i * 0.088
        ax3.text(0.08, y, k,  transform=ax3.transAxes, color=GREY,  fontsize=10)
        ax3.text(0.92, y, v,  transform=ax3.transAxes, color=WHITE, fontsize=10,
                 ha='right', fontweight='bold')
        ax3.plot([0.05, 0.95], [y-0.025, y-0.025],
                 color=BORDER, lw=0.5, transform=ax3.transAxes)

    save(fig, "01_training_history.png")


# ══════════════════════════════════════════════════════════════════════════════
# 2. MODEL ARCHITECTURE DIAGRAM
# ══════════════════════════════════════════════════════════════════════════════

def plot_architecture():
    print("[2/5] Architecture Diagram …")
    fig = _fig(20, 12, "VitalRadar — TCN-Attention v2  Architecture")
    ax  = fig.add_subplot(111)
    ax.set_facecolor(BG)
    ax.axis('off')
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)

    def box(x, y, w, h, label, sub="", color=CYAN, fontsize=9):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.08",
                              facecolor=PANEL, edgecolor=color, lw=1.8)
        ax.add_patch(rect)
        ax.text(x+w/2, y+h/2+(0.15 if sub else 0), label,
                ha='center', va='center', color=color,
                fontsize=fontsize, fontweight='bold')
        if sub:
            ax.text(x+w/2, y+h/2-0.22, sub,
                    ha='center', va='center', color=GREY, fontsize=7.5)

    def arrow(x1, y1, x2, y2, color=BORDER):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.5))

    # ── TCN Stream (left) ─────────────────────────────────────────────────────
    ax.text(5, 11.3, "TCN  STREAM  (Time-Domain)", ha='center',
            color=ORANGE, fontsize=11, fontweight='bold')

    blocks = [
        ("Input\n[B,1,64]",   "[B, 1, 64]",  CYAN),
        ("Conv1D\nEmbed",      "1→32, k=3",   ORANGE),
        ("TCNBlock 1",         "32→64  d=1  RF=0.3s",  BLUE),
        ("TCNBlock 2",         "64→64  d=2  RF=0.9s",  BLUE),
        ("TCNBlock 3",         "64→128 d=4  RF=2.1s",  PURPLE),
        ("TCNBlock 4  ★NEW",   "128→128 d=8 RF=4.5s",  GREEN),
        ("Multi-Head\nAttn",   "128 dim, 4 heads",     CYAN),
        ("AvgPool\n[B,128]",   "AdaptiveAvgPool1d",    ORANGE),
    ]
    bw, bh, bx, by0 = 2.8, 0.82, 1.0, 10.2
    for i, (lbl, sub, col) in enumerate(blocks):
        by = by0 - i * 1.12
        box(bx, by, bw, bh, lbl, sub, col)
        if i > 0:
            arrow(bx+bw/2, by+bh+0.01, bx+bw/2, by0-(i-1)*1.12)

    # ── FFT Stream (right) ────────────────────────────────────────────────────
    ax.text(15, 11.3, "FFT  STREAM  (Freq-Domain)", ha='center',
            color=PURPLE, fontsize=11, fontweight='bold')

    fblocks = [
        ("Input\n[B,1,33]",   "[B, 1, 33]",   CYAN),
        ("Conv1D\n1→16",       "k=3, BN, GELU", PURPLE),
        ("Conv1D\n16→32",      "k=5, BN, GELU", PURPLE),
        ("AvgPool\n[B,32]",    "AdaptiveAvgPool1d", ORANGE),
        ("Linear\n[B,64]",     "32→64, GELU",   GREEN),
    ]
    fx, fy0 = 13.2, 10.2
    for i, (lbl, sub, col) in enumerate(fblocks):
        fy = fy0 - i * 1.12
        box(fx, fy, bw, bh, lbl, sub, col)
        if i > 0:
            arrow(fx+bw/2, fy+bh+0.01, fx+bw/2, fy0-(i-1)*1.12)

    # ── Fusion ────────────────────────────────────────────────────────────────
    concat_y = 4.4
    box(7.6, concat_y, 4.8, 0.9, "CONCAT  [B, 192]",
        "128 (TCN) + 64 (FFT)", CYAN, fontsize=10)

    # arrows from streams to concat
    arrow(bx+bw/2,   by0-7*1.12+bh/2, 8.2, concat_y+0.9, GREEN)
    arrow(fx+bw/2,   fy0-4*1.12+bh/2, 12.0, concat_y+0.9, GREEN)

    # ── Head ──────────────────────────────────────────────────────────────────
    head = [
        ("Linear 192→96", "GELU + Dropout(0.2)", ORANGE),
        ("Linear 96→2",   "class logits",         BLUE),
        ("Softmax",        "confidence ∈ [0,1]",   CYAN),
    ]
    hy = concat_y - 1.3
    for i, (lbl, sub, col) in enumerate(head):
        y = hy - i*1.1
        box(7.6, y, 4.8, 0.85, lbl, sub, col)
        if i > 0:
            arrow(10.0, hy-(i-1)*1.1, 10.0, hy-i*1.1+0.85)
    arrow(10.0, concat_y, 10.0, hy+0.85)

    # output label
    out_y = hy - 2*1.1 - 0.6
    ax.text(10.0, out_y, "Output: no_breathing / breathing  +  confidence",
            ha='center', color=GREEN, fontsize=11, fontweight='bold')

    # param count badge
    ax.text(19.5, 11.5, "~340K\nparams", ha='center', color=GREY,
            fontsize=9, style='italic')

    save(fig, "02_architecture.png")


# ══════════════════════════════════════════════════════════════════════════════
# 3. SYNTHETIC SIGNAL BREAKDOWN  (no real data file required)
# ══════════════════════════════════════════════════════════════════════════════

def plot_signal_breakdown():
    print("[3/5] Signal Breakdown …")
    rng = np.random.default_rng(42)
    t   = np.linspace(0, 6.4, 64)

    # Simulate a breathing signal
    raw = (180                            # baseline distance cm
           + 4.0 * np.sin(2*np.pi*0.25*t)  # breathing at 0.25 Hz
           + 1.5 * np.sin(2*np.pi*1.2*t)   # motion artefact
           + rng.normal(0, 0.8, 64))        # sensor noise

    # Preprocessing (simplified)
    from scipy import signal as sp
    detrended = sp.detrend(raw)
    sos       = sp.butter(4, 0.1, btype='high', output='sos', fs=10.0)
    filtered  = sp.sosfilt(sos, detrended)
    norm      = filtered / (np.max(np.abs(filtered)) + 1e-8)

    fft_mag = np.abs(np.fft.rfft(sp.detrend(raw)))
    fft_mag = fft_mag / (np.max(fft_mag) + 1e-8)
    freqs   = np.linspace(0, 5.0, len(fft_mag))

    fig = _fig(16, 11, "VitalRadar — Signal Processing Pipeline")
    gs  = gridspec.GridSpec(3, 1, figure=fig, hspace=0.5,
                            left=0.08, right=0.97, top=0.90, bottom=0.06)

    # Raw
    ax0 = _ax(fig.add_subplot(gs[0]), "Sample index", "Distance (cm)",
              "①  Raw LD2410 Radar Distance")
    ax0.plot(raw, color=ORANGE, lw=1.8)
    ax0.fill_between(range(64), raw, raw.min(), alpha=0.15, color=ORANGE)

    # Preprocessed
    ax1 = _ax(fig.add_subplot(gs[1]), "Sample index", "Amplitude",
              "②  Preprocessed Waveform  (Detrended + High-pass + Normalised  →  TCN Stream Input)")
    ax1.plot(norm, color=BLUE, lw=1.8)
    ax1.fill_between(range(64), norm, 0, alpha=0.15, color=BLUE)
    ax1.set_ylim(-1.3, 1.3)
    ax1.axhline(0, color=BORDER, lw=0.8)

    # FFT
    ax2 = _ax(fig.add_subplot(gs[2]), "Frequency (Hz)", "Magnitude",
              "③  FFT Power Spectrum  →  FFT Stream Input  (33 bins)")
    ax2.plot(freqs, fft_mag, color=PURPLE, lw=2)
    ax2.fill_between(freqs, fft_mag, alpha=0.2, color=PURPLE)
    ax2.axvspan(0.15, 0.67, color=GREEN, alpha=0.12, label="Breathing Band (0.15–0.67 Hz)")
    ax2.axvline(0.25, color=GREEN, lw=1.5, ls='--', alpha=0.8, label="Simulated breath peak")
    ax2.set_xlim(0, 5)
    ax2.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=WHITE, fontsize=9)


    save(fig, "03_signal_breakdown.png")


# ══════════════════════════════════════════════════════════════════════════════
# 4. DATASET STATISTICS  (from training_history.json proxy + synthetic)
# ══════════════════════════════════════════════════════════════════════════════

def plot_dataset_stats(history_path="training_history.json"):
    print("[4/5] Dataset Statistics …")

    fig = _fig(18, 10, "VitalRadar — Dataset & Training Statistics")
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38,
                            left=0.07, right=0.97, top=0.90, bottom=0.08)

    # ── Epoch-wise val acc distribution ──────────────────────────────────────
    if os.path.exists(history_path):
        with open(history_path) as f:
            h = json.load(f)
        v_acc  = [e['val_acc']   for e in h]
        t_acc  = [e['train_acc'] for e in h]
        epochs = [e['epoch']     for e in h]

        ax0 = _ax(fig.add_subplot(gs[0, :2]), "Epoch",
                  "Accuracy (%)", "Accuracy Convergence")
        ax0.plot(epochs, t_acc, color=ORANGE, lw=2, label="Train")
        ax0.plot(epochs, v_acc, color=CYAN,   lw=2, label="Val")
        # Moving average
        win = 5
        ma  = np.convolve(v_acc, np.ones(win)/win, mode='valid')
        ax0.plot(epochs[win-1:], ma, color=GREEN, lw=1.5,
                 ls='--', label=f"Val MA-{win}")
        ax0.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=WHITE)

        # Histogram of val acc
        ax1 = _ax(fig.add_subplot(gs[1, :2]), "Val Accuracy (%)",
                  "Frequency", "Validation Accuracy Distribution")
        ax1.hist(v_acc, bins=20, color=CYAN, edgecolor=BG, alpha=0.85)
        ax1.axvline(np.mean(v_acc), color=ORANGE, lw=2,
                    label=f"Mean {np.mean(v_acc):.1f}%")
        ax1.axvline(max(v_acc),    color=GREEN,  lw=2, ls='--',
                    label=f"Best {max(v_acc):.1f}%")
        ax1.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=WHITE)

    # ── Simulated class balance ────────────────────────────────────────────────
    ax2 = _ax(fig.add_subplot(gs[0, 2]))
    ax2.set_title("Class Distribution (Train)", color=WHITE, fontsize=11)
    ax2.axis('off')
    sizes  = [552, 552]   # balanced dataset (approximated)
    labels = ["No Breathing", "Breathing"]
    colors = [RED, GREEN]
    wedges, texts, autotexts = ax2.pie(
        sizes, labels=labels, autopct='%1.0f%%',
        colors=colors, startangle=90,
        textprops={'color': WHITE, 'fontsize': 10},
        wedgeprops={'edgecolor': BG, 'linewidth': 2},
        pctdistance=0.75)
    for at in autotexts: at.set_color(BG); at.set_fontweight('bold')

    # ── Model param breakdown ─────────────────────────────────────────────────
    ax3 = _ax(fig.add_subplot(gs[1, 2]))
    ax3.set_title("Parameter Distribution", color=WHITE, fontsize=11)
    ax3.axis('off')
    # Approximate param counts per module
    components = ["Embed\n(2K)", "TCN Blocks\n(230K)", "Attention\n(66K)",
                  "FFT Stream\n(4K)", "Head\n(19K)"]
    param_vals  = [2048, 230000, 65536, 3920, 19008]
    bar_colors  = [ORANGE, BLUE, CYAN, PURPLE, GREEN]
    xs = np.arange(len(components))
    bars = ax3.bar(xs, param_vals, color=bar_colors, edgecolor=BG,
                   width=0.6)
    ax3.set_xticks(xs)
    ax3.set_xticklabels(components, color=GREY, fontsize=8)
    ax3.set_facecolor(PANEL)
    for spine in ax3.spines.values(): spine.set_edgecolor(BORDER)
    ax3.tick_params(colors=GREY)
    ax3.set_ylabel("Parameters", color=GREY)
    ax3.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
    for bar, v in zip(bars, param_vals):
        ax3.text(bar.get_x()+bar.get_width()/2,
                 bar.get_height()+500, f"{v/1000:.1f}K",
                 ha='center', color=WHITE, fontsize=8)

    save(fig, "04_dataset_stats.png")


# ══════════════════════════════════════════════════════════════════════════════
# 5. MODEL SPECS CARD
# ══════════════════════════════════════════════════════════════════════════════

def plot_model_card():
    print("[5/5] Model Specs Card …")
    fig = _fig(16, 9, None)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0, 16); ax.set_ylim(0, 9)

    # Title banner
    banner = FancyBboxPatch((0.3, 7.5), 15.4, 1.2,
                            boxstyle="round,pad=0.1",
                            facecolor=PANEL, edgecolor=CYAN, lw=2)
    ax.add_patch(banner)
    ax.text(8, 8.2, "VitalRadar  TCN-Attention v2  —  Model Specification Card",
            ha='center', va='center', color=CYAN, fontsize=15, fontweight='bold',
            fontfamily='monospace')

    specs = [
        # col1
        [("Architecture",  "TCN + Multi-Head Attention + FFT Dual-Stream"),
         ("Input (TCN)",   "[1, 64]  — 64 radar distance samples  @10 Hz"),
         ("Input (FFT)",   "[1, 33]  — 33-bin FFT power spectrum"),
         ("Output",        "[2]  — no_breathing / breathing logits"),
         ("Parameters",    "~340 K  (~1.3 MB)"),
         ("Receptive Field","61 samples  ≈  6.1 seconds"),
         ("TCN Dilations", "d = 1, 2, 4, 8"),
         ("Attention Heads","4"),],
        # col2
        [("Task",          "Binary classification"),
         ("Loss",          "CrossEntropyLoss + label smoothing 0.05"),
         ("Recall Bias",   "2×  on breathing class (rescue priority)"),
         ("Optimiser",     "AdamW  lr=1e-3  wd=1e-4"),
         ("Scheduler",     "CosineAnnealing  eta_min=1e-5"),
         ("Epochs",        "100"),
         ("Batch Size",    "32"),
         ("Augmentation",  "Noise / Scale / Roll  (train only)"),],
        # col3
        [("Best Val Acc",  "92.03%  (epoch 91)"),
         ("Final Val Acc", "90.58%"),
         ("Final Train Acc","99.82%"),
         ("Device",        "CPU  (Raspberry Pi 4)"),
         ("Inference Time","~12 ms  / window"),
         ("Sample Rate",   "10 Hz  (LD2410 radar)"),
         ("Window Size",   "6.4 s  (64 samples)"),
         ("Checkpoint",    "tcn_attention_vitalradar_v2.pt"),],
    ]

    col_titles = ["[Architecture]", "[Training Config]", "[Performance]"]
    col_colors = [ORANGE, BLUE, GREEN]
    xs = [0.5, 5.6, 10.8]

    for ci, (col, title, cx, cc) in enumerate(zip(specs, col_titles, xs, col_colors)):
        # column header
        ax.text(cx, 7.1, title, color=cc, fontsize=10, fontweight='bold')
        ax.plot([cx, cx+4.8], [7.0, 7.0], color=cc, lw=1.2)
        for ri, (k, v) in enumerate(col):
            y = 6.4 - ri * 0.78
            ax.text(cx, y, k+":", color=GREY, fontsize=8.5)
            ax.text(cx+0.1, y-0.28, v, color=WHITE, fontsize=8, wrap=True)

    # footer
    ax.text(8, 0.25,
            "Designed for real-time rescue detection through walls / rubble  •  "
            "Raspberry Pi 4 + LD2410 mmWave Radar",
            ha='center', color=GREY, fontsize=8.5, style='italic')

    save(fig, "05_model_card.png")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    hist_path  = os.path.join(os.path.dirname(__file__), "training_history.json")
    model_path = os.path.join(os.path.dirname(__file__), "tcn_attention_vitalradar_v2.pt")

    print("=" * 60)
    print("  VitalRadar Visualization Suite")
    print(f"  Output -> {OUT_DIR}")
    print("=" * 60)

    plot_training_history(hist_path)
    plot_architecture()
    plot_signal_breakdown()
    plot_dataset_stats(hist_path)
    plot_model_card()

    print("\n" + "="*60)
    print(f"  All 5 images saved to: {OUT_DIR}")
    print("  Files:")
    for f in sorted(os.listdir(OUT_DIR)):
        fp = os.path.join(OUT_DIR, f)
        size_kb = os.path.getsize(fp)//1024
        print(f"    {f}  ({size_kb} KB)")
    print("="*60)
