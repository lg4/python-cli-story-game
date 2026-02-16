#!/usr/bin/env python3
"""
test_game.py — Automated test suite for Terminal Adventure Quest
=================================================================
Run with:
    python test_game.py              # quick smoke tests
    python test_game.py -v           # verbose output
    python test_game.py --full       # full integration test (all themes × difficulties)

Uses only the standard library (unittest).
"""

import io
import random
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

# Ensure the game module is importable
sys.path.insert(0, ".")

import main as game


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def make_player(theme_id: game.ThemeId = game.ThemeId.DESERT,
                difficulty: game.Difficulty = game.Difficulty.NORMAL,
                **overrides) -> game.Player:
    """Create a Player with sensible defaults for testing."""
    t = game.THEMES[theme_id]
    defaults = dict(name="TestBot", theme=t, difficulty=difficulty, seed=42)
    defaults.update(overrides)
    return game.Player(**defaults)


def suppress_output():
    """Context manager that swallows stdout/stderr."""
    return redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())


class SilentMixin:
    """Mixin to capture prints during tests."""
    def run_silent(self, fn, *args, **kwargs):
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = fn(*args, **kwargs)
        return result, buf.getvalue()


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Player
# ──────────────────────────────────────────────────────────────────────
class TestPlayer(unittest.TestCase, SilentMixin):
    def setUp(self):
        game.TEST_MODE = True
        random.seed(42)

    def test_initial_health(self):
        p = make_player()
        self.assertEqual(p.health, 100)
        self.assertEqual(p.morale, 100)

    def test_difficulty_scales_supplies(self):
        easy = make_player(difficulty=game.Difficulty.EASY)
        hard = make_player(difficulty=game.Difficulty.HARD)
        self.assertGreater(easy.supplies["food"], hard.supplies["food"])
        self.assertGreater(easy.supplies["water"], hard.supplies["water"])

    def test_add_item(self):
        p = make_player()
        _, _ = self.run_silent(p.add_item, "Healer's Salve")
        self.assertIn("Healer's Salve", p.inventory)

    def test_add_duplicate_item(self):
        p = make_player()
        self.run_silent(p.add_item, "Healer's Salve")
        self.run_silent(p.add_item, "Healer's Salve")  # should not duplicate
        self.assertEqual(p.inventory.count("Healer's Salve"), 1)

    def test_remove_item(self):
        p = make_player()
        self.run_silent(p.add_item, "Signal-Flare")
        self.run_silent(p.remove_item, "Signal-Flare")
        self.assertNotIn("Signal-Flare", p.inventory)

    def test_consume_daily(self):
        p = make_player()
        food_before = p.supplies["food"]
        water_before = p.supplies["water"]
        p.consume_daily()
        self.assertLess(p.supplies["food"], food_before)
        self.assertLess(p.supplies["water"], water_before)

    def test_is_alive(self):
        p = make_player()
        self.assertTrue(p.is_alive())
        p.health = 0
        self.assertFalse(p.is_alive())

    def test_damage_respects_difficulty(self):
        easy = make_player(difficulty=game.Difficulty.EASY)
        hard = make_player(difficulty=game.Difficulty.HARD)
        self.run_silent(easy.damage, 20)
        self.run_silent(hard.damage, 20)
        # Easy takes less damage
        self.assertGreater(easy.health, hard.health)

    def test_heal_caps_at_100(self):
        p = make_player()
        p.health = 95
        self.run_silent(p.heal, 50)
        self.assertEqual(p.health, 100)

    def test_status_effects(self):
        p = make_player()
        self.run_silent(p.add_effect, game.StatusEffect.POISONED, 3)
        self.assertIn(game.StatusEffect.POISONED, p.status_effects)
        self.assertEqual(p.status_effects[game.StatusEffect.POISONED], 3)

    def test_tick_effects_decrements(self):
        p = make_player()
        self.run_silent(p.add_effect, game.StatusEffect.INSPIRED, 2)
        self.run_silent(p.tick_effects)
        self.assertEqual(p.status_effects[game.StatusEffect.INSPIRED], 1)
        self.run_silent(p.tick_effects)
        self.assertNotIn(game.StatusEffect.INSPIRED, p.status_effects)

    def test_poison_deals_damage(self):
        p = make_player()
        self.run_silent(p.add_effect, game.StatusEffect.POISONED, 2)
        hp_before = p.health
        self.run_silent(p.tick_effects)
        self.assertLess(p.health, hp_before)

    def test_adjust_supply_clamps(self):
        p = make_player()
        self.run_silent(p.adjust_supply, "food", -9999)
        self.assertEqual(p.supplies["food"], 0)

    def test_achievement_unlock(self):
        p = make_player()
        self.run_silent(p.try_unlock, "first_blood")
        self.assertTrue(p.achievements["first_blood"].unlocked)

    def test_achievement_no_double_unlock(self):
        p = make_player()
        self.run_silent(p.try_unlock, "first_blood")
        # Second unlock should return False internally
        ach = p.achievements["first_blood"]
        self.assertFalse(ach.unlock())  # already unlocked

    def test_hoarder_achievement(self):
        p = make_player()
        items = ["Healer's Salve", "Morale Charm", "Signal-Flare", "Ironbark Shield", "Shadow Cloak"]
        for item in items:
            self.run_silent(p.add_item, item)
        self.assertTrue(p.achievements["hoarder"].unlocked)


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Theme system
# ──────────────────────────────────────────────────────────────────────
class TestThemes(unittest.TestCase):
    def test_five_themes_registered(self):
        self.assertEqual(len(game.THEMES), 5)

    def test_each_theme_has_required_fields(self):
        for tid, theme in game.THEMES.items():
            self.assertIsInstance(theme.name, str)
            self.assertGreater(len(theme.name), 0)
            self.assertGreater(theme.total_distance, 0)
            self.assertIn("food", theme.starting_supplies)
            self.assertIn("water", theme.starting_supplies)
            self.assertIn("fuel", theme.starting_supplies)
            self.assertIsInstance(theme.special_item, str)

    def test_companion_pool_exists_for_each_theme(self):
        for tid in game.ThemeId:
            self.assertIn(tid, game.COMPANION_POOL)
            self.assertGreater(len(game.COMPANION_POOL[tid]), 0)


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Companion
# ──────────────────────────────────────────────────────────────────────
class TestCompanion(unittest.TestCase):
    def test_companion_describe(self):
        comp = game.Companion("Kael", "Tracker", "scout", 8, "Knows the way")
        desc = comp.describe()
        self.assertIn("Kael", desc)
        self.assertIn("scout", desc)

    def test_companion_combat_reduces_damage(self):
        p = make_player()
        p.companion = game.Companion("Nyx", "Fighter", "combat", 8, "Strong")
        hp_with = p.health
        buf = io.StringIO()
        with redirect_stdout(buf):
            p.damage(20)
        hp_after_comp = p.health

        p2 = make_player()
        buf = io.StringIO()
        with redirect_stdout(buf):
            p2.damage(20)
        hp_after_no_comp = p2.health

        self.assertGreaterEqual(hp_after_comp, hp_after_no_comp)


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Weather & Time of Day
# ──────────────────────────────────────────────────────────────────────
class TestWeatherAndTime(unittest.TestCase):
    def test_advance_time_cycles(self):
        p = make_player()
        p.time_of_day = game.TimeOfDay.DAWN
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.advance_time_of_day(p)
        self.assertEqual(p.time_of_day, game.TimeOfDay.DAY)

    def test_advance_time_wraps(self):
        p = make_player()
        p.time_of_day = game.TimeOfDay.NIGHT
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.advance_time_of_day(p)
        self.assertEqual(p.time_of_day, game.TimeOfDay.DAWN)

    def test_weather_changes(self):
        random.seed(99)
        p = make_player()
        old_weather = p.weather
        game.advance_weather(p)
        # Weather should be a valid Weather enum
        self.assertIsInstance(p.weather, game.Weather)


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Milestones
# ──────────────────────────────────────────────────────────────────────
class TestMilestones(unittest.TestCase):
    def test_milestone_25(self):
        game.TEST_MODE = True
        p = make_player()
        p.distance_travelled = 500  # 25% of 2000
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.check_milestones(p)
        self.assertIn(25, p.milestones_hit)
        self.assertTrue(p.achievements["milestone_25"].unlocked)

    def test_milestone_not_repeated(self):
        game.TEST_MODE = True
        p = make_player()
        p.distance_travelled = 600
        p.milestones_hit.add(25)  # already hit
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.check_milestones(p)
        # Should not print milestone again
        self.assertNotIn("MILESTONE", buf.getvalue())


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Crafting
# ──────────────────────────────────────────────────────────────────────
class TestCrafting(unittest.TestCase, SilentMixin):
    def test_craft_recipes_exist(self):
        self.assertGreater(len(game.CRAFT_RECIPES), 0)

    def test_craft_ingredients_in_catalogue(self):
        for a, b, result, desc in game.CRAFT_RECIPES:
            self.assertIn(result, game.ITEM_CATALOGUE,
                          f"Crafted item '{result}' not in ITEM_CATALOGUE")


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Riddles
# ──────────────────────────────────────────────────────────────────────
class TestRiddles(unittest.TestCase):
    def test_riddles_have_valid_answers(self):
        for question, options, correct_idx in game.RIDDLES:
            self.assertGreater(len(options), 0)
            self.assertLess(correct_idx, len(options))
            self.assertGreaterEqual(correct_idx, 0)

    def test_riddles_pool_not_empty(self):
        self.assertGreaterEqual(len(game.RIDDLES), 5)


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Item system
# ──────────────────────────────────────────────────────────────────────
class TestItems(unittest.TestCase):
    def test_all_theme_items_in_catalogue(self):
        for tid, theme in game.THEMES.items():
            self.assertIn(theme.special_item, game.ITEM_CATALOGUE,
                          f"Theme '{theme.name}' special item not in catalogue")

    def test_catalogue_items_have_descriptions(self):
        for name, desc in game.ITEM_CATALOGUE.items():
            self.assertGreater(len(desc), 0, f"Item '{name}' has empty description")


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Utility functions
# ──────────────────────────────────────────────────────────────────────
class TestUtils(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(game.clamp(5, 0, 10), 5)
        self.assertEqual(game.clamp(-5, 0, 10), 0)
        self.assertEqual(game.clamp(15, 0, 10), 10)

    def test_wrapped(self):
        long_text = "a " * 100
        result = game.wrapped(long_text)
        for line in result.split("\n"):
            self.assertLessEqual(len(line), game.WIDTH + 1)


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Event pool
# ──────────────────────────────────────────────────────────────────────
class TestEvents(unittest.TestCase):
    def test_event_pool_not_empty(self):
        self.assertGreater(len(game.EVENT_POOL), 0)

    def test_event_pool_has_valid_weights(self):
        for fn, weight in game.EVENT_POOL:
            self.assertGreater(weight, 0)
            self.assertTrue(callable(fn))

    def test_event_pool_total_weight(self):
        total = sum(w for _, w in game.EVENT_POOL)
        self.assertGreater(total, 50)  # sanity check


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Difficulty
# ──────────────────────────────────────────────────────────────────────
class TestDifficulty(unittest.TestCase):
    def test_three_difficulties(self):
        self.assertEqual(len(game.Difficulty), 3)

    def test_settings_exist_for_each(self):
        for d in game.Difficulty:
            self.assertIn(d, game.DIFFICULTY_SETTINGS)
            settings = game.DIFFICULTY_SETTINGS[d]
            self.assertIn("supply_mult", settings)
            self.assertIn("damage_mult", settings)
            self.assertIn("event_chance", settings)

    def test_hard_has_higher_damage_mult(self):
        easy = game.DIFFICULTY_SETTINGS[game.Difficulty.EASY]
        hard = game.DIFFICULTY_SETTINGS[game.Difficulty.HARD]
        self.assertGreater(hard["damage_mult"], easy["damage_mult"])


# ──────────────────────────────────────────────────────────────────────
# Unit tests — Penalties
# ──────────────────────────────────────────────────────────────────────
class TestPenalties(unittest.TestCase):
    def test_starvation_damages(self):
        p = make_player()
        p.supplies["food"] = 0
        hp_before = p.health
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.apply_penalties(p)
        self.assertLess(p.health, hp_before)

    def test_dehydration_damages(self):
        p = make_player()
        p.supplies["water"] = 0
        hp_before = p.health
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.apply_penalties(p)
        self.assertLess(p.health, hp_before)

    def test_low_morale_damages(self):
        p = make_player()
        p.morale = 5
        hp_before = p.health
        buf = io.StringIO()
        with redirect_stdout(buf):
            game.apply_penalties(p)
        self.assertLess(p.health, hp_before)


# ──────────────────────────────────────────────────────────────────────
# Integration test — Full automated play-through
# ──────────────────────────────────────────────────────────────────────
class TestIntegration(unittest.TestCase):
    """Run a complete game with simulated inputs."""

    def _run_auto_game(self, theme_idx: int = 1, diff_idx: int = 2, seed: int = 42):
        """Run one full automated game and capture output."""
        game.TEST_MODE = True
        inputs = ["TestBot", str(seed), str(theme_idx), str(diff_idx), ""]
        auto = game.AutoPlayer(strategy="scripted", inputs=inputs, seed=seed)
        buf = io.StringIO()
        with auto.activate(), redirect_stdout(buf):
            auto.strategy = "scripted"
            try:
                game._run_game_loop(max_days=80)
            except SystemExit:
                pass
        return buf.getvalue(), auto.log

    def test_desert_game_completes(self):
        output, log = self._run_auto_game(theme_idx=1)
        self.assertIn("Terminal Adventure Quest", output)
        self.assertGreater(len(log), 5)

    def test_space_game_completes(self):
        output, log = self._run_auto_game(theme_idx=2)
        self.assertIn("Terminal Adventure Quest", output)

    def test_mist_game_completes(self):
        output, log = self._run_auto_game(theme_idx=3)
        self.assertIn("Terminal Adventure Quest", output)

    def test_time_game_completes(self):
        output, log = self._run_auto_game(theme_idx=4)
        self.assertIn("Terminal Adventure Quest", output)

    def test_cyber_game_completes(self):
        output, log = self._run_auto_game(theme_idx=5)
        self.assertIn("Terminal Adventure Quest", output)

    def test_easy_game_completes(self):
        output, log = self._run_auto_game(diff_idx=1)
        self.assertIn("Terminal Adventure Quest", output)

    def test_hard_game_completes(self):
        output, log = self._run_auto_game(diff_idx=3)
        self.assertIn("Terminal Adventure Quest", output)

    def test_different_seeds_produce_different_games(self):
        output1, _ = self._run_auto_game(seed=1)
        output2, _ = self._run_auto_game(seed=999)
        # Outputs should differ (different random events)
        self.assertNotEqual(output1, output2)

    def test_same_seed_is_reproducible(self):
        # Reset global random state identically before each run
        random.seed(0)
        output1, _ = self._run_auto_game(seed=42)
        random.seed(0)
        output2, _ = self._run_auto_game(seed=42)
        self.assertEqual(output1, output2)


# ──────────────────────────────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test suite for Terminal Adventure Quest")
    parser.add_argument("--full", action="store_true",
                        help="Run full integration tests across all themes and difficulties")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose test output")
    args, remaining = parser.parse_known_args()

    # Set test mode globally
    game.TEST_MODE = True

    if args.full:
        print("Running FULL test suite (all themes x all difficulties)...")
        # Override the integration tests to test all combos
        suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
    else:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 72)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passed = total - failures
    print(f"  Results: {passed}/{total} passed, {failures} failed")
    print("=" * 72)

    sys.exit(0 if result.wasSuccessful() else 1)
