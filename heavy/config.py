"""Konfiguration (config.json im Projektordner)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .progression import Rule

ROOT = Path(__file__).resolve().parent.parent  # Projektordner = Hauptprofil
HOME = Path(os.environ.get("HEAVY_HOME", ROOT))
CONFIG_PATH = HOME / "config.json"
PROFILE = os.environ.get("HEAVY_PROFILE", "")
RESERVED = {"data", "report", "profile", "heavy", "tests", "dist", "synology"}


def use_profile(name: str) -> None:
    """Weitere Person: eigener Ordner profile/<name> mit eigener Config, DB und eigenem Token."""
    global HOME, CONFIG_PATH, PROFILE
    import re

    name = name.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,30}", name) or name in RESERVED:
        raise SystemExit(f"Ungültiger Profilname '{name}' (erlaubt: a-z, 0-9, - und _).")
    HOME = ROOT / "profile" / name
    CONFIG_PATH = HOME / "config.json"
    PROFILE = name
    if not CONFIG_PATH.exists():
        HOME.mkdir(parents=True, exist_ok=True)
        base = json.loads((ROOT / "config.json").read_text(encoding="utf-8")) if (ROOT / "config.json").exists() \
            else json.loads(json.dumps(DEFAULT_CONFIG))
        base["managed_workouts"] = []  # Workouts der anderen Person wählt sie selbst
        base["tokenstore"] = ".garminconnect-heavy"  # Token liegt im Profilordner
        save(base)
        print(f"Neues Profil '{name}' angelegt (Regeln vom Hauptprofil übernommen): {HOME}")


def profiles() -> list[str]:
    d = ROOT / "profile"
    return sorted(p.name for p in d.iterdir() if (p / "config.json").exists()) if d.exists() else []

DEFAULT_CONFIG: dict = {
    "_hilfe": "Siehe README.md. Modi: double = Doppel-Progression, carry = nur letztes Gewicht übernehmen, off = nicht anfassen.",
    "managed_workouts": [],
    "hauptprofil": "haupt",
    "push_to_device": True,
    "history_days": 365,
    "tokenstore": "~/.garminconnect-heavy",
    "db_path": "data/heavy.db",
    "report_path": "report/dashboard.html",
    "default_rule": {
        "mode": "double",
        "increment": 2.5,
        "round_to": 0.5,
        "deload_after": 3,
        "deload_pct": 0.10,
        "warmup_ratio": 0.6,
        "rep_range": [8, 12],
        "allow_decrease": False,
    },
    "name_rules": [
        {"_info": "Smith-Maschine", "match": ["SMITH"], "increment": 2.5},
        {"_info": "Kurzhanteln", "match": ["DUMBBELL"], "increment": 1.0},
        {"_info": "Maschinen & Kabel", "match": ["CABLE", "MACHINE", "LEG_PRESS", "CHEST_PRESS", "LEG_CURL",
                                                  "LEG_EXTENSION", "PULLDOWN", "PULL_DOWN", "WEIGHTED_PULL_UP",
                                                  "SEATED", "KICKBACK", "PRESSDOWN", "PEC_DECK", "WEIGHTED_CRUNCH"],
         "increment": 5.0},
    ],
    "category_rules": {
        "CURL": {"increment": 1.0},
        "LATERAL_RAISE": {"increment": 1.0},
        "TRICEPS_EXTENSION": {"increment": 1.0},
        "FLYE": {"increment": 1.0},
        "SHRUG": {"increment": 2.0},
        "LEG_CURL": {"increment": 2.5},
        "SQUAT": {"increment": 2.5},
        "DEADLIFT": {"increment": 5.0},
    },
    "exercise_rules": {
        "_beispiel BENCH_PRESS/BARBELL_BENCH_PRESS": {"rep_range": [6, 10], "increment": 2.5}
    },
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        save(DEFAULT_CONFIG)
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


def save(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def path(cfg: dict, key: str) -> Path:
    p = Path(os.path.expanduser(cfg[key]))
    return p if p.is_absolute() else HOME / p


def name_rule(cfg: dict, key: str) -> dict | None:
    """Erste passende Regel aus `name_rules` (Stichwort im Übungsnamen, z. B. DUMBBELL)."""
    name = key.split("/", 1)[1] if "/" in key else key
    for r in cfg.get("name_rules") or []:
        if any(m.upper() in name for m in r.get("match", [])):
            return {k: v for k, v in r.items() if k not in ("match", "_info")}
    return None


def rule_factory(cfg: dict):
    def rule_for(key: str, category: str) -> Rule:
        return Rule.merged(
            cfg.get("default_rule"),
            (cfg.get("category_rules") or {}).get(category),
            name_rule(cfg, key),
            (cfg.get("exercise_rules") or {}).get(key),
        )

    return rule_for
