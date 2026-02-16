"""Test AI scenario deduplication to ensure no duplicates"""
import sys
sys.path.insert(0, '.')

from main import generate_ai_scenario, ThemeId

def test_deduplication():
    """Generate multiple scenarios and verify uniqueness"""
    seen = set()
    scenarios = []
    
    print("Testing AI Scenario Deduplication")
    print("=" * 50)
    
    # Generate 10 scenarios
    for i in range(10):
        scenario = generate_ai_scenario(ThemeId.SPACE, "general", seen)
        scenarios.append(scenario)
        seen.add(scenario)
        print(f"\n{i+1}. {scenario[:80]}...")
        
    # Check for duplicates
    print("\n" + "=" * 50)
    print(f"Generated: {len(scenarios)} scenarios")
    print(f"Unique: {len(set(scenarios))} scenarios")
    
    if len(scenarios) == len(set(scenarios)):
        print("✅ SUCCESS: All scenarios are unique!")
    else:
        print("❌ FAILURE: Found duplicate scenarios")
        duplicates = [s for s in scenarios if scenarios.count(s) > 1]
        for dup in set(duplicates):
            print(f"  Duplicate: {dup[:60]}...")
    
    # Show what's being tracked
    print(f"\nSeen scenarios tracked: {len(seen)}")

if __name__ == "__main__":
    test_deduplication()
