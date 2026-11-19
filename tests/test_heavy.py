import tempfile
import unittest
from pathlib import Path

from heavy.db import DB
from heavy.demo import FakeGarmin, build_strength_workout
from heavy.engine import run_progress
from heavy.garmin import parse_exercise_sets
from heavy.muscles import muscles_for
from heavy.progression import Rule, Session, Set, decide, raw_weight_to_kg, summarize
from heavy.workouts import exercises_in, plan_changes

BENCH = ("BENCH_PRESS", "BARBELL_BENCH_PRESS")


def sess(aid, day, sets):
    return Session(aid, f"2026-11-{day:02d} 18:00:00", [Set(r, kg) for r, kg in sets])


class ProgressionTest(unittest.TestCase):
    def test_weight_units(self):
        self.assertEqual(raw_weight_to_kg(60000.0), 60.0)
        self.assertEqual(raw_weight_to_kg(62.5), 62.5)
        self.assertEqual(raw_weight_to_kg(None), 0.0)

    def test_carry_over_spontaneous_increase(self):
        # Plan sagte 70 kg, auf der Uhr auf 75 erhöht, Ziel nicht ganz geschafft -> 75 übernehmen
        h = [sess(1, 1, [(8, 40), (8, 75), (7, 75), (6, 75)])]
        d = decide(Rule(), 8, h)
        self.assertEqual(d.new_kg, 75.0)
        self.assertEqual(d.base_kg, 75.0)

    def test_increase_when_all_sets_hit_target(self):
        d = decide(Rule(increment=2.5), 8, [sess(1, 1, [(8, 80), (9, 80), (8, 80)])])
        self.assertEqual(d.new_kg, 82.5)

    def test_warmups_ignored(self):
        d = decide(Rule(), 8, [sess(1, 1, [(5, 40), (8, 80), (8, 80)])])
        self.assertEqual(d.new_kg, 82.5)

    def test_deload_after_three_misses(self):
        h = [sess(i, i, [(6, 100), (5, 100)]) for i in range(1, 4)]
        d = decide(Rule(deload_after=3, deload_pct=0.1), 8, h)
        self.assertEqual(d.new_kg, 90.0)
        d2 = decide(Rule(deload_after=3), 8, h[:2])
        self.assertEqual(d2.new_kg, 100.0)

    def test_deload_snaps_to_plate_grid(self):
        h = [sess(i, i, [(3, 97.5)]) for i in range(1, 4)]
        self.assertEqual(decide(Rule(increment=2.5, round_to=0.5), 6, h).new_kg, 87.5)

    def test_double_progression_rep_range(self):
        r = Rule(rep_range=(8, 12))
        d = decide(r, 10, [sess(1, 1, [(10, 50), (9, 50)])])
        self.assertEqual((d.new_kg, d.new_reps), (50.0, 10))
        d = decide(r, 12, [sess(1, 1, [(12, 50), (12, 50)])])
        self.assertEqual((d.new_kg, d.new_reps), (52.5, 8))

    def test_carry_mode_and_bodyweight(self):
        self.assertEqual(decide(Rule(mode="carry"), 8, [sess(1, 1, [(12, 60)])]).new_kg, 60.0)
        self.assertIsNone(decide(Rule(), 10, [sess(1, 1, [(10, 0), (10, 0)])]))
        self.assertIsNone(decide(Rule(mode="off"), 8, [sess(1, 1, [(8, 60)])]))

    def test_summary(self):
        s = summarize([Set(10, 100), Set(5, 40)])
        self.assertEqual(s["sets"], 1)
        self.assertAlmostEqual(s["e1rm"], 133.33, places=2)


class WorkoutPatchTest(unittest.TestCase):
    def setUp(self):
        self.wk = build_strength_workout(1, "Push", [(*BENCH, 4, 8, 70.0), ("CURL", "BARBELL_BICEPS_CURL", 3, 10, 25.0)])

    def test_patch_in_grams_and_original_untouched(self):
        hist = {"BENCH_PRESS/BARBELL_BENCH_PRESS": [sess(5, 2, [(8, 72.5)] * 4)]}
        new, ch = plan_changes(self.wk, hist, lambda k, c: Rule(), lambda k, a: False)
        step = exercises_in(new)["BENCH_PRESS/BARBELL_BENCH_PRESS"][0]
        self.assertEqual(step["weightValue"], 75000.0)
        self.assertEqual(exercises_in(self.wk)["BENCH_PRESS/BARBELL_BENCH_PRESS"][0]["weightValue"], 70000.0)
        self.assertEqual(len(ch), 1)
        self.assertEqual((ch[0].old_kg, ch[0].new_kg), (70.0, 75.0))
        # Curl ohne Daten bleibt unverändert
        self.assertEqual(exercises_in(new)["CURL/BARBELL_BICEPS_CURL"][0]["weightValue"], 25000.0)

    def test_already_applied_is_skipped(self):
        hist = {"BENCH_PRESS/BARBELL_BENCH_PRESS": [sess(5, 2, [(8, 72.5)] * 4)]}
        _, ch = plan_changes(self.wk, hist, lambda k, c: Rule(), lambda k, a: True)
        self.assertEqual(ch, [])

    def test_kg_scale_workout_and_pyramid(self):
        wk = build_strength_workout(2, "Pyr", [(*BENCH, 1, 8, 0.0)])
        grp = wk["workoutSegments"][0]["workoutSteps"][0]
        a = grp["workoutSteps"][0]
        a["weightValue"] = 60.0  # kg-Skala
        b = dict(a, weightValue=70.0)
        grp["workoutSteps"].insert(1, b)
        hist = {"BENCH_PRESS/BARBELL_BENCH_PRESS": [sess(5, 2, [(8, 60), (8, 70)])]}
        new, ch = plan_changes(wk, hist, lambda k, c: Rule(), lambda k, a: False)
        vals = [s["weightValue"] for s in exercises_in(new)["BENCH_PRESS/BARBELL_BENCH_PRESS"]]
        self.assertEqual(vals, [62.5, 72.5])

    def test_never_decrease_but_deload_allowed(self):
        key = "BENCH_PRESS/BARBELL_BENCH_PRESS"
        lighter = {key: [sess(5, 2, [(7, 60)] * 4)]}
        _, ch = plan_changes(self.wk, lighter, lambda k, c: Rule(), lambda k, a: False)
        self.assertEqual(ch[0].new_kg, 70.0)
        self.assertFalse(ch[0].changed)
        _, ch = plan_changes(self.wk, lighter, lambda k, c: Rule(allow_decrease=True), lambda k, a: False)
        self.assertEqual(ch[0].new_kg, 60.0)
        fails = {key: [sess(i, i, [(5, 70)] * 3) for i in range(1, 4)]}
        _, ch = plan_changes(self.wk, fails, lambda k, c: Rule(increment=2.5), lambda k, a: False)
        self.assertEqual(ch[0].new_kg, 62.5)

    def test_name_rules_priority(self):
        from heavy.config import rule_factory

        cfg = {"default_rule": {"increment": 2.5, "rep_range": [8, 12]},
               "category_rules": {"CURL": {"increment": 1.0}},
               "name_rules": [{"match": ["SMITH"], "increment": 2.5}, {"match": ["DUMBBELL"], "increment": 1.0},
                              {"match": ["CABLE", "LEG_PRESS"], "increment": 5.0}],
               "exercise_rules": {"SQUAT/LEG_PRESS": {"increment": 10.0}}}
        rf = rule_factory(cfg)
        self.assertEqual(rf("BENCH_PRESS/INCLINE_SMITH_MACHINE_BENCH_PRESS", "BENCH_PRESS").increment, 2.5)
        self.assertEqual(rf("SHOULDER_PRESS/DUMBBELL_SHOULDER_PRESS", "SHOULDER_PRESS").increment, 1.0)
        self.assertEqual(rf("ROW/SEATED_CABLE_ROW", "ROW").increment, 5.0)
        self.assertEqual(rf("SQUAT/LEG_PRESS", "SQUAT").increment, 10.0)
        self.assertEqual(rf("ROW/SEATED_CABLE_ROW", "ROW").rep_range, (8, 12))

    def test_category_only_match(self):
        hist = {"BENCH_PRESS/": [sess(5, 2, [(8, 80)] * 3)]}
        _, ch = plan_changes(self.wk, hist, lambda k, c: Rule(), lambda k, a: False)
        self.assertEqual(ch[0].new_kg, 82.5)


class ParserTest(unittest.TestCase):
    def test_parse_exercise_sets(self):
        payload = {"exerciseSets": [
            {"setType": "ACTIVE", "repetitionCount": 8, "weight": 80000.0,
             "exercises": [{"category": "SQUAT", "name": None, "probability": 20.0},
                           {"category": "BENCH_PRESS", "name": "BARBELL_BENCH_PRESS", "probability": 80.0}]},
            {"setType": "REST", "duration": 90},
            {"setType": "ACTIVE", "repetitionCount": 12, "weight": None,
             "exercises": [{"category": "PUSH_UP", "name": "PUSH_UP", "probability": 100}]},
        ]}
        self.assertEqual(parse_exercise_sets(payload),
                         [("BENCH_PRESS", "BARBELL_BENCH_PRESS", 8, 80.0), ("PUSH_UP", "PUSH_UP", 12, 0.0)])

    def test_muscles(self):
        self.assertIn("hamstrings", muscles_for("DEADLIFT", "ROMANIAN_DEADLIFT"))
        self.assertEqual(muscles_for("BENCH_PRESS", "BARBELL_BENCH_PRESS")["chest"], 1.0)


class SyncTest(unittest.TestCase):
    def test_sync_stores_and_skips_known(self):
        from heavy.garmin import sync

        class G:
            calls = 0

            def get_activities_by_date(self, s, e, t):
                assert t == "fitness_equipment"
                return [{"activityId": 11, "startTimeLocal": "2026-11-10 18:00:00", "activityName": "Push", "duration": 3000,
                         "activityType": {"typeKey": "strength_training"}},
                        {"activityId": 12, "startTimeLocal": "2026-11-11 18:00:00", "activityName": "Rudern",
                         "activityType": {"typeKey": "indoor_rowing"}}]

            def get_activity_exercise_sets(self, aid):
                G.calls += 1
                return {"exerciseSets": [{"setType": "ACTIVE", "repetitionCount": 8, "weight": 70000.0,
                                          "exercises": [{"category": "BENCH_PRESS", "name": "BARBELL_BENCH_PRESS", "probability": 99}]}]}

        with tempfile.TemporaryDirectory() as tmp:
            db = DB(Path(tmp) / "s.db")
            cfg = {"history_days": 30}
            self.assertEqual(sync(G(), db, cfg, log=lambda *a: None), 1)
            self.assertEqual(sync(G(), db, cfg, log=lambda *a: None), 0)
            self.assertEqual(G.calls, 1)
            h = db.history()["BENCH_PRESS/BARBELL_BENCH_PRESS"]
            self.assertEqual(h[0].sets, [Set(8, 70.0)])
            db.close()


class ProfileTest(unittest.TestCase):
    def test_invalid_profile_names(self):
        from heavy import config

        for bad in ("data", "report", "../x", "a b", ""):
            with self.assertRaises(SystemExit):
                config.use_profile(bad)


class EngineTest(unittest.TestCase):
    def test_end_to_end_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DB(Path(tmp) / "t.db")
            g = FakeGarmin([build_strength_workout(7, "Push", [(*BENCH, 3, 8, 70.0)])])
            cfg = {"managed_workouts": [7], "push_to_device": True, "default_rule": {}}
            db.save_activity(1, "2026-11-10 18:00:00", "Push", 3600,
                             [("BENCH_PRESS", "BARBELL_BENCH_PRESS", 8, 72.5)] * 3)
            quiet = lambda *a: None  # noqa: E731
            self.assertEqual(run_progress(g, db, cfg, log=quiet), 1)
            self.assertEqual(g.updates, [7])
            self.assertEqual(g.pushes, [7])
            step = exercises_in(g.workouts[7])["BENCH_PRESS/BARBELL_BENCH_PRESS"][0]
            self.assertEqual(step["weightValue"], 75000.0)
            # zweiter Lauf ohne neues Training -> nichts passiert
            self.assertEqual(run_progress(g, db, cfg, log=quiet), 0)
            self.assertEqual(g.updates, [7])
            # Dry-Run sendet nichts
            db.save_activity(2, "2026-11-12 18:00:00", "Push", 3600,
                             [("BENCH_PRESS", "BARBELL_BENCH_PRESS", 8, 75.0)] * 3)
            run_progress(g, db, cfg, dry_run=True, log=quiet)
            self.assertEqual(g.updates, [7])
            db.close()


if __name__ == "__main__":
    unittest.main()
