"""Wendet die Progression auf die verwalteten Garmin-Workouts an."""

from __future__ import annotations

from .config import rule_factory
from .workouts import plan_changes


def managed_ids(g, cfg: dict) -> list[int]:
    m = cfg.get("managed_workouts") or []
    if m == "all":
        from .garmin import list_strength_workouts

        return [int(w["workoutId"]) for w in list_strength_workouts(g)]
    return [int(x) for x in m]


def run_progress(g, db, cfg: dict, dry_run: bool = False, log=print, ts: str | None = None) -> int:
    ids = managed_ids(g, cfg)
    if not ids:
        log("Keine Workouts verwaltet. Mit `heavy workouts` auflisten und `heavy manage <ID>` hinzufügen.")
        return 0
    history = db.history()
    rule_for = rule_factory(cfg)
    total = 0
    for wid in ids:
        wk = g.get_workout_by_id(wid)
        name = wk.get("workoutName", str(wid))
        new_wk, changes = plan_changes(wk, history, rule_for, lambda k, a: db.applied(wid, k, a))
        real = [c for c in changes if c.changed]
        log(f"\n[{name}] ({wid})")
        if not changes:
            log("  keine neuen Trainingsdaten für dieses Workout")
            continue
        for c in changes:
            log(("  ✎ " if c.changed else "  = ") + c.describe())
        if real and not dry_run:
            g.update_workout(wid, new_wk)
            if cfg.get("push_to_device", True) and hasattr(g, "push_workout_to_device"):
                try:
                    g.push_workout_to_device(wid)
                    log("  → an die Uhr gesendet (kommt mit dem nächsten Sync)")
                except Exception as e:  # noqa: BLE001
                    log(f"  ! Push an Uhr fehlgeschlagen ({e}) – Workout ist trotzdem in Connect aktualisiert")
        for c in changes:
            db.log_change(wid, name, c, dry_run, ts)
        total += len(real)
    if dry_run:
        log("\n(Testlauf – nichts an Garmin gesendet)")
    return total
