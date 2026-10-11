"""Run the baseline on every clean session and write an accuracy report.

Usage: .venv/bin/python -m analysis.evaluate   (from repcounter/)
Criterion from the brief: at most 1 error per 20 reps, i.e. |count - true| <= ceil(true / 20).
"""
from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import pandas as pd

from .baseline import DEFAULT, PROFILES, count_reps
from .dataset import load_sessions

REPORTS = Path(__file__).resolve().parent / "reports"


def tolerance(true: int) -> int:
    return max(1, math.ceil(true / 20))


def main(write: bool = True) -> pd.DataFrame:
    rows = []
    for s in load_sessions():
        prof = PROFILES.get(s.exercise, DEFAULT)
        r = count_reps(s.df, profile=prof)
        err = r.count - s.true_reps
        rows.append({"session": s.path.stem, "exercise": s.exercise, "true": s.true_reps, "count": r.count, "err": err,
                     "ok": abs(err) <= tolerance(s.true_reps), "axis": r.axis, "period_s": round(r.period_s, 2),
                     "tempo": s.meta.get("tempo"), "dirty": bool(s.meta.get("dirty")), "notes": (s.meta.get("notes") or "")[:40]})
    df = pd.DataFrame(rows)
    per_ex = df.groupby("exercise").agg(sets=("ok", "size"), ok=("ok", "sum"), reps=("true", "sum"),
                                        abs_err=("err", lambda e: int(e.abs().sum())), mae=("err", lambda e: round(e.abs().mean(), 2)))
    per_ex["ok_pct"] = (100 * per_ex["ok"] / per_ex["sets"]).round(0).astype(int)
    total = {"sets": len(df), "ok": int(df.ok.sum()), "reps": int(df.true.sum()), "abs_err": int(df.err.abs().sum())}
    pd.set_option("display.width", 220)
    print(df.to_string(index=False))
    print()
    print(per_ex.to_string())
    print(f"\nRAZEM: {total['ok']}/{total['sets']} serii w tolerancji, {total['abs_err']} błędnych powtórzeń na {total['reps']} "
          f"({100 * total['abs_err'] / total['reps']:.1f} %)")
    if write:
        REPORTS.mkdir(exist_ok=True)
        out = REPORTS / f"baseline_{date.today().isoformat()}.md"
        md = [f"# Baseline — {date.today().isoformat()}", "",
              f"Kryterium: |błąd| ≤ ceil(prawda/20). RAZEM: **{total['ok']}/{total['sets']}** serii w tolerancji, "
              f"{total['abs_err']} błędnych powtórzeń na {total['reps']} ({100 * total['abs_err'] / total['reps']:.1f} %).", "",
              "## Na ćwiczenie", "", per_ex.to_markdown(), "", "## Serie", "", df.to_markdown(index=False), ""]
        out.write_text("\n".join(md), encoding="utf-8")
        print("report:", out)
    return df


if __name__ == "__main__":
    main()
