# 🧠 Self-Improving Game System

## For End Users (Simple Version)

### **Just Play - The Game Learns Automatically!**

```bash
python main.py
```

That's it! Every time you play:
1. ✅ **Your gameplay is logged automatically** (in `logs/` folder)
2. ✅ **Game analyzes patterns** every 10 sessions
3. ✅ **Improvements apply automatically** next time you play

The game gets better the more you (and others) play it!

---

## 📊 What Gets Improved Automatically?

### **Balance Issues**
- **Too Hard?** → Increases starting supplies, reduces consumption
- **Too Easy?** → Adds more challenges, reduces resources
- **Target:** 40-60% win rate for balanced gameplay

### **Death Patterns**
- **Everyone dying of thirst?** → Increases water supplies
- **Food problems?** → Adjusts food availability
- **Combat too deadly?** → Reduces monster damage

### **Progression Pacing**
- **Games too short?** → Balances difficulty curve
- **Too long/boring?** → Increases event frequency

### **Error Fixes**
- Crashes logged with full details
- Auto-detected and (where possible) auto-fixed

---

## 🔧 Manual Mode (Optional)

Want to tune the game manually? You have full control:

### **Check Balance**
```bash
python analyze_logs.py --balance
```
Shows win rates, death causes, and problem areas.

### **See Statistics**
```bash
python analyze_logs.py --stats
```
Detailed metrics: survival times, choices made, achievements.

### **Apply Tuning Manually**
```bash
python game_tuner.py --apply
```
Generates and applies improvements based on logged data.

### **Check Specific Session**
```bash
python analyze_logs.py --session game_20260215_211819
```

---

## ⚙️ Configuration

### **Adjust Auto-Tuning Frequency**

Edit `main.py` (near the bottom):
```python
# Auto-tune every 10 sessions (default)
check_and_apply_auto_tuning(min_sessions=10)

# Or more/less frequent:
check_and_apply_auto_tuning(min_sessions=5)   # Tune every 5 games
check_and_apply_auto_tuning(min_sessions=20)  # Tune every 20 games
```

### **Disable Auto-Tuning**

Remove or comment out this line in `main.py`:
```python
# check_and_apply_auto_tuning()  # Disabled
```

### **Silent Mode (No Messages)**
```python
check_and_apply_auto_tuning(silent=True)
```

---

## 📁 What Gets Saved?

### **Log Files** (`logs/`)
```
game_20260215_211819.jsonl    ← Your gameplay session
game_20260215_214530.jsonl    ← Next session
...
```
Each file contains:
- Player choices and outcomes
- Random events encountered
- Death causes and victory conditions
- Timing and performance data

### **Tuning Config** (`game_tuning.json`)
```json
{
  "adjustments": {
    "desert_caravan": {
      "starting_supplies": 1.3,  ← 30% more supplies
      "consumption_rate": 0.85   ← 15% less consumption
    }
  },
  "metadata": {
    "sessions_analyzed": 15,
    "insights": ["Desert too hard - win rate: 12%"]
  }
}
```

**Auto-loads on every startup** - no action needed!

---

## 🎮 How It Works Behind the Scenes

```
┌─────────────┐
│  You Play   │
│   main.py   │
└──────┬──────┘
       │
       ├──► 📝 Logs created automatically (logs/*.jsonl)
       │
       └──► Every 10 sessions:
            ├──► 🔍 Analyze patterns (analyze_logs.py)
            ├──► 🎯 Generate fixes (game_tuner.py)
            └──► ✅ Apply adjustments (game_tuning.json)
                 
Next startup → ✨ Game auto-loads improvements
```

---

## ❓ FAQ

### **Q: Do I need to do anything special?**
**A:** No! Just play normally. Logging and tuning happen automatically.

### **Q: Can I turn off logging?**
**A:** Yes. In `main.py`, set `LOGGING_ENABLED = False` at the top.

### **Q: What if I disagree with the tuning?**
**A:** Delete `game_tuning.json` or edit it manually. It's just a JSON file.

### **Q: Does it send data anywhere?**
**A:** No! Everything stays on your computer in the `logs/` folder.

### **Q: How much disk space does it use?**
**A:** ~2-3 KB per game session. 100 sessions ≈ 250 KB. Minimal!

### **Q: Can I reset everything?**
**A:** Yes! Delete the `logs/` folder and `game_tuning.json`.

### **Q: Can I share logs with others?**
**A:** Yes! Logs combine across users. Share your `logs/` folder to help improve the game faster.

---

## 🚀 Advanced: Contributing Your Data

Want to help improve the game for everyone?

1. **Play a lot!** (10+ sessions)
2. **Share your logs/** folder via GitHub/Discord/email
3. **Game developers** merge logs from all players
4. **Everyone benefits** from collective gameplay data

This creates a **crowdsourced game improvement system**! 🎯

---

## 🔍 Privacy & Data

**What's logged:**
- ✅ Game choices and outcomes
- ✅ Theme selected, difficulty, survival time
- ✅ Random events, deaths, victories
- ✅ Timing and performance metrics

**What's NOT logged:**
- ❌ Your name or personal info
- ❌ Computer details (beyond OS type)
- ❌ Any data outside the game

**All data stays local** unless you choose to share it.

---

## 📚 For Developers

### **Integration in main.py**
```python
from auto_tune import check_and_apply_auto_tuning

if __name__ == "__main__":
    # Enable auto-tuning (runs every 10 sessions)
    check_and_apply_auto_tuning(min_sessions=10, silent=False)
    
    # Start game
    main()
```

### **Testing Auto-Tune**
```bash
# Check if tuning would run
python auto_tune.py

# Force tuning regardless of session count
python game_tuner.py --apply --min-sessions 1

# Test with verbose output
python analyze_logs.py --balance --verbose
```

### **CI/CD Integration**
```yaml
# GitHub Actions example
- name: Run auto-tuning analysis
  run: |
    python analyze_logs.py --stats > metrics.txt
    python game_tuner.py --dry-run
```

---

## 🎯 Success Metrics

The system aims for:
- **Win Rate:** 40-60% (balanced challenge)
- **Survival Time:** 40-80 days average
- **Death Variety:** No single cause >30%
- **Event Frequency:** 1-3 events per 10 days
- **Player Engagement:** 50%+ games reach day 50+

All tracked and tuned automatically! ✨
