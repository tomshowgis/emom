"""Diagnostic figure for one session: raw chosen axis, band-passed signal, kept/rejected peaks.

Usage: python -m analysis.debug_plot <session stem or substring> [out.png]
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .baseline import DEFAULT, PROFILES, count_reps
from .dataset import load_sessions

OUT = Path("/private/tmp/claude-501/-Users-tszoldrowski-repo-emom/ab056e59-04c8-4417-a119-9812a1b7586f/scratchpad")


def render(stem: str, out: Path | None = None) -> Path:
    s = next(x for x in load_sessions(include_all=True) if stem in x.path.stem)
    r = count_reps(s.df, profile=PROFILES.get(s.exercise, DEFAULT))
    t = s.df["t_s"].values
    fig, ax = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    ax[0].plot(t, s.df[r.axis] if r.axis in s.df else r.signal, lw=0.8); ax[0].set_ylabel(f"{r.axis} raw" if r.axis in s.df else "pca (band)")
    ax[1].plot(t, r.signal, lw=1, color="#1f77b4"); ax[1].set_ylabel(f"band-pass @ {1/r.period_s:.2f} Hz")
    rej = [p for p in r.peaks_all if p not in r.peak_times]
    ax[1].plot(r.peak_times, np.interp(r.peak_times, t, r.signal), "go", label=f"liczone {r.count}")
    ax[1].plot(rej, np.interp(rej, t, r.signal), "rx", label=f"odrzucone {len(rej)}")
    ax[1].legend(loc="upper right")
    mag = np.sqrt(s.df.gx**2 + s.df.gy**2 + s.df.gz**2)
    ax[2].plot(t, mag, lw=0.8, color="#9467bd"); ax[2].set_ylabel("|gyro| [rad/s]"); ax[2].set_xlabel("t [s]")
    for a in ax: a.grid(alpha=0.3)
    fig.suptitle(f"{s.path.stem} · prawda {s.true_reps} · policzone {r.count} · oś {r.axis} · T={r.period_s:.2f} s · tempo {s.meta.get('tempo')}")
    fig.tight_layout()
    out = out or OUT / f"dbg_{s.path.stem}.png"
    fig.savefig(out, dpi=100); plt.close(fig)
    return out


if __name__ == "__main__":
    print(render(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None))
