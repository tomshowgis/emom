"""Rep counter based on the multi-axis loop: project the acceleration vector on its
two principal components, track the phase angle, count full turns.

Why: each rep draws one closed loop in the 3-D acceleration space (see the 3-D
plots). Counting turns of the phase angle needs no tempo estimate, so it survives
tempo changes inside a set; small extra bumps (double peaks) are small loops near
the centre and are gated out by a radius threshold.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt


@dataclass
class PhaseResult:
    count: int
    turns: float
    phase: np.ndarray
    radius: np.ndarray
    pcs: np.ndarray


def _lowpass(x, fs, fc=3.0):
    b, a = butter(2, fc / (fs / 2))
    return filtfilt(b, a, x, axis=0)


def _highpass(x, fs, fc):
    b, a = butter(2, fc / (fs / 2), btype="high")
    return filtfilt(b, a, x, axis=0)


def count_reps_phase(df: pd.DataFrame, fs: float = 100.0, use_gyro: bool = True,
                     hp_hz: float = 0.15, radius_ratio: float = 0.35) -> PhaseResult:
    cols = ["ax", "ay", "az"] + (["gx", "gy", "gz"] if use_gyro else [])
    X = df[cols].values.astype(float)
    X = _lowpass(X, fs)
    X = _highpass(X, fs, hp_hz)                 # drop gravity / slow orientation drift
    if use_gyro:                                # put gyro on a comparable scale
        X[:, 3:] *= np.std(X[:, :3]) / (np.std(X[:, 3:]) + 1e-9)
    X = X - X.mean(axis=0)
    # PCA via SVD: first two components span the plane of the loops
    _, _, vt = np.linalg.svd(X, full_matrices=False)
    pcs = X @ vt[:2].T
    phase = np.unwrap(np.arctan2(pcs[:, 1], pcs[:, 0]))
    radius = np.hypot(pcs[:, 0], pcs[:, 1])
    # integrate phase only while the point is far enough from the centre
    r_gate = radius_ratio * np.median(radius[radius > np.percentile(radius, 50)])
    dphi = np.diff(phase)
    active = radius[1:] > r_gate
    turns = np.sum(dphi[active]) / (2 * np.pi)
    return PhaseResult(int(round(abs(turns))), float(turns), phase, radius, pcs)
