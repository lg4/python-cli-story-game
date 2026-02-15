# Terminal Adventure Quest

A text-based interactive story game for the terminal, inspired by classic travel adventures like *The Oregon Trail*. Built with **simple event-driven logic and choice-based gameplay**, the game demonstrates how **GitHub Copilot agent skills** can automatically learn from gameplay logs and improve game balance in real-time.

**Showcase features:**
- **Simple choice-based terminal gameplay** — players make branching decisions at each turn
- **Event-driven logic** — random events trigger based on game state and player choices
- **Comprehensive logging system** — every choice, event, and outcome is captured for analysis
- **GitHub Copilot agent skills** — AI agents can analyze logs, detect balance issues, and automatically adjust game parameters
- **Continuous improvement loop** — game learns and balances itself through data-driven optimization

> **Disclaimer: This project is fictional and AI-generated only.**

---

## Features

| Feature | Details |
|---|---|
| **5 Adventure Themes** | The Desert Caravan · Space Colony Expedition · Lost Kingdom of the Mist · Time-Travel Expedition · Cyberpunk Heist |
| **3 Difficulty Levels** | Easy / Normal / Hard — affects supply amounts, damage taken, and event frequency |
| **Oregon-Trail Travel** | Travel a set distance in daily increments while managing food, water, and fuel |
| **Inventory & Crafting** | 17+ original items; combine pairs into powerful crafted gear |
| **Companion System** | Recruit theme-specific allies (scout, combat, healer, morale, supply) with unique bonuses |
| **Status Effects** | Poisoned, Inspired, Exhausted, Shielded, Lucky — each changes gameplay for several days |
| **Day / Night Cycle** | Four phases (Dawn → Day → Dusk → Night); night increases danger and slows travel |
| **Weather System** | Clear, Rain, Fog, Storm — weather affects travel speed and can trigger events |
| **Branching Choices** | Every decision affects health, morale, supplies, companion interactions, and ending |
| **Riddle Mini-Game** | Solve riddles from sphinx-like figures for rewards or punishment |
| **Dice Gambling** | Wager supplies against traders in a dice game |
| **Milestone Narratives** | Unique story beats at 25%, 50%, and 75% progress for each theme |
| **12 Events** | Bandits, river crossings, storms, wildlife, traders, discoveries, campfire, special items, riddles, companions, elite battles, weather shifts |
| **16 Achievements** | Track accomplishments across categories (combat, exploration, crafting, endings) |
| **5+ Endings** | Death, incomplete, arrived, good arrival, perfect legendary victory |
| **ASCII Art** | 20+ art blocks at key transitions — title, themes, weather, camps, battles, crafting, achievements, and more |
| **Replayability** | Seed system lets you replay the exact same journey or start a fresh random one |
| **Automated Testing** | `--test` and `--test-all` flags for fully automated play-throughs; `test_game.py` with 35+ unit & integration tests |
| **Gameplay Logging** | Comprehensive JSONL logs capture every decision, event, and outcome for analysis and improvement |
| **Auto-Balancing** | `game_tuner.py` learns from logs and automatically adjusts difficulty parameters to fix balance issues |
| **Colour Support** | Optional colour via `colorama`; works fine without it |

---

## How to Play

### Requirements

- **Python 3.10+** (standard library only — no third-party packages required)
- *Optional*: `colorama` for coloured terminal output

### Run the game

```bash
python main.py
```

### Optional: enable colours

```bash
pip install colorama
python main.py
```

### CLI flags

| Flag | Description |
|---|---|
| `--test` | Run one automated play-through (no user input needed) |
| `--test-all` | Run automated tests across all 5 themes × 3 difficulties |
| `--seed N` | Set the random seed (default: 42) |
| `--max-days N` | Cap the game at N days (test mode, default: 200) |
| `--fast` | Disable slow text printing for faster play |
| `--no-log` | Disable gameplay logging |

### Run the test suite

```bash
python test_game.py          # quick — all unit tests
python test_game.py -v       # verbose output
python test_game.py --full   # full integration tests
```

### Gameplay tips

1. **Choose a theme** — each has unique flavour text, supply names, a special item, and companions.
2. **Pick a difficulty** — Easy gives generous supplies; Hard is brutal.
3. **Travel forward** each day to cover the required distance (2 000 units).
4. **Manage supplies** — food and water drop daily; fuel drops when you travel.
5. **Watch the clock** — night travel is slower and more dangerous without a light source.
6. **Check the weather** — storms reduce travel distance; rain in the desert is a blessing.
7. **Random events** present branching choices that affect your stats.
8. **Trade with merchants** or gamble at the dice table for supplies.
9. **Solve riddles** for bonus items and morale.
10. **Recruit a companion** — they provide ongoing bonuses to combat, scouting, healing, morale, or supplies.
11. **Craft items** — combine pairs of items into powerful crafted gear (e.g., Healer's Salve + Morale Charm = Elixir of Vitality).
12. **Find the theme's special item** — it helps at the final encounter.
13. **Collect a Signal-Flare** (or craft a Beacon Array) for the best ending.
14. **Rest** when health is low; **scout** to trigger events on your terms.
15. At the end you can **replay with the same seed** to try different choices.

---

## Gameplay Analysis & Logging

Every game session is automatically logged to `logs/game_YYYYMMDD_HHMMSS.jsonl` in JSON Lines format. These logs capture:

- Player state snapshots (health, supplies, inventory, effects)
- Every choice made (travel, rest, combat, etc.)
- Random event triggers and outcomes
- Deaths (cause, day, distance progress)
- Victories (ending type, final stats)
- Achievement unlocks
- Penalties applied

### Analyze your gameplay

Use the included log analyzer to learn from your games:

```bash
python analyze_logs.py              # Analyze all sessions
python analyze_logs.py --stats      # Overall statistics
python analyze_logs.py --deaths     # Death pattern analysis
python analyze_logs.py --balance    # Check game balance issues
```

**What the analyzer shows:**

- **Win rate** by theme and difficulty
- **Death causes** and when players typically die
- **Average survival** metrics (days, distance %)
- **Balance issues** (themes too hard/easy, difficulty scaling problems)
- **Early death warnings** (flagged if players die before 20% completion)
- **Achievement unlock rates**

### Use logs to improve the game

The logs help you:

1. **Identify balance issues** — if a theme has < 20% win rate, it may be too hard
2. **Find death hotspots** — if most deaths happen on Day 5-10, early game needs adjustment
3. **Test difficulty scaling** — Hard should be harder than Easy (logs verify this)
4. **Track engagement** — see how many choices players make, which events trigger most
5. **Optimize random events** — if certain events never appear, adjust their weights

### Disable logging

```bash
python main.py --no-log   # Play without creating log files
```

---

## Automatic Game Balancing (Learning from Logs)

The game includes an **intelligent tuning system** that learns from gameplay logs and automatically adjusts difficulty parameters to improve balance.

### How it works

1. **Play games** → logs are written to `logs/`  
2. **Run the tuner** → analyzes aggregate data and detects patterns  
3. **Apply adjustments** → generates `game_tuning.json` with recommended changes  
4. **Next playthrough** → game automatically loads tuning config and applies adjustments

### Run the auto-tuner

```bash
python game_tuner.py                    # Analyze and show recommendations
python game_tuner.py --apply            # Generate tuning config file
python game_tuner.py --min-sessions 10  # Require more data before tuning
python game_tuner.py --reset            # Remove tuning and reset to defaults
```

### What gets auto-tuned

The tuner detects and fixes these balance issues:

| Issue Detected | Auto-Adjustment Applied |
|---|---|
| **Theme too hard** (< 25% win rate) | Increase starting supplies by 30% |
| **Theme too easy** (> 75% win rate) | Reduce starting supplies by 20% |
| **Difficulty scaling broken** | Adjust difficulty multipliers |
| **Starvation kills > 50%** | Reduce food consumption by 15% |
| **Dehydration kills > 50%** | Reduce water consumption by 15% |
| **Combat kills > 50%** | Reduce combat damage by 10% |
| **Early deaths** (< 20% progress) | Flag for manual review |
| **Events never trigger** | Recommend weight adjustment |

### Example tuning session

```bash
# Play 10 games
python main.py --test-all

# Analyze and apply tuning
python game_tuner.py --apply

# Example output:
# 📊 Theme 'The Desert Caravan': 15.0% win rate (too hard)
#    → Increase starting supplies by 30%
# ⚠️  50% of deaths from dehydration
#    → Reduce water consumption by 15%
# ✅ Tuning config saved to: game_tuning.json

# Next game will automatically use these adjusted values
python main.py
```

### The learning loop

```
┌─────────────┐
│  Play Game  │  → Logs written to logs/
└──────┬──────┘
       ↓
┌─────────────┐
│  Analyze    │  → game_tuner.py detects patterns
└──────┬──────┘
       ↓
┌─────────────┐
│   Tune      │  → game_tuning.json generated
└──────┬──────┘
       ↓
┌─────────────┐
│  Play Game  │  → Adjusted parameters loaded
└─────────────┘  → Better balanced experience
       ↑               ↓
       └───────────────┘
```

This creates a **continuous improvement cycle** where the game gets better balanced over time based on real gameplay data.

---

## Project Structure

```
python-cli-story-game/
├── main.py                          # Complete game script (single file, no dependencies)
├── test_game.py                     # Automated test suite (unittest)
├── analyze_logs.py                  # Log analyzer for gameplay insights
├── game_tuner.py                    # Automatic game balancing (learns from logs)
├── logs/                            # Gameplay logs directory (auto-created)
├── game_tuning.json                 # Auto-tuning config (created by game_tuner.py)
├── .github/
│   └── skills/
│       └── game-improvement/        # GitHub Copilot Agent Skill
│           └── SKILL.md             # Skill definition for AI agents
└── README.md                        # This file
```

---

## GitHub Copilot Agent Skills

This project includes a **GitHub Copilot agent skill** (`.github/skills/game-improvement/SKILL.md`) that enables AI agents to automatically improve the game.

### What the skill enables

The **game-improvement agent skill** allows Copilot agents to:

- **Analyze gameplay logs** — understand player behavior and identify patterns
- **Detect balance issues** — find themes that are too hard/easy or mechanics that are broken
- **Automatically tune parameters** — generate `game_tuning.json` with intelligent adjustments
- **Debug crashes** — find and fix errors by analyzing error logs and tracebacks
- **Verify improvements** — run tests and validate that changes improve balance
- **Optimize engagement** — suggest event frequency, difficulty scaling, and progression pacing improvements

### How agents use this skill

```bash
# An agent can run these commands to improve the game:

# 1. Collect gameplay data
python main.py --test-all

# 2. Analyze and identify issues
python analyze_logs.py --balance
python analyze_logs.py --errors

# 3. Auto-generate fixes
python game_tuner.py --apply

# 4. Verify improvements
python main.py --test-all
python analyze_logs.py --stats
```

### Agent workflows

The skill includes predefined workflows for common improvement tasks:

| Task | Workflow | Commands |
|------|----------|----------|
| **Balance a theme** | Collect → Analyze → Tune → Test → Verify | analyze_logs.py --balance → game_tuner.py --apply |
| **Debug a crash** | Find error → Extract context → Fix code → Test | analyze_logs.py --errors → test_game.py |
| **Improve engagement** | Analyze patterns → Adjust events → Test balance | analyze_logs.py --stats → modify game → test |
| **Test new features** | Baseline metrics → Add feature → Compare → Balance | analyze_logs.py → code changes → game_tuner.py |

### Using the skill with Copilot

The skill is automatically discoverable by GitHub Copilot agents in conversations about:
- Game balance and difficulty
- Crash debugging and error handling
- Player engagement and progression
- Automated testing and parameter tuning

Simply mention game improvement, balance issues, or ask an agent to "improve the game" and Copilot can apply the **game-improvement** skill.

### Skill highlights

- **905 lines** of detailed AI guidance
- **Data-driven approach** — all decisions based on gameplay metrics
- **Automated workflows** — complete procedures for common tasks
- **Error handling** — comprehensive debugging procedures with examples
- **Integration checklist** — ensures new features support auto-tuning
- **Decision trees** — guidance for different scenarios and issues

For full details, see [.github/skills/game-improvement/SKILL.md](.github/skills/game-improvement/SKILL.md).

---

## Extending the Game

- **Add a new theme**: create a new `ThemeId` enum value and register a `Theme` in `_register_themes()`. Add companions in `COMPANION_POOL` and milestone narratives in `MILESTONE_NARRATIVES`.
- **Add events**: write a function `_event_xxx(player: Player)` and add it to `EVENT_POOL` with a weight.
- **Add items**: insert entries into `ITEM_CATALOGUE` and optionally into the `use_item()` consumables dict.
- **Add crafting recipes**: append to `CRAFT_RECIPES` with `(ingredient_a, ingredient_b, result, description)`.
- **Add achievements**: add entries in `_make_achievements()` and call `player.try_unlock("id")` at the appropriate moment.
- **Add riddles**: append `(question, [options], correct_index)` tuples to `RIDDLES`.
- **ASCII art**: replace or add triple-quoted raw strings in the ASCII Art section.
- **Seeded runs**: use `--seed N` on the command line for reproducible runs.

---

## License

MIT — feel free to modify, extend, and redistribute.

> **Disclaimer: This project is fictional and AI-generated only.**
