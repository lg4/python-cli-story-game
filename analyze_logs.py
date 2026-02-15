"""
Log Analyzer for Terminal Adventure Quest

This script analyzes gameplay logs to provide insights for game balance
and improvement. Run it after playing games to see patterns.

Usage:
    python analyze_logs.py                    # Analyze all logs
    python analyze_logs.py --session 20260214_153022  # Analyze specific session
    python analyze_logs.py --stats            # Show summary statistics
    python analyze_logs.py --deaths           # Analyze death patterns
    python analyze_logs.py --balance          # Check game balance issues
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_session(log_file: Path) -> list[dict[str, Any]]:
    """Load all events from a JSONL log file."""
    events = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    except Exception as e:
        print(f"Error loading {log_file}: {e}")
    return events


def analyze_session(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze a single session's events."""
    if not events:
        return {}
    
    session_start = next((e for e in events if e["type"] == "session_start"), {})
    session_end = next((e for e in events if e["type"] == "session_end"), {})
    game_start = next((e for e in events if e["type"] == "game_start"), {})
    
    deaths = [e for e in events if e["type"] == "death"]
    victories = [e for e in events if e["type"] == "victory"]
    choices = [e for e in events if e["type"] == "choice"]
    random_events = [e for e in events if e["type"] == "event_start"]
    achievements = [e for e in events if e["type"] == "achievement_unlock"]
    penalties = [e for e in events if e["type"] == "penalties_applied"]
    errors = [e for e in events if e["type"] == "error"]
    
    # Get final state
    player_states = [e for e in events if e["type"].startswith("player_")]
    final_state = player_states[-1] if player_states else {}
    
    return {
        "session_id": game_start.get("seed"),
        "test_mode": session_start.get("test_mode", False),
        "theme": game_start.get("theme"),
        "difficulty": game_start.get("difficulty"),
        "duration": session_end.get("duration_seconds", 0),
        "outcome": "death" if deaths else "victory" if victories else "incomplete",
        "death_cause": deaths[0].get("cause") if deaths else None,
        "death_day": deaths[0].get("day") if deaths else None,
        "death_distance_pct": deaths[0].get("distance_pct") if deaths else None,
        "ending_type": victories[0].get("ending") if victories else None,
        "total_choices": len(choices),
        "total_events": len(random_events),
        "achievements_unlocked": len(achievements),
        "penalties_count": len(penalties),
        "final_day": final_state.get("day", 0),
        "final_health": final_state.get("health", 0),
        "final_distance": final_state.get("distance", 0),
        "errors": errors,  # Include full error list
        "error_count": len(errors),
    }


def print_summary_stats(sessions: list[dict[str, Any]]) -> None:
    """Print overall statistics across all sessions."""
    print("\n" + "=" * 70)
    print(" GAMEPLAY SUMMARY STATISTICS")
    print("=" * 70)
    
    if not sessions:
        print("  No sessions found.")
        return
    
    total = len(sessions)
    test_mode_sessions = sum(1 for s in sessions if s.get("test_mode"))
    deaths = sum(1 for s in sessions if s["outcome"] == "death")
    victories = sum(1 for s in sessions if s["outcome"] == "victory")
    
    print(f"\n  Total Sessions: {total}")
    print(f"  Test Mode: {test_mode_sessions} | Interactive: {total - test_mode_sessions}")
    print(f"  Deaths: {deaths} ({deaths/total*100:.1f}%)")
    print(f"  Victories: {victories} ({victories/total*100:.1f}%)")
    print(f"  Win Rate: {victories/total*100:.1f}%")
    
    # Theme breakdown
    theme_counter = Counter(s["theme"] for s in sessions if s.get("theme"))
    print(f"\n  Themes Played:")
    for theme, count in theme_counter.most_common():
        wins = sum(1 for s in sessions if s.get("theme") == theme and s["outcome"] == "victory")
        win_rate = wins / count * 100 if count > 0 else 0
        print(f"    {theme:15s}: {count:3d} plays, {win_rate:5.1f}% win rate")
    
    # Difficulty breakdown
    diff_counter = Counter(s["difficulty"] for s in sessions if s.get("difficulty"))
    print(f"\n  Difficulty Levels:")
    for diff, count in diff_counter.most_common():
        wins = sum(1 for s in sessions if s.get("difficulty") == diff and s["outcome"] == "victory")
        win_rate = wins / count * 100 if count > 0 else 0
        print(f"    {diff:10s}: {count:3d} plays, {win_rate:5.1f}% win rate")
    
    # Average metrics
    avg_choices = sum(s["total_choices"] for s in sessions) / total
    avg_events = sum(s["total_events"] for s in sessions) / total
    avg_achievements = sum(s["achievements_unlocked"] for s in sessions) / total
    avg_day = sum(s["final_day"] for s in sessions) / total
    
    print(f"\n  Average Metrics per Session:")
    print(f"    Days Survived: {avg_day:.1f}")
    print(f"    Choices Made: {avg_choices:.1f}")
    print(f"    Random Events: {avg_events:.1f}")
    print(f"    Achievements: {avg_achievements:.1f}")
    
    # Error summary
    total_errors = sum(s.get("error_count", 0) for s in sessions)
    if total_errors > 0:
        sessions_with_errors = sum(1 for s in sessions if s.get("error_count", 0) > 0)
        print(f"\n  ⚠️  Errors Detected:")
        print(f"    Total errors: {total_errors}")
        print(f"    Sessions with errors: {sessions_with_errors}/{total}")
        
        # Collect error types
        error_types = []
        for s in sessions:
            for err in s.get("errors", []):
                error_types.append(err.get("error_type", "Unknown"))
        if error_types:
            error_counts = Counter(error_types)
            print(f"    Most common errors:")
            for err_type, count in error_counts.most_common(5):
                print(f"      {err_type}: {count}")


def analyze_deaths(sessions: list[dict[str, Any]]) -> None:
    """Analyze death patterns to identify balance issues."""
    print("\n" + "=" * 70)
    print(" DEATH PATTERN ANALYSIS")
    print("=" * 70)
    
    deaths = [s for s in sessions if s["outcome"] == "death"]
    
    if not deaths:
        print("  No deaths recorded.")
        return
    
    print(f"\n  Total Deaths: {len(deaths)}")
    
    # Death causes
    cause_counter = Counter(s["death_cause"] for s in deaths if s.get("death_cause"))
    print(f"\n  Death Causes:")
    for cause, count in cause_counter.most_common():
        pct = count / len(deaths) * 100
        print(f"    {cause:15s}: {count:3d} ({pct:5.1f}%)")
    
    # Average survival metrics
    avg_survival_day = sum(s["death_day"] for s in deaths if s.get("death_day")) / len(deaths)
    avg_distance_pct = sum(s["death_distance_pct"] for s in deaths if s.get("death_distance_pct")) / len(deaths)
    
    print(f"\n  Average Survival:")
    print(f"    Days: {avg_survival_day:.1f}")
    print(f"    Distance: {avg_distance_pct:.1f}% of journey")
    
    # Early deaths (< 20% distance)
    early_deaths = [s for s in deaths if s.get("death_distance_pct", 100) < 20]
    if early_deaths:
        print(f"\n  ⚠️  Early Deaths (< 20% distance): {len(early_deaths)}")
        early_causes = Counter(s["death_cause"] for s in early_deaths if s.get("death_cause"))
        for cause, count in early_causes.most_common(3):
            print(f"      {cause}: {count}")
    
    # Death by difficulty
    print(f"\n  Deaths by Difficulty:")
    for diff in ["easy", "normal", "hard"]:
        diff_deaths = [s for s in deaths if s.get("difficulty") == diff]
        if diff_deaths:
            avg_day = sum(s["death_day"] for s in diff_deaths if s.get("death_day")) / len(diff_deaths)
            print(f"    {diff:10s}: {len(diff_deaths):3d} deaths (avg day {avg_day:.1f})")


def check_balance(sessions: list[dict[str, Any]]) -> None:
    """Check for potential game balance issues."""
    print("\n" + "=" * 70)
    print(" BALANCE ANALYSIS")
    print("=" * 70)
    
    if not sessions:
        print("  No sessions to analyze.")
        return
    
    issues = []
    
    # Check win rates by theme
    themes = set(s["theme"] for s in sessions if s.get("theme"))
    theme_win_rates = {}
    for theme in themes:
        theme_sessions = [s for s in sessions if s.get("theme") == theme]
        if theme_sessions:
            wins = sum(1 for s in theme_sessions if s["outcome"] == "victory")
            win_rate = wins / len(theme_sessions)
            theme_win_rates[theme] = win_rate
            if win_rate < 0.2:
                issues.append(f"⚠️  Theme '{theme}' has low win rate: {win_rate*100:.1f}%")
            elif win_rate > 0.8:
                issues.append(f"⚠️  Theme '{theme}' has high win rate: {win_rate*100:.1f}% (too easy?)")
    
    # Check difficulty scaling
    difficulties = {"easy": 0, "normal": 0, "hard": 0}
    for diff in difficulties:
        diff_sessions = [s for s in sessions if s.get("difficulty") == diff]
        if diff_sessions:
            wins = sum(1 for s in diff_sessions if s["outcome"] == "victory")
            difficulties[diff] = wins / len(diff_sessions)
    
    # Check if difficulty order makes sense
    if difficulties["easy"] > 0 and difficulties["hard"] > 0:
        if difficulties["easy"] < difficulties["hard"]:
            issues.append("⚠️  Hard mode has higher win rate than Easy mode!")
    
    # Check for death clusters
    deaths = [s for s in sessions if s["outcome"] == "death"]
    if deaths:
        death_days = [s["death_day"] for s in deaths if s.get("death_day")]
        if death_days:
            avg_death_day = sum(death_days) / len(death_days)
            if avg_death_day < 10:
                issues.append(f"⚠️  Average death day is very early: {avg_death_day:.1f} days")
    
    # Check achievement unlock rates
    avg_achievements = sum(s["achievements_unlocked"] for s in sessions) / len(sessions)
    if avg_achievements < 0.5:
        issues.append(f"⚠️  Low achievement unlock rate: {avg_achievements:.1f} per game")
    
    if issues:
        print("\n  Potential Balance Issues:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("\n  ✓ No major balance issues detected.")
    
    # Recommendations
    print("\n  Win Rate by Theme:")
    for theme, rate in sorted(theme_win_rates.items(), key=lambda x: x[1]):
        status = "Too Hard" if rate < 0.3 else "Balanced" if rate < 0.6 else "Too Easy"
        print(f"    {theme:15s}: {rate*100:5.1f}% - {status}")


def analyze_errors(sessions: list[dict[str, Any]]) -> None:
    """Analyze errors, crashes, and invalid inputs."""
    print("\n" + "=" * 70)
    print(" ERROR & CRASH ANALYSIS")
    print("=" * 70)
    
    sessions_with_errors = [s for s in sessions if s.get("error_count", 0) > 0]
    
    if not sessions_with_errors:
        print("\n  ✅ No errors detected in any session.")
        return
    
    total_errors = sum(s.get("error_count", 0) for s in sessions)
    print(f"\n  Total Sessions with Errors: {len(sessions_with_errors)}/{len(sessions)}")
    print(f"  Total Errors Logged: {total_errors}")
    
    # Collect all errors
    all_errors = []
    for s in sessions_with_errors:
        for err in s.get("errors", []):
            all_errors.append({
                "type": err.get("error_type", "Unknown"),
                "message": err.get("message", ""),
                "context": err.get("context", {}),
                "traceback": err.get("traceback"),
                "session": s.get("session_id"),
                "theme": s.get("theme"),
                "difficulty": s.get("difficulty"),
            })
    
    # Group by error type
    error_types = Counter(e["type"] for e in all_errors)
    print(f"\n  Error Types:")
    for err_type, count in error_types.most_common():
        pct = count / total_errors * 100
        print(f"    {err_type:25s}: {count:3d} ({pct:5.1f}%)")
    
    # Show critical errors (with tracebacks)
    critical_errors = [e for e in all_errors if e.get("traceback")]
    if critical_errors:
        print(f"\n  ⚠️  Critical Errors (with tracebacks): {len(critical_errors)}")
        for i, err in enumerate(critical_errors[:3], 1):  # Show first 3
            print(f"\n    Error #{i}:")
            print(f"      Type: {err['type']}")
            print(f"      Message: {err['message']}")
            if err.get("context"):
                print(f"      Context: {err['context']}")
            if i <= 1 and err.get("traceback"):  # Show full traceback for first error
                print(f"      Traceback:")
                for line in err['traceback'].split('\n')[:5]:  # First 5 lines
                    print(f"        {line}")
    
    # Invalid input analysis
    invalid_inputs = [e for e in all_errors if e["type"] == "InvalidInput"]
    if invalid_inputs:
        print(f"\n  Invalid Input Attempts: {len(invalid_inputs)}")
        # Show some examples
        messages = Counter(e["message"] for e in invalid_inputs)
        print(f"    Most common:")
        for msg, count in messages.most_common(5):
            print(f"      {msg}: {count}x")
    
    # User interrupts
    interrupts = [e for e in all_errors if e["type"] == "UserInterrupt"]
    if interrupts:
        print(f"\n  User Interrupts: {len(interrupts)}")
        contexts = Counter(str(e["context"]) for e in interrupts)
        for ctx, count in contexts.most_common(3):
            print(f"    At {ctx}: {count}x")


def main():
    parser = argparse.ArgumentParser(description="Analyze Terminal Adventure Quest logs")
    parser.add_argument("--session", type=str, help="Analyze specific session ID")
    parser.add_argument("--stats", action="store_true", help="Show summary statistics")
    parser.add_argument("--deaths", action="store_true", help="Analyze death patterns")
    parser.add_argument("--balance", action="store_true", help="Check game balance")
    parser.add_argument("--errors", action="store_true", help="Analyze errors and crashes")
    parser.add_argument("--all", action="store_true", help="Show all analyses")
    args = parser.parse_args()
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print(f"No logs directory found. Play some games first!")
        return
    
    # Load sessions
    log_files = list(log_dir.glob("game_*.jsonl"))
    if not log_files:
        print("No log files found.")
        return
    
    print(f"Found {len(log_files)} log file(s)")
    
    # Filter by session if specified
    if args.session:
        log_files = [f for f in log_files if args.session in f.name]
        if not log_files:
            print(f"No logs found for session: {args.session}")
            return
    
    # Load and analyze all sessions
    all_sessions = []
    for log_file in log_files:
        events = load_session(log_file)
        if events:
            session_data = analyze_session(events)
            all_sessions.append(session_data)
    
    if not all_sessions:
        print("No valid sessions to analyze.")
        return
    
    # Run requested analyses
    if args.all or (not args.stats and not args.deaths and not args.balance and not args.errors):
        # Show everything by default
        print_summary_stats(all_sessions)
        analyze_deaths(all_sessions)
        check_balance(all_sessions)
        analyze_errors(all_sessions)
    else:
        if args.stats:
            print_summary_stats(all_sessions)
        if args.deaths:
            analyze_deaths(all_sessions)
        if args.balance:
            check_balance(all_sessions)
        if args.errors:
            analyze_errors(all_sessions)
    
    print("\n" + "=" * 70)
    print(" Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
