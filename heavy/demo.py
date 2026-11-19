"""Demo-Modus: simuliert 20 Wochen Push/Pull/Beine inkl. Auto-Progression,
ohne Garmin-Konto. Nutzt dieselbe Engine wie der echte Betrieb."""

from __future__ import annotations

import copy
import math
import random
from datetime import date, timedelta
from pathlib import Path

from .db import DB
from .engine import run_progress
from .workouts import exercises_in, step_reps
from .progression import raw_weight_to_kg


def build_strength_workout(wid: int, name: str, exercises: list[tuple[str, str, int, int, float]]) -> dict:
    """Erzeugt Garmin-Connect-Workout-JSON (gleiche Struktur wie get_workout_by_id)."""
    steps, order = [], 1
    for gi, (cat, ex, sets, reps, kg) in enumerate(exercises, start=1):
        group = {
            "type": "RepeatGroupDTO", "stepOrder": order, "childStepId": gi,
            "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat"},
            "numberOfIterations": sets, "smartRepeat": False,
            "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations"},
            "endConditionValue": float(sets), "workoutSteps": [],
        }
        order += 1
        group["workoutSteps"].append({
            "type": "ExecutableStepDTO", "stepOrder": order, "childStepId": gi,
            "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
            "endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps"},
            "endConditionValue": float(reps), "category": cat, "exerciseName": ex,
            "weightValue": kg * 1000.0,
            "weightUnit": {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0},
        })
        order += 1
        group["workoutSteps"].append({
            "type": "ExecutableStepDTO", "stepOrder": order, "childStepId": gi,
            "stepType": {"stepTypeId": 5, "stepTypeKey": "rest"},
            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
            "endConditionValue": 120.0,
        })
        order += 1
        steps.append(group)
    return {
        "workoutId": wid, "workoutName": name,
        "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
        "workoutSegments": [{"segmentOrder": 1, "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
                             "workoutSteps": steps}],
    }


class FakeGarmin:
    """Minimaler Ersatz für garminconnect.Garmin (nur Workout-Methoden)."""

    def __init__(self, workouts: list[dict]):
        self.workouts = {w["workoutId"]: w for w in workouts}
        self.updates: list[int] = []
        self.pushes: list[int] = []

    def get_workout_by_id(self, wid):
        return copy.deepcopy(self.workouts[int(wid)])

    def update_workout(self, wid, body):
        self.workouts[int(wid)] = copy.deepcopy(body) | {"workoutId": int(wid)}
        self.updates.append(int(wid))
        return {}

    def push_workout_to_device(self, wid):
        self.pushes.append(int(wid))
        return {}

    def get_workouts(self, start=0, limit=100):
        return list(self.workouts.values())


PLAN = {
    101: ("Push", [
        ("BENCH_PRESS", "BARBELL_BENCH_PRESS", 4, 8, 70.0, 0.0045),
        ("SHOULDER_PRESS", "DUMBBELL_SHOULDER_PRESS", 3, 10, 18.0, 0.004),
        ("BENCH_PRESS", "INCLINE_DUMBBELL_BENCH_PRESS", 3, 10, 24.0, 0.0035),
        ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE", 3, 12, 8.0, 0.0008),
        ("TRICEPS_EXTENSION", "ROPE_PRESSDOWN", 3, 12, 22.0, 0.004),
    ]),
    102: ("Pull", [
        ("DEADLIFT", "BARBELL_DEADLIFT", 3, 5, 110.0, 0.004),
        ("PULL_UP", "CLOSE_GRIP_LAT_PULLDOWN", 4, 10, 55.0, 0.0035),
        ("ROW", "SEATED_CABLE_ROW", 3, 10, 50.0, 0.003),
        ("ROW", "FACE_PULL", 3, 15, 20.0, 0.002),
        ("CURL", "BARBELL_BICEPS_CURL", 3, 10, 25.0, 0.0025),
    ]),
    103: ("Beine", [
        ("SQUAT", "BARBELL_BACK_SQUAT", 4, 6, 90.0, 0.005),
        ("DEADLIFT", "ROMANIAN_DEADLIFT", 3, 8, 80.0, 0.004),
        ("SQUAT", "LEG_PRESS", 3, 10, 150.0, 0.0045),
        ("LEG_CURL", "LEG_CURL", 3, 12, 40.0, 0.0015),
        ("CALF_RAISE", "STANDING_CALF_RAISE", 4, 12, 60.0, -0.001),
    ]),
}

COMPOUND = {"BARBELL_BENCH_PRESS", "BARBELL_DEADLIFT", "BARBELL_BACK_SQUAT", "ROMANIAN_DEADLIFT"}


def run_demo(home: Path, weeks: int = 20, seed: int = 7, log=print) -> tuple[Path, DB]:
    rng = random.Random(seed)
    db_path = home / "data" / "demo.db"
    if db_path.exists():
        db_path.unlink()
    db = DB(db_path)
    g = FakeGarmin([build_strength_workout(wid, nm, [(c, e, s, r, kg) for c, e, s, r, kg, _ in ex])
                    for wid, (nm, ex) in PLAN.items()])
    cfg = {
        "managed_workouts": list(PLAN), "push_to_device": True,
        "default_rule": {"mode": "double", "increment": 2.5, "round_to": 0.5, "deload_after": 3,
                         "deload_pct": 0.1, "warmup_ratio": 0.6},
        "category_rules": {"CURL": {"increment": 1.0}, "LATERAL_RAISE": {"increment": 1.0},
                           "TRICEPS_EXTENSION": {"increment": 1.0}, "DEADLIFT": {"increment": 5.0},
                           "SQUAT": {"increment": 2.5}},
        "exercise_rules": {"PULL_UP/CLOSE_GRIP_LAT_PULLDOWN": {"rep_range": [8, 12]}},
    }
    # "wahre" Kraft pro Übung: Start leicht über Plan-Gewicht
    true_1rm = {}
    for wid, (_, exs) in PLAN.items():
        for c, e, s, r, kg, rate in exs:
            true_1rm[(c, e)] = kg * (1 + (r + 1.5) / 30)
    rates = {(c, e): rate for _, (_, exs) in PLAN.items() for c, e, s, r, kg, rate in exs}

    today = date.today()
    start = today - timedelta(weeks=weeks)
    start -= timedelta(days=start.weekday())
    d, aid, n = start, 9_000_000, 0
    while d <= today:
        wd = d.weekday()
        wid = {0: 101, 2: 102, 4: 103}.get(wd)
        if wid and rng.random() > 0.08:  # ab und zu ausgelassen
            wk = g.get_workout_by_id(wid)
            sets = []
            for key, steps in exercises_in(wk).items():
                cat, ex = key.split("/", 1)
                target = raw_weight_to_kg(steps[0].get("weightValue"))
                reps_t = step_reps(steps[0]) or 8
                nsets = next(int(grp["numberOfIterations"]) for grp in wk["workoutSegments"][0]["workoutSteps"]
                             if grp["workoutSteps"][0].get("exerciseName") == ex)
                t = true_1rm[(cat, ex)]
                # Plateau-/Rückschritt-Phasen für realistischere Kurven
                phase = math.sin(n / 9.0 + sum(map(ord, ex)) % 7)
                t *= 1 + rates[(cat, ex)] * (1.0 + 0.6 * phase) + rng.gauss(0, 0.004)
                if ex == "BARBELL_DEADLIFT" and 30 < n < 38:
                    t *= 0.992  # kleiner Einbruch (z. B. Rücken)
                true_1rm[(cat, ex)] = t
                w = target
                # manchmal erhöht man spontan auf der Uhr
                if rng.random() < 0.12:
                    w = target + (2.5 if target >= 20 else 1.0)
                if ex in COMPOUND:
                    sets.append((cat, ex, 8, round(w * 0.5 / 2.5) * 2.5))
                for i in range(nsets):
                    cap = 30 * (t / max(w, 1) - 1) + 1.0 - i * 0.4 + rng.gauss(0, 0.6)
                    reps = max(1, min(reps_t + 3, int(cap)))
                    sets.append((cat, ex, reps, w))
            aid += 1
            n += 1
            ts = f"{d.isoformat()} 18:{rng.randint(0, 59):02d}:00"
            db.save_activity(aid, ts, PLAN[wid][0], 3600.0, sets)
            run_progress(g, db, cfg, log=lambda *_: None, ts=ts)
        d += timedelta(days=1)
    log(f"Demo: {n} Trainings simuliert, {len(g.updates)} Workout-Updates an (Fake-)Garmin gesendet.")
    return db_path, db
