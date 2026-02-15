---
name: game-improvement
description: Comprehensive game improvement system using gameplay logs, analytics, and automatic balancing. Analyzes player data to identify balance issues, fix difficulty scaling, and improve game design. Keywords: logs analysis, game balance, difficulty tuning, crash debugging, player patterns, auto-tuning, error detection, win rate optimization.
---

# Game Improvement Agent Skill

This skill provides a complete data-driven system for improving game balance, debugging crashes, and optimizing player experience through automated log analysis and intelligent parameter tuning.

## Agent Role & Capabilities

As a **game balance engineer agent**, you have access to:
- Comprehensive gameplay logs (`logs/game_*.jsonl`)
- Log analysis tool (`analyze_logs.py`)
- Automatic tuning system (`game_tuner.py`)
- Game source code (`main.py`, `test_game.py`)
- Error tracking with full tracebacks
- Statistical analysis for balance optimization

---

## System Overview

The game implements a **continuous improvement feedback loop**:

```
Play → Log → Analyze → Tune → Apply → Repeat
  ↑                                      ↓
  └──────────────────────────────────────┘
         (Game improves automatically)
```

### What Gets Logged

Every game session creates `logs/game_YYYYMMDD_HHMMSS.jsonl` capturing:
- **Player state snapshots** (health, supplies, inventory, status effects, achievements)
- **Player choices** (travel, rest, scout, craft, combat decisions)
- **Random events** (triggers, outcomes, rewards/penalties)
- **Deaths** (cause, day, distance progress %, final stats)
- **Victories** (ending type, achievements unlocked)
- **Errors** (invalid inputs, exceptions with full tracebacks)
- **Penalties** (starvation, dehydration, low morale)

### Logging API
```python
GAME_LOGGER.log_event(event_type, data)       # Generic event
GAME_LOGGER.log_player_state(player, label)   # State snapshot
GAME_LOGGER.log_choice(prompt, choice, ctx)   # Player decision
GAME_LOGGER.log_death(cause, player)          # Death context
GAME_LOGGER.log_error(type, msg, ctx)         # Error
GAME_LOGGER.log_exception(exc, ctx)           # Exception with traceback
```

---

## Agent Commands & Tools

### Data Collection
```bash
python main.py                              # Interactive play
python main.py --test --fast                # Quick automated test
python main.py --test-all                   # Test all themes × difficulties
python main.py --seed N                     # Reproducible game
python main.py --no-log                     # Disable logging
```

### Analysis
```bash
python analyze_logs.py                      # Full analysis (all sections)
python analyze_logs.py --stats              # Win rates, error counts
python analyze_logs.py --balance            # Theme/difficulty balance check
python analyze_logs.py --deaths             # Death pattern analysis
python analyze_logs.py --errors             # Crash/exception debugging
```

### Auto-Tuning
```bash
python game_tuner.py                        # Show recommendations
python game_tuner.py --apply                # Generate game_tuning.json
python game_tuner.py --min-sessions N       # Require more data (default: 5)
python game_tuner.py --reset                # Remove tuning, reset defaults
```

### Testing
```bash
python test_game.py                         # Unit tests (52 tests)
python test_game.py -v                      # Verbose output
python test_game.py --full                  # Integration tests
```

---

## Agent Workflows

### Workflow 1: Balance Issue ("Theme X is too hard")

**Symptoms:** Players report they can't win on a specific theme.

**Agent Actions:**
1. **Collect data:**
   ```bash
   # Play 10+ games on the problematic theme
   for i in {1..10}; do python main.py --test --seed $i; done
   ```

2. **Analyze:**
   ```bash
   python analyze_logs.py --balance
   ```
   **Look for:**
   - Win rate < 25% (too hard)
   - Win rate > 75% (too easy)
   - Death clustering at specific days

3. **Auto-tune:**
   ```bash
   python game_tuner.py --apply
   ```
   **Expected output:**
   ```
   📊 Theme 'Desert Caravan': 0% win rate → +30% supplies
   ⚠️  71% deaths from starvation → -15% food consumption
   ```

4. **Test improvement:**
   ```bash
   python main.py --test --seed 999
   ```

5. **Verify:**
   ```bash
   python analyze_logs.py --stats
   # Check: Win rate should increase to 30-50%
   ```

**Manual adjustments if auto-tune insufficient:**
- Increase theme starting supplies in `_register_themes()`
- Add theme-specific items/companions
- Adjust daily consumption rates in `DIFFICULTY_SETTINGS`

---

### Workflow 2: Crash Debug ("Game crashed")

**Symptoms:** Game exits with error code 1, player loses progress.

**Agent Actions:**
1. **Get crash details:**
   ```bash
   python analyze_logs.py --errors
   ```
   **Extract:**
   - Error type (ValueError, KeyError, etc.)
   - Error message
   - Context (day, action, prompt)
   - Full traceback

2. **Example output:**
   ```
   Critical Errors: 1
     Type: ValueError
     Message: invalid literal for int(): 'abc'
     Context: {"prompt": "daily_action", "day": 8}
     Traceback:
       File "main.py", line 1234, in get_choice
         num = int(line)
   ```

3. **Locate bug:**
   - Check code at traceback location
   - Identify missing validation
   - Find edge case not handled

4. **Fix:** Add input validation or error handling:
   ```python
   def get_choice(prompt, valid_range, retries=3):
       for attempt in range(retries):
           try:
               line = input(prompt).strip()
               if line.isdigit():
                   num = int(line)
                   if num in valid_range:
                       return str(num)
               # Log invalid input
               if GAME_LOGGER:
                   GAME_LOGGER.log_error("InvalidInput", 
                       f"Invalid: '{line}'", 
                       {"prompt": prompt, "attempt": attempt})
           except Exception as e:
               if GAME_LOGGER:
                   GAME_LOGGER.log_exception(e, {"prompt": prompt})
   ```

5. **Test fix:**
   ```bash
   python test_game.py
   python main.py --test
   ```

---

### Workflow 3: Engagement Analysis ("How are players doing?")

**Symptoms:** Want to understand player behavior and engagement.

**Agent Actions:**
1. **Run full analysis:**
   ```bash
   python analyze_logs.py --stats
   ```

2. **Check key metrics:**
   - **Win rate:** 40-60% is ideal
   - **Avg survival days:** 40-80 is good pacing
   - **Achievement rate:** Target 3+ per session
   - **Error rate:** Should be < 5%

3. **Identify issues:**
   - Low achievement rate → events too rare
   - High error rate → bugs blocking gameplay
   - Low win rate → too punishing
   - Players quit early → boring start

4. **Death analysis:**
   ```bash
   python analyze_logs.py --deaths
   ```
   **Look for:**
   - Single cause > 50% (one mechanic broken)
   - Early deaths < 20% progress (intro too hard)
   - Late deaths > 80% progress (finale too hard)

5. **Propose improvements:**
   - Add more varied events
   - Adjust early game difficulty
   - Increase reward frequency
   - Fix blocking bugs

---

### Workflow 4: Feature Testing ("Does my change break anything?")

**Symptoms:** New feature added, need to verify it doesn't break balance.

**Agent Actions:**
1. **Baseline (before change):**
   ```bash
   python main.py --test-all
   python analyze_logs.py --all
   # Save metrics: win rates, avg survival, error count
   ```

2. **Apply change:**
   - Modify game code
   - Add logging for new feature
   - Update tests if needed

3. **Test (after change):**
   ```bash
   python test_game.py              # Unit tests pass?
   python main.py --test-all        # Integration works?
   python analyze_logs.py --all     # Balance maintained?
   ```

4. **Compare metrics:**
   - **Win rates unchanged:** ✅ Good
   - **Win rates ±5%:** ✅ Acceptable
   - **Win rates ±20%:** ❌ Rebalance needed
   - **New errors:** ❌ Fix bugs first

5. **Decision:**
   - If balanced → merge
   - If imbalanced → apply auto-tune or manual tweak
   - If buggy → debug and fix

---

## Auto-Tuning System

The tuner detects patterns and generates `game_tuning.json` with parameter adjustments.

### Detection Rules

| Pattern | Adjustment Applied |
|---------|-------------------|
| Win rate < 25% | `theme_X_supply_multiplier: 1.3` (+30% supplies) |
| Win rate > 75% | `theme_X_supply_multiplier: 0.8` (-20% supplies) |
| >50% starvation deaths | `food_consumption_rate: 0.85` (-15%) |
| >50% dehydration deaths | `water_consumption_rate: 0.85` (-15%) |
| >50% combat deaths | `combat_damage_multiplier: 0.9` (-10%) |
| Easy < 50% win rate | `global_easy_boost: 1.2` (+20% easy supplies) |
| Normal < 35% win rate | `difficulty_normal_multiplier: 1.15` (+15%) |

### Tuning Config Structure
```json
{
  "version": "1.0",
  "generated": "2026-02-14",
  "note": "Auto-generated by game_tuner.py",
  "adjustments": {
    "theme_The Desert Caravan_supply_multiplier": 1.3,
    "food_consumption_rate": 0.85,
    "difficulty_normal_multiplier": 1.15
  }
}
```

### How Game Loads Tuning
```python
# In Player.__post_init__()
load_tuning_config()
mult = DIFFICULTY_SETTINGS[difficulty]["supply_mult"]
mult *= get_tuned_value(f"theme_{theme.name}_supply_multiplier", 1.0)
mult *= get_tuned_value("global_easy_boost", 1.0)  # If easy mode
supplies = {k: int(v * mult) for k, v in starting_supplies.items()}
```

---

## Key Metrics & Targets

### Balance Health
- **Win Rate per Theme:** 40-60% (35-50% if normal, 50-65% if easy, 20-35% if hard)
- **Death Distribution:** No single cause > 50%
- **Avg Survival:** 40-80 days (30-50 for hard, 50-80 for easy)

### Engagement
- **Choices per Session:** Higher = more interactive (target: 80+)
- **Achievement Unlock Rate:** Target 3+ per session
- **Event Variety:** Each event type 5-15% of total

### Quality
- **Error Rate:** < 5% of sessions
- **Invalid Input Rate:** Should decrease over time
- **Crash-Free Rate:** > 95%

---

## Manual Improvements

Beyond auto-tuning, agents can make manual code improvements:

### 1. Event Balance

If certain events never trigger or dominate:

```python
# In main.py EVENT_POOL
EVENT_POOL = [
    (_event_storm, 8),      # Reduced from 12 (too common)
    (_event_trader, 10),    # Increased from 6 (too rare)
    (_event_riddle, 8),     # Balanced
]
```

### 2. Difficulty Scaling

If Easy doesn't feel easier than Hard:

```python
# In main.py DIFFICULTY_SETTINGS
DIFFICULTY_SETTINGS = {
    Difficulty.EASY: {
        "supply_mult": 1.5,      # Increase if too hard
        "damage_mult": 0.5,      # Reduce if dying too much
        "daily_consume": 0.7,    # Lower = less punishing
    },
    Difficulty.HARD: {
        "supply_mult": 0.65,     # Decrease if too easy
        "damage_mult": 1.5,      # Increase for challenge
        "daily_consume": 1.3,    # Higher = more punishing
    },
}
```

### 3. Theme-Specific Fixes

If one theme is much harder than others:

```python
# In _register_themes()
THEMES[ThemeId.DESERT] = Theme(
    starting_supplies={"food": 70, "water": 85, "fuel": 50},  # Increased
    daily_distance=(20, 50),  # Increased max for faster completion
    # Add theme-specific beneficial companion
)
```

### 4. Add Logging to New Features

When adding features, always add logging:

```python
def new_feature(player):
    # ... feature code ...
    
    # Log the feature usage
    if GAME_LOGGER:
        GAME_LOGGER.log_event("feature_used", {
            "feature": "new_feature",
            "outcome": outcome,
            "player_day": player.days,
        })
    
    # Log choices made
    choice = get_choice("What to do? ", range(1, 4))
    if GAME_LOGGER:
        GAME_LOGGER.log_choice("new_feature", choice, {"day": player.days})
```

---

## Agent Decision Trees

### When User Reports: "Game is broken"

```
Is there data (5+ sessions)?
├─ No  → Collect: python main.py --test-all
└─ Yes → Analyze: python analyze_logs.py

What's the issue?
├─ Can't win (low win rate)
│  └─ Auto-tune: python game_tuner.py --apply
├─ Crashes (errors logged)
│  └─ Debug: python analyze_logs.py --errors → fix code
├─ Too easy (high win rate)
│  └─ Auto-tune or manual difficulty increase
└─ Boring (low engagement)
   └─ Analyze deaths, add variety to events
```

### When User Asks: "Is this balanced?"

```
Check win rate:
├─ 40-60% → ✅ Balanced
├─ 30-40% → ⚠️  Slightly hard (acceptable for Normal)
├─ < 30%  → ❌ Too hard, needs tuning
└─ > 70%  → ❌ Too easy, needs tuning

Check death distribution:
├─ Varied (no cause > 40%) → ✅ Healthy
└─ Dominated (one cause > 50%) → ❌ Fix that mechanic

Check error rate:
├─ < 5%  → ✅ Stable
└─ > 10% → ❌ Fix bugs first
```

---

## Code Patterns to Recognize

### Supporting Auto-Tuning in New Features

```python
# Bad: Hard-coded value
damage = 10

# Good: Supports tuning
base_damage = 10
mult = get_tuned_value("new_feature_damage_mult", 1.0)
damage = int(base_damage * mult)
```

### Error Handling

```python
# Add error logging to all try/except blocks
try:
    result = risky_operation()
except ValueError as e:
    if GAME_LOGGER:
        GAME_LOGGER.log_exception(e, {"context": "operation_name"})
    # Handle error gracefully
```

---

## Agent Red Flags

**Stop and warn user if:**

❌ **< 5 sessions** → "Need more data for analysis"
❌ **10+ changes at once** → "Change one thing at a time"
❌ **Error rate > 20%** → "Fix critical bugs before tuning balance"
❌ **Auto-tune has no effect** → "Need manual investigation of root cause"
❌ **Conflicting adjustments** → "Manual review required"

---

## Success Criteria

Agent improvements are successful when:

✅ **Balance:** Win rates 40-60% across themes/difficulties
✅ **Stability:** Error rate < 5%
✅ **Engagement:** 3+ achievements/session, varied events
✅ **Progression:** Players survive 40-80 days average
✅ **Quality:** No repeated crashes, all errors logged

---

## Integration Checklist

When adding features, ensure:

- [ ] New events have logging (`GAME_LOGGER.log_event()`)
- [ ] New parameters support tuning (`get_tuned_value()`)
- [ ] Errors are caught and logged
- [ ] Unit tests updated (`test_game.py`)
- [ ] Integration tests pass (`python test_game.py --full`)
- [ ] Auto-tuner can optimize new parameters

---

## Example: Complete Improvement Cycle

**Goal:** Fix "Desert Caravan has 0% win rate"

```bash
# 1. Collect 10 games
for i in {1..10}; do python main.py --test --seed $i; done

# 2. Analyze
python analyze_logs.py --balance
# Output: "Desert Caravan: 0% win → Too Hard"
# Output: "71% deaths from starvation"

# 3. Auto-tune
python game_tuner.py --apply
# Generated adjustments:
#   theme_Desert Caravan_supply_multiplier: 1.3
#   food_consumption_rate: 0.85

# 4. Test
python main.py --test --seed 999

# 5. Verify improvement
python analyze_logs.py --stats
# New win rate: 35% (much better!)

# 6. If still too hard, manual tweak:
# Edit main.py THEMES[ThemeId.DESERT]
#   starting_supplies={"food": 75, "water": 90, ...}

# 7. Re-test
python main.py --test-all

# 8. Final verification
python analyze_logs.py --balance
# Target: 40-50% win rate ✅
```

---

## Resources

- **Logs:** `logs/` (JSON Lines format)
- **Analysis:** `analyze_logs.py` with `--stats`, `--balance`, `--deaths`, `--errors`
- **Tuning:** `game_tuner.py` with `--apply`, `--reset`
- **Config:** `game_tuning.json` (auto-generated)
- **Tests:** `test_game.py` (52 unit tests)
- **Code:** `main.py` (logging system), `game_tuner.py` (tuning logic)

---

## Agent Usage Summary

**When to use this skill:**
1. Balancing difficulty
2. Debugging crashes
3. Understanding player behavior
4. Improving engagement
5. Automating improvements
6. Testing new features
7. Tracking progress

**Agent capabilities:**
- Run analysis commands
- Interpret metrics
- Apply auto-tuning
- Propose manual fixes
- Test improvements
- Verify balance

**Agent limitations:**
- Need 5+ sessions for statistical significance
- Can't judge "fun factor" (subjective)
- Auto-tune may not fix all issues (manual tweaks needed)
- Must test after changes to verify improvement

### 2. Log Analysis (`analyze_logs.py`)

Analyzes gameplay logs to identify patterns and issues.

**Commands:**
```bash
python analyze_logs.py              # Full analysis (all sections)
python analyze_logs.py --stats      # Overall statistics
python analyze_logs.py --deaths     # Death pattern analysis
python analyze_logs.py --errors     # Error and crash analysis
python analyze_logs.py --balance    # Game balance check
```

**What each shows:**

| Command | Analysis |
|---------|----------|
| `--stats` | Win rates, avg survival, error count, achievement rates |
| `--deaths` | Death causes, early/late deaths, patterns by difficulty |
| `--errors` | Crash types, invalid inputs, exceptions with tracebacks |
| `--balance` | Themes too hard/easy, difficulty scaling, progression pacing |

**Example output:**
```
Win Rate by Theme:
  The Desert Caravan:    0.0% - Too Hard  ← Needs +30% supplies
  Space Colony:         10.0% - Too Hard
  Mist Kingdom:         45.0% - Balanced

Deaths:
  Starvation: 71%  ← Food consumption too high
  Combat: 20%
  Dehydration: 9%

Errors:
  InvalidInput:    12  ← Bad input validation
  UserInterrupt:    3  ← Ctrl+C handling
```

---

### 3. Automatic Game Tuner (`game_tuner.py`)

Analyzes logs and **auto-generates tuning recommendations** that the game loads on startup.

**Commands:**
```bash
python game_tuner.py                    # Show recommendations
python game_tuner.py --apply            # Generate game_tuning.json
python game_tuner.py --min-sessions 10  # Require more data
python game_tuner.py --reset            # Remove tuning, reset to default
```

**What it auto-detects:**

| Pattern | Fix Applied |
|---------|------------|
| Win rate < 25% | +30% starting supplies |
| Win rate > 75% | -20% starting supplies |
| 50%+ starvation deaths | -15% food consumption |
| 50%+ dehydration deaths | -15% water consumption |
| 50%+ combat deaths | -10% combat damage |
| Easy mode win rate < 50% | +20% easy supplies |

**Generated config** (`game_tuning.json`):
```json
{
  "adjustments": {
    "theme_The Desert Caravan_supply_multiplier": 1.3,
    "food_consumption_rate": 0.85,
    "difficulty_normal_multiplier": 1.15
  }
}
```

Game loads this automatically → adjustments applied to gameplay.

---

## The Learning Loop

```
Play Games         Logs to logs/
    ↓
Analyze Logs       Identify patterns
    ↓
Auto-Tune          Generate game_tuning.json
    ↓
Apply Tuning       Load on game startup
    ↓
Repeat             Game improves iteratively
```

---

## Usage Workflow

### Step 1: Collect Data

Play multiple games to gather statistics:
```bash
# Play interactively
python main.py

# Or auto-play for faster testing
python main.py --test --fast
python main.py --test-all  # Test all themes
```

### Step 2: Analyze Issues

Identify what's wrong:
```bash
python analyze_logs.py --balance   # What's too hard/easy?
python analyze_logs.py --deaths    # Why do players die?
python analyze_logs.py --errors    # What crashes occur?
```

### Step 3: Apply Automatic Tuning

Generate and apply recommended fixes:
```bash
python game_tuner.py --apply
# Creates game_tuning.json with recommended adjustments
```

### Step 4: Test Improvements

Play again with adjustments active:
```bash
python main.py  # Game automatically loads game_tuning.json
```

### Step 5: Iterate

Analyze again to see if balance improved:
```bash
python analyze_logs.py --stats
# Check: Is win rate closer to target (40-50%)?
```

---

## Real-World Example

**Problem:** "Desert Caravan has 0% win rate (players can't win)"

**Steps:**

```bash
# 1. Play 10 test games
for i in {1..10}; do python main.py --test; done

# 2. Analyze what's wrong
python analyze_logs.py --balance
# Output: "Desert Caravan: 0% win rate → Too Hard"
# Output: "71% of deaths from starvation"

# 3. Auto-generate fixes
python game_tuner.py --apply
# Creates game_tuning.json:
#   theme_The Desert Caravan_supply_multiplier: 1.3
#   food_consumption_rate: 0.85

# 4. Test with adjustments
python main.py --test --max-days 50

# 5. Verify improvement
python analyze_logs.py --stats
# New win rate should be 30-50% (much better!)
```

---

## Key Metrics to Track

### Balance Health

- **Win Rate** (target: 40-60% per theme/difficulty)
- **Average Survival Days** (target: 40-80 days)
- **Death Distribution** (no single cause > 50%)

### Engagement

- **Avg Choices/Session** (higher = more interaction)
- **Achievement Rate** (target: 3+ per session)
- **Event Variety** (each event 5-15% of total)

### Quality

- **Error Rate** (target: < 5%)
- **Invalid Input Rate** (should decrease iteratively)
- **Crash-Free Rate** (target: 95%+)

---

## Manual Improvements Beyond Auto-Tuning

### 1. Event Balance

**Check:** Which events trigger most/least?
```bash
python analyze_logs.py  # See "Event Types"
```

**Improve:** Adjust weights in EVENT_POOL
```python
EVENT_POOL = [
    (_event_storm, 8),    # Was 12, too common
    (_event_trader, 10),  # Increase from 6
    (_event_bandit, 8),   # Keep balanced
]
```

### 2. Theme-Specific Design

**Check:** Is one theme significantly harder?

**Improve:** Add theme-specific compensations:
- More favorable companion options
- Better starting items
- More forgiving milestone narratives
- Increased travel distance per day

### 3. Difficulty Scaling

**Check:** Does Easy feel easier than Normal?

**Improve:** Verify DIFFICULTY_SETTINGS:
```python
DIFFICULTY_SETTINGS: dict = {
    Difficulty.EASY: {"supply_mult": 1.5, "damage_mult": 0.5, ...},
    Difficulty.NORMAL: {"supply_mult": 1.0, "damage_mult": 1.0, ...},
    Difficulty.HARD: {"supply_mult": 0.65, "damage_mult": 1.5, ...},
}
```

### 4. Error Handling

**Check:** Common invalid inputs from logs
```bash
python analyze_logs.py --errors
```

**Improve:** Override `get_choice()` with better validation:
```python
def get_choice(prompt, valid_range, retries=3):
    # Max 3 invalid attempts before defaulting
    # Log each invalid input for analysis
    # Provide helpful error messages
```

---

## Best Practices

### Do ✅
- ✅ Collect 10+ sessions before analyzing
- ✅ Test ALL themes and difficulties
- ✅ Check error logs for crashes first
- ✅ Review auto-tuning before applying
- ✅ Track metrics over time
- ✅ Reset tuning between major changes

### Don't ❌
- ❌ Tune on < 5 sessions (insufficient data)
- ❌ Blindly apply all auto-tuning suggestions
- ❌ Ignore error logs and crashes
- ❌ Make 10 changes at once (can't isolate what worked)
- ❌ Mark game as "balanced" without play-testing

---

## GitHub Copilot Integration

When improving the game, use Copilot with clear directives:

**For balance issues:**
> "The logs show Desert Caravan has 0% win rate. Auto-tuner recommends +30% supplies. Update the theme to have more forgiving starting inventory and reduce food consumption by 15%."

**For crash debugging:**
> "Error logs show 5 InvalidInput crashes on day 8. Add validation in get_choice() to retry up to 3 times before defaulting. Log each invalid attempt."

**For feature design:**
> "71% of deaths are starvation. What new item, companion skill, or event would help players manage food better? Design something thematic for the Desert Caravan."

**For testing:**
> "Generate 15 automated test games across all themes/difficulties. After each 5 games, run auto-tuner and re-test. Show before/after win rate statistics."

---

## Resources

- **Logs:** `logs/` directory (JSON Lines format)
- **Analysis:** `python analyze_logs.py --help`
- **Tuning:** `python game_tuner.py --help`
- **Config:** `game_tuning.json` (auto-generated)
- **Code:** Main logging in `main.py`, analysis in `analyze_logs.py`

## When to Use This Skill

Use the game improvement skill when:

1. **Balancing difficulty** — "My game is too hard, how do I fix it?"
2. **Debugging crashes** — "The game crashed, what went wrong?"
3. **Understanding player behavior** — "What do players do most? What kills them?"
4. **Improving engagement** — "Are players having fun? What keeps them playing?"
5. **Automating improvement** — "Can the game learn and improve itself?"
6. **Testing new features** — "Did my change break anything?"
7. **Tracking progress** — "Is the game more balanced than last week?"

This skill provides the analysis, tuning, and debugging infrastructure to answer all these questions with data.
