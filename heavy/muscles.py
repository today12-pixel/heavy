"""Zuordnung Garmin-Übung -> Muskelgruppen (primär 1.0, sekundär 0.5)."""

from __future__ import annotations

MUSCLES = {
    "chest": "Brust",
    "front_delts": "Vordere Schulter",
    "side_delts": "Seitliche Schulter",
    "rear_delts": "Hintere Schulter",
    "biceps": "Bizeps",
    "triceps": "Trizeps",
    "forearms": "Unterarme",
    "abs": "Bauch",
    "obliques": "Seitl. Bauch",
    "traps": "Nacken (Trapez)",
    "upper_back": "Oberer Rücken",
    "lats": "Latissimus",
    "lower_back": "Unterer Rücken",
    "glutes": "Gesäß",
    "quads": "Quadrizeps",
    "hamstrings": "Beinbeuger",
    "adductors": "Adduktoren",
    "calves": "Waden",
}

P, S = 1.0, 0.5

CATEGORY_MAP: dict[str, dict[str, float]] = {
    "BENCH_PRESS": {"chest": P, "triceps": S, "front_delts": S},
    "PUSH_UP": {"chest": P, "triceps": S, "front_delts": S, "abs": S},
    "FLYE": {"chest": P, "front_delts": S},
    "SHOULDER_PRESS": {"front_delts": P, "side_delts": S, "triceps": S},
    "LATERAL_RAISE": {"side_delts": P},
    "SHOULDER_STABILITY": {"rear_delts": P, "upper_back": S},
    "SHRUG": {"traps": P, "forearms": S},
    "ROW": {"upper_back": P, "lats": P, "biceps": S, "rear_delts": S},
    "PULL_UP": {"lats": P, "biceps": S, "upper_back": S},
    "CURL": {"biceps": P, "forearms": S},
    "TRICEPS_EXTENSION": {"triceps": P},
    "SQUAT": {"quads": P, "glutes": P, "adductors": S, "lower_back": S},
    "LUNGE": {"quads": P, "glutes": P, "adductors": S, "hamstrings": S},
    "DEADLIFT": {"hamstrings": P, "glutes": P, "lower_back": P, "traps": S, "forearms": S},
    "LEG_CURL": {"hamstrings": P},
    "HIP_RAISE": {"glutes": P, "hamstrings": S},
    "HIP_STABILITY": {"glutes": P, "adductors": S},
    "HIP_SWING": {"glutes": P, "hamstrings": P, "lower_back": S},
    "HYPEREXTENSION": {"lower_back": P, "glutes": S, "hamstrings": S},
    "CALF_RAISE": {"calves": P},
    "CRUNCH": {"abs": P},
    "SIT_UP": {"abs": P},
    "LEG_RAISE": {"abs": P},
    "PLANK": {"abs": P, "obliques": S},
    "CORE": {"abs": P, "obliques": S},
    "CHOP": {"obliques": P, "abs": S},
    "CARRY": {"forearms": P, "traps": P, "abs": S},
    "OLYMPIC_LIFT": {"quads": P, "glutes": P, "traps": P, "hamstrings": S, "front_delts": S},
    "TOTAL_BODY": {"quads": S, "glutes": S, "chest": S, "upper_back": S},
    "SANDBAG": {"glutes": S, "quads": S, "upper_back": S},
    "SLED": {"quads": P, "glutes": P, "calves": S},
    "TIRE": {"glutes": P, "hamstrings": S, "lower_back": S},
    "SUSPENSION": {"upper_back": S, "chest": S, "abs": S},
    "BATTLE_ROPE": {"front_delts": S, "abs": S},
    "PLYO": {"quads": S, "glutes": S, "calves": S},
}

# Namensschlüsselwörter, die das Kategorie-Mapping überschreiben (erste passende Regel gewinnt).
NAME_RULES: list[tuple[tuple[str, ...], dict[str, float]]] = [
    (("ROMANIAN", "STIFF_LEG", "RDL", "GOOD_MORNING"), {"hamstrings": P, "glutes": P, "lower_back": S}),
    (("LEG_PRESS",), {"quads": P, "glutes": S, "adductors": S}),
    (("CHEST_PRESS", "PEC_DECK", "BUTTERFLY"), {"chest": P, "triceps": S, "front_delts": S}),
    (("HIP_THRUST", "GLUTE_BRIDGE"), {"glutes": P, "hamstrings": S}),
    (("LEG_EXTENSION",), {"quads": P}),
    (("CLOSE_GRIP_BARBELL_BENCH", "CLOSE_GRIP_BENCH"), {"triceps": P, "chest": S, "front_delts": S}),
    (("DIP",), {"triceps": P, "chest": P, "front_delts": S}),
    (("FACE_PULL", "REAR_DELT", "REVERSE_FLY", "REVERSE_FLYE", "REAR_FLY"), {"rear_delts": P, "upper_back": S}),
    (("UPRIGHT_ROW",), {"side_delts": P, "traps": P}),
    (("FRONT_RAISE",), {"front_delts": P}),
    (("HAMMER", "REVERSE_GRIP_CURL", "WRIST"), {"forearms": P, "biceps": S}),
    (("LAT_PULL", "LATPULL", "PULLDOWN", "PULL_DOWN", "PULLOVER"), {"lats": P, "biceps": S}),
    (("CHIN_UP",), {"lats": P, "biceps": P}),
    (("SUMO",), {"glutes": P, "adductors": P, "quads": S, "hamstrings": S, "lower_back": S}),
    (("FRONT_SQUAT",), {"quads": P, "glutes": S, "abs": S}),
    (("ADDUCT",), {"adductors": P}),
    (("ABDUCT", "CLAM"), {"glutes": P}),
    (("CALF",), {"calves": P}),
    (("RUSSIAN_TWIST", "SIDE_PLANK", "OBLIQUE", "WOODCHOP"), {"obliques": P, "abs": S}),
]


def muscles_for(category: str | None, name: str | None) -> dict[str, float]:
    n = (name or "").upper()
    for keys, mapping in NAME_RULES:
        if any(k in n for k in keys):
            return dict(mapping)
    return dict(CATEGORY_MAP.get((category or "").upper(), {}))


_DISPLAY: dict[tuple[str, str], str] | None = None


def display_name(category: str | None, name: str | None) -> str:
    """Lesbarer Name aus dem Garmin-Katalog, sonst aus dem Enum gebildet."""
    global _DISPLAY
    if _DISPLAY is None:
        _DISPLAY = {}
        try:
            from garminconnect.exercises import _RAW  # type: ignore

            for disp, cat, ex in _RAW:
                _DISPLAY[(cat, ex)] = disp
        except Exception:
            pass
    cat = (category or "").upper()
    ex = (name or "").upper()
    if (cat, ex) in _DISPLAY:
        return _DISPLAY[(cat, ex)]
    raw = ex or cat or "Unbekannt"
    return raw.replace("_", " ").strip().title()
