# 🎮 Terminal Adventure Quest - Quick Start

## Installation

```bash
# 1. Clone or download this repository
git clone <repo-url>
cd python-cli-story-game

# 2. (Optional) Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies (if any - currently none required)
pip install -r requirements.txt  # if file exists

# 4. Play!
python main.py
```

## 🧠 Self-Improving Game Feature

**The game automatically learns and improves as you play!**

### How It Works (No Setup Needed!)

1. **Just play normally** - Every game is logged automatically
2. **After 10 games** - System analyzes patterns (win rates, death causes, etc.)
3. **Improvements auto-apply** - Balance fixes load on next startup

### What You'll See

```
🔧 Auto-tuning: 10 new sessions detected...
   Analyzing gameplay patterns and applying fixes...
   ✅ Applied 3 adjustments
   Changes will apply to your next game!

TERMINAL ADVENTURE QUEST
...
```

### What Gets Improved

- **Balance**: If win rate too low/high → adjusts resources
- **Death patterns**: If everyone dies same way → fixes that issue
- **Difficulty**: Automatically tunes challenge level
- **Errors**: Crashes logged for fixing

### Configuration

**Default:** Auto-tunes every 10 sessions

To change frequency, edit [main.py](main.py#L3475) (bottom of file):
```python
check_and_apply_auto_tuning(min_sessions=5)   # Tune every 5 games
check_and_apply_auto_tuning(min_sessions=20)  # Tune every 20 games
```

**To disable:** Comment out the auto-tune line:
```python
# check_and_apply_auto_tuning(min_sessions=10)  # Disabled
```

## 📊 Manual Analysis (Optional)

Want to see the data yourself?

```bash
# Check game balance
python analyze_logs.py --balance

# View statistics
python analyze_logs.py --stats

# Apply tuning manually
python game_tuner.py --apply
```

## 📁 Files Created

- `logs/game_*.jsonl` - Your gameplay sessions (2-3 KB each)
- `game_tuning.json` - Auto-generated balance adjustments (auto-loads)

**Privacy:** All data stays on your computer. Nothing sent anywhere.

## 🚀 Advanced: Crowdsourced Improvement

Want to help improve the game faster?

1. Play multiple sessions (10+)
2. Share your `logs/` folder with game developer
3. Combined data from all players → better game for everyone!

## ❓ Troubleshooting

**"Auto-tuning skipped" message?**
- Normal if `auto_tune.py` missing or `game_tuner.py` has issues
- Game still works fine - just no automatic improvements
- Check `analyze_logs.py` and `game_tuner.py` exist

**Want to reset everything?**
```bash
# Delete logs and tuning config
rm -rf logs/
rm game_tuning.json
```

**Logs taking up space?**
```bash
# Archive old logs
mkdir logs/archive
mv logs/game_2026*.jsonl logs/archive/
```

## 📚 More Info

- [LEARNING_SYSTEM.md](LEARNING_SYSTEM.md) - Complete documentation
- [README.md](README.md) - Game features and gameplay
- [AI_LEARNING_STATUS.md](AI_LEARNING_STATUS.md) - Current learning system status

---

**That's it! Just run `python main.py` and enjoy a game that gets better over time! 🎯**
