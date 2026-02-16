#!/usr/bin/env python3
"""Test AI scenario variety and deduplication"""

import sys
sys.path.insert(0, '.')
import main

def test_scenario_variety():
    """Test that we can generate many unique scenarios"""
    # Enable test mode to suppress debug messages
    main.TEST_MODE = True
    main.LOGGING_ENABLED = False
    
    seen = set()
    theme = main.ThemeId.AI_GENERATED
    
    print("Testing AI Scenario Variety")
    print("=" * 60)
    
    # Try to generate 50 scenarios
    scenarios = []
    for i in range(50):
        scenario = main.generate_ai_scenario(theme, "general", seen)
        scenarios.append(scenario[:80])  # Store first 80 chars for display
        seen.add(scenario)
    
    unique_count = len(set(scenarios))
    print(f"\nGenerated {len(scenarios)} scenarios")
    print(f"Unique scenarios: {unique_count}")
    print(f"Uniqueness rate: {unique_count/len(scenarios)*100:.1f}%")
    
    print(f"\nFirst 10 scenarios:")
    for i, s in enumerate(scenarios[:10], 1):
        print(f"{i:2}. {s}...")
    
    # Check template pool size
    if theme in main.AI_SCENARIO_TEMPLATES:
        template_count = len(main.AI_SCENARIO_TEMPLATES[theme])
        print(f"\nAI_GENERATED templates available: {template_count}")
        
        # Check other themes
        total_templates = sum(len(templates) for templates in main.AI_SCENARIO_TEMPLATES.values())
        print(f"Total templates across all themes: {total_templates}")
    
    if unique_count >= 40:
        print("\n✓ PASS: High variety (40+ unique out of 50)")
    elif unique_count >= 30:
        print("\n⚠ WARN: Moderate variety (30-39 unique out of 50)")
    else:
        print("\n✗ FAIL: Low variety (< 30 unique out of 50)")

if __name__ == "__main__":
    test_scenario_variety()
