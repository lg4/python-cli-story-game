"""
Automatic Game Balancer - Learn from logs to improve gameplay

This script analyzes gameplay logs and automatically generates tuning
recommendations to improve game balance. It can create a config file
that the game will load to adjust difficulty parameters.

Usage:
    python game_tuner.py                    # Analyze and show recommendations
    python game_tuner.py --apply            # Generate tuning config file
    python game_tuner.py --reset            # Remove tuning config
    python game_tuner.py --min-sessions 10  # Require minimum sessions
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


class GameTuner:
    """Analyzes logs and generates automatic balance adjustments."""

    def __init__(self, log_dir: Path = Path("logs"), min_sessions: int = 5):
        self.log_dir = log_dir
        self.min_sessions = min_sessions
        self.adjustments = {}
        self.insights = []

    def load_all_sessions(self) -> list[dict[str, Any]]:
        """Load all session data from log files."""
        sessions = []
        log_files = list(self.log_dir.glob("game_*.jsonl"))

        for log_file in log_files:
            events = []
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))
            except Exception:
                continue

            if not events:
                continue

            # Extract session metadata
            session_start = next((e for e in events if e["type"] == "session_start"), {})
            game_start = next((e for e in events if e["type"] == "game_start"), {})
            deaths = [e for e in events if e["type"] == "death"]
            victories = [e for e in events if e["type"] == "victory"]
            player_states = [e for e in events if e["type"].startswith("player_")]
            final_state = player_states[-1] if player_states else {}

            session = {
                "test_mode": session_start.get("test_mode", False),
                "theme": game_start.get("theme"),
                "difficulty": game_start.get("difficulty"),
                "outcome": "death" if deaths else "victory" if victories else "incomplete",
                "death_cause": deaths[0].get("cause") if deaths else None,
                "death_day": deaths[0].get("day") if deaths else None,
                "death_distance_pct": deaths[0].get("distance_pct") if deaths else None,
                "final_day": final_state.get("day", 0),
                "final_health": final_state.get("health", 0),
                "events": events,
            }
            sessions.append(session)

        return sessions

    def analyze_theme_balance(self, sessions: list[dict[str, Any]]) -> None:
        """Detect themes that are too hard or too easy."""
        themes = defaultdict(lambda: {"plays": 0, "wins": 0, "deaths": []})

        for s in sessions:
            if not s.get("theme"):
                continue
            theme = s["theme"]
            themes[theme]["plays"] += 1
            if s["outcome"] == "victory":
                themes[theme]["wins"] += 1
            if s["outcome"] == "death":
                themes[theme]["deaths"].append(s["death_day"] or 0)

        for theme, data in themes.items():
            if data["plays"] < self.min_sessions:
                continue  # Not enough data

            win_rate = data["wins"] / data["plays"]
            avg_death_day = sum(data["deaths"]) / len(data["deaths"]) if data["deaths"] else 0

            # Target win rate: 40-60% (balanced)
            if win_rate < 0.25:
                # Too hard - increase starting supplies
                supply_boost = 1.3  # 30% more supplies
                self.adjustments[f"theme_{theme}_supply_multiplier"] = supply_boost
                self.insights.append(
                    f"📊 Theme '{theme}': {win_rate*100:.1f}% win rate (too hard) "
                    f"→ Increase starting supplies by 30%"
                )
            elif win_rate > 0.75:
                # Too easy - reduce starting supplies
                supply_nerf = 0.8  # 20% fewer supplies
                self.adjustments[f"theme_{theme}_supply_multiplier"] = supply_nerf
                self.insights.append(
                    f"📊 Theme '{theme}': {win_rate*100:.1f}% win rate (too easy) "
                    f"→ Reduce starting supplies by 20%"
                )

            # Check for early death clusters
            if avg_death_day < 20 and len(data["deaths"]) >= 3:
                self.insights.append(
                    f"⚠️  Theme '{theme}': Average death at day {avg_death_day:.0f} "
                    f"→ Early game may be too punishing"
                )

    def analyze_difficulty_scaling(self, sessions: list[dict[str, Any]]) -> None:
        """Verify that difficulty levels scale properly."""
        difficulties = {"easy": [], "normal": [], "hard": []}

        for s in sessions:
            diff = s.get("difficulty")
            if diff in difficulties:
                difficulties[diff].append(s)

        # Calculate win rates
        win_rates = {}
        for diff, sess_list in difficulties.items():
            if len(sess_list) >= self.min_sessions:
                wins = sum(1 for s in sess_list if s["outcome"] == "victory")
                win_rates[diff] = wins / len(sess_list)

        # Check if scaling makes sense
        if "easy" in win_rates and "hard" in win_rates:
            if win_rates["easy"] < win_rates["hard"]:
                self.insights.append(
                    f"⚠️  SCALING ISSUE: Easy ({win_rates['easy']*100:.1f}%) "
                    f"has lower win rate than Hard ({win_rates['hard']*100:.1f}%) "
                    f"→ Difficulty multipliers may be inverted"
                )
            elif win_rates["easy"] < 0.5:
                # Even easy mode is too hard
                self.adjustments["global_easy_boost"] = 1.2
                self.insights.append(
                    f"📊 Easy mode: {win_rates['easy']*100:.1f}% win rate "
                    f"→ Boost easy mode supplies by 20%"
                )

        # Individual difficulty adjustments
        for diff, rate in win_rates.items():
            if diff == "normal" and rate < 0.35:
                self.adjustments[f"difficulty_{diff}_multiplier"] = 1.15
                self.insights.append(
                    f"📊 Normal difficulty: {rate*100:.1f}% win rate "
                    f"→ Increase supplies by 15%"
                )

    def analyze_death_causes(self, sessions: list[dict[str, Any]]) -> None:
        """Identify common death causes that may indicate balance issues."""
        deaths = [s for s in sessions if s["outcome"] == "death"]
        if len(deaths) < self.min_sessions:
            return

        causes = Counter(s["death_cause"] for s in deaths if s.get("death_cause"))
        total_deaths = len(deaths)

        for cause, count in causes.most_common():
            pct = count / total_deaths * 100

            # If >50% of deaths are from one cause, that's a problem
            if pct > 50:
                if cause == "starvation":
                    self.adjustments["food_consumption_rate"] = 0.85  # 15% slower
                    self.insights.append(
                        f"⚠️  {pct:.0f}% of deaths from starvation "
                        f"→ Reduce food consumption by 15%"
                    )
                elif cause == "dehydration":
                    self.adjustments["water_consumption_rate"] = 0.85
                    self.insights.append(
                        f"⚠️  {pct:.0f}% of deaths from dehydration "
                        f"→ Reduce water consumption by 15%"
                    )
                elif cause == "combat":
                    self.adjustments["combat_damage_multiplier"] = 0.9
                    self.insights.append(
                        f"⚠️  {pct:.0f}% of deaths from combat "
                        f"→ Reduce combat damage by 10%"
                    )

    def analyze_event_frequency(self, sessions: list[dict[str, Any]]) -> None:
        """Check if certain events never trigger or trigger too often."""
        all_events = []
        for s in sessions:
            events = [e for e in s["events"] if e["type"] == "event_start"]
            all_events.extend([e.get("event") for e in events])

        if not all_events:
            return

        event_counts = Counter(all_events)
        total_events = len(all_events)

        # Expected event types (from EVENT_POOL in main.py)
        expected_events = [
            "bandit", "river", "storm", "wildlife", "trader", "discovery",
            "morale", "special_item", "riddle", "companion", "ambush_elite",
            "weather_shift"
        ]

        for expected in expected_events:
            count = event_counts.get(expected, 0)
            if total_events > 20 and count == 0:
                self.insights.append(
                    f"📊 Event '{expected}' never triggered in {len(sessions)} sessions "
                    f"→ May need higher weight"
                )

    def analyze_progression_pacing(self, sessions: list[dict[str, Any]]) -> None:
        """Check if players are progressing too fast or too slow."""
        completed = [s for s in sessions if s["outcome"] == "victory"]
        if len(completed) < self.min_sessions:
            return

        avg_completion_days = sum(s["final_day"] for s in completed) / len(completed)

        # Target: 40-80 days for completion
        if avg_completion_days < 30:
            self.insights.append(
                f"⚠️  Average completion: {avg_completion_days:.0f} days (too fast) "
                f"→ Consider increasing total distance"
            )
        elif avg_completion_days > 100:
            self.insights.append(
                f"⚠️  Average completion: {avg_completion_days:.0f} days (too slow) "
                f"→ Consider increasing travel speed or reducing distance"
            )

    def analyze_damage_balance(self, sessions: list[dict[str, Any]]) -> None:
        """Analyze if damage_mult per difficulty needs adjustment."""
        difficulties = defaultdict(lambda: {"deaths": 0, "avg_health_at_death": [], "total_games": 0})
        
        for s in sessions:
            diff = s.get("difficulty")
            if not diff:
                continue
                
            difficulties[diff]["total_games"] += 1
            
            if s["outcome"] == "death":
                difficulties[diff]["deaths"] += 1
                if s.get("final_health") is not None:
                    difficulties[diff]["avg_health_at_death"].append(s["final_health"])
        
        for diff, data in difficulties.items():
            if data["total_games"] < self.min_sessions:
                continue
            
            death_rate = data["deaths"] / data["total_games"]
            
            # Check if deaths are too frequent or health drops too fast
            if diff == "easy" and death_rate > 0.60:
                # Easy mode too deadly
                mult_key = f"difficulty_{diff}_damage_reduction"
                self.adjustments[mult_key] = 0.8  # 20% less damage
                self.insights.append(
                    f"📊 {diff.capitalize()} mode: {death_rate*100:.0f}% death rate "
                    f"→ Reduce damage taken by 20%"
                )
            elif diff == "normal" and death_rate > 0.75:
                # Normal too punishing
                mult_key = f"difficulty_{diff}_damage_reduction"
                self.adjustments[mult_key] = 0.9  # 10% less damage
                self.insights.append(
                    f"📊 {diff.capitalize()} mode: {death_rate*100:.0f}% death rate "
                    f"→ Reduce damage taken by 10%"
                )
            elif diff == "hard" and death_rate > 0.90:
                # Hard mode is impossible
                mult_key = f"difficulty_{diff}_damage_reduction"
                self.adjustments[mult_key] = 0.85  # 15% less damage
                self.insights.append(
                    f"📊 {diff.capitalize()} mode: {death_rate*100:.0f}% death rate "
                    f"→ Reduce damage taken by 15%"
                )

    def analyze_event_rates(self, sessions: list[dict[str, Any]]) -> None:
        """Analyze if event_chance per difficulty needs adjustment."""
        difficulties = defaultdict(lambda: {"events": 0, "days": 0})
        
        for s in sessions:
            diff = s.get("difficulty")
            if not diff:
                continue
            
            event_count = len([e for e in s["events"] if e["type"] == "event_start"])
            difficulties[diff]["events"] += event_count
            difficulties[diff]["days"] += s.get("final_day", 0)
        
        for diff, data in difficulties.items():
            if data["days"] < 50:  # Need enough gameplay days
                continue
            
            events_per_day = data["events"] / data["days"] if data["days"] > 0 else 0
            
            # Target event rates: Easy 0.30, Normal 0.40, Hard 0.55
            target_rates = {"easy": 0.30, "normal": 0.40, "hard": 0.55}
            target = target_rates.get(diff, 0.40)
            
            # If event rate is significantly off (>30% deviation)
            deviation = abs(events_per_day - target) / target
            if deviation > 0.30:
                adjustment = target / events_per_day if events_per_day > 0 else 1.0
                mult_key = f"difficulty_{diff}_event_chance"
                self.adjustments[mult_key] = adjustment
                direction = "Increase" if adjustment > 1.0 else "Decrease"
                self.insights.append(
                    f"📊 {diff.capitalize()} mode: {events_per_day:.2f} events/day "
                    f"(target {target:.2f}) → {direction} event rate by {abs(1-adjustment)*100:.0f}%"
                )

    def analyze_health_survivability(self, sessions: list[dict[str, Any]]) -> None:
        """Analyze if initial health pool needs adjustment."""
        early_deaths = []  # Deaths before day 15
        
        for s in sessions:
            if s["outcome"] == "death" and s.get("death_day"):
                if s["death_day"] < 15:
                    early_deaths.append({
                        "day": s["death_day"],
                        "health": s.get("final_health", 0),
                        "cause": s.get("death_cause")
                    })
        
        if len(early_deaths) >= self.min_sessions:
            # Many early deaths - might need more starting health
            avg_early_death_day = sum(d["day"] for d in early_deaths) / len(early_deaths)
            
            if avg_early_death_day < 10:
                self.adjustments["initial_health_multiplier"] = 1.2  # 20% more health
                self.insights.append(
                    f"⚠️  {len(early_deaths)} deaths before day 15 "
                    f"(avg day {avg_early_death_day:.1f}) → Increase starting health by 20%"
                )
            elif avg_early_death_day < 12:
                self.adjustments["initial_health_multiplier"] = 1.1  # 10% more health
                self.insights.append(
                    f"⚠️  {len(early_deaths)} deaths before day 15 "
                    f"(avg day {avg_early_death_day:.1f}) → Increase starting health by 10%"
                )

    def generate_report(self) -> str:
        """Generate a human-readable tuning report."""
        report = []
        report.append("=" * 70)
        report.append(" AUTOMATIC GAME TUNING REPORT")
        report.append("=" * 70)

        if not self.insights:
            report.append("\n✅ No significant balance issues detected.")
            report.append("   The game appears well-balanced based on current data.")
            return "\n".join(report)

        report.append(f"\n📈 Analyzed gameplay data - found {len(self.insights)} insights:\n")
        for insight in self.insights:
            report.append(f"  {insight}")

        if self.adjustments:
            report.append(f"\n⚙️  Recommended adjustments ({len(self.adjustments)} parameters):\n")
            for param, value in self.adjustments.items():
                report.append(f"    {param}: {value}")

        return "\n".join(report)

    def calculate_metrics(self, sessions: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate key metrics from sessions for history tracking."""
        if not sessions:
            return {}
        
        metrics = {
            "total_sessions": len(sessions),
            "win_rate": sum(1 for s in sessions if s["outcome"] == "victory") / len(sessions),
            "death_rate": sum(1 for s in sessions if s["outcome"] == "death") / len(sessions),
            "avg_days": sum(s.get("final_day", 0) for s in sessions) / len(sessions),
        }
        
        # Death causes percentage
        deaths = [s for s in sessions if s["outcome"] == "death"]
        if deaths:
            from collections import Counter
            causes = Counter(s.get("death_cause") for s in deaths)
            total = len(deaths)
            metrics["death_causes"] = {
                cause: count / total for cause, count in causes.items()
            }
        
        return metrics

    def save_tuning_config(self, config_path: Path = Path("game_tuning.json")) -> None:
        """Save tuning adjustments with version history."""
        from datetime import datetime
        
        # Load existing config if present
        existing_config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
            except Exception:
                pass
        
        # Get session metrics for this iteration
        sessions = self.load_all_sessions()
        current_metrics = self.calculate_metrics(sessions)
        
        # Initialize tuning history
        tuning_history = existing_config.get("tuning_history", [])
        previous_metrics = existing_config.get("metrics_before", {})
        
        # Create new history entry
        new_history_entry = {
            "iteration": len(tuning_history) + 1,
            "date": datetime.now().isoformat(),
            "sessions_analyzed": len(sessions),
            "adjustments": self.adjustments,
            "metrics": current_metrics,
            "previous_metrics": previous_metrics if tuning_history else None,
            "insights_count": len(self.insights),
        }
        
        # Determine if tuning is improving or regressing
        if tuning_history and previous_metrics:
            prev_wr = previous_metrics.get("win_rate", 0)
            curr_wr = current_metrics.get("win_rate", 0)
            if curr_wr > prev_wr:
                new_history_entry["outcome"] = "improving"
            elif curr_wr < prev_wr:
                new_history_entry["outcome"] = "regressing"
            else:
                new_history_entry["outcome"] = "neutral"
        else:
            new_history_entry["outcome"] = "initial_tuning"
        
        tuning_history.append(new_history_entry)
        
        # Get baseline values (from first iteration or stored baseline)
        baseline = existing_config.get("baseline", {
            "difficulty_normal_multiplier": 1.0,
            "food_consumption_rate": 1.0,
            "difficulty_normal_damage_reduction": 1.0,
            "difficulty_normal_event_chance": 0.40,
            "combat_damage_multiplier": 1.0,
            "initial_health_multiplier": 1.0,
        })
        
        # Build comprehensive config
        config = {
            "version": "1.1",
            "metadata": {
                "generated": datetime.now().isoformat(),
                "tuning_iteration": len(tuning_history),
                "sessions_analyzed": len(sessions),
                "status": new_history_entry.get("outcome", "unknown"),
            },
            "baseline": baseline,
            "current_adjustments": self.adjustments,
            "metrics_before": previous_metrics,
            "metrics_after": current_metrics,
            "tuning_history": tuning_history[-5:],  # Keep last 5 iterations
            "insights": self.insights,
            "note": "Auto-generated by game_tuner.py. Tracks tuning history to prevent circular logic.",
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Tuning config saved to: {config_path}")
        print(f"   Iteration {len(tuning_history)}: {new_history_entry['outcome']}")
        if previous_metrics:
            print(f"   Win rate: {previous_metrics.get('win_rate', 0)*100:.1f}% → {current_metrics.get('win_rate', 0)*100:.1f}%")
        print(f"   The game will automatically load these adjustments on next run.")

    def run_analysis(self) -> None:
        """Run all analysis steps."""
        sessions = self.load_all_sessions()

        if len(sessions) < self.min_sessions:
            print(f"\n⚠️  Only {len(sessions)} session(s) found.")
            print(f"   Need at least {self.min_sessions} sessions for meaningful analysis.")
            print(f"   Play more games and try again!")
            return

        print(f"\n📊 Analyzing {len(sessions)} gameplay session(s)...\n")

        # Run all analyses
        self.analyze_theme_balance(sessions)
        self.analyze_difficulty_scaling(sessions)
        self.analyze_death_causes(sessions)
        self.analyze_damage_balance(sessions)  # NEW: Tier 1 analysis
        self.analyze_event_rates(sessions)  # Enhanced with tuning
        self.analyze_health_survivability(sessions)  # NEW: Tier 1 analysis
        self.analyze_progression_pacing(sessions)

        # Show report
        print(self.generate_report())


def main():
    parser = argparse.ArgumentParser(description="Automatic game balance tuner")
    parser.add_argument("--apply", action="store_true",
                        help="Apply tuning by generating game_tuning.json config")
    parser.add_argument("--reset", action="store_true",
                        help="Remove tuning config file")
    parser.add_argument("--min-sessions", type=int, default=5,
                        help="Minimum sessions required for analysis (default: 5)")
    args = parser.parse_args()

    config_path = Path("game_tuning.json")

    if args.reset:
        if config_path.exists():
            config_path.unlink()
            print(f"✅ Removed tuning config: {config_path}")
        else:
            print(f"No tuning config found.")
        return

    tuner = GameTuner(min_sessions=args.min_sessions)
    tuner.run_analysis()

    if args.apply and tuner.adjustments:
        tuner.save_tuning_config(config_path)
        print("\n💡 Next time you run the game, it will use these tuned parameters.")
    elif args.apply:
        print("\n⚠️  No adjustments to apply (game is already balanced).")

    print("\n" + "=" * 70)
    print(" Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
