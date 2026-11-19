"""Erzeugt das HTML-Dashboard aus der lokalen Datenbank."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .muscles import MUSCLES, display_name, muscles_for
from .progression import summarize

TEMPLATE = Path(__file__).parent / "templates" / "dashboard.html"


def build_data(db, warmup_ratio: float = 0.6, demo: bool = False, user: str = "") -> dict:
    exercises = []
    for key, sessions in db.history().items():
        cat, name = key.split("/", 1)
        rows = []
        for s in sessions:
            sm = summarize(s.sets, warmup_ratio)
            if sm["sets"] == 0:
                continue
            rows.append({
                "d": s.date[:10], "a": s.activity_id,
                "sets": [[x.reps, x.kg] for x in s.sets if x.reps > 0],
                "top": sm["top"], "e1rm": sm["e1rm"], "vol": sm["volume"],
                "reps": sm["reps"], "n": sm["sets"],
            })
        if rows:
            exercises.append({"key": key, "name": display_name(cat, name), "category": cat,
                              "muscles": muscles_for(cat, name), "sessions": rows})
    changes = [c for c in db.changes()
               if c["old_kg"] is None or abs((c["old_kg"] or 0) - c["new_kg"]) > 0.001
               or (c["new_reps"] is not None and c["new_reps"] != c["old_reps"])]
    return {
        "generated": datetime.now().isoformat(timespec="minutes"),
        "demo": demo,
        "user": user,
        "muscles": MUSCLES,
        "exercises": exercises,
        "activities": [{"id": a[0], "d": a[1][:10], "name": a[2], "dur": a[3]} for a in db.activities()],
        "changes": changes[:200],
    }


def write_report(db, out: Path, warmup_ratio: float = 0.6, demo: bool = False, user: str = "") -> Path:
    data = build_data(db, warmup_ratio, demo, user)
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
