#!/usr/bin/env python3
"""
Test Auto-Improvement System - Run 50 Games
===========================================
Tests the auto-tuning system by simulating 50 games and observing improvements.
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Any

# Import game components
from main import GameState, THEMES, DIFFICULTIES, GameLogger


def simulate_game(theme_idx: int, difficulty_idx: int, game_num: int) -> dict[str, Any]:
    """
    Simulate a single game playthrough.
    
    Returns:
        dict with game results (days_survived, outcome, death_cause, etc.)
    """
    theme = THEMES[theme_idx]
    difficulty = DIFFICULTIES[difficulty_idx]
    
    # Create game state
    state = GameState(theme, difficulty)
    
    # Enable logging
    session_id = f"auto_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{game_num}"
    logger = GameLogger(session_id=session_id)
    logger.start_session(theme.name, difficulty.name)
    
    # Simulate gameplay (random decisions)
    days_survived = 0
    max_days = 100
    outcome = "in_progress"
    death_cause = None
    
    for day in range(1, max_days + 1):
        days_survived = day
        
        # Random event chance
        if random.random() < 0.3:  # 30% event chance per day
            event_outcome = random.choice(["positive", "negative", "neutral"])
            logger.log_event("random_event", {
                "day": day,
                "outcome": event_outcome,
                "description": f"Event on day {day}"
            })
            
            if event_outcome == "negative":
                # Possibly lethal
                if random.random() < 0.15:  # 15% death chance on negative event
                    outcome = "death"
                    death_causes = [
                        "starvation", "dehydration", "combat", "exposure",
                        "illness", "accident", "monster_attack"
                    ]
                    death_cause = random.choice(death_causes)
                    logger.log_event("death", {
                        "day": day,
                        "cause": death_cause,
                        "final_health": state.health
                    })
                    break
        
        # Resource depletion
        state.water -= random.randint(2, 5)
        state.food -= random.randint(1, 4)
        
        if state.water <= 0:
            outcome = "death"
            death_cause = "dehydration"
            logger.log_event("death", {"day": day, "cause": death_cause})
            break
        
        if state.food <= 0:
            outcome = "death"
            death_cause = "starvation"
            logger.log_event("death", {"day": day, "cause": death_cause})
            break
        
        # Random resource replenishment (found supplies)
        if random.random() < 0.2:
            state.water += random.randint(5, 15)
            state.food += random.randint(3, 10)
        
        # Victory condition
        if day >= state.goal_days:
            outcome = "victory"
            logger.log_event("victory", {
                "day": day,
                "final_health": state.health,
                "final_water": state.water,
                "final_food": state.food
            })
            break
    
    logger.end_session(outcome)
    logger.save()
    
    return {
        "game_num": game_num,
        "theme": theme.name,
        "difficulty": difficulty.name,
        "days_survived": days_survived,
        "outcome": outcome,
        "death_cause": death_cause,
        "session_id": session_id
    }


def run_test_suite(num_games: int = 50) -> list[dict[str, Any]]:
    """Run a suite of test games."""
    print(f"🎮 Running {num_games} test games...")
    print("=" * 60)
    
    results = []
    
    # Vary themes and difficulties
    for i in range(num_games):
        theme_idx = random.randint(0, len(THEMES) - 1)
        difficulty_idx = random.randint(0, len(DIFFICULTIES) - 1)
        
        theme_name = THEMES[theme_idx].name
        difficulty_name = DIFFICULTIES[difficulty_idx].name
        
        print(f"Game {i+1}/{num_games}: {theme_name} / {difficulty_name}...", end=" ")
        
        result = simulate_game(theme_idx, difficulty_idx, i+1)
        results.append(result)
        
        outcome_emoji = "💀" if result["outcome"] == "death" else "🏆" if result["outcome"] == "victory" else "⏸️"
        print(f"{outcome_emoji} Day {result['days_survived']}")
    
    return results


def analyze_results(results: list[dict[str, Any]]) -> None:
    """Analyze and display test results."""
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS ANALYSIS")
    print("=" * 60)
    
    total = len(results)
    deaths = sum(1 for r in results if r["outcome"] == "death")
    victories = sum(1 for r in results if r["outcome"] == "victory")
    
    print(f"\nTotal Games: {total}")
    print(f"Deaths: {deaths} ({deaths/total*100:.1f}%)")
    print(f"Victories: {victories} ({victories/total*100:.1f}%)")
    print(f"Win Rate: {victories/total*100:.1f}%")
    
    # Average survival
    avg_survival = sum(r["days_survived"] for r in results) / total
    print(f"Avg Survival: {avg_survival:.1f} days")
    
    # Death causes
    death_causes = {}
    for r in results:
        if r["death_cause"]:
            death_causes[r["death_cause"]] = death_causes.get(r["death_cause"], 0) + 1
    
    if death_causes:
        print("\nDeath Causes:")
        for cause, count in sorted(death_causes.items(), key=lambda x: x[1], reverse=True):
            pct = count / deaths * 100 if deaths > 0 else 0
            print(f"  {cause}: {count} ({pct:.1f}%)")
    
    # By theme
    theme_stats = {}
    for r in results:
        theme = r["theme"]
        if theme not in theme_stats:
            theme_stats[theme] = {"total": 0, "victories": 0}
        theme_stats[theme]["total"] += 1
        if r["outcome"] == "victory":
            theme_stats[theme]["victories"] += 1
    
    print("\nWin Rate by Theme:")
    for theme, stats in sorted(theme_stats.items()):
        win_rate = stats["victories"] / stats["total"] * 100
        print(f"  {theme}: {win_rate:.1f}% ({stats['victories']}/{stats['total']})")
    
    # By difficulty
    diff_stats = {}
    for r in results:
        diff = r["difficulty"]
        if diff not in diff_stats:
            diff_stats[diff] = {"total": 0, "victories": 0}
        diff_stats[diff]["total"] += 1
        if r["outcome"] == "victory":
            diff_stats[diff]["victories"] += 1
    
    print("\nWin Rate by Difficulty:")
    for diff, stats in sorted(diff_stats.items()):
        win_rate = stats["victories"] / stats["total"] * 100
        print(f"  {diff}: {win_rate:.1f}% ({stats['victories']}/{stats['total']})")


if __name__ == "__main__":
    import time
    
    start_time = time.time()
    
    # Run tests
    results = run_test_suite(num_games=50)
    
    # Analyze
    analyze_results(results)
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.1f}s ({elapsed/len(results):.2f}s per game)")
    
    # Save results
    results_file = Path("test_results_auto_improvement.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "num_games": len(results),
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("\nNext steps:")
    print("  1. Run: python auto_tune.py")
    print("  2. Check: game_tuning.json (should have adjustments)")
    print("  3. Run: python test_auto_improvement.py (again)")
    print("  4. Compare before/after win rates!")
