"""Progressionslogik (rein, ohne Garmin-Abhängigkeit -> gut testbar).

Kernidee: Das nächste Zielgewicht basiert IMMER auf dem, was du zuletzt
tatsächlich gestemmt hast (auch wenn du das Gewicht auf der Uhr spontan
erhöht hast). Optional kommt automatische Doppel-Progression dazu.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Set:
    reps: int
    kg: float


@dataclass
class Session:
    activity_id: int
    date: str  # ISO "YYYY-MM-DD HH:MM:SS"
    sets: list[Set] = field(default_factory=list)


@dataclass
class Rule:
    mode: str = "double"  # double | carry | off
    increment: float = 2.5
    round_to: float = 0.5
    rep_range: tuple[int, int] | None = None
    deload_after: int = 3
    deload_pct: float = 0.10
    warmup_ratio: float = 0.6
    allow_decrease: bool = False  # Vorlage nie senken (außer Deload)

    @classmethod
    def merged(cls, *dicts: dict | None) -> "Rule":
        data: dict = {}
        for d in dicts:
            if d:
                data.update(d)
        r = cls()
        for k, v in data.items():
            if hasattr(r, k):
                setattr(r, k, tuple(v) if k == "rep_range" and v else v)
        return r


@dataclass
class Decision:
    base_kg: float
    new_kg: float
    new_reps: int | None
    reason: str
    activity_id: int
    kind: str = "hold"  # increase | hold | deload | carry


def raw_weight_to_kg(value: float | None) -> float:
    """Garmin liefert Gewichte meist in Gramm (60000 = 60 kg). Werte < 500
    werden als kg interpretiert (0,5 kg in Gramm wäre sinnlos)."""
    if not value or value <= 0:
        return 0.0
    return value / 1000.0 if value >= 500 else float(value)


def round_to(value: float, step: float) -> float:
    if step <= 0:
        return round(value, 2)
    return round(round(value / step) * step, 2)


def working_sets(sets: list[Set], warmup_ratio: float = 0.6) -> list[Set]:
    """Entfernt leere Sätze und Aufwärmsätze (< warmup_ratio * Topgewicht)."""
    s = [x for x in sets if x.reps > 0]
    if not s:
        return []
    top = max(x.kg for x in s)
    if top <= 0:
        return s
    return [x for x in s if x.kg >= top * warmup_ratio]


def e1rm(kg: float, reps: int) -> float:
    """Geschätztes 1RM nach Epley."""
    if kg <= 0 or reps <= 0:
        return 0.0
    if reps == 1:
        return kg
    return kg * (1 + min(reps, 15) / 30.0)


def summarize(sets: list[Set], warmup_ratio: float = 0.6) -> dict:
    ws = working_sets(sets, warmup_ratio)
    if not ws:
        return {"top": 0.0, "e1rm": 0.0, "volume": 0.0, "reps": 0, "sets": 0}
    return {
        "top": max(x.kg for x in ws),
        "e1rm": round(max(e1rm(x.kg, x.reps) for x in ws), 2),
        "volume": round(sum(x.kg * x.reps for x in ws), 1),
        "reps": sum(x.reps for x in ws),
        "sets": len(ws),
    }


def _top_sets(session: Session, rule: Rule) -> tuple[float, list[Set]]:
    ws = working_sets(session.sets, rule.warmup_ratio)
    if not ws:
        return 0.0, []
    base = max(x.kg for x in ws)
    return base, [x for x in ws if x.kg >= base - 0.01]


def decide(rule: Rule, template_reps: int | None, history: list[Session]) -> Decision | None:
    """Berechnet das Zielgewicht fürs nächste Training aus der Historie (aufsteigend sortiert)."""
    if rule.mode == "off" or not history:
        return None
    last = history[-1]
    base, top = _top_sets(last, rule)
    if not top or base <= 0:
        return None  # keine Daten oder Körpergewichtsübung

    if rule.mode == "carry" or (template_reps is None and rule.rep_range is None):
        return Decision(base, base, None, f"Zuletzt {fmt(base)} kg – übernommen", last.activity_id, "carry")

    lo, hi = rule.rep_range or (template_reps, template_reps)
    min_reps = min(x.reps for x in top)
    reps_str = "/".join(str(x.reps) for x in top)

    if min_reps >= hi:
        new = round_to(base + rule.increment, rule.round_to)
        if new <= base:
            new = round(base + max(rule.round_to, 0.25), 2)
        return Decision(base, new, lo if rule.rep_range else None,
                        f"{reps_str} Wdh @ {fmt(base)} kg ≥ Ziel {hi} → +{fmt(new - base)} kg",
                        last.activity_id, "increase")

    if min_reps < lo:
        fails = 0
        for sess in reversed(history):
            b, t = _top_sets(sess, rule)
            if t and abs(b - base) < 0.01 and min(x.reps for x in t) < lo:
                fails += 1
            else:
                break
        if fails >= rule.deload_after:
            # auf das Steigerungsraster runden (z. B. 2,5-kg-Schritte), damit Scheiben passen
            new = round_to(base * (1 - rule.deload_pct), max(rule.round_to, rule.increment))
            return Decision(base, new, lo if rule.rep_range else None,
                            f"{fails}× Ziel {lo} Wdh verfehlt → Deload −{int(rule.deload_pct * 100)} %",
                            last.activity_id, "deload")
        return Decision(base, base, None,
                        f"{reps_str} Wdh < Ziel {lo} ({fails}/{rule.deload_after}) → {fmt(base)} kg halten",
                        last.activity_id)

    # im Wiederholungsbereich, aber noch nicht oben angekommen
    new_reps = min(hi, min_reps + 1) if rule.rep_range else None
    msg = f"{reps_str} Wdh @ {fmt(base)} kg → Gewicht halten"
    if new_reps:
        msg += f", Ziel {new_reps} Wdh"
    return Decision(base, base, new_reps, msg, last.activity_id)


def fmt(kg: float) -> str:
    return f"{kg:.2f}".rstrip("0").rstrip(".").replace(".", ",")
