"""Garmin-Connect-Anbindung (über die Bibliothek python-garminconnect)."""

from __future__ import annotations

import getpass
import os
from datetime import date, datetime, timedelta

from .muscles import display_name
from .progression import raw_weight_to_kg


class LoginRequired(RuntimeError):
    pass


def connect(cfg: dict, interactive: bool = False):
    from garminconnect import Garmin

    from . import config as _config

    tokenstore = os.path.expanduser(os.environ.get("HEAVY_TOKENSTORE") or cfg["tokenstore"])
    if not os.path.isabs(tokenstore):  # relativ = im Profilordner
        tokenstore = str(_config.HOME / tokenstore)
    if not interactive:
        try:
            g = Garmin()
            g.login(tokenstore)
            return g
        except Exception as e:  # noqa: BLE001
            prof = f"--profil {_config.PROFILE} " if _config.PROFILE else ""
            raise LoginRequired(
                f"Keine gültige Anmeldung gefunden ({e}). Bitte einmal `heavy.cmd {prof}login` ausführen."
            ) from e

    email = input("Garmin-E-Mail: ").strip()
    password = getpass.getpass("Garmin-Passwort (wird nicht gespeichert): ")
    g = Garmin(email=email, password=password, prompt_mfa=lambda: input("MFA-Code: ").strip())
    os.makedirs(tokenstore, exist_ok=True)
    g.login(tokenstore)
    return g


def _top_exercise(es: dict) -> tuple[str | None, str | None]:
    ex = sorted(es.get("exercises") or [], key=lambda e: -(e.get("probability") or 0))
    if not ex:
        return None, None
    return ex[0].get("category"), ex[0].get("name")


def parse_exercise_sets(payload: dict) -> list[tuple[str | None, str | None, int, float]]:
    out = []
    for es in payload.get("exerciseSets") or []:
        if (es.get("setType") or "").upper() != "ACTIVE":
            continue
        cat, name = _top_exercise(es)
        if not cat:
            continue
        out.append((cat, name, int(es.get("repetitionCount") or 0), raw_weight_to_kg(es.get("weight"))))
    return out


def sync(g, db, cfg: dict, log=print, refresh_days: int = 0) -> int:
    latest = db.latest_start()
    refresh_from = (date.today() - timedelta(days=refresh_days)).isoformat() if refresh_days else None
    if refresh_from and (not latest or refresh_from < latest[:10]):
        start = date.fromisoformat(refresh_from)
    elif latest:
        start = (datetime.fromisoformat(latest[:10]) - timedelta(days=3)).date()
    else:
        start = date.today() - timedelta(days=int(cfg.get("history_days", 365)))
    # strength_training ist bei Garmin ein Untertyp von fitness_equipment
    acts = g.get_activities_by_date(start.isoformat(), date.today().isoformat(), "fitness_equipment")
    acts = [a for a in acts if (a.get("activityType") or {}).get("typeKey") == "strength_training"]
    new = 0
    for a in sorted(acts, key=lambda x: x.get("startTimeLocal") or ""):
        aid = int(a["activityId"])
        refresh = refresh_from and (a.get("startTimeLocal") or "")[:10] >= refresh_from
        if db.has_activity(aid) and not refresh:
            continue
        sets = parse_exercise_sets(g.get_activity_exercise_sets(aid) or {})
        db.save_activity(aid, a.get("startTimeLocal") or "", a.get("activityName") or "Krafttraining",
                         float(a.get("duration") or 0), sets)
        new += 1
        log(f"  + {a.get('startTimeLocal', '')[:16]}  {a.get('activityName')}  ({len(sets)} Sätze)")
    return new


def list_strength_workouts(g) -> list[dict]:
    res = g.get_workouts(0, 200)
    return [w for w in res if ((w.get("sportType") or {}).get("sportTypeKey") == "strength_training")]


__all__ = ["connect", "sync", "list_strength_workouts", "parse_exercise_sets", "display_name", "LoginRequired"]
