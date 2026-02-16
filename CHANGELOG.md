# Changelog

All notable changes to Terminal Adventure Quest will be documented in this file.

## [1.0.0] - 2026-02-16

### Added
- **Auto-tuning system** - Game learns from logs and auto-improves balance
  - `auto_tune.py` module automatically detects when tuning should run (every 10 sessions)
  - `game_tuner.py` analyzes themes, death patterns, difficulty scaling, progression pacing
  - `game_tuning.json` auto-generated with intelligent parameter adjustments
  - Auto-loads on startup without user intervention
  - Graceful error handling - never crashes game if tuning fails
  - Fully configurable: adjust `min_sessions`, disable with comments, silent mode available
- **Comprehensive test suite** - 54 automated games across all 6 themes
  - Tests all 5 themes + AI-Generated theme (6 total)
  - 3 difficulty levels per theme
  - Run with: `python main.py --test-all`
  - Generates representative logs for analysis and tuning
- **Agent skills documentation** - Master guide for GitHub Copilot agents
  - `.github/skills/AGENT_SKILLS_GUIDE.md` - comprehensive skills overview
  - `.github/skills/auto-tuning/` - auto-tuning system documentation
  - Explains complementary relationship between auto-tuning and agent skills
  - Lists recommended skills to add (Storytelling, Testing, Content Generator, etc.)
- **Normal difficulty as default** - Faster game startup
  - Difficulty selection now accepts empty input (just press Enter)
  - Normal marked with `[DEFAULT]` indicator in green
  - Prompt text updated to indicate Enter defaults to Normal
  - Users can now start game with 2 Enter presses instead of manually selecting

### Changed
- **README condensed** - Reduced from ~550 lines to ~240 lines
  - Maintained essential information and quick start
  - Moved detailed guides to `docs/` folder
  - Added links to comprehensive documentation
  - More approachable for new users
- **Workspace reorganized** - Professional project structure
  - Core files in root: main.py, analyze_logs.py, game_tuner.py, auto_tune.py
  - `docs/` - User documentation (QUICKSTART, guides)
  - `tests/` - Test scripts (7 automated test files)
  - `.github/skills/` - Agent skills (game-improvement, auto-tuning)
  - `logs/` - Gameplay logs, `logs/archive/` for archived temp files
  - 75% reduction in root directory clutter (31 → 8 files)

### Improved
- AI scenario variety expanded with cross-theme template borrowing
  - AI_GENERATED theme uses 20 dedicated templates
  - Can borrow from other themes (45 total templates available)
  - Reduced duplicate scenario rate
- Auto-tuning integration with main.py
  - Checks and applies tuning on every startup
  - Shows user-friendly messages when adjustments applied
  - Silent mode option for clean output
  - Try/except wrapper prevents tuning from breaking game
- Testing infrastructure
  - 54 comprehensive tests validate all themes
  - AI-Generated theme validated with localhost Ollama
  - Tests use varied seeds for statistical reliability

### Fixed
- Added missing method names in auto_tune.py
  - Changed `analyze_death_patterns` → `analyze_death_causes`
  - Added `analyze_event_frequency` call to analysis pipeline

---

## [Initial Build] - 2026-02-14

### Added
- Complete Terminal Adventure Quest game engine
- 5 adventure themes with unique mechanics and narratives
- AI-powered scenario generation using Ollama
- Comprehensive logging system for gameplay analysis
- Game tuning and balance analysis tools
- Test suite for automated play-testing


- Rich narrative flavor text throughout gameplay
  - Travel action: Varied atmospheric descriptions, weather-specific narratives
  - Rest action: Multiple rest flavor texts, healing feedback varies by amount
  - Scout action: Exploration-themed descriptions, varied discovery messages
  - Distance progress messages now have multiple variations
  - Weather effects include descriptive text explaining impact
- Significantly improved ASCII art clarity and visual complexity
  - Storm: Box-drawn header with stylized text and rain effects
  - Battle: Framed encounter card with sword symbols and opponent positions  
  - River/Water: Wave patterns (≈) with dimensional depth and framed header
  - Treasure: Framed discovery header maintaining chest detail
  - Riddle: Enhanced sphinx face with framed header
  - All event art now uses Unicode box-drawing characters for professional appearance
  - Uses robust Gemma 3 4B model for high-quality storytelling
  - Integrates seamlessly with existing event system
  - Gracefully falls back to curated templates if Ollama unavailable
- New 6th adventure option: "AI-Generated Adventure"
  - Queries Ollama on localhost for available models
  - Lists models sorted by size (smallest first)
  - Auto-selects gemma3:4b if available, otherwise prompts user to choose
  - Dynamic scenarios throughout the journey powered by selected model
  - Generates unique Unicode ASCII art patterns on each playthrough
- Streamlined game startup flow
  - Removed name prompt (uses "You" for all narratives)
  - Removed seed prompt (uses random seed automatically)
  - Theme selection is now the first prompt

### Changed
- All story ending messages now use "You" instead of player name for better immersion

---

## [1.0.0] - 2026-02-14

### Added
- Initial release of Terminal Adventure Quest
- Five unique adventure themes (Desert, Space, Mist, Time, Cyber)
- Difficulty levels (Easy, Normal, Hard)
- Status effects system (Poisoned, Inspired, Exhausted, Shielded, Lucky)
- Companion recruitment system with themed allies
- Milestone narrative beats at 25%, 50%, 75% progress
- Riddle and puzzle mini-games
- Day/night cycle with weather system
- Achievements system (16 total)
- Crafting system for combining items
- Gambling/dice mini-game at traders
- Automated gameplay logging and analysis
- Game tuning system for balance adjustments
- Automated test mode for batch processing
