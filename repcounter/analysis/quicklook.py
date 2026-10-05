"""Quick look at one recording: all axes as PNG, plus a naive peak count for orientation.

Usage: .venv/bin/python repcounter/analysis/quicklook.py <csv> [out.png]
The peak count here is NOT the algorithm; it only helps eyeball whether reps are visible.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks

csv = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else csv.with_suffix(".png")
meta = json.loads(csv.with_suffix(".json").read_text(encoding="utf-8")) if csv.with_suffix(".json").exists() else {}
df = pd.read_csv(csv)
t = (df.t_ms - df.t_ms.iloc[0]) / 1000.0
fs = 1000.0 / np.median(np.diff(df.t_ms))

def lowpass(x, fc=3.0):
    b, a = butter(2, fc / (fs / 2))
    return filtfilt(b, a, x)

cols = [("ax", "acc X"), ("ay", "acc Y"), ("az", "acc Z"), ("gx", "gyro X"), ("gy", "gyro Y"), ("gz", "gyro Z")]
fig, axes = plt.subplots(len(cols) + 1, 1, figsize=(14, 14), sharex=True)
for ax_, (c, name) in zip(axes, cols):
    ax_.plot(t, df[c], lw=0.8, color="#888", label="surowe")
    ax_.plot(t, lowpass(df[c].values), lw=1.4, color="#1f77b4", label="filtr 3 Hz")
    ax_.set_ylabel(name + (" [m/s²]" if c.startswith("a") else " [rad/s]"))
    ax_.grid(alpha=0.3)
axes[0].legend(loc="upper right")

# naive orientation count: pick the axis with the largest low-passed std, count peaks
best, best_std = None, 0
for c, _ in cols:
    s = np.std(lowpass(df[c].values))
    if s > best_std:
        best, best_std = c, s
sig = lowpass(df[best].values)
sig = sig - np.median(sig)
peaks, _ = find_peaks(sig, prominence=0.5 * sig.std(), distance=int(0.6 * fs))
axes[-1].plot(t, sig, color="#d62728")
axes[-1].plot(t.iloc[peaks], sig[peaks], "ko")
for i, p in enumerate(peaks, 1):
    axes[-1].annotate(str(i), (t.iloc[p], sig[p]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
axes[-1].set_ylabel(f"{best} (filtr, −mediana)")
axes[-1].set_xlabel("t [s]")
axes[-1].grid(alpha=0.3)
title = f"{meta.get('exercise_name', csv.stem)} · {meta.get('mount','')} · prawdziwe powt.: {meta.get('true_reps','?')} · naiwne szczyty na {best}: {len(peaks)} · {fs:.0f} Hz"
fig.suptitle(title)
fig.tight_layout()
fig.savefig(out, dpi=110)
print(out, "| dominant axis:", best, "| naive peaks:", len(peaks), "| true:", meta.get("true_reps"))
