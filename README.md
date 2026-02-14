# Terminal Adventure Quest

A text-based interactive story game inspired by classic travel adventures like *The Oregon Trail*.  
Choose from five unique themes, manage supplies, make branching narrative choices, and try to survive the journey.

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

## Project Structure

```
python-cli-story-game/
├── main.py         # Complete game script (single file, no dependencies)
├── test_game.py    # Automated test suite (unittest)
└── README.md       # This file
```

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
