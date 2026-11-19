"""Lokale SQLite-Ablage für Trainings, Sätze und Progressions-Log."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .progression import Session, Set
from .workouts import exercise_key

SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    start TEXT NOT NULL,
    name TEXT,
    duration REAL
);
CREATE TABLE IF NOT EXISTS sets (
    activity_id INTEGER NOT NULL,
    idx INTEGER NOT NULL,
    category TEXT,
    name TEXT,
    reps INTEGER,
    kg REAL,
    PRIMARY KEY (activity_id, idx)
);
CREATE TABLE IF NOT EXISTS changes (
    ts TEXT NOT NULL,
    workout_id INTEGER,
    workout_name TEXT,
    key TEXT,
    exercise TEXT,
    activity_id INTEGER,
    old_kg REAL,
    new_kg REAL,
    old_reps INTEGER,
    new_reps INTEGER,
    reason TEXT,
    dry_run INTEGER DEFAULT 0
);
"""


class DB:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(path)
        self.con.executescript(SCHEMA)

    def close(self):
        self.con.commit()
        self.con.close()

    # --- Aktivitäten -------------------------------------------------------
    def has_activity(self, activity_id: int) -> bool:
        return self.con.execute("SELECT 1 FROM activities WHERE id=?", (activity_id,)).fetchone() is not None

    def latest_start(self) -> str | None:
        row = self.con.execute("SELECT MAX(start) FROM activities").fetchone()
        return row[0] if row else None

    def save_activity(self, activity_id: int, start: str, name: str, duration: float,
                      sets: list[tuple[str | None, str | None, int, float]]):
        c = self.con
        c.execute("INSERT OR REPLACE INTO activities VALUES (?,?,?,?)", (activity_id, start, name, duration))
        c.execute("DELETE FROM sets WHERE activity_id=?", (activity_id,))
        c.executemany(
            "INSERT INTO sets VALUES (?,?,?,?,?,?)",
            [(activity_id, i, cat, nm, reps, kg) for i, (cat, nm, reps, kg) in enumerate(sets)],
        )
        c.commit()

    def history(self) -> dict[str, list[Session]]:
        """Übungsschlüssel -> Sessions (aufsteigend nach Datum)."""
        rows = self.con.execute(
            """SELECT a.id, a.start, s.category, s.name, s.reps, s.kg
               FROM sets s JOIN activities a ON a.id = s.activity_id
               ORDER BY a.start, s.activity_id, s.idx"""
        ).fetchall()
        out: dict[str, dict[int, Session]] = {}
        for aid, start, cat, nm, reps, kg in rows:
            key = exercise_key(cat, nm)
            sess = out.setdefault(key, {}).setdefault(aid, Session(aid, start, []))
            sess.sets.append(Set(int(reps or 0), float(kg or 0)))
        return {k: list(v.values()) for k, v in out.items()}

    def activities(self) -> list[tuple]:
        return self.con.execute("SELECT id, start, name, duration FROM activities ORDER BY start").fetchall()

    # --- Progressions-Log ----------------------------------------------------
    def applied(self, workout_id: int, key: str, activity_id: int) -> bool:
        return self.con.execute(
            "SELECT 1 FROM changes WHERE workout_id=? AND key=? AND activity_id=? AND dry_run=0",
            (workout_id, key, activity_id),
        ).fetchone() is not None

    def log_change(self, workout_id: int, workout_name: str, ch, dry_run: bool, ts: str | None = None):
        self.con.execute(
            "INSERT INTO changes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (ts or datetime.now().isoformat(timespec="seconds"), workout_id, workout_name, ch.key,
             ch.exercise, ch.activity_id, ch.old_kg, ch.new_kg, ch.old_reps, ch.new_reps,
             ch.reason, int(dry_run)),
        )
        self.con.commit()

    def changes(self) -> list[dict]:
        cur = self.con.execute("SELECT * FROM changes WHERE dry_run=0 ORDER BY ts DESC")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
