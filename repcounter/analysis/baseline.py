"""Baseline rep counter: band-pass around the set's own tempo, count cycles.

Idea (from the recordings log): every exercise looked different when counting
peaks of one axis (double peaks in swings, troughs in squats, two sub-movements
in curl+press), but all of them are periodic at the rep frequency. So:

1. pick the axis with the most energy in the rep band (0.25–3 Hz) — adaptive;
2. estimate the dominant period T from the autocorrelation of that signal;
3. band-pass narrowly around 1/T (suppresses the 2nd harmonic = double peaks);
4. count peaks of the band-passed signal that are at least `amp_ratio` of the
   median peak height (rejects lift/put-down bumps) and at least 0.6·T apart.

Exercise profiles only carry thresholds; the method is shared.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks

from .dataset import AXES


@dataclass
class Profile:
    period_min: float = 0.5   # s, fastest plausible rep
    period_max: float = 4.0   # s, slowest plausible rep
    amp_ratio: float = 0.45   # peak must be >= this * median peak height
    band: tuple[float, float] = (0.5, 1.6)  # band-pass as multiples of the rep frequency
    axes: tuple[str, ...] = tuple(AXES)      # candidate signals
    min_reps_run: int = 2      # ignore isolated cycles (lead-in/out)
    gyro_ratio: tuple[float, float] = (0.35, 2.2)  # cycle max|gyro| must be within these multiples of the median cycle


DEFAULT = Profile()
# Tempo bounds are physiological limits of one full repetition, not the timer's
# nominal reps/minute (which include rest). Two-move reps (curl+press, squat)
# get a floor above their sub-movement period so the period estimator cannot
# lock onto half a rep.
PROFILES: dict[str, Profile] = {
    "biceps-curl":           Profile(period_min=0.8, period_max=8.0),
    "russian-swing":         Profile(period_min=0.8, period_max=4.0),
    "sumo-high-pull":        Profile(period_min=0.8, period_max=6.0),
    "bent-over-row":         Profile(period_min=0.6, period_max=6.0),
    "goblet-shoulder-press": Profile(period_min=0.8, period_max=4.5),
    "goblet-squat":          Profile(period_min=1.3, period_max=8.0),
    "curl-press":            Profile(period_min=2.4, period_max=8.0),
    "halo":                  Profile(period_min=1.5, period_max=5.0),
}


@dataclass
class Result:
    count: int
    axis: str
    period_s: float
    peak_times: list[float]
    signal: np.ndarray          # band-passed signal used for counting
    peaks_all: list[float]      # all candidate peaks before the amplitude gate


def _bandpass(x: np.ndarray, fs: float, lo: float, hi: float) -> np.ndarray:
    lo = max(lo, 0.05)
    hi = min(hi, fs / 2 * 0.95)
    b, a = butter(2, [lo / (fs / 2), hi / (fs / 2)], btype="band")
    return filtfilt(b, a, x)


def _dominant_period(x: np.ndarray, fs: float, pmin: float, pmax: float) -> float:
    """Rep period from the unbiased autocorrelation.

    Lag with the highest autocorrelation inside the profile's tempo bounds;
    among near-equal candidates (within 5 %) the shortest wins.
    """
    x = x - x.mean()
    n = len(x)
    ac = np.correlate(x, x, mode="full")[n - 1:]
    # biased normalisation (tested 2026-10-11 against unbiased and capped variants:
    # biased gave the fewest errors; unbiased blows up at long lags and picks
    # whole-set structure instead of the rep). Sub-movement locking is handled by
    # the per-exercise period floor instead.
    ac = ac / (ac[0] + 1e-9)
    lo, hi = int(pmin * fs), min(int(pmax * fs), n // 2)
    if hi <= lo + 2:
        return pmin
    seg = ac[lo:hi]
    pk, _ = find_peaks(seg, prominence=0.02)
    if len(pk) == 0:
        return (lo + int(np.argmax(seg))) / fs
    vals = seg[pk]
    cands = pk[vals >= 0.95 * vals.max()]
    return (lo + int(cands.min())) / fs


def count_reps(df: pd.DataFrame, fs: float = 100.0, profile: Profile = DEFAULT) -> Result:
    # 1. choose the axis with the most energy in the generic rep band
    best_axis, best_energy = None, -1.0
    for c in profile.axes:
        y = _bandpass(df[c].values, fs, 1 / profile.period_max, 1 / profile.period_min)
        e = float(np.var(y))
        if e > best_energy:
            best_axis, best_energy = c, e
    y = _bandpass(df[best_axis].values, fs, 1 / profile.period_max, 1 / profile.period_min)
    # 2. tempo
    T = _dominant_period(y, fs, profile.period_min, profile.period_max)
    f0 = 1.0 / T
    # 3. narrow band around the rep frequency
    z = _bandpass(df[best_axis].values, fs, profile.band[0] * f0, profile.band[1] * f0)
    # 4. extrema with adaptive amplitude gate and rotation-consistency gate.
    #    A full cycle needs both a peak and a trough; a lead-in or put-down adds a lone
    #    extremum, so the cycle count is min(valid peaks, valid troughs).
    gmag = np.sqrt(df["gx"].values ** 2 + df["gy"].values ** 2 + df["gz"].values ** 2)
    win = max(1, int(0.35 * T * fs))

    def valid_extrema(sig):
        pk, _ = find_peaks(sig, distance=int(0.6 * T * fs), prominence=1e-6)
        if len(pk) == 0:
            return pk, pk
        heights = sig[pk]
        ref = np.median(np.sort(heights)[-max(3, len(heights) // 2):])  # median of the upper half
        keep = heights >= profile.amp_ratio * ref
        gmax = np.array([gmag[max(0, p - win):p + win].max() for p in pk])
        if keep.sum() >= 3:
            med = np.median(gmax[keep])
            lo_r, hi_r = profile.gyro_ratio
            keep &= (gmax >= lo_r * med) & (gmax <= hi_r * med)
        kept = pk[keep]
        if profile.min_reps_run > 1 and len(kept) >= profile.min_reps_run:  # drop isolated cycles
            gaps = np.diff(kept) / fs
            ok = np.ones(len(kept), dtype=bool)
            for i in range(len(kept)):
                left = gaps[i - 1] if i > 0 else np.inf
                right = gaps[i] if i < len(gaps) else np.inf
                if min(left, right) > 2.5 * T:
                    ok[i] = False
            kept = kept[ok]
        return kept, pk

    peaks, peaks_all = valid_extrema(z)
    troughs, _ = valid_extrema(-z)
    count = min(len(peaks), len(troughs))
    t = df["t_s"].values
    return Result(int(count), best_axis, T, list(t[peaks]), z, list(t[peaks_all]))
