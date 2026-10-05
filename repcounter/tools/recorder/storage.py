"""Session files: data/raw/YYYY-MM-DD/HHMMSS_<exercise>_<mount>.csv + .json sidecar."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from .protocol import Sample

DATA = Path(__file__).resolve().parents[2] / "data" / "raw"
COLUMNS = ["t_ms", "ax", "ay", "az", "gx", "gy", "gz"]


def save_session(samples: list[Sample], meta: dict) -> Path:
    now = datetime.now()
    folder = DATA / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{now.strftime('%H%M%S')}_{meta['exercise_id']}_{meta['mount']}"
    csv_path = folder / f"{stem}.csv"
    if csv_path.exists():  # never overwrite raw recordings
        stem += now.strftime("_%f")
        csv_path = folder / f"{stem}.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for s in samples:
            w.writerow([s.t_ms, f"{s.ax:.4f}", f"{s.ay:.4f}", f"{s.az:.4f}", f"{s.gx:.4f}", f"{s.gy:.4f}", f"{s.gz:.4f}"])
    meta = dict(meta)
    meta.update({
        "file": csv_path.name,
        "saved_at": now.isoformat(timespec="seconds"),
        "samples": len(samples),
        "duration_s": round((samples[-1].t_ms - samples[0].t_ms) / 1000, 2) if len(samples) > 1 else 0,
    })
    (folder / f"{stem}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return csv_path


def list_sessions() -> list[dict]:
    out = []
    if not DATA.exists():
        return out
    for j in sorted(DATA.glob("*/*.json"), reverse=True):
        try:
            meta = json.loads(j.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        meta["path"] = str(j.with_suffix(".csv"))
        meta["day"] = j.parent.name
        out.append(meta)
    return out


def load_session(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["t_s"] = (df["t_ms"] - df["t_ms"].iloc[0]) / 1000.0
    df["a_mag"] = (df["ax"] ** 2 + df["ay"] ** 2 + df["az"] ** 2) ** 0.5
    df["g_mag"] = (df["gx"] ** 2 + df["gy"] ** 2 + df["gz"] ** 2) ** 0.5
    return df


def samples_to_df(samples: list[Sample]) -> pd.DataFrame:
    if not samples:
        return pd.DataFrame(columns=COLUMNS + ["t_s", "a_mag", "g_mag"])
    df = pd.DataFrame([asdict(s) for s in samples])
    df["t_s"] = (df["t_ms"] - df["t_ms"].iloc[0]) / 1000.0
    df["a_mag"] = (df["ax"] ** 2 + df["ay"] ** 2 + df["az"] ** 2) ** 0.5
    df["g_mag"] = (df["gx"] ** 2 + df["gy"] ** 2 + df["gz"] ** 2) ** 0.5
    return df
