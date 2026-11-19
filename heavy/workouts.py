"""Lesen und Anpassen von Garmin-Connect-Workout-JSON (Strength)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Iterator

from .muscles import display_name
from .progression import Decision, Rule, Session, decide, fmt, raw_weight_to_kg

WEIGHT_UNIT_KILOGRAM = {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0}


def exercise_key(category: str | None, name: str | None) -> str:
    return f"{(category or '').upper()}/{(name or '').upper()}"


def iter_steps(workout: dict) -> Iterator[dict]:
    def walk(steps: list[dict]) -> Iterator[dict]:
        for st in steps or []:
            if st.get("type") == "RepeatGroupDTO" or "workoutSteps" in st:
                yield from walk(st.get("workoutSteps") or [])
            else:
                yield st

    for seg in workout.get("workoutSegments") or []:
        yield from walk(seg.get("workoutSteps") or [])


def is_work_step(step: dict) -> bool:
    key = ((step.get("stepType") or {}).get("stepTypeKey") or "").lower()
    return bool(step.get("category")) and key in ("interval", "main", "")


def step_reps(step: dict) -> int | None:
    cond = (step.get("endCondition") or {}).get("conditionTypeKey")
    if cond == "reps" and step.get("endConditionValue"):
        return int(step["endConditionValue"])
    return None


def weight_scale(workout: dict) -> float:
    """Faktor, mit dem kg in weightValue umgerechnet werden (1000 = Gramm)."""
    for st in iter_steps(workout):
        v = st.get("weightValue")
        if v and v > 0:
            return 1000.0 if v >= 500 else 1.0
    return 1000.0


def exercises_in(workout: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for st in iter_steps(workout):
        if is_work_step(st):
            out.setdefault(exercise_key(st.get("category"), st.get("exerciseName")), []).append(st)
    return out


@dataclass
class Change:
    key: str
    exercise: str
    old_kg: float | None
    new_kg: float
    old_reps: int | None
    new_reps: int | None
    reason: str
    activity_id: int

    @property
    def changed(self) -> bool:
        return (self.old_kg is None or abs(self.old_kg - self.new_kg) > 0.001) or (
            self.new_reps is not None and self.new_reps != self.old_reps
        )

    def describe(self) -> str:
        old = "–" if self.old_kg is None else f"{fmt(self.old_kg)} kg"
        s = f"{self.exercise}: {old} → {fmt(self.new_kg)} kg"
        if self.new_reps is not None and self.new_reps != self.old_reps:
            s += f", {self.old_reps}→{self.new_reps} Wdh"
        return s + f"  ({self.reason})"


def match_history(key: str, history: dict[str, list[Session]]) -> list[Session]:
    if key in history:
        return history[key]
    cat, name = key.split("/", 1)
    if not name:  # Vorlage hat nur Kategorie -> jüngste Übung dieser Kategorie
        cands = [v for k, v in history.items() if k.startswith(cat + "/") and v]
        if cands:
            return max(cands, key=lambda v: v[-1].date)
    else:  # Uhr hat evtl. nur die Kategorie erkannt
        return history.get(f"{cat}/", [])
    return []


def plan_changes(
    workout: dict,
    history: dict[str, list[Session]],
    rule_for,  # callable(key, category) -> Rule
    already_applied,  # callable(key, activity_id) -> bool
) -> tuple[dict, list[Change]]:
    """Gibt (neues Workout-JSON, Änderungen) zurück. Original bleibt unverändert."""
    wk = copy.deepcopy(workout)
    scale = weight_scale(wk)
    changes: list[Change] = []
    for key, steps in exercises_in(wk).items():
        hist = match_history(key, history)
        if not hist or already_applied(key, hist[-1].activity_id):
            continue
        cat = key.split("/", 1)[0]
        rule: Rule = rule_for(key, cat)
        reps = step_reps(steps[0])
        d: Decision | None = decide(rule, reps, hist)
        if d is None:
            continue
        olds = [raw_weight_to_kg(s.get("weightValue")) or None for s in steps]
        known = [w for w in olds if w]
        old_ref = max(known) if known else None
        uniform = len(set(known)) <= 1
        if (not rule.allow_decrease and d.kind != "deload" and old_ref is not None
                and d.new_kg < old_ref - 0.001):
            d.reason += f" – Vorlage bleibt {fmt(old_ref)} kg (nie senken)"
            d.new_kg = old_ref
        for st, w in zip(steps, olds):
            if uniform or w is None or old_ref is None:
                target = d.new_kg
            else:  # Pyramide: alle Stufen um dasselbe Delta verschieben
                target = max(0.0, round(w + (d.new_kg - old_ref), 2))
            st["weightValue"] = round(target * scale, 3)
            st["weightUnit"] = dict(WEIGHT_UNIT_KILOGRAM)
            if d.new_reps is not None and step_reps(st) is not None:
                st["endConditionValue"] = float(d.new_reps)
        changes.append(Change(key, display_name(*key.split("/", 1)), old_ref, d.new_kg,
                              reps, d.new_reps, d.reason, d.activity_id))
    return wk, changes


def summarize_workout(workout: dict) -> list[dict[str, Any]]:
    rows = []
    for key, steps in exercises_in(workout).items():
        w = [raw_weight_to_kg(s.get("weightValue")) for s in steps]
        rows.append({"key": key, "exercise": display_name(*key.split("/", 1)),
                     "steps": len(steps), "reps": step_reps(steps[0]),
                     "kg": max(w) if w else 0.0})
    return rows
