# Terminal Adventure Quest

A text-based survival game featuring **choice-based gameplay, automatic game balancing, and GitHub Copilot agent skills**.

**Key features:**
- 🎮 **5 themes** (Desert, Space, Mist, Time, Cyberpunk) with branching choices and consequences
- 📊 **Auto-balancing system** — game learns from logs and tunes itself for better balance
- 🧠 **GitHub Copilot agent skills** — AI agents can analyze logs, detect issues, and improve gameplay
- 📈 **Comprehensive logging** — every decision and outcome is captured for analysis
- 🏆 **Survival mechanics** — manage supplies, health, companions, and inventory as you travel 2000 units
- 🎯 **Multiple endings** — victory, survival, death, and legendary achievements based on your choices

> **Note:** This project is AI-generated and fictional. It's a showcase for GitHub Copilot agent skills and automated game balancing.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Optional: `pip install colorama` for colors

### Play the game

```bash
python main.py          # Start a new game
python main.py --test   # Run automated test
```

**Gameplay tips:**
1. Choose your theme and difficulty
2. Each day: travel forward, rest, scout, manage supplies
3. Make choices during random events (combat, trading, discovery)
4. Manage food, water, and fuel to reach 2000 units
5. Recruit companions and craft items for bonuses
6. Survive or find the legendary ending!

### CLI flags

```bash
python main.py --tune           # Auto-tune (54 tests + analysis + cleanup)
python main.py --test-all       # Test all themes (54 automated games)
python main.py --seed 12345     # Replay with same seed
python main.py --fast           # Skip text animations
python main.py --no-log         # Don't create logs
```

---

## Game Features

| Feature | Details |
|---------|---------|
| **5 Themes** | Desert, Space, Mist, Time, Cyberpunk — each with unique items, companions, and narratives |
| **3 Difficulties** | Easy (generous), Normal (balanced), Hard (punishing) |
| **Survival Mechanics** | Travel-based progression, supply management, health/morale tracking |
| **Companion System** | Recruit allies for bonuses: scout, combat, healing, morale, supplies |
| **Inventory & Crafting** | 17+ items; combine pairs into powerful gear |
| **12 Event Types** | Combat, storms, discovery, trading, riddles, wildlife, and more |
| **Day/Night Cycle** | 4 phases (Dawn/Day/Dusk/Night) affecting travel and danger |
| **16 Achievements** | Unlock milestones across multiple categories |
| **Seeded Runs** | Replay exact same games or generate fresh randomness |
| **Auto-Balancing** | Game tunes itself based on gameplay logs |

---

## Auto-Balancing System

The game automatically learns from your gameplay. **One-step tuning:**

```bash
# Run complete tuning cycle in one command
python main.py --tune
# - Runs 54 comprehensive test scenarios
# - Analyzes results automatically
# - Applies optimal tuning parameters
# - Cleans up temporary files
# (Takes 2-3 minutes)
```

**Manual steps (if preferred):**

```bash
# 1. Play games (logs auto-saved to logs/)
python main.py --test-all

# 2. Analyze for balance issues
python analyze_logs.py --balance

# 3. Auto-apply tuning improvements
python game_tuner.py --apply

# 4. Next game loads improved settings
python main.py
```

**Interactive menu:** On startup, press `2` when prompted to trigger auto-tuning without CLI flags.

The auto-tuner adjusts:
- Theme difficulty (supply amounts, damage taken)
- Death patterns (if water kills 60%, increase water)
- Progression difficulty (early vs late game balance)
- Event frequency and weights

**See [docs/QUICKSTART.md](docs/QUICKSTART.md) for more details.**

---

## GitHub Copilot Agent Skills

This project includes an agent skill that enables AI to improve the game autonomously.

**The game-improvement skill enables agents to:**
- Analyze gameplay logs and player behavior
- Detect balance issues (win rates, death patterns)
- Auto-generate tuning recommendations
- Debug crashes and errors
- Run validation tests

**For details, see:**
- 📖 [.github/skills/AGENT_SKILLS_GUIDE.md](.github/skills/AGENT_SKILLS_GUIDE.md) — master guide for all agent skills
- 🎯 [.github/skills/game-improvement/SKILL.md](.github/skills/game-improvement/SKILL.md) — complete skill definition
- ⚙️ [.github/skills/auto-tuning/](.github/skills/auto-tuning/) — auto-tuning system documentation

---

## Analyzing Your Games

```bash
# View overall statistics
python analyze_logs.py --stats

# Check balance by theme/difficulty
python analyze_logs.py --balance

# Analyze death patterns
python analyze_logs.py --deaths

# Check for errors/crashes
python analyze_logs.py --errors
```

Logs are saved to `logs/game_YYYYMMDD_HHMMSS.jsonl` (JSON Lines format).

---

## Project Structure

```
python-cli-story-game/
├── main.py                    # Game engine (complete, single file)
├── analyze_logs.py            # Log analysis tool
├── game_tuner.py              # Auto-balancing engine
├── auto_tune.py               # Auto-tuning wrapper
├── docs/                      # Documentation (QUICKSTART, guides)
├── tests/                     # Test scripts
├── logs/                      # Gameplay logs
├── .github/skills/            # Agent skills
│   ├── AGENT_SKILLS_GUIDE.md
│   ├── game-improvement/
│   └── auto-tuning/
└── README.md                  # This file
```

---

## Extending the Game

- **New theme**: Add `ThemeId` enum, register in `_register_themes()`, add companions and narratives
- **New events**: Write `_event_xxx()` function, add to `EVENT_POOL` with weight
- **New items**: Add to `ITEM_CATALOGUE` and optional `CRAFT_RECIPES`
- **New achievements**: Add to `_make_achievements()`, call `player.try_unlock()` when earned
- **New riddles**: Append tuples to `RIDDLES` list

See `main.py` for examples and patterns.

---

## Testing

```bash
python test_game.py          # Unit tests
python test_game.py -v       # Verbose
python test_game.py --full   # Full integration tests
```

Automated test suite: `tests/` directory

---

## Documentation

- 📖 [docs/QUICKSTART.md](docs/QUICKSTART.md) — Getting started guide
- 📘 [docs/WORKSPACE_CLEANUP.md](docs/WORKSPACE_CLEANUP.md) — Project organization
- 🧠 [.github/skills/AGENT_SKILLS_GUIDE.md](.github/skills/AGENT_SKILLS_GUIDE.md) — Agent skills deep dive
- 📊 [.github/skills/auto-tuning/LEARNING_SYSTEM.md](.github/skills/auto-tuning/LEARNING_SYSTEM.md) — How auto-tuning works

---

## License

MIT — Modify, extend, and redistribute freely.

**Disclaimer:** This project is AI-generated and fictional. It's a showcase for GitHub Copilot agent skills and automated game balancing.
