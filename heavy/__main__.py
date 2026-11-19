"""Kommandozeile:  python -m heavy <befehl>   (oder heavy.cmd <befehl>)"""

from __future__ import annotations

import argparse
import sys
import webbrowser

from . import config
from .db import DB


def _out(*a):
    print(*a, flush=True)


def cmd_profiles(cfg, args):
    import json

    def info(home):
        c = json.loads((home / "config.json").read_text(encoding="utf-8"))
        m = c.get("managed_workouts") or []
        tok = home / ".garminconnect-heavy" / "garmin_tokens.json"
        return f"{'alle' if m == 'all' else len(m)} Workouts verwaltet" + ("" if tok.exists() or home == config.ROOT else ", NICHT angemeldet")

    _out(f"  (Hauptprofil)  {info(config.ROOT)}   → heavy.cmd <befehl>")
    for n in config.profiles():
        _out(f"  {n:<14} {info(config.ROOT / 'profile' / n)}   → heavy.cmd --profil {n} <befehl>")
    _out("\nNeue Person: heavy.cmd --profil <name> login")


def cmd_login(cfg, args):
    from .garmin import connect

    g = connect(cfg, interactive=True)
    _out(f"Angemeldet als {g.get_full_name() if hasattr(g, 'get_full_name') else 'OK'}. "
         f"Token gespeichert in {cfg['tokenstore']} – Passwort wird nicht gespeichert.")


def _client(cfg):
    from .garmin import connect

    return connect(cfg)


def cmd_sync(cfg, args, g=None):
    from .garmin import sync

    g = g or _client(cfg)
    db = DB(config.path(cfg, "db_path"))
    _out("Synchronisiere Krafttrainings …")
    n = sync(g, db, cfg, log=_out, refresh_days=getattr(args, "refresh", 0) or 0)
    _out(f"{n} Trainings gespeichert/aktualisiert.")
    db.close()
    return g


def cmd_workouts(cfg, args):
    from .garmin import list_strength_workouts
    from .workouts import summarize_workout

    g = _client(cfg)
    managed = cfg.get("managed_workouts") or []
    for w in list_strength_workouts(g):
        wid = int(w["workoutId"])
        mark = "★" if managed == "all" or wid in managed else " "
        _out(f"{mark} {wid:>12}  {w.get('workoutName')}")
        if args.details:
            for r in summarize_workout(g.get_workout_by_id(wid)):
                _out(f"      - {r['exercise']}: {r['reps'] or '?'} Wdh @ {r['kg']:g} kg")
    _out("\n★ = wird von Heavy automatisch angepasst.  `heavy manage <ID>` zum Hinzufügen.")


def cmd_manage(cfg, args):
    if args.all:
        cfg["managed_workouts"] = "all"
    else:
        cur = cfg.get("managed_workouts") or []
        if cur == "all":
            cur = []
        for i in args.ids:
            if i not in cur:
                cur.append(i)
        cfg["managed_workouts"] = cur
    config.save(cfg)
    _out(f"Verwaltet: {cfg['managed_workouts']}")


def cmd_unmanage(cfg, args):
    cur = cfg.get("managed_workouts") or []
    cfg["managed_workouts"] = [] if cur == "all" else [i for i in cur if i not in args.ids]
    config.save(cfg)
    _out(f"Verwaltet: {cfg['managed_workouts']}")


def cmd_progress(cfg, args, g=None):
    from .engine import run_progress

    g = g or _client(cfg)
    db = DB(config.path(cfg, "db_path"))
    n = run_progress(g, db, cfg, dry_run=args.dry_run, log=_out)
    db.close()
    _out(f"\n{n} Übungen angepasst.")
    return g


def cmd_report(cfg, args):
    from .report import write_report

    db = DB(config.path(cfg, "db_path"))
    out = write_report(db, config.path(cfg, "report_path"), cfg["default_rule"].get("warmup_ratio", 0.6),
                       user=config.PROFILE)
    db.close()
    _out(f"Dashboard: {out}")
    if getattr(args, "open", False):
        webbrowser.open(out.as_uri())


def cmd_auto(cfg, args):
    g = cmd_sync(cfg, args)
    cmd_progress(cfg, args, g)
    cmd_report(cfg, args)


def cmd_demo(cfg, args):
    from .demo import run_demo
    from .report import write_report

    _, db = run_demo(config.HOME, log=_out)
    out = write_report(db, config.HOME / "report" / "dashboard_demo.html", demo=True)
    db.close()
    _out(f"Demo-Dashboard: {out}")
    if args.open:
        webbrowser.open(out.as_uri())


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="heavy", description="Auto-Progression & Dashboard für Garmin-Krafttraining")
    p.add_argument("-p", "--profil", metavar="NAME",
                   help="weitere Person (eigene Config, Daten und Garmin-Anmeldung in profile/NAME)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("profile", help="Alle Profile auflisten")
    sub.add_parser("login", help="Einmalig bei Garmin Connect anmelden (Token wird gespeichert)")
    s = sub.add_parser("sync", help="Neue Krafttrainings + Sätze von Garmin laden")
    s.add_argument("--refresh", type=int, default=0, metavar="TAGE",
                   help="Trainings der letzten TAGE neu laden (nach Korrekturen in Connect)")
    s = sub.add_parser("workouts", help="Krafttraining-Workouts in Garmin Connect auflisten")
    s.add_argument("-d", "--details", action="store_true", help="Übungen und Gewichte anzeigen")
    s = sub.add_parser("manage", help="Workout(s) für Auto-Progression aktivieren")
    s.add_argument("ids", nargs="*", type=int)
    s.add_argument("--all", action="store_true", help="alle Krafttraining-Workouts verwalten")
    s = sub.add_parser("unmanage", help="Workout(s) nicht mehr anpassen")
    s.add_argument("ids", nargs="+", type=int)
    s = sub.add_parser("progress", help="Zielgewichte berechnen und in Garmin-Workouts schreiben")
    s.add_argument("-n", "--dry-run", action="store_true", help="nur anzeigen, nichts senden")
    s = sub.add_parser("report", help="Dashboard erzeugen")
    s.add_argument("-o", "--open", action="store_true", help="im Browser öffnen")
    s = sub.add_parser("auto", help="sync + progress + report (für den Zeitplan)")
    s.add_argument("-n", "--dry-run", action="store_true")
    s.add_argument("-o", "--open", action="store_true")
    s = sub.add_parser("demo", help="Demo mit simulierten Daten (ohne Garmin-Konto)")
    s.add_argument("-o", "--open", action="store_true")
    args = p.parse_args(argv)

    if args.profil:
        config.use_profile(args.profil)
    cfg = config.load()
    handlers = {"profile": cmd_profiles, "login": cmd_login, "sync": cmd_sync, "workouts": cmd_workouts, "manage": cmd_manage,
                "unmanage": cmd_unmanage, "progress": cmd_progress, "report": cmd_report,
                "auto": cmd_auto, "demo": cmd_demo}
    try:
        handlers[args.cmd](cfg, args)
    except Exception as e:  # noqa: BLE001
        from .garmin import LoginRequired

        if isinstance(e, LoginRequired):
            _out(str(e))
            return 2
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
