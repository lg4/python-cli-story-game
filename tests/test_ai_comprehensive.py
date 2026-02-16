#!/usr/bin/env python3
"""
Comprehensive AI Generation Testing with Logging
=================================================
Tests AI-generated headers, intro text, and scenarios using remote Ollama API.
Runs 100 scenarios to validate variety, quality, and API connectivity.
Includes comprehensive logging and performance metrics for learning analysis.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
sys.path.insert(0, '.')
import main

# Configuration
OLLAMA_TEST_HOST = "192.168.1.22"
OLLAMA_TEST_PORT = 11434
NUM_SCENARIOS = 100
NUM_HEADERS = 10
NUM_INTROS = 10

# Results tracking
test_results = {
    "test_start": datetime.now().isoformat(),
    "config": {
        "host": OLLAMA_TEST_HOST,
        "port": OLLAMA_TEST_PORT,
        "model": None,  # Will be set after model selection
        "num_headers": NUM_HEADERS,
        "num_intros": NUM_INTROS,
        "num_scenarios": NUM_SCENARIOS,
    },
    "headers": [],
    "intros": [],
    "scenarios": [],
    "performance": {
        "headers": {},
        "intros": {},
        "scenarios": {},
    },
    "errors": [],
}


def test_api_connectivity():
    """Test that the Ollama API is accessible"""
    print(f"\n{'='*70}")
    print("API CONNECTIVITY TEST")
    print(f"{'='*70}")
    print(f"Target: http://{OLLAMA_TEST_HOST}:{OLLAMA_TEST_PORT}")
    
    # Configure main.py to use test host
    main.OLLAMA_HOST = OLLAMA_TEST_HOST
    main.OLLAMA_PORT = OLLAMA_TEST_PORT
    main.OLLAMA_URL = f"http://{OLLAMA_TEST_HOST}:{OLLAMA_TEST_PORT}"
    
    try:
        models = main.query_ollama_models()
        print(f"✓ Connection successful!")
        print(f"  Available models: {len(models)}")
        for model in models[:5]:  # Show first 5
            print(f"    - {model.get('name', 'unknown')}")
        
        # Store model info in results
        test_results["config"]["model"] = main.SELECTED_AI_MODEL
        test_results["config"]["available_models"] = [m.get('name') for m in models]
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print(f"\nMake sure Ollama is running on {OLLAMA_TEST_HOST}:{OLLAMA_TEST_PORT}")
        test_results["errors"].append({
            "stage": "connectivity",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        return False


def test_ai_headers(count=10):
    """Test AI-generated ASCII art headers"""
    print(f"\n{'='*70}")
    print(f"AI HEADER GENERATION TEST ({count} samples)")
    print(f"{'='*70}")
    
    headers = []
    failed = 0
    start_time = time.time()
    generation_times = []
    
    for i in range(count):
        print(f"\rGenerating header {i+1}/{count}...", end='', flush=True)
        gen_start = time.time()
        try:
            header = main.generate_ai_ascii_art()
            gen_time = time.time() - gen_start
            generation_times.append(gen_time)
            
            if header and len(header) > 30:
                headers.append(header)
                test_results["headers"].append({
                    "index": i,
                    "content": header,
                    "length": len(header),
                    "lines": header.count('\n'),
                    "generation_time": round(gen_time, 3),
                    "success": True
                })
            else:
                failed += 1
                test_results["errors"].append({
                    "stage": "header",
                    "index": i,
                    "error": "Empty or too short",
                    "generation_time": round(gen_time, 3)
                })
        except Exception as e:
            print(f"\n  Error generating header {i+1}: {e}")
            gen_time = time.time() - gen_start
            failed += 1
            test_results["errors"].append({
                "stage": "header",
                "index": i,
                "error": str(e),
                "generation_time": round(gen_time, 3)
            })
    
    elapsed = time.time() - start_time
    unique = len(set(headers))
    
    # Store performance metrics
    test_results["performance"]["headers"] = {
        "total_count": count,
        "successful": len(headers),
        "failed": failed,
        "unique_count": unique,
        "uniqueness_rate": round(unique/len(headers)*100, 2) if headers else 0,
        "total_time": round(elapsed, 2),
        "avg_time": round(elapsed/count, 3),
        "min_time": round(min(generation_times), 3) if generation_times else 0,
        "max_time": round(max(generation_times), 3) if generation_times else 0,
    }
    
    print(f"\n\nResults:")
    print(f"  Generated: {len(headers)}/{count}")
    print(f"  Failed: {failed}")
    print(f"  Unique: {unique}/{len(headers)} ({unique/len(headers)*100:.1f}%)" if headers else "  Unique: N/A")
    print(f"  Avg time: {elapsed/count:.2f}s per header")
    print(f"  Time range: {min(generation_times):.2f}s - {max(generation_times):.2f}s" if generation_times else "")
    print(f"  Total time: {elapsed:.1f}s")
    
    # Show first 3 samples
    if headers:
        print(f"\nSample headers:")
        for i, header in enumerate(headers[:3], 1):
            print(f"\n  --- Sample {i} ---")
            for line in header.split('\n')[:7]:  # Show first 7 lines
                print(f"  {line}")
    
    return len(headers) > 0


def test_ai_intro_text(count=10):
    """Test AI-generated intro text"""
    print(f"\n{'='*70}")
    print(f"AI INTRO TEXT GENERATION TEST ({count} samples)")
    print(f"{'='*70}")
    
    intros = []
    failed = 0
    start_time = time.time()
    
    for i in range(count):
        print(f"\rGenerating intro {i+1}/{count}...", end='', flush=True)
        try:
            intro = main.generate_ai_intro_text()
            if intro and len(intro) > 50:
                intros.append(intro)
            else:
                failed += 1
        except Exception as e:
            print(f"\n  Error generating intro {i+1}: {e}")
            failed += 1
    
    elapsed = time.time() - start_time
    unique = len(set(intros))
    
    print(f"\n\nResults:")
    print(f"  Generated: {len(intros)}/{count}")
    print(f"  Failed: {failed}")
    print(f"  Unique: {unique}/{len(intros)} ({unique/len(intros)*100:.1f}%)" if intros else "  Unique: N/A")
    print(f"  Avg length: {sum(len(i) for i in intros)/len(intros):.0f} chars" if intros else "  Avg length: N/A")
    print(f"  Avg time: {elapsed/count:.2f}s per intro")
    print(f"  Total time: {elapsed:.1f}s")
    
    # Show first 3 samples
    if intros:
        print(f"\nSample intro texts:")
        for i, intro in enumerate(intros[:3], 1):
            print(f"\n  --- Sample {i} ---")
            print(f"  {intro}")
    
    return len(intros) > 0


def test_ai_scenarios(count=100):
    """Test AI-generated scenarios with comprehensive analysis"""
    print(f"\n{'='*70}")
    print(f"AI SCENARIO GENERATION TEST ({count} samples)")
    print(f"{'='*70}")
    
    seen = set()
    theme = main.ThemeId.AI_GENERATED
    scenarios = []
    failed = 0
    start_time = time.time()
    
    # Track scenario types
    scenario_types = ["general", "danger", "mystery", "discovery", "encounter"]
    type_counts = {t: 0 for t in scenario_types}
    
    for i in range(count):
        scenario_type = scenario_types[i % len(scenario_types)]
        print(f"\rGenerating scenario {i+1}/{count} ({scenario_type})...", end='', flush=True)
        
        try:
            scenario = main.generate_ai_scenario(theme, scenario_type, seen)
            if scenario and len(scenario) > 20:
                scenarios.append(scenario)
                seen.add(scenario)
                type_counts[scenario_type] += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  Error generating scenario {i+1}: {e}")
            failed += 1
    
    elapsed = time.time() - start_time
    unique = len(set(scenarios))
    
    print(f"\n\nResults:")
    print(f"  Generated: {len(scenarios)}/{count}")
    print(f"  Failed: {failed}")
    print(f"  Unique: {unique}/{len(scenarios)} ({unique/len(scenarios)*100:.1f}%)" if scenarios else "  Unique: N/A")
    print(f"  Avg length: {sum(len(s) for s in scenarios)/len(scenarios):.0f} chars" if scenarios else "  Avg length: N/A")
    print(f"  Min/Max length: {min(len(s) for s in scenarios)} / {max(len(s) for s in scenarios)} chars" if scenarios else "  Min/Max: N/A")
    print(f"  Avg time: {elapsed/count:.2f}s per scenario")
    print(f"  Total time: {elapsed:.1f}s")
    
    # Show distribution by type
    print(f"\n  Scenario type distribution:")
    for stype in scenario_types:
        print(f"    {stype:12s}: {type_counts[stype]:3d} scenarios")
    
    # Show first 10 scenarios
    if scenarios:
        print(f"\nFirst 10 scenarios (truncated to 100 chars):")
        for i, scenario in enumerate(scenarios[:10], 1):
            truncated = scenario[:100] + "..." if len(scenario) > 100 else scenario
            print(f"  {i:2d}. {truncated}")
    
    # Quality checks
    print(f"\nQuality Analysis:")
    if scenarios:
        # Check for templates (static fallbacks)
        template_matches = sum(1 for s in scenarios if 
                              any(template in s for template in [
                                  "Reality shifts around you",
                                  "A presence watches from the shadows",
                                  "Time and space fracture"
                              ]))
        ai_generated = len(scenarios) - template_matches
        print(f"  AI-generated: {ai_generated} ({ai_generated/len(scenarios)*100:.1f}%)")
        print(f"  Template-based: {template_matches} ({template_matches/len(scenarios)*100:.1f}%)")
        
        # Check for variety
        avg_words = sum(len(s.split()) for s in scenarios) / len(scenarios)
        print(f"  Avg words per scenario: {avg_words:.1f}")
        
        # Check for common words (diversity indicator)
        all_words = ' '.join(scenarios).lower().split()
        unique_words = len(set(all_words))
        print(f"  Vocabulary diversity: {unique_words} unique words in {len(all_words)} total")
    
    return len(scenarios) > 0


def run_comprehensive_test():
    """Run all tests in sequence"""
    print(f"\n{'#'*70}")
    print("COMPREHENSIVE AI GENERATION TEST SUITE")
    print(f"{'#'*70}")
    print(f"Host: {OLLAMA_TEST_HOST}:{OLLAMA_TEST_PORT}")
    print(f"Model: {main.SELECTED_AI_MODEL}")
    print(f"Total tests: {NUM_HEADERS + NUM_INTROS + NUM_SCENARIOS}")
    
    total_start = time.time()
    
    # Test 1: Connectivity
    if not test_api_connectivity():
        print("\n✗ API connectivity failed. Aborting tests.")
        return False
    
    # Test 2: Headers
    headers_ok = test_ai_headers(NUM_HEADERS)
    
    # Test 3: Intro text
    intros_ok = test_ai_intro_text(NUM_INTROS)
    
    # Test 4: Scenarios
    scenarios_ok = test_ai_scenarios(NUM_SCENARIOS)
    
    # Final summary
    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"  API Connectivity: {'✓ PASS' if True else '✗ FAIL'}")
    print(f"  Header Generation: {'✓ PASS' if headers_ok else '✗ FAIL'}")
    print(f"  Intro Text Generation: {'✓ PASS' if intros_ok else '✗ FAIL'}")
    print(f"  Scenario Generation: {'✓ PASS' if scenarios_ok else '✗ FAIL'}")
    print(f"\n  Total execution time: {total_elapsed/60:.1f} minutes")
    print(f"  Total generations: {NUM_HEADERS + NUM_INTROS + NUM_SCENARIOS}")
    print(f"  Average time per generation: {total_elapsed/(NUM_HEADERS+NUM_INTROS+NUM_SCENARIOS):.2f}s")
    
    all_passed = headers_ok and intros_ok and scenarios_ok
    print(f"\n{'='*70}")
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print(f"{'='*70}\n")
    
    return all_passed


if __name__ == "__main__":
    # Disable TEST_MODE to enable AI generation
    main.TEST_MODE = False
    main.LOGGING_ENABLED = False
    
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
