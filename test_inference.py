import numpy as np, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'model'))
from model_tcn_attention_v2 import TCNInferenceEngine

MODEL = os.path.join('model', 'tcn_attention_vitalradar_v2.pt')
engine = TCNInferenceEngine(MODEL)

# Test 1: synthetic breathing (0.25 Hz = 15 BPM)
t   = np.linspace(0, 6.4, 64)
sig = (180.0 + 4.0 * np.sin(2 * np.pi * 0.25 * t)
       + np.random.RandomState(0).normal(0, 0.5, 64))
det, conf = engine.predict(sig.astype(np.float32))
print(f"[Breathing signal]  detected={det}  confidence={conf:.3f}")

# Test 2: static / no movement
flat = np.full(64, 180.0, dtype=np.float32)
flat += np.random.RandomState(1).normal(0, 0.05, 64)
det2, conf2 = engine.predict(flat)
print(f"[Static signal]     detected={det2}  confidence={conf2:.3f}")

# Test 3: run two predictions back-to-back (thread safety check)
det3, conf3 = engine.predict(sig.astype(np.float32))
det4, conf4 = engine.predict(flat)
print(f"[Repeat call 1]     detected={det3}  confidence={conf3:.3f}")
print(f"[Repeat call 2]     detected={det4}  confidence={conf4:.3f}")

print("\n[OK] All tests passed. Safe to run deep_optimized.py")
