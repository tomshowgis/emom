"""Load recordings from data/raw with their metadata.

A session is "clean" when it has a trusted rep count: true_reps > 0, no time gaps,
and not flagged count_uncertain. Others are kept as edge cases (use include_all).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "raw"
AXES = ["ax", "ay", "az", "gx", "gy", "gz"]


@dataclass
class Session:
    path: Path
    meta: dict
    df: pd.DataFrame = field(repr=False)

    @property
    def exercise(self) -> str:
        return self.meta["exercise_id"]

    @property
    def true_reps(self) -> int:
        return int(self.meta.get("true_reps") or 0)

    @property
    def name(self) -> str:
        return f"{self.path.parent.name}/{self.path.stem}"

    @property
    def clean(self) -> bool:
        m = self.meta
        return self.true_reps > 0 and not m.get("gaps") and not m.get("count_uncertain")


def resample_uniform(df: pd.DataFrame, fs: float = 100.0) -> pd.DataFrame:
    """Uniform time base at fs; small gaps are linearly interpolated."""
    t = (df["t_ms"].values - df["t_ms"].values[0]) / 1000.0
    tu = np.arange(0, t[-1], 1.0 / fs)
    out = {"t_s": tu}
    for c in AXES:
        out[c] = np.interp(tu, t, df[c].values)
    return pd.DataFrame(out)


def load_sessions(include_all: bool = False) -> list[Session]:
    out = []
    for j in sorted(DATA.glob("*/*.json")):
        meta = json.loads(j.read_text(encoding="utf-8"))
        csv = j.with_suffix(".csv")
        if not csv.exists():
            continue
        s = Session(csv, meta, resample_uniform(pd.read_csv(csv)))
        if include_all or s.clean:
            out.append(s)
    return out
