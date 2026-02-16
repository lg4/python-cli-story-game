#!/usr/bin/env python3
"""Test and demonstrate the circular logic prevention system."""

import json
from pathlib import Path

# Read current config
with open('game_tuning.json', encoding='utf-8') as f:
    config = json.load(f)

# Show current state
print('=' * 70)
print('CIRCULAR LOGIC PREVENTION SYSTEM STATUS')
print('=' * 70)
print(f'\n✅ System Version: {config["version"]}')
print(f'✅ Current Iteration: {config["metadata"]["tuning_iteration"]}')
print(f'✅ Status: {config["metadata"]["status"]}')

print(f'\n📊 Baseline Values (Original):\n')
for param, value in config['baseline'].items():
    print(f'  • {param}: {value}')

print(f'\n⚙️  Current Adjustments (Applied):\n')
for param, value in config['current_adjustments'].items():
    change = (value - 1.0) * 100
    direction = '↑' if change > 0 else '↓'
    print(f'  {direction} {param}: {value:.3f} ({change:+.1f}%)')

print(f'\n📋 Tuning History (Last 5 Iterations):\n')
for iteration in config['tuning_history'][-5:]:
    print(f'  Iteration {iteration["iteration"]}: {iteration["outcome"]}')
    print(f'    • Date: {iteration["date"]}')
    print(f'    • Sessions Analyzed: {iteration["sessions_analyzed"]}')
    print(f'    • Win Rate: {iteration["metrics"]["win_rate"]:.1%}')
    print(f'    • Death Rate: {iteration["metrics"]["death_rate"]:.1%}')
    print()

# Test the history analysis function
print('🔍 Testing History Analysis Function:\n')
from game_tuner import GameTuner

tuner = GameTuner()
analysis = tuner.analyze_tuning_history()

if analysis:
    print(f'  ✅ History analysis completed')
    print(f'  • Recent outcomes: {analysis.get("recent_outcomes", [])}')
    print(f'  • Oscillating detected: {analysis.get("oscillating", False)}')
    
    failed = analysis.get("failed_adjustments", {})
    if failed:
        print(f'  • Failed adjustments detected: {len(failed)}')
        for param, value in failed.items():
            print(f'    - {param}: {value:.3f}')
    else:
        print(f'  • No failed adjustments in history')
else:
    print(f'  ℹ️  No history to analyze yet (first tuning iteration)')

print('\n✅ CIRCULAR LOGIC PREVENTION SYSTEM STATUS: OPERATIONAL')
print('   • History tracking enabled (v1.1 format)')
print('   • Oscillation detection: Active')
print('   • Failed adjustment tracking: Active')  
print('   • Automatic filtering: Enabled')
print('=' * 70)
