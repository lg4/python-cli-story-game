#!/usr/bin/env python3
"""
AI Generation Testing with Comprehensive Logging
=================================================
Runs 100 AI-generated scenarios with full logging enabled for learning analysis.
Saves detailed metrics to logs/ directory for game_tuner.py to analyze.

This test:
1. Enables full GameLogger functionality
2. Generates 100 AI scenarios with detailed metrics
3. Tracks performance, uniqueness, and quality
4. Saves results for automated learning/tuning
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

def main_test():
    """Run comprehensive AI scenario test with logging"""
    
    # Configure Ollama to use remote host
    main.OLLAMA_HOST = OLLAMA_TEST_HOST
    main.OLLAMA_PORT = OLLAMA_TEST_PORT
    main.OLLAMA_URL = f"http://{OLLAMA_TEST_HOST}:{OLLAMA_TEST_PORT}"
    
    # Enable logging (this is the key!)
    main.LOGGING_ENABLED = True
    main.TEST_MODE = False  # Allow AI generation
    
    # Create logger
    session_id = f"ai_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger = main.GameLogger(session_id=session_id)
    main._current_logger = logger  # Make it available globally
    
    print(f"\n{'#'*70}")
    print("AI GENERATION TEST WITH COMPREHENSIVE LOGGING")
    print(f"{'#'*70}")
    print(f"Remote API: http://{OLLAMA_TEST_HOST}:{OLLAMA_TEST_PORT}")
    print(f"Model: {main.SELECTED_AI_MODEL}")
    print(f"Session ID: {session_id}")
    print(f"Log file: logs/game_{session_id}.jsonl")
    print(f"Test scenarios: {NUM_SCENARIOS}")
    print(f"Logging: ENABLED")
    
    # Test API connectivity
    print(f"\n{'='*70}")
    print("Testing API connectivity...")
    print(f"{'='*70}")
    try:
        models = main.query_ollama_models()
        print(f"✓ Connected successfully!")
        print(f"  Available models: {', '.join(m['name'] for m in models[:5])}")
        logger.log_event("ai_test_start", {
            "host": OLLAMA_TEST_HOST,
            "port": OLLAMA_TEST_PORT,
            "model": main.SELECTED_AI_MODEL,
            "num_scenarios": NUM_SCENARIOS,
            "available_models": [m['name'] for m in models]
        })
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        logger.log_event("ai_test_error", {"error": str(e), "stage": "connectivity"})
        return False
    
    # Generate scenarios with comprehensive tracking
    print(f"\n{'='*70}")
    print(f"Generating {NUM_SCENARIOS} AI scenarios...")
    print(f"{'='*70}")
    
    seen = set()
    theme = main.ThemeId.AI_GENERATED
    scenarios = []
    scenario_types = ["general", "danger", "mystery", "discovery", "encounter"]
    
    start_time = time.time()
    generation_times = []
    ai_generated_count = 0
    template_count = 0
    failed_count = 0
    
    for i in range(NUM_SCENARIOS):
        scenario_type = scenario_types[i % len(scenario_types)]
        print(f"\r  Progress: {i+1}/{NUM_SCENARIOS} ({(i+1)/NUM_SCENARIOS*100:.1f}%) - Type: {scenario_type:10s}", end='', flush=True)
        
        gen_start = time.time()
        try:
            scenario = main.generate_ai_scenario(theme, scenario_type, seen)
            gen_time = time.time() - gen_start
            generation_times.append(gen_time)
            
            # Check if AI-generated or template
            is_template = any(template in scenario for template in [
                "Reality shifts around you",
                "A presence watches from the shadows",
                "Time and space fracture",
                "The world glitches",
                "A voice echoes from nowhere"
            ])
            
            if is_template:
                template_count += 1
            else:
                ai_generated_count += 1
            
            scenarios.append(scenario)
            seen.add(scenario)
            
            # Log each scenario generation
            logger.log_event("ai_scenario_generated", {
                "index": i,
                "scenario_type": scenario_type,
                "content": scenario,
                "length": len(scenario),
                "word_count": len(scenario.split()),
                "generation_time": round(gen_time, 3),
                "is_template": is_template,
                "success": True
            })
            
        except Exception as e:
            gen_time = time.time() - gen_start
            failed_count += 1
            logger.log_event("ai_scenario_error", {
                "index": i,
                "scenario_type": scenario_type,
                "error": str(e),
                "generation_time": round(gen_time, 3)
            })
    
    total_time = time.time() - start_time
    unique_count = len(set(scenarios))
    
    # Calculate statistics
    avg_gen_time = sum(generation_times) / len(generation_times) if generation_times else 0
    min_gen_time = min(generation_times) if generation_times else 0
    max_gen_time = max(generation_times) if generation_times else 0
    avg_length = sum(len(s) for s in scenarios) / len(scenarios) if scenarios else 0
    avg_words = sum(len(s.split()) for s in scenarios) / len(scenarios) if scenarios else 0
    
    # Vocabulary diversity
    all_words = ' '.join(scenarios).lower().split()
    unique_words = len(set(all_words))
    
    print(f"\n\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"  Total scenarios: {len(scenarios)}/{NUM_SCENARIOS}")
    print(f"  Unique scenarios: {unique_count} ({unique_count/len(scenarios)*100:.1f}%)" if scenarios else "  Unique: N/A")
    print(f"  AI-generated: {ai_generated_count} ({ai_generated_count/len(scenarios)*100:.1f}%)" if scenarios else "")
    print(f"  Template-based: {template_count} ({template_count/len(scenarios)*100:.1f}%)" if scenarios else "")
    print(f"  Failed: {failed_count}")
    print(f"\n  Generation time:")
    print(f"    Total: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"    Average: {avg_gen_time:.2f}s per scenario")
    print(f"    Min/Max: {min_gen_time:.2f}s / {max_gen_time:.2f}s")
    print(f"    Throughput: {len(scenarios)/total_time:.2f} scenarios/second")
    print(f"\n  Content quality:")
    print(f"    Avg length: {avg_length:.0f} characters")
    print(f"    Avg words: {avg_words:.1f} words")
    print(f"    Vocabulary: {unique_words} unique words in {len(all_words)} total")
    print(f"    Diversity: {unique_words/len(all_words)*100:.1f}%")
    
    # Show first 10 scenarios
    print(f"\n  First 10 scenarios (truncated):")
    for i, scenario in enumerate(scenarios[:10], 1):
        truncated = scenario[:80] + "..." if len(scenario) > 80 else scenario
        marker = "[AI]" if not any(t in scenario for t in ["Reality shifts", "A presence watches", "Time and space"]) else "[TPL]"
        print(f"    {i:2d}. {marker} {truncated}")
    
    # Log final summary
    logger.log_event("ai_test_complete", {
        "total_scenarios": len(scenarios),
        "unique_scenarios": unique_count,
        "uniqueness_rate": round(unique_count/len(scenarios)*100, 2) if scenarios else 0,
        "ai_generated": ai_generated_count,
        "template_based": template_count,
        "failed": failed_count,
        "total_time": round(total_time, 2),
        "avg_gen_time": round(avg_gen_time, 3),
        "min_gen_time": round(min_gen_time, 3),
        "max_gen_time": round(max_gen_time, 3),
        "avg_length": round(avg_length, 1),
        "avg_words": round(avg_words, 1),
        "unique_words": unique_words,
        "total_words": len(all_words),
        "vocabulary_diversity": round(unique_words/len(all_words)*100, 2) if all_words else 0
    })
    
    print(f"\n{'='*70}")
    print(f"✓ Test complete! Logged {len(logger.events)} events")
    print(f"  Log file: {logger.log_file}")
    print(f"\n  Next steps:")
    print(f"    - Run 'python analyze_logs.py --session {session_id}' to analyze")
    print(f"    - Run 'python game_tuner.py' to generate tuning recommendations")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
