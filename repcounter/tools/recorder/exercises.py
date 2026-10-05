"""Exercise list taken from the timer (emom_timer.html) so ids match the app."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
TIMER = ROOT / "emom_timer.html"

MOUNTS = [
    ("kettlebell", "Kettlebell (dno)"),
    ("chest", "Klatka (klips na koszulce)"),
    ("wrist", "Nadgarstek"),
    ("belt", "Pasek"),
]

EXTRA = [
    ("cal-pushup", "Pompki"),
    ("cal-pullup", "Podciągnięcia"),
]


def load_exercises() -> list[tuple[str, str]]:
    """Return [(id, name)] for rep-based exercises (timed ones excluded)."""
    out: list[tuple[str, str]] = []
    try:
        text = TIMER.read_text(encoding="utf-8")
        m = re.search(r"const EXERCISES = \[(.*?)\n\];", text, re.S)
        body = m.group(1) if m else ""
        for line in body.splitlines():
            mid = re.search(r'id:"([^"]+)"', line)
            mname = re.search(r'name:"([^"]+)"', line)
            if not mid or not mname:
                continue
            if "work:" in line or mid.group(1) == "rest":
                continue
            out.append((mid.group(1), mname.group(1)))
    except OSError:
        pass
    out.extend(EXTRA)
    return out
