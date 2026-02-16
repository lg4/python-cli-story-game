#!/usr/bin/env python3
"""
Terminal Adventure Quest
========================
A text-based interactive story game inspired by classic travel adventures
such as The Oregon Trail. Choose from five unique themes, manage supplies,
make branching narrative choices, and try to survive the journey.

New in v2:
  - Automated test mode (--test flag)
  - Difficulty levels (Easy / Normal / Hard)
  - Status effects (Poisoned, Inspired, Exhausted, Shielded)
  - Companion system (recruit allies with unique bonuses)
  - Milestone narrative beats at 25%, 50%, 75% progress
  - Riddle / puzzle mini-game event
  - Day / night cycle that affects events
  - Achievements system
  - Expanded event pool with richer combat
  - Gambling / dice mini-game at traders
  - Weather system
  - Crafting basics (combine items)

Author : AI-Generated
Python : 3.10+
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
import random
import sys
import textwrap
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Callable, TextIO, Any

# ──────────────────────────────────────────────────────────────────────
# Optional colour support  (pip install colorama)
# ──────────────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    class _NoColor:
        def __getattr__(self, _: str) -> str:
            return ""
    Fore = _NoColor()   # type: ignore[assignment]
    Style = _NoColor()  # type: ignore[assignment]
    HAS_COLOR = False

# ──────────────────────────────────────────────────────────────────────
# Global flags (set by CLI or test harness)
# ──────────────────────────────────────────────────────────────────────
TEST_MODE: bool = False        # when True, skip delays & read from input queue
SLOW_PRINT_DELAY: float = 0.02  # character delay for theatrical prints
LOGGING_ENABLED: bool = True    # when True, writes gameplay logs to disk
SELECTED_AI_MODEL: str = "gemma3:4b"  # Selected Ollama model for AI scenarios

# Ollama API Configuration
OLLAMA_HOST: str = "localhost"  # Using local Ollama instance
OLLAMA_PORT: int = 11434         # Default Ollama port
OLLAMA_URL: str = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"  # Full API endpoint

# ──────────────────────────────────────────────────────────────────────
# Auto-tuning system (learns from logs)
# ──────────────────────────────────────────────────────────────────────
TUNING_CONFIG: dict[str, Any] = {}
TUNING_LOADED: bool = False


def load_tuning_config() -> dict[str, Any]:
    """Load automatic tuning adjustments from game_tuning.json if it exists."""
    global TUNING_CONFIG, TUNING_LOADED
    if TUNING_LOADED:
        return TUNING_CONFIG
    
    tuning_file = Path("game_tuning.json")
    if tuning_file.exists():
        try:
            with open(tuning_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                TUNING_CONFIG = config.get("adjustments", {})
                if TUNING_CONFIG and not TEST_MODE:
                    print(f"{Fore.CYAN}[Auto-tuning enabled: {len(TUNING_CONFIG)} adjustments loaded]{Style.RESET_ALL}")
        except Exception:
            pass
    
    TUNING_LOADED = True
    return TUNING_CONFIG


def get_tuned_value(param_name: str, default: float) -> float:
    """Get a parameter value, applying tuning adjustment if available."""
    if param_name in TUNING_CONFIG:
        return default * TUNING_CONFIG[param_name]
    return default


# ──────────────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────────────
WIDTH = 72


def clamp(value: int | float, lo: int | float, hi: int | float) -> int | float:
    return max(lo, min(hi, value))


def slow_print(text: str, delay: float | None = None) -> None:
    """Print text character-by-character for dramatic effect."""
    if TEST_MODE:
        print(text)
        return
    d = delay if delay is not None else SLOW_PRINT_DELAY
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(d)
    print()


def print_bar(label: str, current: int, maximum: int, color: str = "") -> None:
    bar_len = 20
    filled = int(bar_len * clamp(current, 0, maximum) / maximum) if maximum > 0 else 0
    empty = bar_len - filled
    bar = f"{color}{'█' * filled}{'░' * empty}{Style.RESET_ALL}"
    print(f"  {label:<12} {bar}  {current}/{maximum}")


def hr(char: str = "─") -> None:
    print(char * WIDTH)


def clear_screen() -> None:
    """Clear the terminal screen. Works on Windows, macOS, and Linux."""
    import os
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


# ──────────────────────────────────────────────────────────────────────
# ASCII Art colorization helpers
# ──────────────────────────────────────────────────────────────────────
def colorize_ascii(text: str, color: str) -> str:
    """Apply a single color to ASCII art."""
    if not HAS_COLOR or not text:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def colorize_ascii_gradient(text: str, colors: list[str]) -> str:
    """Apply gradient of colors to ASCII art (cycling through colors per line)."""
    if not HAS_COLOR or not text or not colors:
        return text
    lines = text.split('\n')
    colored_lines = []
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        colored_lines.append(f"{color}{line}{Style.RESET_ALL}")
    return '\n'.join(colored_lines)


def get_theme_ascii_color(theme_id: ThemeId) -> str:
    """Get the appropriate color for a theme's ASCII art."""
    color_map = {
        ThemeId.DESERT: Fore.YELLOW,      # Sand/sun
        ThemeId.SPACE: Fore.CYAN,         # Sci-fi glow
        ThemeId.MIST: Fore.MAGENTA,       # Mystical purple
        ThemeId.TIME: Fore.WHITE,         # Glitchy white
        ThemeId.CYBER: Fore.GREEN,        # Hacker aesthetic
    }
    return color_map.get(theme_id, Fore.WHITE)


def wrapped(text: str) -> str:
    return textwrap.fill(text, width=WIDTH)


def get_choice(prompt: str, valid: range | list[str], *, allow_empty: bool = False) -> str:
    """Robustly get a validated input. Handles EOF / Ctrl-C."""
    acceptable: list[str]
    if isinstance(valid, range):
        acceptable = [str(v) for v in valid]
    else:
        acceptable = [v.lower() for v in valid]

    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)
        if not raw and allow_empty:
            return ""
        if raw.lower() in acceptable:
            return raw
        print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")


def pause(seconds: float = 1.0) -> None:
    """Sleep unless in test mode."""
    if not TEST_MODE:
        time.sleep(seconds)


def pause_for_action(seconds: float = 1.5) -> None:
    """
    Pause between actions with visual separator.
    Can be interrupted by pressing Enter in test/interactive mode.
    Shows a subtle prompt if not in test mode.
    """
    if TEST_MODE:
        return
    
    hr()  # Print separator line
    try:
        # Use a non-blocking approach: give user option to press Enter or wait
        import select
        import sys as _sys
        if hasattr(select, 'select') and _sys.platform != 'win32':
            # Unix-like systems
            rlist, _, _ = select.select([_sys.stdin], [], [], seconds)
            if rlist:
                input()  # Consume the keypress
        else:
            # Windows or fallback
            time.sleep(seconds)
    except Exception:
        # Fallback if select fails
        time.sleep(seconds)


# ──────────────────────────────────────────────────────────────────────
# Logging System
# ──────────────────────────────────────────────────────────────────────
class GameLogger:
    """Comprehensive gameplay logger for analytics and improvement."""

    def __init__(self, log_dir: Path = Path("logs"), session_id: str | None = None):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"game_{self.session_id}.jsonl"
        self.events: list[dict[str, Any]] = []
        self.start_time = time.time()

        # Initialize session metadata
        self.log_event("session_start", {
            "timestamp": datetime.now().isoformat(),
            "test_mode": TEST_MODE,
        })

    def log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Log a single event with timestamp."""
        if not LOGGING_ENABLED:
            return

        event = {
            "timestamp": datetime.now().isoformat(),
            "elapsed": round(time.time() - self.start_time, 2),
            "type": event_type,
            **data,
        }
        self.events.append(event)

        # Write to file immediately (JSONL format)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass  # Don't crash game on logging errors

    def log_player_state(self, player: 'Player', label: str = "state") -> None:
        """Log full player state snapshot."""
        self.log_event(f"player_{label}", {
            "name": player.name,
            "theme": player.theme.name,
            "difficulty": player.difficulty.value,
            "day": player.days,
            "distance": player.distance_travelled,
            "health": player.health,
            "morale": player.morale,
            "supplies": dict(player.supplies),
            "inventory_count": len(player.inventory),
            "inventory": player.inventory[:],
            "companion": player.companion.name if player.companion else None,
            "effects": {e.value: d for e, d in player.status_effects.items()},
            "achievements": sum(1 for a in player.achievements.values() if a.unlocked),
            "time_of_day": player.time_of_day.value,
            "weather": player.weather.value,
        })

    def log_choice(self, prompt: str, choice: str, context: dict[str, Any] | None = None) -> None:
        """Log a player decision."""
        self.log_event("choice", {
            "prompt": prompt[:100],  # truncate long prompts
            "choice": choice,
            "context": context or {},
        })

    def log_event_trigger(self, event_name: str, outcome: str, details: dict[str, Any] | None = None) -> None:
        """Log a random event and its outcome."""
        self.log_event("random_event", {
            "event": event_name,
            "outcome": outcome,
            "details": details or {},
        })

    def log_death(self, cause: str, player: 'Player') -> None:
        """Log player death with full context."""
        self.log_event("death", {
            "cause": cause,
            "day": player.days,
            "distance": player.distance_travelled,
            "distance_pct": int(player.distance_travelled / player.theme.total_distance * 100),
            "health": player.health,
            "food": player.supplies["food"],
            "water": player.supplies["water"],
            "fuel": player.supplies["fuel"],
            "difficulty": player.difficulty.value,
            "theme": player.theme.name,
        })

    def log_victory(self, ending_type: str, player: 'Player') -> None:
        """Log successful completion."""
        self.log_event("victory", {
            "ending": ending_type,
            "day": player.days,
            "health": player.health,
            "morale": player.morale,
            "achievements": sum(1 for a in player.achievements.values() if a.unlocked),
            "difficulty": player.difficulty.value,
            "theme": player.theme.name,
        })

    def log_error(self, error_type: str, message: str, context: dict[str, Any] | None = None, traceback_str: str | None = None) -> None:
        """Log an error, exception, or invalid input."""
        error_data = {
            "error_type": error_type,
            "message": message,
            "context": context or {},
        }
        if traceback_str:
            error_data["traceback"] = traceback_str
        self.log_event("error", error_data)

    def log_exception(self, exc: Exception, context: dict[str, Any] | None = None) -> None:
        """Log an unhandled exception with full traceback."""
        import traceback as tb
        self.log_error(
            error_type=type(exc).__name__,
            message=str(exc),
            context=context,
            traceback_str=tb.format_exc(),
        )

    def get_summary(self) -> dict[str, Any]:
        """Generate analytics summary from events."""
        if not self.events:
            return {}

        choices = [e for e in self.events if e["type"] == "choice"]
        events = [e for e in self.events if e["type"] == "random_event"]
        deaths = [e for e in self.events if e["type"] == "death"]
        victories = [e for e in self.events if e["type"] == "victory"]
        errors = [e for e in self.events if e["type"] == "error"]

        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "duration_seconds": round(time.time() - self.start_time, 1),
            "choices_made": len(choices),
            "random_events": len(events),
            "deaths": len(deaths),
            "victories": len(victories),
            "errors": len(errors),
            "error_types": [e.get("error_type") for e in errors],
            "event_types": {e["event"]: e.get("outcome") for e in events[-10:]},  # last 10
        }


# Global logger instance
GAME_LOGGER: GameLogger | None = None


def init_logger(session_id: str | None = None) -> GameLogger:
    """Initialize the global game logger."""
    global GAME_LOGGER
    GAME_LOGGER = GameLogger(session_id=session_id)
    return GAME_LOGGER


def log_game(event_type: str, data: dict[str, Any]) -> None:
    """Convenience function for logging."""
    if GAME_LOGGER:
        GAME_LOGGER.log_event(event_type, data)


# ──────────────────────────────────────────────────────────────────────
# ASCII Art Assets
# ──────────────────────────────────────────────────────────────────────
ASCII_TITLE = r"""
 ___________                    .__              .__
 \__    ___/__________  _____ |__| ____ _____  |  |
   |    | / __ \_  __ \/     \|  |/    \\__  \ |  |
   |    |\  ___/|  | \/  Y Y  \  |   |  \/ __ \|  |__
   |____| \___  >__|  |__|_|  /__|___|  (____  /____/
              \/            \/        \/     \/
     _____       .___                    __
    /  _  \   __| _/__  __ ____   _____/  |_ __ _________   ____
   /  /_\  \ / __ |\  \/ // __ \ /    \   __\  |  \_  __ \_/ __ \
  /    |    \/ /_/ | \   /\  ___/|   |  \  | |  |  /|  | \/\  ___/
  \____|__  /\____ |  \_/  \___  >___|  /__| |____/ |__|    \___  >
          \/      \/           \/     \/                        \/
       ________                          __
      \_____  \  __ __   ____   _______/  |_
       /  / \  \|  |  \_/ __ \ /  ___/\   __\
      /   \_/.  \  |  /\  ___/ \___ \  |  |
      \_____\ \_/____/  \___  >____  > |__|
             \__>           \/     \/
"""

ASCII_DESERT = r"""
                               _.---.
                    _        /  .  . \
                   ( `.     / '.|  |'. \
                    `\ \   /  .-|  |-.  \
                      ; ;-'  / _|  |_ \  ;
                     / /    ( / |  | \ ) |
                    / /      |  `--'  |  |
                   / /       |  .--'  |  ;
                  ;  ;   _.-'  / |  \ `-._
        ,=.      ;  ,`--'     /  |  \     `--.
       /  (\   .-|  ;  .---. /   |   \ ,---.  |
      /    `\_/ /|  ;  |   |'    |    |   |  `;
     ( .-,   / / ;  ;  |   |    _|_   |   |   ;
      ) \ `-'  ; (  (  /   |  .' _ `. |   \  _)
      `- `-.   |  ;  `.|   |  | (_) | |    |`
  ~-~-~-~-~\  |  |    |   |  `.___.' |    |~-~-~-~
             ; |  |    |   |         |    ;
         ~-~-~-~-~   ~-~-~-~     ~-~-~-~-~-~
"""

ASCII_SPACE = r"""
          .    *       .   *    .        *
    *  .    .    *         .       .
         .       .    ___
      *     .      .-'   '-.     *   .
   .     *   .   .'  .  .   '.
    .      .    |  .       . |      *
   *    .      |     /^\     |
     .    *    |    /   \    |    .
      .       |   | === |   |
   *     .    |   | === |   |   *   .
       .      '.  |     |  .'
    .     *     '-.`---'.-'    *
               *   `---`  .      .     *
"""

ASCII_MIST = r"""
  ~~  .  ~~  .  ~~  .  ~~  .  ~~  .  ~~
       .         _            .
   ~~     .    /   \     ~~      .    ~~
      .       / _ _ \        .
  ~~    .    |  / \  |   ~~       ~~
    .        | | O | |       .
  ~~   .     |  \_/  |    ~~    .     ~~
     .     __|       |__      .
  ~~      /  |_______|  \        ~~
    .    /    |       |    \  .
  ~~  . /___ |       | ___\   ~~  .  ~~
       ~~  .  ~~  .  ~~  .  ~~  .  ~~
"""

ASCII_TIME = r"""
          .--.      .--.
         /    \    /    \
        |  12  |  | 12  |
        | 9  3 |  | 9 3 |
        |  6   |  |  6  |
         \    /    \    /
          '--'      '--'
       ~~~~~~~~~~~~~~~~~~~~
      ~ Past  <---> Future ~
       ~~~~~~~~~~~~~~~~~~~~
"""

ASCII_CYBER = r"""
    ______   ______  ______  ______  ______
   /\  == \ /\  __ \/\  ___\/\  ___\/\  ___\
   \ \  __< \ \  __ \ \___  \ \___  \ \___  \
    \ \_____\\ \_\ \_\/\_____\/\_____\/\_____\
     \/_____/ \/_/\/_/\/_____/\/_____/\/_____/

   [>] SYS BREACH DETECTED ────────── 100%
   [>] NEURAL LINK ACTIVE  ────────── OK
   [>] DECRYPTION MODULE   ────────── READY
"""

ASCII_RIVER = r"""
    ╔═══════════════════════════════════╗
    ║    🌊  WATER CROSSING  🌊        ║
    ╚═══════════════════════════════════╝
      ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
    ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈
  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈
    ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈  ≈≈
      ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
"""

ASCII_BATTLE = r"""
    ╔═══════════════════════════════╗
    ║   ⚔️  COMBAT ENCOUNTER  ⚔️    ║
    ╚═══════════════════════════════╝
         ⚔                    ⚔
        /|\      * * *       /|\
         |     *  CLASH  *    |
        / \   * * *  * * *   / \
       /   \                /   \
      █████                 █████
    [ENEMY]                [YOU]
"""

ASCII_TREASURE = r"""
    ╔═══════════════════════════════╗
    ║      ✨  DISCOVERY  ✨       ║
    ╚═══════════════════════════════╝
            _.---.
        _.-'  _  `-.
    _.-' .--.' `.--. `-.
   :   .'   /    \   `.  :
   :  /    /  ()  \    \ :
   : |    |   /\   |    |:
   : |    |  /  \  |    |:
   :  \    \/    \/    / :
   :   `.   `----'   .'  :
    `-._  `-.____.-'  _.-'
        `-.________.-'
           | LOOT |
"""

ASCII_CAMP = r"""
        /\         *  .  *
       /  \      .  *  .
      /    \       *  .
     / CAMP \   *   .   *
    /________\
      ||  ||      ~ campfire ~
      ||  ||    (  (   )  )
   ___||__||___  )  ) (  (
"""

ASCII_STORM = r"""
       __   _  __   _   __  __   _
     (  _ ( \( _) ( ) (  \/  ) ( \  
     \_\  )   ( (_  )_\  ))  ((  )  ) 
      (_(_)\_)(__)(___)(__)(__)(__)  
    ╔════════════════════════════╗
    ║  ≋≋≋  THE STORM RAGES  ≋≋≋  ║
    ╚════════════════════════════╝
       |||  |||  |||  |||  |||
        ||  ||  ||  ||  ||  ||
"""

ASCII_NIGHT = r"""
         .  *  .    *    .  *
    *  .    .    *    .
       .  *   .   .  *  .
     *    .  *  .     *
   .   *    .    *  .    *  .
   *     .      *    .
"""

ASCII_DAWN = r"""
                 .
           .    / \    .
     .    /  \  / | \  /  \    .
    ~~~~~~~~~/  |  \~~~~~~~~~
      -------   |   -------
    ~~~~~~~~~\  |  /~~~~~~~~~
              \ | /
               \|/
    ============*============
"""

ASCII_COMPANION = r"""
      O    O
     /|\  /|\
     / \  / \
    You  Ally
"""

ASCII_RIDDLE = r"""
    ╔═══════════════════════════════╗
    ║    🎭  RIDDLE TIME  🎭        ║
    ╚═══════════════════════════════╝
         ___________
        /           \
       |  ?       ?  |
       |      ^      |
       |   \     /   |
       |    \___/    |
        \___________/
      The Sphinx waits...
"""

ASCII_DICE = r"""
     _______
    /\      \
   /  \  o   \
  / o  \      \
 /      \ o   /
 \  o   /\   /
  \    /  \ /
   \  / o  /
    \/____/
"""

ASCII_WEATHER_CLEAR = r"""
        \   |   /
         .---.
    --- (     ) ---
         `---'
        /   |   \
"""

ASCII_WEATHER_RAIN = r"""
          .---.
       .--(     )--.
      (             )
       `---.___,---'
        / / / / / /
       / / / / / /
"""

ASCII_WEATHER_FOG = r"""
   ~~~~~~~~~~~~~~~~
  ~~  ~~  ~~  ~~  ~~
   ~~~~~~~~~~~~~~~~
  ~~  ~~  ~~  ~~  ~~
   ~~~~~~~~~~~~~~~~
"""

ASCII_ACHIEVEMENT = r"""
     .----.
    / GOAL \
   |  ****  |
   |  ****  |
    \      /
     `----'
"""

ASCII_VICTORY = r"""
     *    *    *    *    *
   *    *    *    *    *    *
      ___   ___   ___
     |   | |   | |   |
     | V | | I | | C |
     |   | |   | |   |
     |___| |___| |___|
      ___   ___   ___    ___
     |   | |   | |   |  |   |
     | T | | O | | R | | Y |
     |   | |   | |   |  |   |
     |___| |___| |___|  |___|
   *    *    *    *    *    *
     *    *    *    *    *
"""

ASCII_GAMEOVER = r"""
      ____                         ___
     / ___| __ _ _ __ ___   ___   / _ \__   _____ _ __
    | |  _ / _` | '_ ` _ \ / _ \ | | | \ \ / / _ \ '__|
    | |_| | (_| | | | | | |  __/ | |_| |\ V /  __/ |
     \____|\__,_|_| |_| |_|\___|  \___/  \_/ \___|_|
"""

ASCII_CRAFT = r"""
    [Item A] + [Item B]
         \     /
          \   /
           \ /
        [New Item!]
"""

ASCII_MILESTONE = r"""
    ============================
    ||  MILESTONE REACHED!   ||
    ============================
"""


# ──────────────────────────────────────────────────────────────────────
# Dynamic ASCII Art Generator for AI-Generated Theme
# ──────────────────────────────────────────────────────────────────────
def generate_ai_ascii_art() -> str:
    """
    Generate dynamic ASCII art header using AI.
    Creates a unique, thematic visual header for each AI-generated adventure.
    Falls back to static patterns if AI generation fails.
    """
    # Skip AI generation in TEST_MODE or if we want to use fallback
    if TEST_MODE:
        return generate_ai_ascii_art_fallback()
    
    try:
        # Request AI to generate an ASCII art header
        prompt = (
            "Create a unique ASCII art header (5-8 lines) for a dynamic text adventure game. "
            "Use Unicode symbols like ═ ║ ╔ ╗ ╚ ╝ ▓ ▒ ░ ◆ ◊ ✧ ✦ ━ ─ │ ┌ ┐ └ ┘. "
            "Include a title (2-4 words) that evokes mystery, adventure, or the unknown. "
            "Add a short tagline (3-6 words). Make it visually striking and centered. "
            "Output ONLY the ASCII art, no explanations."
        )
        
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                "model": SELECTED_AI_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 1.2,  # Higher creativity for art
                "top_p": 0.95,
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json().get('response', '').strip()
            # Clean up any meta-text
            if result and len(result) > 30 and len(result) < 800:
                # Remove common AI prefixes
                for prefix in ["Here's", "Here is", "Sure", "Okay", "```", "**"]:
                    if result.startswith(prefix):
                        # Try to extract just the ASCII art
                        lines = result.split('\n')
                        result = '\n'.join(lines[1:]).strip()
                        break
                
                # Remove markdown code blocks
                result = result.replace('```', '').strip()
                
                if result and not result.startswith('I '):
                    return result
    except Exception as e:
        pass
    
    # Fallback to static patterns
    return generate_ai_ascii_art_fallback()


def generate_ai_intro_text() -> str:
    """
    Generate dynamic intro text using AI for the AI-Generated theme.
    Creates a unique narrative setup for each adventure.
    Falls back to default text if AI generation fails.
    """
    if TEST_MODE:
        return (
            "You embark on an adventure unlike any other. The path ahead is "
            "uncertain, shaped by forces beyond your control. Each moment brings "
            "new challenges, new mysteries. Powered by AI, your journey will be "
            "unique — no two adventures are ever the same."
        )
    
    try:
        prompt = (
            "Write a 3-4 sentence dramatic introduction for a text adventure game. "
            "The setting is mysterious and adaptive - could be any genre (fantasy, sci-fi, horror, etc). "
            "Make it atmospheric and intriguing. Emphasize that the journey is unique and unpredictable. "
            "Use second person ('You'). Keep it under 250 characters. "
            "Output ONLY the introduction text, no quotes or explanations."
        )
        
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                "model": SELECTED_AI_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 1.1,
                "top_p": 0.9,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json().get('response', '').strip()
            # Clean up quotes and meta-text
            result = result.strip('"\'').strip()
            if result and len(result) > 50 and len(result) < 600 and not result.startswith('I '):
                return result
    except Exception:
        pass
    
    # Fallback
    return (
        "You embark on an adventure unlike any other. The path ahead is "
        "uncertain, shaped by forces beyond your control. Each moment brings "
        "new challenges, new mysteries. Powered by AI, your journey will be "
        "unique — no two adventures are ever the same."
    )


def generate_ai_ascii_art_fallback() -> str:
    """
    Fallback static ASCII art patterns when AI generation unavailable.
    """
    patterns = [
        # Pattern 1: Hexagonal grid with stars
        r"""
    ▓▒░  ◊  UNWRITTEN DESTINY  ◊  ░▒▓
    ════════════════════════════════════
      ✦   Every choice shapes reality   ✦
    ════════════════════════════════════
            ╔═══════════════╗
            ║    ▓█░░░▓█    ║
            ║    ░░░░░░░░    ║
            ║    ░ TALE ░    ║
            ║    ░░░░░░░░    ║
            ╚═══════════════╝
        """,
        # Pattern 2: Cosmic/void theme
        r"""
    ◆ ▓▒░ INFINITE PATHS ░▒▓ ◆
    ━━━━━━━━━━━━━━━━━━━━━━━━━━
      ✧   A thousand futures await   ✧
    ━━━━━━━━━━━━━━━━━━━━━━━━━━
        ✧ ✦ ✧ ✦ ✧
       ✦   Reality bends   ✦
        ✧ ✦ ✧ ✦ ✧
        """,
        # Pattern 3: Fractal/recursive theme
        r"""
    ▓▒░ FRACTURED NARRATIVES ░▒▓
    ╔═══════════════════════════════╗
    ║  ┌─────────────────────────┐  ║
    ║  │  ◊ Your  Story ◊        │  ║
    ║  │  Echoes Across  Worlds  │  ║
    ║  └─────────────────────────┘  ║
    ╚═══════════════════════════════╝
        """,
        # Pattern 4: Probability/quantum theme
        r"""
      ◊ ▓▒░  QUANTUM ADVENTURE  ░▒▓ ◊
    ═══════════════════════════════════
       ✧ Superposition of all tales ✧
    ═══════════════════════════════════
       |⚛| OBSERVATION PENDING |⚛|
        """,
    ]
    return random.choice(patterns).strip()


# ──────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────
class ThemeId(Enum):
    DESERT = "desert"
    SPACE = "space"
    MIST = "mist"
    TIME = "time"
    CYBER = "cyber"
    AI_GENERATED = "ai_generated"


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class TimeOfDay(Enum):
    DAWN = "dawn"
    DAY = "day"
    DUSK = "dusk"
    NIGHT = "night"


class Weather(Enum):
    CLEAR = "clear"
    RAIN = "rain"
    FOG = "fog"
    STORM = "storm"


class StatusEffect(Enum):
    POISONED = "poisoned"
    INSPIRED = "inspired"
    EXHAUSTED = "exhausted"
    SHIELDED = "shielded"
    LUCKY = "lucky"


# ──────────────────────────────────────────────────────────────────────
# Difficulty multipliers
# ──────────────────────────────────────────────────────────────────────
DIFFICULTY_SETTINGS: dict[Difficulty, dict] = {
    Difficulty.EASY: {
        "supply_mult": 1.4,
        "damage_mult": 0.6,
        "event_chance": 0.30,
        "daily_consume": 0.7,
        "label": "Easy   — generous supplies, reduced damage",
    },
    Difficulty.NORMAL: {
        "supply_mult": 1.0,
        "damage_mult": 1.0,
        "event_chance": 0.40,
        "daily_consume": 1.0,
        "label": "Normal — balanced challenge",
    },
    Difficulty.HARD: {
        "supply_mult": 0.7,
        "damage_mult": 1.5,
        "event_chance": 0.55,
        "daily_consume": 1.3,
        "label": "Hard   — scarce supplies, brutal encounters",
    },
}


# ──────────────────────────────────────────────────────────────────────
# Theme definitions
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Theme:
    id: ThemeId
    name: str
    tagline: str
    ascii_art: str
    distance_unit: str
    total_distance: int
    supply_names: dict[str, str]
    starting_supplies: dict[str, int]
    special_item: str
    special_item_desc: str
    daily_distance: tuple[int, int]
    intro_text: str
    extra_events: list[Callable] = field(default_factory=list)


THEMES: dict[ThemeId, Theme] = {}


def _register_themes() -> None:
    THEMES[ThemeId.DESERT] = Theme(
        id=ThemeId.DESERT, name="The Desert Caravan",
        tagline="Cross the endless sands before your water runs out.",
        ascii_art=ASCII_DESERT, distance_unit="km", total_distance=2000,
        supply_names={"food": "Rations", "water": "Water Skins", "fuel": "Camel Stamina"},
        starting_supplies={"food": 60, "water": 70, "fuel": 40},
        special_item="Quicksilver Flask",
        special_item_desc="Purifies tainted water found in oases.",
        daily_distance=(15, 45),
        intro_text=(
            "The year is 1342 of the Amber Calendar.  You lead a caravan of "
            "merchants across the Great Vytharian Desert, a vast expanse of "
            "golden dunes where sandstorms can bury entire caravans overnight.  "
            "Your goal: reach the fortified trade city of Alqarim, 2 000 km to "
            "the east, before your water runs dry."
        ),
    )
    THEMES[ThemeId.SPACE] = Theme(
        id=ThemeId.SPACE, name="Space Colony Expedition",
        tagline="Navigate the void between stars to reach a new home.",
        ascii_art=ASCII_SPACE, distance_unit="AU", total_distance=2000,
        supply_names={"food": "Nutrient Packs", "water": "Hydro-Gel", "fuel": "Plasma Cells"},
        starting_supplies={"food": 55, "water": 55, "fuel": 50},
        special_item="Solar-Charger",
        special_item_desc="Recharges plasma cells using nearby star radiation.",
        daily_distance=(20, 55),
        intro_text=(
            "Aboard the colony ship *Aethon VII*, you are the expedition leader "
            "tasked with reaching the habitable moon Erythia-4.  The journey "
            "spans 2 000 AU through uncharted space.  Micro-meteorites, solar "
            "flares, and dwindling supplies threaten your crew of 200 colonists. "
            "Every decision you make could mean life or death."
        ),
    )
    THEMES[ThemeId.MIST] = Theme(
        id=ThemeId.MIST, name="Lost Kingdom of the Mist",
        tagline="Venture through enchanted fog to find the Forgotten Throne.",
        ascii_art=ASCII_MIST, distance_unit="leagues", total_distance=2000,
        supply_names={"food": "Dried Herbs", "water": "Moonwell Vials", "fuel": "Torchlight"},
        starting_supplies={"food": 65, "water": 50, "fuel": 35},
        special_item="Eldritch Lantern",
        special_item_desc="Reveals hidden paths obscured by magical mist.",
        daily_distance=(10, 40),
        intro_text=(
            "Legends speak of Valdros, a kingdom swallowed by an ancient mist "
            "spell centuries ago.  You are a wandering scholar who has found "
            "part of a map leading deep into the Shrouded Expanse.  The mist "
            "distorts time and space — travel 2 000 leagues and you may reach "
            "the Forgotten Throne, or you may lose yourself forever."
        ),
    )
    THEMES[ThemeId.TIME] = Theme(
        id=ThemeId.TIME, name="Time-Travel Expedition",
        tagline="Leap across eras to repair the fractured timeline.",
        ascii_art=ASCII_TIME, distance_unit="chrono-leaps", total_distance=2000,
        supply_names={"food": "Ration Capsules", "water": "Temporal Coolant", "fuel": "Flux Energy"},
        starting_supplies={"food": 50, "water": 50, "fuel": 55},
        special_item="Chrono-Filter",
        special_item_desc="Protects against temporal distortions and paradoxes.",
        daily_distance=(20, 60),
        intro_text=(
            "The Temporal Concord has detected fractures across the timeline.  "
            "As a licensed Chrono-Agent, you must pilot the Drift-Vessel through "
            "2 000 chrono-leaps, mending paradoxes before they unravel reality. "
            "Time itself fights back — expect echoes of erased futures and "
            "hostile anachronisms at every turn."
        ),
    )
    THEMES[ThemeId.CYBER] = Theme(
        id=ThemeId.CYBER, name="Cyberpunk Heist",
        tagline="Infiltrate the mega-corp tower before the net-cops trace you.",
        ascii_art=ASCII_CYBER, distance_unit="nodes", total_distance=2000,
        supply_names={"food": "Stim-Packs", "water": "Coolant Gel", "fuel": "Battery Charge"},
        starting_supplies={"food": 45, "water": 45, "fuel": 60},
        special_item="Ghost-Cipher",
        special_item_desc="Masks your digital signature from corporate sentries.",
        daily_distance=(25, 65),
        intro_text=(
            "Neo-Karvost, 2187.  The mega-corporation Omnivault controls the "
            "city's neural grid.  You are a freelance net-runner hired by the "
            "underground to breach Omnivault Tower — 2 000 security nodes deep. "
            "Hack, bluff, and fight your way through corporate ICE, rogue AIs, "
            "and rival runners.  The payout is freedom… if you survive."
        ),
    )
    THEMES[ThemeId.AI_GENERATED] = Theme(
        id=ThemeId.AI_GENERATED, name="AI-Generated Adventure",
        tagline="Dynamic scenarios powered by Ollama — every playthrough is unique.",
        ascii_art="[Generating unique ASCII art...]",  # Placeholder; actual art generated dynamically
        distance_unit="km", total_distance=2000,
        supply_names={"food": "Provisions", "water": "Water", "fuel": "Energy"},
        starting_supplies={"food": 60, "water": 70, "fuel": 50},
        special_item="Adaptive Toolkit",
        special_item_desc="A versatile tool that adapts to any situation.",
        daily_distance=(20, 50),
        intro_text=(
            "You embark on an adventure unlike any other. The path ahead is "
            "uncertain, shaped by forces beyond your control. Each moment brings "
            "new challenges, new mysteries. Powered by AI, your journey will be "
            "unique — no two adventures are ever the same."
        ),
    )


_register_themes()


# ──────────────────────────────────────────────────────────────────────
# Companion definitions
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Companion:
    name: str
    title: str
    bonus_type: str          # "health" | "morale" | "supply" | "combat" | "scout"
    bonus_value: int
    flavour: str

    def describe(self) -> str:
        return f"{self.name} the {self.title} — {self.flavour} (bonus: +{self.bonus_value} {self.bonus_type})"


COMPANION_POOL: dict[ThemeId, list[Companion]] = {
    ThemeId.DESERT: [
        Companion("Kael", "Sand Tracker", "scout", 8, "Knows every dune and oasis"),
        Companion("Mirra", "Herbalist", "health", 5, "Brews healing salves from desert plants"),
        Companion("Daro", "Blade Dancer", "combat", 6, "Fearsome with twin curved blades"),
    ],
    ThemeId.SPACE: [
        Companion("AXON-7", "Repair Drone", "supply", 4, "Patches hull breaches and recycles waste"),
        Companion("Dr. Voss", "Xenobiologist", "health", 5, "Expert in alien biology and medicine"),
        Companion("Renko", "Pilot", "scout", 7, "Can navigate asteroid fields blindfolded"),
    ],
    ThemeId.MIST: [
        Companion("Thalia", "Mist Seer", "scout", 9, "Sees through enchanted fog"),
        Companion("Grumm", "Stone Golem", "combat", 7, "Slow but nearly indestructible"),
        Companion("Elara", "Bard", "morale", 8, "Her songs lift spirits and ward off despair"),
    ],
    ThemeId.TIME: [
        Companion("Epoch", "Chrono-Cat", "scout", 6, "Senses temporal anomalies before they strike"),
        Companion("Lysander", "Historian", "morale", 7, "Knowledge of past eras prevents mistakes"),
        Companion("Bolt", "Temporal Mechanic", "supply", 5, "Keeps the Drift-Vessel running"),
    ],
    ThemeId.CYBER: [
        Companion("Nyx", "Street Samurai", "combat", 8, "Chrome-plated and lethal"),
        Companion("Pixel", "Info Broker", "scout", 6, "Has eyes in every camera"),
        Companion("Patch", "Street Doc", "health", 6, "Keeps you alive with back-alley surgery"),
    ],
}


# ──────────────────────────────────────────────────────────────────────
# Riddle pool
# ──────────────────────────────────────────────────────────────────────
RIDDLES: list[tuple[str, list[str], int]] = [
    # (question, [options], correct_index_0based)
    (
        "I have cities but no houses, forests but no trees, water but no fish.\n  What am I?",
        ["A globe", "A map", "A painting", "A dream"],
        1,
    ),
    (
        "The more you take, the more you leave behind. What am I?",
        ["Breaths", "Steps", "Footsteps", "Memories"],
        2,
    ),
    (
        "I speak without a mouth and hear without ears.\n  I have no body, but I come alive with the wind. What am I?",
        ["A ghost", "An echo", "A shadow", "A whisper"],
        1,
    ),
    (
        "What has keys but no locks, space but no room,\n  and you can enter but can't go inside?",
        ["A riddle", "A keyboard", "A mansion", "A treasure chest"],
        1,
    ),
    (
        "I am not alive, but I grow; I have no lungs, but I need air;\n  I have no mouth, but water kills me. What am I?",
        ["A crystal", "Ice", "Fire", "A mushroom"],
        2,
    ),
    (
        "What can travel around the world while staying in a corner?",
        ["A spider", "A stamp", "A shadow", "The wind"],
        1,
    ),
    (
        "I have hands but cannot clap. What am I?",
        ["A statue", "A clock", "A puppet", "A glove"],
        1,
    ),
    (
        "What gets wetter the more it dries?",
        ["Sand", "A sponge", "A towel", "Salt"],
        2,
    ),
]

# ──────────────────────────────────────────────────────────────────────
# AI Scenario Generation (Ollama)
# ──────────────────────────────────────────────────────────────────────

# Cache for Ollama model list to avoid repeated queries
_OLLAMA_MODEL_CACHE: list[dict[str, Any]] | None = None
_OLLAMA_CACHE_TIME: float = 0.0
OLLAMA_CACHE_DURATION: float = 300.0  # Cache models for 5 minutes

AI_SCENARIO_TEMPLATES: dict[ThemeId, list[str]] = {
    ThemeId.DESERT: [
        "You discover ancient ruins half-buried in the sand. Inscriptions glow faintly.",
        "A mirage appears—but it feels too real. Something moves within it.",
        "The sand beneath your feet suddenly shifts. You've stumbled upon a hidden cavern.",
        "A solitary figure on the horizon signals urgently. They seem to know you're coming.",
        "You find strange crystalline formations that sing in the wind.",
    ],
    ThemeId.SPACE: [
        "An unidentified signal emanates from nearby asteroids. It's in a familiar frequency.",
        "The ship's scanners detect an artificial construct from unknown origins.",
        "Spatial radiation spikes. Your instruments show a temporal distortion ahead.",
        "You receive a distress beacon—but it's dated from 50 years in the future.",
        "A dormant alien probe awakens as you pass. It begins transmitting.",
    ],
    ThemeId.MIST: [
        "The fog parts briefly, revealing a city that shouldn't exist on any map.",
        "Ancient music echoes through the mist. Your companions feel strangely drawn to it.",
        "A figure made of mist approaches. It wears a crown of spectral light.",
        "The ground beneath you becomes solid—a bridge appears out of nowhere.",
        "The mist turns colours you've never seen before. It feels alive.",
    ],
    ThemeId.TIME: [
        "You stumble upon a moment where two timelines overlap. You see yourself arriving.",
        "A chrono-anomaly reveals futures that never were. Some look better, some worse.",
        "You find a journal written in your own handwriting... decades in the future.",
        "The fabric of time stutters. You catch glimpses of parallel journeys.",
        "A Time Guardian manifests, warning of a paradox in your path ahead.",
    ],
    ThemeId.CYBER: [
        "You intercept a data stream from a rival runner—they know your infiltration path.",
        "The building's AI suddenly goes silent. Someone else has jacked in.",
        "A black-market neural implant vendor contacts you with intel on the vault.",
        "Ghost code—remnants of a previous hack—activates and helps you bypass security.",
        "A corporate kill-team arrives early. Someone leaked your timeline.",
    ],
    ThemeId.AI_GENERATED: [
        "Reality shifts around you. The path ahead morphs into something unexpected.",
        "A presence watches from the shadows. It knows your name, though you've never met.",
        "Time and space fracture. You glimpse a thousand possible futures at once.",
        "The world glitches. For a moment, you see the code underlying everything.",
        "A voice echoes from nowhere: 'This is not how your story was meant to unfold.'",
        "The environment warps. Colors bleed into sounds, and gravity becomes optional.",
        "You encounter a door that wasn't there before. It bears your initials.",
        "Memory fragments from lives you never lived flood your consciousness.",
        "A strange artifact pulses with energy. It reacts specifically to your presence.",
        "The boundary between dream and reality thins. Which side are you on?",
        "Symbols appear in the air around you, rearranging into a warning message.",
        "You hear your own voice calling from the distance, but different—older, wiser.",
        "The path splits into impossible directions. Each feels equally certain and wrong.",
        "Something ancient stirs. It has been waiting specifically for you to arrive.",
        "Reality loops. You've experienced this exact moment before, but differently.",
        "A threshold appears. Crossing it will change everything, but standing still will too.",
        "The narrative itself seems to falter. You sense the story rewriting around you.",
        "Probability collapses. Multiple outcomes exist simultaneously until you choose.",
        "You discover evidence of your own future actions. The causality makes no sense.",
        "The journey reveals itself to be a test. But who set it, and why?",
    ],
}


def query_ollama_models() -> list[dict[str, Any]]:
    """
    Query Ollama for available models, sorted by size (smallest first).
    Returns list of model info dicts with 'name' and 'size' keys.
    Uses caching to avoid repeated network calls.
    """
    global _OLLAMA_MODEL_CACHE, _OLLAMA_CACHE_TIME
    
    # Check cache validity
    current_time = time.time()
    if _OLLAMA_MODEL_CACHE is not None and (current_time - _OLLAMA_CACHE_TIME) < OLLAMA_CACHE_DURATION:
        return _OLLAMA_MODEL_CACHE
    
    try:
        response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            # Sort by size (smallest first)
            sorted_models = sorted(models, key=lambda m: m.get('size', 0))
            # Update cache
            _OLLAMA_MODEL_CACHE = sorted_models
            _OLLAMA_CACHE_TIME = current_time
            return sorted_models
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        pass
    return []


def select_ai_model() -> str:
    """
    Let user select an Ollama model from available models.
    Returns selected model name, defaults to gemma3:4b if available.
    """
    global SELECTED_AI_MODEL
    
    print(f"\n  {Fore.CYAN}Querying Ollama for available models...{Style.RESET_ALL}")
    models = query_ollama_models()
    
    if not models:
        print(f"  {Fore.YELLOW}Warning: Could not connect to Ollama.{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Make sure Ollama is running on {OLLAMA_URL}{Style.RESET_ALL}")
        print(f"  Using fallback templates for scenarios.\n")
        return "gemma3:4b"  # Will fall back to templates
    
    print(f"\n  {Fore.GREEN}Found {len(models)} model(s):{Style.RESET_ALL}\n")
    
    # Find default (gemma3:4b if available)
    default_idx = 0
    for idx, model in enumerate(models):
        name = model.get('name', 'unknown')
        size = model.get('size', 0)
        size_mb = size / (1024 * 1024)
        size_gb = size / (1024 * 1024 * 1024)
        
        if size_gb >= 1:
            size_str = f"{size_gb:.1f}GB"
        else:
            size_str = f"{size_mb:.0f}MB"
        
        is_default = "gemma3:4b" in name.lower()
        if is_default:
            default_idx = idx
            print(f"  {idx + 1}. {Fore.GREEN}{name:30}{Style.RESET_ALL} ({size_str}) {Fore.CYAN}[RECOMMENDED]{Style.RESET_ALL}")
        else:
            print(f"  {idx + 1}. {name:30} ({size_str})")
    
    if not TEST_MODE:
        print(f"\n  Select model (default: {default_idx + 1}): ", end="")
        choice = input().strip()
        if not choice:
            choice = str(default_idx + 1)
    else:
        choice = str(default_idx + 1)
    
    try:
        selected = models[int(choice) - 1]
        SELECTED_AI_MODEL = selected.get('name', 'gemma3:4b')
        print(f"  {Fore.GREEN}Selected: {SELECTED_AI_MODEL}{Style.RESET_ALL}\n")
    except (ValueError, IndexError):
        SELECTED_AI_MODEL = models[default_idx].get('name', 'gemma3:4b')
        print(f"  {Fore.YELLOW}Invalid choice. Using: {SELECTED_AI_MODEL}{Style.RESET_ALL}\n")
    
    return SELECTED_AI_MODEL


def generate_ai_scenario(theme: ThemeId, scenario_type: str = "general", seen_scenarios: set[str] = None) -> str:
    """
    Generate a scenario using selected Ollama model, with template fallback.
    Returns a single-paragraph scenario description (truncated for readability).
    Guarantees uniqueness by checking against seen_scenarios.
    
    scenario_type: 'general', 'danger', 'mystery', 'discovery', 'encounter'
    seen_scenarios: set of previously seen scenario texts to avoid duplicates
    """
    if seen_scenarios is None:
        seen_scenarios = set()
    
    # For AI_GENERATED theme, pick a random theme for context
    original_theme = theme
    if theme == ThemeId.AI_GENERATED:
        theme = random.choice([ThemeId.DESERT, ThemeId.SPACE, ThemeId.MIST, ThemeId.TIME, ThemeId.CYBER])
    
    # Skip AI generation in TEST_MODE - go straight to templates
    if not TEST_MODE:
        try:
            # Show loading indicator
            print(f"  {Fore.CYAN}[Generating scenario...]{Style.RESET_ALL}")
            
            # Vary prompts based on scenario type for more diversity
            prompt_variations = {
                "general": [
                    f"Write a mysterious 2-3 sentence event in a {theme.value} adventure. Include sensory details.",
                    f"Describe an unexpected discovery in a {theme.value} setting. Be atmospheric and vivid.",
                    f"Create a tense moment of choice in a {theme.value} journey. Focus on mood and stakes.",
                ],
                "danger": [
                    f"Write a dangerous encounter in a {theme.value} world. Build suspense in 2-3 sentences.",
                    f"Describe a threat emerging in a {theme.value} environment. Make it visceral.",
                ],
                "mystery": [
                    f"Write a cryptic discovery in a {theme.value} setting. Leave questions unanswered.",
                    f"Describe something impossible in a {theme.value} world. Create wonder and unease.",
                ],
                "discovery": [
                    f"Write about finding something valuable in a {theme.value} journey. Build excitement.",
                    f"Describe stumbling upon secrets in a {theme.value} landscape. Make it feel earned.",
                ],
                "encounter": [
                    f"Write about meeting someone unique in a {theme.value} world. Show character through details.",
                    f"Describe an unexpected ally or enemy in a {theme.value} setting. Make them memorable.",
                ],
            }
            
            prompt = random.choice(prompt_variations.get(scenario_type, prompt_variations["general"]))
            # Vary temperature for more diversity (higher = more creative)
            temperature = random.uniform(0.75, 1.1)
            
            import time
            start_time = time.time()
            response = requests.post(
                f'{OLLAMA_URL}/api/generate',
                json={
                    "model": SELECTED_AI_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40,
                },
                timeout=10  # Reduced from 15s for better responsiveness
            )
            gen_time = time.time() - start_time
            
            # Log generation performance for monitoring
            if LOGGING_ENABLED and hasattr(globals().get('_current_logger'), 'log_event'):
                try:
                    _current_logger.log_event({
                        "type": "ai_generation_performance",
                        "model": SELECTED_AI_MODEL,
                        "scenario_type": scenario_type,
                        "generation_time_seconds": round(gen_time, 3),
                        "success": False  # Will be updated if successful
                    })
                except:
                    pass
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                # Filter out meta-text and unwanted patterns from Ollama
                unwanted_prefixes = (
                    "Okay, here's", "Here's a", "Sure, here",
                    "**", "Alright", "Certainly,", "I'll create",
                )
                for prefix in unwanted_prefixes:
                    if result.startswith(prefix):
                        result = ""  # Mark for fallback
                        break
                
                # Truncate to ~300 chars (roughly 2-3 sentences) for better pacing
                if result and len(result) > 20:
                    if len(result) > 350:
                        # Find good truncation point (end of sentence)
                        result = result[:350]
                        last_period = result.rfind('.')
                        if last_period > 100:  # Ensure we keep at least some content
                            result = result[:last_period + 1]
                    
                    if result not in seen_scenarios:  # Ensure unique output
                        return result
                # If we got a duplicate, fall through to try again with template
        except (requests.RequestException, json.JSONDecodeError, KeyError, requests.Timeout, ConnectionError) as e:
            # Log AI generation failure for debugging
            if not TEST_MODE:
                try:
                    print(f"  {Fore.YELLOW}[AI generation failed, using template]{Style.RESET_ALL}")
                except:
                    pass
    
    # Fallback: use template scenarios (filter out seen ones)
    # For AI_GENERATED theme, if templates exhausted, borrow from other themes
    if theme == ThemeId.AI_GENERATED and theme in AI_SCENARIO_TEMPLATES:
        available_templates = [t for t in AI_SCENARIO_TEMPLATES[theme] if t not in seen_scenarios]
        if not available_templates:
            # All AI_GENERATED templates seen, borrow from other themes
            all_other_templates = []
            for t_id in [ThemeId.DESERT, ThemeId.SPACE, ThemeId.MIST, ThemeId.TIME, ThemeId.CYBER]:
                all_other_templates.extend(AI_SCENARIO_TEMPLATES[t_id])
            available_templates = [t for t in all_other_templates if t not in seen_scenarios]
            if available_templates:
                return random.choice(available_templates)
        if available_templates:
            return random.choice(available_templates)
    elif theme in AI_SCENARIO_TEMPLATES:
        available_templates = [t for t in AI_SCENARIO_TEMPLATES[theme] if t not in seen_scenarios]
        if available_templates:
            return random.choice(available_templates)
        # If all templates seen, allow reuse but modify slightly
        base = random.choice(AI_SCENARIO_TEMPLATES[theme])
        variations = [
            f"{base} The situation feels eerily familiar.",
            f"{base} Something about this reminds you of before.",
            f"{base} Déjà vu washes over you.",
        ]
        return random.choice(variations)
    
    return "A strange turn of events unfolds before you. The air crackles with possibility."


# ──────────────────────────────────────────────────────────────────────
# Crafting recipes
# ──────────────────────────────────────────────────────────────────────
CRAFT_RECIPES: list[tuple[str, str, str, str]] = [
    # (ingredient_a, ingredient_b, result, description)
    ("Healer's Salve", "Morale Charm", "Elixir of Vitality",
     "Restores 40 health and 30 morale."),
    ("Signal-Flare", "Solar-Charger", "Beacon Array",
     "A powerful rescue signal. Guarantees the best ending."),
    ("Ironbark Shield", "Wanderer's Compass", "Guardian's Mantle",
     "Blocks one attack AND boosts travel distance."),
    ("Quicksilver Flask", "Healer's Salve", "Purified Tonic",
     "Restores 15 water and 20 health."),
]

# ──────────────────────────────────────────────────────────────────────
# Achievement definitions
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Achievement:
    id: str
    name: str
    description: str
    unlocked: bool = False

    def unlock(self) -> bool:
        """Returns True if newly unlocked."""
        if not self.unlocked:
            self.unlocked = True
            return True
        return False


def _make_achievements() -> dict[str, Achievement]:
    defs = [
        ("first_blood", "First Blood", "Survive your first combat encounter"),
        ("trader", "Shrewd Trader", "Complete a trade with a merchant"),
        ("riddler", "Riddle Master", "Solve a riddle correctly"),
        ("crafter", "Artisan", "Craft an item from two components"),
        ("companion", "Fellowship", "Recruit a companion"),
        ("survivor", "Survivor", "Complete the journey alive"),
        ("flawless", "Flawless", "Finish with health >= 80"),
        ("hoarder", "Hoarder", "Collect 5 or more items"),
        ("explorer", "Explorer", "Scout 5 times during the journey"),
        ("night_owl", "Night Owl", "Travel during the night"),
        ("milestone_25", "Quarter Way", "Reach 25% of the journey"),
        ("milestone_50", "Halfway There", "Reach 50% of the journey"),
        ("milestone_75", "Final Stretch", "Reach 75% of the journey"),
        ("best_ending", "Legend", "Achieve the best possible ending"),
        ("gambler", "High Roller", "Win the dice game"),
        ("weather_master", "Storm Chaser", "Push through a storm successfully"),
    ]
    return {d[0]: Achievement(*d) for d in defs}


# ──────────────────────────────────────────────────────────────────────
# Item catalogue (expanded)
# ──────────────────────────────────────────────────────────────────────
ITEM_CATALOGUE: dict[str, str] = {
    "Quicksilver Flask": "Purifies tainted water sources, restoring +10 water.",
    "Eldritch Lantern": "Reveals hidden paths and wards off mist creatures.",
    "Chrono-Filter": "Shields you from temporal paradoxes and traps.",
    "Solar-Charger": "Recharges fuel reserves by +15 using ambient energy.",
    "Ghost-Cipher": "Masks your digital signature, bypassing security nodes.",
    "Signal-Flare": "Attracts rescue parties; used at journey's end.",
    "Ironbark Shield": "Absorbs one lethal attack, saving your life.",
    "Wanderer's Compass": "Increases daily travel distance by 10.",
    "Healer's Salve": "Restores 25 health when applied.",
    "Morale Charm": "Boosts morale by 20; a trinket of good fortune.",
    # v2 items
    "Elixir of Vitality": "Restores 40 health and 30 morale. (Crafted)",
    "Beacon Array": "A powerful rescue signal. Guarantees the best ending. (Crafted)",
    "Guardian's Mantle": "Blocks one attack AND boosts travel distance. (Crafted)",
    "Purified Tonic": "Restores 15 water and 20 health. (Crafted)",
    "Shadow Cloak": "Lets you avoid one hostile encounter entirely.",
    "Stormglass Vial": "Predicts weather, lets you prepare for storms.",
    "Ember Stone": "Keeps your camp warm, reducing night penalties.",
}


# ──────────────────────────────────────────────────────────────────────
# Player
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Player:
    name: str
    theme: Theme
    difficulty: Difficulty = Difficulty.NORMAL
    health: int = 100
    morale: int = 100
    supplies: dict[str, int] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    distance_travelled: int = 0
    days: int = 0
    seed: int | None = None
    companion: Companion | None = None
    status_effects: dict[StatusEffect, int] = field(default_factory=dict)  # effect -> remaining days
    achievements: dict[str, Achievement] = field(default_factory=dict)
    time_of_day: TimeOfDay = TimeOfDay.DAWN
    weather: Weather = Weather.CLEAR
    scout_count: int = 0
    combats_survived: int = 0
    milestones_hit: set[int] = field(default_factory=set)  # percentages hit
    food_debt: float = 0.0  # Track fractional food consumption
    water_debt: float = 0.0  # Track fractional water consumption
    seen_scenarios: set[str] = field(default_factory=set)  # AI scenarios seen this playthrough

    def __post_init__(self) -> None:
        if not self.supplies:
            # Apply difficulty multiplier
            mult = DIFFICULTY_SETTINGS[self.difficulty]["supply_mult"]
            
            # Apply auto-tuning adjustments
            load_tuning_config()
            theme_key = f"theme_{self.theme.name}_supply_multiplier"
            mult *= get_tuned_value(theme_key, 1.0)
            
            # Global easy mode boost if tuning recommends
            if self.difficulty == Difficulty.EASY:
                mult *= get_tuned_value("global_easy_boost", 1.0)
            
            # Difficulty-specific multipliers
            diff_key = f"difficulty_{self.difficulty.value}_multiplier"
            mult *= get_tuned_value(diff_key, 1.0)
            
            self.supplies = {k: int(v * mult) for k, v in self.theme.starting_supplies.items()}
        
        # Apply initial health tuning
        health_mult = get_tuned_value("initial_health_multiplier", 1.0)
        if health_mult != 1.0:
            self.health = int(self.health * health_mult)
        
        if not self.achievements:
            self.achievements = _make_achievements()

    # --- helpers ---
    def has(self, item: str) -> bool:
        return item in self.inventory

    def add_item(self, item: str) -> None:
        if item not in self.inventory:
            self.inventory.append(item)
            print(f"  {Fore.GREEN}+ {item}{Style.RESET_ALL} added to inventory.")
            if len(self.inventory) >= 5:
                self.try_unlock("hoarder")
        else:
            print(f"  (You already have {item}.)")

    def remove_item(self, item: str) -> None:
        if item in self.inventory:
            self.inventory.remove(item)
            print(f"  {Fore.YELLOW}- {item}{Style.RESET_ALL} removed from inventory.")

    def adjust_supply(self, key: str, delta: int) -> None:
        old = self.supplies[key]
        self.supplies[key] = int(clamp(old + delta, 0, 999))
        label = self.theme.supply_names.get(key, key)
        colour = Fore.GREEN if delta > 0 else Fore.RED
        sign = "+" if delta > 0 else ""
        print(f"  {colour}{sign}{delta} {label}{Style.RESET_ALL}")

    def damage(self, amount: int) -> None:
        """Apply damage scaled by difficulty and status effects."""
        mult = DIFFICULTY_SETTINGS[self.difficulty]["damage_mult"]
        
        # Apply auto-tuning for combat damage
        mult *= get_tuned_value("combat_damage_multiplier", 1.0)
        
        # Apply difficulty-specific damage reduction tuning
        diff_dmg_key = f"difficulty_{self.difficulty.value}_damage_reduction"
        mult *= get_tuned_value(diff_dmg_key, 1.0)
        
        if StatusEffect.SHIELDED in self.status_effects:
            mult *= 0.5
            print(f"  {Fore.CYAN}(Shielded — damage halved!){Style.RESET_ALL}")
        if self.companion and self.companion.bonus_type == "combat":
            mult *= 0.8
        actual = max(1, int(amount * mult))
        self.health -= actual
        print(f"  {Fore.RED}Health -{actual}{Style.RESET_ALL}")

    def heal(self, amount: int) -> None:
        old = self.health
        self.health = int(clamp(self.health + amount, 0, 100))
        gained = self.health - old
        if gained > 0:
            print(f"  {Fore.GREEN}Health +{gained}{Style.RESET_ALL}")

    def consume_daily(self) -> None:
        # Use fractional debt accumulation to allow tuning to work with values < 1.0
        # This prevents the rounding issue where 0.65 → 0 → max(1,0) → 1 (broken)
        mult = DIFFICULTY_SETTINGS[self.difficulty]["daily_consume"]
        
        # Apply auto-tuning for consumption rates
        mult *= get_tuned_value("food_consumption_rate", 1.0)
        self.food_debt += mult
        food_cost = int(self.food_debt)
        self.food_debt -= food_cost
        
        mult_water = DIFFICULTY_SETTINGS[self.difficulty]["daily_consume"]
        mult_water *= get_tuned_value("water_consumption_rate", 1.0)
        self.water_debt += mult_water
        water_cost = int(self.water_debt)
        self.water_debt -= water_cost
        
        if StatusEffect.EXHAUSTED in self.status_effects:
            food_cost += 1
            water_cost += 1
        if self.companion and self.companion.bonus_type == "supply":
            food_cost = max(0, food_cost - 1)
        self.supplies["food"] = max(0, self.supplies["food"] - food_cost)
        self.supplies["water"] = max(0, self.supplies["water"] - water_cost)

    def is_alive(self) -> bool:
        return self.health > 0

    def is_starving(self) -> bool:
        return self.supplies["food"] <= 0 or self.supplies["water"] <= 0

    def add_effect(self, effect: StatusEffect, duration: int) -> None:
        self.status_effects[effect] = duration
        icons = {
            StatusEffect.POISONED: f"{Fore.RED}POISONED{Style.RESET_ALL}",
            StatusEffect.INSPIRED: f"{Fore.GREEN}INSPIRED{Style.RESET_ALL}",
            StatusEffect.EXHAUSTED: f"{Fore.YELLOW}EXHAUSTED{Style.RESET_ALL}",
            StatusEffect.SHIELDED: f"{Fore.CYAN}SHIELDED{Style.RESET_ALL}",
            StatusEffect.LUCKY: f"{Fore.MAGENTA}LUCKY{Style.RESET_ALL}",
        }
        print(f"  Status effect: {icons.get(effect, effect.value)} for {duration} days")

    def tick_effects(self) -> None:
        """Process status effects each day."""
        expired = []
        for effect, remaining in self.status_effects.items():
            if effect == StatusEffect.POISONED:
                self.health -= 5
                print(f"  {Fore.RED}Poison deals 5 damage...{Style.RESET_ALL}")
            elif effect == StatusEffect.INSPIRED:
                self.morale = int(clamp(self.morale + 3, 0, 100))
            if remaining <= 1:
                expired.append(effect)
            else:
                self.status_effects[effect] = remaining - 1
        for e in expired:
            del self.status_effects[e]
            print(f"  Status effect {e.value} has worn off.")

    def try_unlock(self, ach_id: str) -> None:
        if ach_id in self.achievements and self.achievements[ach_id].unlock():
            ach = self.achievements[ach_id]
            print(f"\n  {Fore.YELLOW}{ASCII_ACHIEVEMENT}{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}★ Achievement Unlocked: {ach.name}{Style.RESET_ALL}")
            print(f"    {ach.description}\n")
            log_game("achievement_unlock", {"achievement": ach_id, "name": ach.name})
            pause(0.8)

    def status_text(self) -> str:
        t = self.theme
        pct = int(self.distance_travelled / t.total_distance * 100)
        return (
            f"  Day {self.days}  |  "
            f"{self.distance_travelled}/{t.total_distance} {t.distance_unit} ({pct}%)  |  "
            f"{self.time_of_day.value.title()} — {self.weather.value.title()}"
        )


# ──────────────────────────────────────────────────────────────────────
# Weather system
# ──────────────────────────────────────────────────────────────────────
def advance_weather(player: Player) -> None:
    """Shift weather each day based on probabilities."""
    if player.has("Stormglass Vial"):
        # player can see forecast
        pass  # shown in status
    weights = {
        Weather.CLEAR: 45,
        Weather.RAIN: 25,
        Weather.FOG: 20,
        Weather.STORM: 10,
    }
    # storms more likely at night
    if player.time_of_day == TimeOfDay.NIGHT:
        weights[Weather.STORM] += 15
        weights[Weather.CLEAR] -= 10
    player.weather = random.choices(list(weights.keys()), list(weights.values()), k=1)[0]


def advance_time_of_day(player: Player) -> None:
    """Cycle through 4 times of day."""
    cycle = [TimeOfDay.DAWN, TimeOfDay.DAY, TimeOfDay.DUSK, TimeOfDay.NIGHT]
    idx = cycle.index(player.time_of_day)
    player.time_of_day = cycle[(idx + 1) % 4]

    if player.time_of_day == TimeOfDay.DAWN:
        print(colorize_ascii(ASCII_DAWN, Fore.YELLOW))
        print(f"  {Fore.YELLOW}A new dawn breaks.{Style.RESET_ALL}")
    elif player.time_of_day == TimeOfDay.NIGHT:
        print(colorize_ascii(ASCII_NIGHT, Fore.CYAN))
        print(f"  {Fore.CYAN}Night falls. Dangers increase.{Style.RESET_ALL}")
        if not player.has("Ember Stone"):
            print(f"  {Fore.YELLOW}The cold saps your energy without an Ember Stone.{Style.RESET_ALL}")
            player.morale = max(0, player.morale - 3)


def weather_art(w: Weather) -> str:
    return {
        Weather.CLEAR: ASCII_WEATHER_CLEAR,
        Weather.RAIN: ASCII_WEATHER_RAIN,
        Weather.FOG: ASCII_WEATHER_FOG,
        Weather.STORM: ASCII_STORM,
    }.get(w, "")


# ──────────────────────────────────────────────────────────────────────
# Milestone narrative events
# ──────────────────────────────────────────────────────────────────────
MILESTONE_NARRATIVES: dict[ThemeId, dict[int, str]] = {
    ThemeId.DESERT: {
        25: "You crest a ridge and see a vast salt flat shimmering below.  Halfway to "
            "the first oasis.  The caravan's spirits rise — or maybe it's just a mirage.",
        50: "The ancient Well of Embers appears as marked on your map.  You fill your "
            "skins while your scouts report distant dust clouds — another caravan, or raiders?",
        75: "The towers of Alqarim are visible on the horizon like teeth of gold.  But "
            "the Scorched Pass lies between you and the city — the most dangerous stretch.",
    },
    ThemeId.SPACE: {
        25: "The Aethon VII passes through the Kalari Nebula.  Sensors light up with "
            "exotic particles.  The crew gathers at the viewports in rare wonder.",
        50: "You reach the midpoint refuelling beacon — but it's been stripped.  Someone "
            "was here before you.  Scorch marks suggest they didn't leave willingly.",
        75: "Erythia-4's pale blue glow fills the cockpit.  Almost there — but long-range "
            "scans detect an orbital minefield from an ancient war.",
    },
    ThemeId.MIST: {
        25: "The mist thins for a moment and you see the ruins of an old watchtower.  "
            "Carved into the stone: 'Turn back.  The Throne defends itself.'",
        50: "You find a Valdrosian way-station, its hearth still warm.  Someone — or "
            "something — was here moments ago.  The mist closes in tighter.",
        75: "The Forgotten Throne's silhouette looms through the fog, impossibly tall. "
            "The ground hums with ancient magic.  Your lantern flickers.",
    },
    ThemeId.TIME: {
        25: "You emerge in the Bronze Age.  Mammoths graze peacefully nearby.  The next "
            "fracture beacon pulses at the edge of a glacier.",
        50: "The timeline shudders.  You glimpse your own ship arriving just moments ago — "
            "a paradox loop.  Your Chrono-Filter crackles with strain.",
        75: "The origin fracture is visible: a swirling maelstrom of past, present, and "
            "future colliding.  This is where reality broke.",
    },
    ThemeId.CYBER: {
        25: "You breach the outer firewall.  Omnivault's security AI pings your location "
            "but your Ghost-Cipher holds… for now.",
        50: "Floor 50 of the tower.  The server farms here hum with stolen data.  A rival "
            "runner's body lies slumped at a terminal — a warning.",
        75: "The executive sub-net.  Holographic boardrooms and vaults of encrypted wealth.  "
            "One final firewall stands between you and the core server.",
    },
}


def check_milestones(player: Player) -> None:
    """Trigger milestone narratives at 25/50/75 % progress."""
    pct = int(player.distance_travelled / player.theme.total_distance * 100)
    for threshold in (25, 50, 75):
        if pct >= threshold and threshold not in player.milestones_hit:
            player.milestones_hit.add(threshold)
            print(colorize_ascii(ASCII_MILESTONE, Fore.MAGENTA))
            narrative = MILESTONE_NARRATIVES.get(player.theme.id, {}).get(threshold, "")
            if narrative:
                slow_print(wrapped(f"  {narrative}"), delay=0.012)
            ach_map = {25: "milestone_25", 50: "milestone_50", 75: "milestone_75"}
            player.try_unlock(ach_map.get(threshold, ""))
            pause(1.0)


# ──────────────────────────────────────────────────────────────────────
# Event system (expanded)
# ──────────────────────────────────────────────────────────────────────
def _event_bandit(player: Player) -> None:
    labels = {
        ThemeId.DESERT: ("Sand Raiders", "raiders", "Nomadic bandits emerge from dunes, weapons gleaming."),
        ThemeId.SPACE: ("Void Pirates", "pirates", "Rogue ships decloak, weapons hot and shields up."),
        ThemeId.MIST: ("Mist Wraiths", "wraiths", "Spectral figures coalesce from the fog, hungry and hostile."),
        ThemeId.TIME: ("Temporal Echoes", "echoes", "Displaced warriors from another era materialize, confused and aggressive."),
        ThemeId.CYBER: ("Rogue ICE Drones", "drones", "Hostile security programs lock onto your signature."),
    }
    name, noun, description = labels.get(player.theme.id, ("Bandits", "bandits", "Hostile figures block your path."))

    if player.has("Shadow Cloak"):
        print(f"  {name} approach, but your Shadow Cloak bends light around you...")
        print(f"  {Fore.GREEN}They pass by without noticing!{Style.RESET_ALL}")
        player.remove_item("Shadow Cloak")
        print("  The cloak's magic is spent, but you're safe.")
        return

    print(colorize_ascii(ASCII_BATTLE, Fore.RED))
    print(f"  {Fore.RED}{name} block your path!{Style.RESET_ALL}")
    print(f"  {description}")
    print()
    print("  What's your move?")
    print(f"  1. Stand and fight the {noun}")
    print(f"  2. Attempt a tactical retreat")
    print(f"  3. Offer supplies in exchange for safe passage")
    print(f"  4. Try to intimidate them into backing down")
    if player.companion and player.companion.bonus_type == "combat":
        print(f"  5. Let {player.companion.name} take the lead in combat")
    if player.has("Signal-Flare"):
        print(f"  {6 if (player.companion and player.companion.bonus_type == 'combat') else 5}. Fire Signal-Flare to scare them off")
    
    max_choice = 6 if (player.has("Signal-Flare") and player.companion and player.companion.bonus_type == "combat") else (
        5 if (player.has("Signal-Flare") or (player.companion and player.companion.bonus_type == "combat")) else 4
    )
    choice = get_choice("  > ", range(1, max_choice + 1))

    if choice == "1":
        print(f"  You steel yourself and prepare for battle!")
        luck = StatusEffect.LUCKY in player.status_effects
        shield = player.has("Ironbark Shield") or player.has("Guardian's Mantle")
        
        if shield:
            print(f"  {Fore.GREEN}Your shield absorbs their initial assault!{Style.RESET_ALL}")
            if player.has("Ironbark Shield"):
                player.remove_item("Ironbark Shield")
                print("  The shield splinters but saves your life!")
            print(f"  You counter-attack and defeat the {noun}!")
            # Small reward for skilled victory
            if random.random() < 0.3:
                loot = random.choice(["Healer's Salve", "Morale Charm"])
                player.add_item(loot)
                print(f"  You find {loot} among their belongings.")
        elif random.random() < (0.65 if luck else 0.55):
            print(f"  {Fore.YELLOW}You fight bravely and drive them off!{Style.RESET_ALL}")
            player.adjust_supply("food", -3)
            player.damage(random.randint(5, 12))
            print("  Victory, but at a cost.")
        else:
            print(f"  {Fore.RED}The {noun} overwhelm you!{Style.RESET_ALL}")
            player.damage(25)
            player.adjust_supply("food", -5)
            player.morale -= 10
            print("  You barely escape with your life.")
        player.combats_survived += 1
        player.try_unlock("first_blood")
    
    elif choice == "2":
        print(f"  You turn and run!")
        if random.random() < 0.5:
            print(f"  {Fore.GREEN}You escape cleanly!{Style.RESET_ALL}")
            print("  Though you drop some supplies in your haste.")
            player.adjust_supply("fuel", -4)
        else:
            print(f"  {Fore.RED}You stumble while fleeing!{Style.RESET_ALL}")
            player.damage(15)
            player.morale -= 8
            print(f"  The {noun} land a few blows before you get away.")
    
    elif choice == "3":
        print(f"  You raise your hands and offer tribute.")
        print(f"  The {noun} consider your offer...")
        pause(1.0)
        if random.random() < 0.7:
            print(f"  {Fore.CYAN}They accept and let you pass.{Style.RESET_ALL}")
            player.adjust_supply("food", -8)
            player.adjust_supply("water", -5)
            print("  Sometimes gold is cheaper than blood.")
        else:
            print(f"  {Fore.RED}They take your supplies AND attack anyway!{Style.RESET_ALL}")
            player.adjust_supply("food", -5)
            player.adjust_supply("water", -3)
            player.damage(15)
            print("  Treachery! You barely fight them off.")
    
    elif choice == "4":
        print(f"  You step forward boldly and meet their gaze!")
        intimidation_bonus = (StatusEffect.INSPIRED in player.status_effects) or (player.health > 80)
        if random.random() < (0.6 if intimidation_bonus else 0.35):
            print(f"  {Fore.GREEN}Your presence unnerves them!{Style.RESET_ALL}")
            print(f"  The {noun} back down and scatter.")
            player.morale += 15
            print("  Victory without bloodshed!")
        else:
            print(f"  {Fore.YELLOW}They laugh at your bravado!{Style.RESET_ALL}")
            print(f"  Enraged, they attack with fury!")
            player.damage(20)
            player.morale -= 5
    
    elif choice in ["5", "6"] and player.companion and player.companion.bonus_type == "combat" and choice == "5":
        print(f"  {player.companion.name} steps forward with confidence!")
        print(f"  {Fore.GREEN}With expert martial skill, they dispatch the {noun}!{Style.RESET_ALL}")
        print("  'That was almost too easy,' they say, wiping their blade.")
        player.combats_survived += 1
        player.try_unlock("first_blood")
        player.morale += 10
        # Companion finds something
        if random.random() < 0.4:
            player.adjust_supply("food", 5)
            print(f"  {player.companion.name} salvages supplies from the encounter.")
    
    else:
        # Signal flare option
        if player.has("Signal-Flare"):
            print("  You fire the Signal-Flare into the air!")
            print(f"  {Fore.CYAN}The bright explosion startles the {noun}!{Style.RESET_ALL}")
            player.remove_item("Signal-Flare")
            if random.random() < 0.8:
                print(f"  They flee, thinking reinforcements are coming!")
                player.morale += 5
            else:
                print(f"  Some flee, but the bravest charge!")
                player.damage(12)
                print("  You drive off the remainder.")
                player.combats_survived += 1


def _event_river(player: Player) -> None:
    print(colorize_ascii(ASCII_RIVER, Fore.CYAN))
    labels = {
        ThemeId.DESERT: "a flash-flood canyon",
        ThemeId.SPACE: "an asteroid belt",
        ThemeId.MIST: "a spectral river",
        ThemeId.TIME: "a rift in the timeline",
        ThemeId.CYBER: "a corrupted data-stream",
    }
    obstacle = labels.get(player.theme.id, "a wide river")
    print(f"  You encounter {obstacle}!")
    print("  1. Ford through carefully")
    print("  2. Search for a safer crossing")
    print("  3. Build a makeshift bridge / bypass")
    choice = get_choice("  > ", range(1, 4))

    if choice == "1":
        if random.random() < 0.5:
            print("  You cross safely!")
        else:
            print("  The crossing is treacherous — you lose supplies.")
            player.adjust_supply("fuel", -3)
            player.adjust_supply("water", -3)
    elif choice == "2":
        if player.has("Eldritch Lantern") or player.has("Wanderer's Compass"):
            print("  Your gear reveals a hidden safe passage!")
        elif player.companion and player.companion.bonus_type == "scout":
            print(f"  {player.companion.name} finds a safe path!")
        else:
            print("  You spend extra time but find a path. A day is lost.")
            player.consume_daily()
    else:
        print("  Building a bypass costs resources but keeps you safe.")
        player.adjust_supply("fuel", -5)


def _event_storm(player: Player) -> None:
    print(colorize_ascii(ASCII_STORM, Fore.RED))
    labels = {
        ThemeId.DESERT: ("A violent sandstorm", "Sand whips around you, reducing visibility to nothing."),
        ThemeId.SPACE: ("A solar flare", "Radiation warnings blare as stellar plasma surges toward your ship."),
        ThemeId.MIST: ("An arcane tempest", "Reality itself seems to buckle under eldritch winds."),
        ThemeId.TIME: ("A chrono-quake", "Time ripples and stutters. Past and future collide."),
        ThemeId.CYBER: ("A system-wide power surge", "The grid overloads. Sparks rain from damaged nodes."),
    }
    storm, description = labels.get(player.theme.id, ("A storm", "Nature's fury is upon you."))
    print(f"  {Fore.YELLOW}{storm} strikes!{Style.RESET_ALL}")
    print(f"  {description}")
    print()
    print("  How will you handle this?")
    print("  1. Take shelter and wait it out (safe but costly)")
    print("  2. Push through quickly (risky but saves supplies)")
    print("  3. Use the storm as cover to gain distance")
    if player.has("Stormglass Vial"):
        print(f"  4. Use your Stormglass Vial to navigate safely")
    if player.companion:
        print(f"  {5 if player.has('Stormglass Vial') else 4}. Trust {player.companion.name}'s instincts")
    
    max_choice = 5 if (player.has('Stormglass Vial') and player.companion) else (4 if (player.has('Stormglass Vial') or player.companion) else 3)
    choice = get_choice("  > ", range(1, max_choice + 1))

    if choice == "1":
        print("  You hunker down and weather the storm.")
        print(f"  {Fore.CYAN}Time passes slowly. Supplies dwindle.{Style.RESET_ALL}")
        player.adjust_supply("food", -3)
        player.adjust_supply("water", -2)
        print("  Finally, the storm breaks. You emerge unscathed.")
    
    elif choice == "2":
        print("  You grit your teeth and press forward into the maelstrom!")
        if random.random() < 0.4:
            print(f"  {Fore.GREEN}Through sheer determination, you push through!{Style.RESET_ALL}")
            player.adjust_supply("fuel", -2)
            print("  You emerge battered but alive, having saved time.")
            player.distance_travelled += random.randint(5, 10)
            player.try_unlock("storm_chaser")
        else:
            print(f"  {Fore.RED}The storm batters you mercilessly!{Style.RESET_ALL}")
            player.damage(20)
            player.adjust_supply("food", -4)
            player.adjust_supply("water", -3)
            print("  You survive, but barely. The cost was steep.")
    
    elif choice == "3":
        print("  You decide to use the chaos to your advantage!")
        if random.random() < 0.5:
            print(f"  {Fore.GREEN}The reduced visibility helps you avoid detection!{Style.RESET_ALL}")
            player.distance_travelled += random.randint(10, 20)
            player.morale += 10
            print("  You make excellent progress under cover of the storm!")
            player.try_unlock("storm_chaser")
        else:
            print(f"  {Fore.YELLOW}You get turned around in the chaos!{Style.RESET_ALL}")
            player.distance_travelled -= random.randint(5, 10)
            player.damage(10)
            print("  When the storm clears, you realize you've gone the wrong way.")
    
    elif choice == "4" and player.has("Stormglass Vial"):
        print("  The Stormglass Vial pulses with an inner light...")
        print(f"  {Fore.CYAN}It guides you through the safest path!{Style.RESET_ALL}")
        player.distance_travelled += random.randint(8, 15)
        print("  You navigate the storm like a seasoned expert!")
        player.try_unlock("storm_chaser")
    
    else:
        # Companion option
        print(f"  You follow {player.companion.name}'s lead through the storm.")
        if player.companion.bonus_type == "scout":
            print(f"  {Fore.GREEN}Their pathfinding skills prove invaluable!{Style.RESET_ALL}")
            player.distance_travelled += random.randint(10, 15)
            player.adjust_supply("food", -1)
        else:
            print(f"  {Fore.CYAN}Together, you weather it better than alone.{Style.RESET_ALL}")
            player.adjust_supply("food", -2)
            player.adjust_supply("water", -1)
            player.morale += 5


def _event_wildlife(player: Player) -> None:
    labels = {
        ThemeId.DESERT: ("a giant sand-wyrm", "Wyrm"),
        ThemeId.SPACE: ("an alien organism", "Organism"),
        ThemeId.MIST: ("a spectral beast", "Beast"),
        ThemeId.TIME: ("a displaced dinosaur", "Creature"),
        ThemeId.CYBER: ("a feral maintenance bot", "Bot"),
    }
    desc, short = labels.get(player.theme.id, ("a wild creature", "Creature"))
    print(f"  You spot {desc} nearby!")
    print(f"  1. Approach cautiously")
    print(f"  2. Scare it away")
    print(f"  3. Avoid it entirely")
    choice = get_choice("  > ", range(1, 4))

    if choice == "1":
        if random.random() < 0.5:
            print(f"  The {short} is friendly! It leads you to a cache of supplies.")
            player.adjust_supply("food", 5)
            player.adjust_supply("water", 5)
        else:
            print(f"  The {short} attacks!")
            player.damage(15)
            # chance to get poisoned
            if random.random() < 0.3:
                print(f"  {Fore.RED}Its strike was venomous!{Style.RESET_ALL}")
                player.add_effect(StatusEffect.POISONED, 3)
    elif choice == "2":
        if random.random() < 0.6:
            print(f"  The {short} flees. You find a Signal-Flare it was guarding.")
            player.add_item("Signal-Flare")
        else:
            print(f"  The {short} charges! You dodge but twist your ankle.")
            player.damage(10)
            player.morale -= 5
    else:
        print("  You give it a wide berth. Nothing happens.")


def _event_trader(player: Player) -> None:
    labels = {
        ThemeId.DESERT: "A nomad merchant",
        ThemeId.SPACE: "A drifting trade barge",
        ThemeId.MIST: "A wandering alchemist",
        ThemeId.TIME: "A temporal peddler",
        ThemeId.CYBER: "A black-market dealer",
    }
    trader = labels.get(player.theme.id, "A trader")
    print(f"  {trader} appears!")
    print("  1. Browse their wares")
    print("  2. Try a game of dice (gamble supplies)")
    print("  3. Move along")
    choice = get_choice("  > ", range(1, 4))

    if choice == "1":
        tradeable = [i for i in ITEM_CATALOGUE if i not in player.inventory]
        if not tradeable:
            print("  They have nothing you need. You exchange pleasantries.")
            player.morale += 5
            return
        offered = random.choice(tradeable)
        cost_food = random.randint(5, 12)
        cost_water = random.randint(3, 8)
        print(f"  They offer: {Fore.CYAN}{offered}{Style.RESET_ALL}")
        print(f"    \"{ITEM_CATALOGUE[offered]}\"")
        print(f"  Cost: {cost_food} {player.theme.supply_names['food']}, "
              f"{cost_water} {player.theme.supply_names['water']}")
        print("  1. Accept trade")
        print("  2. Decline")
        tc = get_choice("  > ", range(1, 3))
        if tc == "1":
            if player.supplies["food"] >= cost_food and player.supplies["water"] >= cost_water:
                player.adjust_supply("food", -cost_food)
                player.adjust_supply("water", -cost_water)
                player.add_item(offered)
                player.try_unlock("trader")
            else:
                print("  You can't afford the trade!")
        else:
            print("  You decline.")

    elif choice == "2":
        _mini_game_dice(player)
    else:
        print("  You nod and continue on your way.")


def _event_discovery(player: Player) -> None:
    print(colorize_ascii(ASCII_TREASURE, Fore.YELLOW))
    labels = {
        ThemeId.DESERT: "a buried sandstone vault",
        ThemeId.SPACE: "a derelict cargo pod",
        ThemeId.MIST: "ruins of a Valdrosian temple",
        ThemeId.TIME: "a collapsed time-bubble",
        ThemeId.CYBER: "an abandoned server room",
    }
    desc = labels.get(player.theme.id, "a hidden cache")
    print(f"  You discover {desc}!")
    print("  1. Investigate thoroughly")
    print("  2. Grab what you can and leave quickly")
    print("  3. Leave it alone")
    choice = get_choice("  > ", range(1, 4))

    if choice == "1":
        if random.random() < 0.6:
            print("  You carefully explore and find valuable supplies!")
            player.adjust_supply("food", 8)
            player.adjust_supply("water", 6)
            player.adjust_supply("fuel", 4)
            player.morale += 10
        else:
            print("  A trap springs! You take damage but find some loot.")
            player.damage(15)
            player.adjust_supply("food", 4)
    elif choice == "2":
        print("  You snatch a few items and run.")
        player.adjust_supply("food", 4)
        player.adjust_supply("water", 3)
    else:
        print("  You leave it undisturbed. Caution is its own reward.")
        player.morale += 5


def _event_morale(player: Player) -> None:
    print(colorize_ascii(ASCII_CAMP, Fore.YELLOW))
    labels = {
        ThemeId.DESERT: "Your caravan gathers around a fire beneath the stars.",
        ThemeId.SPACE: "The crew gathers in the observation lounge.",
        ThemeId.MIST: "You find a clearing and light a fire against the fog.",
        ThemeId.TIME: "A pocket of calm in the time-stream lets you rest.",
        ThemeId.CYBER: "You find a safe-house and power down for the night.",
    }
    scene = labels.get(player.theme.id, "Your group rests for a while.")
    print(f"  {scene}")
    print("  1. Share stories and boost morale")
    print("  2. Repair gear (restore supplies)")
    print("  3. Stand watch (improve safety)")
    if player.companion:
        print(f"  4. Talk with {player.companion.name}")
    choice = get_choice("  > ", range(1, 5 if player.companion else 4))

    if choice == "1":
        boost = random.randint(10, 20)
        player.morale = int(clamp(player.morale + boost, 0, 100))
        print(f"  {Fore.GREEN}Morale +{boost}!{Style.RESET_ALL}")
        if player.companion and player.companion.bonus_type == "morale":
            extra = player.companion.bonus_value
            player.morale = int(clamp(player.morale + extra, 0, 100))
            print(f"  {player.companion.name} lifts spirits further! {Fore.GREEN}Morale +{extra}{Style.RESET_ALL}")
    elif choice == "2":
        player.adjust_supply("fuel", 5)
    elif choice == "3":
        player.heal(5)
        player.add_effect(StatusEffect.SHIELDED, 1)
    elif choice == "4" and player.companion:
        print(f"  You share a moment with {player.companion.name}.")
        print(f"  \"{player.companion.flavour}\"")
        player.morale = int(clamp(player.morale + 8, 0, 100))
        player.heal(3)
        print(f"  {Fore.GREEN}Morale +8{Style.RESET_ALL}")


def _event_special_item(player: Player) -> None:
    item = player.theme.special_item
    if player.has(item):
        print("  You find a hidden stash of supplies!")
        player.adjust_supply("food", 5)
        player.adjust_supply("water", 5)
        return
    print(f"  You discover the legendary {Fore.CYAN}{item}{Style.RESET_ALL}!")
    print(f"    \"{player.theme.special_item_desc}\"")
    print("  1. Take it")
    print("  2. Leave it (it looks cursed...)")
    choice = get_choice("  > ", range(1, 3))
    if choice == "1":
        player.add_item(item)
    else:
        print("  You decide against it and move on.")


def _event_riddle(player: Player) -> None:
    """A sphinx-like figure poses a riddle."""
    print(colorize_ascii(ASCII_RIDDLE, Fore.MAGENTA))
    labels = {
        ThemeId.DESERT: "A stone sphinx rises from the sand",
        ThemeId.SPACE: "An alien monolith broadcasts a signal",
        ThemeId.MIST: "A spectral guardian appears in the fog",
        ThemeId.TIME: "A temporal echo speaks in riddles",
        ThemeId.CYBER: "A rogue AI locks the corridor and demands you prove your intelligence",
    }
    intro = labels.get(player.theme.id, "A mysterious figure blocks your path")
    print(f"  {intro}!")
    print(f"  {Fore.CYAN}\"Answer my riddle to pass unharmed.\"{Style.RESET_ALL}\n")

    question, options, correct = random.choice(RIDDLES)
    print(f"  {question}\n")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    answer = get_choice("  > ", range(1, len(options) + 1))

    if int(answer) - 1 == correct:
        print(f"\n  {Fore.GREEN}\"Correct! You may pass.\"{Style.RESET_ALL}")
        player.morale += 15
        player.heal(10)
        player.try_unlock("riddler")
        # bonus: sometimes get an item
        if random.random() < 0.4:
            bonus_items = [i for i in ("Shadow Cloak", "Stormglass Vial", "Ember Stone")
                           if i not in player.inventory]
            if bonus_items:
                gift = random.choice(bonus_items)
                print(f"  The figure gifts you a {Fore.CYAN}{gift}{Style.RESET_ALL}!")
                player.add_item(gift)
    else:
        print(f"\n  {Fore.RED}\"Wrong! The correct answer was: {options[correct]}\"{Style.RESET_ALL}")
        print("  The figure punishes you!")
        player.damage(15)
        player.morale -= 10


def _event_companion(player: Player) -> None:
    """Chance to recruit a companion (only one at a time)."""
    if player.companion:
        # already have a companion — companion event becomes a shared mini-story
        print(colorize_ascii(ASCII_COMPANION, Fore.GREEN))
        print(f"  {player.companion.name} tells you about a shortcut they remember.")
        if random.random() < 0.6:
            bonus = random.randint(15, 30)
            player.distance_travelled += bonus
            print(f"  You take the shortcut! +{bonus} {player.theme.distance_unit}")
        else:
            print("  The shortcut leads to a dead end. You backtrack.")
            player.consume_daily()
        return

    pool = COMPANION_POOL.get(player.theme.id, [])
    if not pool:
        return
    companion = random.choice(pool)
    print(colorize_ascii(ASCII_COMPANION, Fore.GREEN))
    print(f"  You encounter {Fore.CYAN}{companion.name} the {companion.title}{Style.RESET_ALL}!")
    print(f"  \"{companion.flavour}\"")
    print(f"  Bonus: +{companion.bonus_value} {companion.bonus_type}")
    print()
    print("  1. Invite them to join you")
    print("  2. Decline politely")
    choice = get_choice("  > ", range(1, 3))
    if choice == "1":
        player.companion = companion
        print(f"  {Fore.GREEN}{companion.name} joins your party!{Style.RESET_ALL}")
        player.try_unlock("companion")
    else:
        print(f"  {companion.name} nods and disappears into the distance.")


def _event_ambush_elite(player: Player) -> None:
    """A tougher combat encounter with tactical choices."""
    labels = {
        ThemeId.DESERT: ("Vytharian War-Lord", "war-lord"),
        ThemeId.SPACE: ("Void Leviathan", "leviathan"),
        ThemeId.MIST: ("Wraith King", "wraith king"),
        ThemeId.TIME: ("Paradox Hydra", "hydra"),
        ThemeId.CYBER: ("Corporate Sentinel AI", "sentinel"),
    }
    name, noun = labels.get(player.theme.id, ("Elite Enemy", "enemy"))
    print(ASCII_BATTLE)
    print(f"  {Fore.RED}A {name} appears — a fearsome foe!{Style.RESET_ALL}")
    print("  This is a tough fight. Choose your strategy:")
    print("  1. All-out assault (high risk, high reward)")
    print("  2. Defensive stance (safer, but costs supplies)")
    print("  3. Use terrain / environment to your advantage")
    print("  4. Attempt to parley")
    choice = get_choice("  > ", range(1, 5))

    lucky = StatusEffect.LUCKY in player.status_effects
    comp_combat = player.companion and player.companion.bonus_type == "combat"

    if choice == "1":
        chance = 0.40
        if lucky:
            chance += 0.15
        if comp_combat:
            chance += 0.15
        if random.random() < chance:
            print(f"  A decisive victory! The {noun} falls!")
            player.adjust_supply("food", 8)
            player.adjust_supply("water", 5)
            player.morale += 15
            player.add_effect(StatusEffect.INSPIRED, 3)
        else:
            print(f"  The {noun} is too powerful! You barely survive.")
            player.damage(35)
            player.morale -= 15
        player.combats_survived += 1
        player.try_unlock("first_blood")

    elif choice == "2":
        print("  You hold your ground and endure the assault.")
        player.damage(15)
        player.adjust_supply("fuel", -5)
        player.combats_survived += 1
        player.try_unlock("first_blood")

    elif choice == "3":
        scout_bonus = player.companion and player.companion.bonus_type == "scout"
        if scout_bonus or player.has("Wanderer's Compass"):
            print("  Your knowledge of the terrain gives you the edge!")
            print(f"  The {noun} is outmanoeuvred!")
            player.morale += 10
        else:
            if random.random() < 0.5:
                print("  You use the environment cleverly!")
                player.adjust_supply("fuel", -3)
            else:
                print("  Your plan backfires!")
                player.damage(20)
        player.combats_survived += 1
        player.try_unlock("first_blood")

    elif choice == "4":
        if player.morale >= 60:
            print(f"  Your confident demeanour impresses the {noun}.")
            print("  They let you pass and grant a boon!")
            player.add_effect(StatusEffect.LUCKY, 3)
        else:
            print(f"  The {noun} senses weakness. They attack!")
            player.damage(25)
            player.combats_survived += 1


def _event_weather_shift(player: Player) -> None:
    """The weather changes dramatically mid-day."""
    old = player.weather
    new_options = [w for w in Weather if w != old]
    player.weather = random.choice(new_options)
    print(weather_art(player.weather))
    print(f"  The weather shifts from {old.value} to {Fore.CYAN}{player.weather.value}{Style.RESET_ALL}!")

    if player.weather == Weather.STORM:
        print("  The sudden storm catches you off guard!")
        player.adjust_supply("water", -2)
        player.morale -= 5
    elif player.weather == Weather.CLEAR:
        print("  Clear skies! Your spirits lift.")
        player.morale += 5
    elif player.weather == Weather.FOG:
        print("  Dense fog rolls in. You slow your pace.")
    elif player.weather == Weather.RAIN:
        if player.theme.id == ThemeId.DESERT:
            print("  Rain in the desert! A rare blessing!")
            player.adjust_supply("water", 8)
        else:
            print("  The rain dampens your gear.")
            player.morale -= 3


def _event_generated_scenario(player: Player) -> None:
    """AI-generated scenario using Ollama with fallback templates - interactive with dynamic outcomes!"""
    print()
    scenario_type = random.choice(["general", "danger", "mystery", "discovery", "encounter"])
    
    # Try up to 5 times to get a unique scenario
    max_attempts = 5
    scenario = None
    for attempt in range(max_attempts):
        candidate = generate_ai_scenario(player.theme.id, scenario_type, player.seen_scenarios)
        if candidate not in player.seen_scenarios:
            scenario = candidate
            player.seen_scenarios.add(scenario)  # Track this scenario
            break
    
    # If all attempts failed (unlikely), use the last one anyway
    if scenario is None:
        scenario = generate_ai_scenario(player.theme.id, scenario_type, player.seen_scenarios)
    
    print(f"  {Fore.MAGENTA}{scenario}{Style.RESET_ALL}")
    print()
    
    # More contextual responses based on scenario type
    response_options = {
        "danger": [
            ("1. Face the danger head-on", lambda p: (
                (p.damage(random.randint(10, 20)) if random.random() < 0.4 else (p.morale + random.randint(5, 15))),
                print(f"  {Fore.YELLOW}You push through the danger!{Style.RESET_ALL}") if random.random() > 0.4 else print(f"  {Fore.RED}The danger takes its toll...{Style.RESET_ALL}")
            )),
            ("2. Find a clever way around it", lambda p: (p.morale + random.randint(8, 15), p.distance_travelled + random.randint(5, 10))),
            ("3. Wait it out cautiously", lambda p: (p.adjust_supply("food", -2), print("  You weather the situation. Supplies dwindle."))),
            ("4. Use what you have to escape", lambda p: (p.distance_travelled + random.randint(15, 25), print("  Quick thinking lets you slip away!"))),
        ],
        "mystery": [
            ("1. Investigate the mystery thoroughly", lambda p: (p.morale + random.randint(5, 12), print("  Understanding brings peace of mind."))),
            ("2. Leave it unsolved and move on", lambda p: (p.morale - random.randint(2, 5), print("  The unanswered question nags at you."))),
            ("3. Share what you learn with others", lambda p: (p.morale + random.randint(3, 8), print("  Knowledge is power."))),
            ("4. Use it to your advantage", lambda p: (p.distance_travelled + random.randint(10, 20), p.morale + random.randint(5, 10))),
        ],
        "discovery": [
            ("1. Claim it for yourself", lambda p: (p.add_item(random.choice(["Healer's Salve", "Morale Charm"])) if len(p.inventory) < 8 else None, print("  A valuable find!"))),
            ("2. Share it and gain favor", lambda p: (p.morale + random.randint(8, 15), print("  Generosity earns respect."))),
            ("3. Study it carefully", lambda p: (p.morale + random.randint(3, 8), print("  You learn something valuable."))),
            ("4. Leave it for someone else", lambda p: (p.morale - random.randint(1, 3), print("  Restraint is sometimes harder than taking."))),
        ],
        "encounter": [
            ("1. Approach peacefully", lambda p: (p.morale + random.randint(5, 10), print("  A friendly encounter brightens your day."))),
            ("2. Keep your distance", lambda p: (p.morale - random.randint(1, 3), print("  Caution, but also missed opportunity."))),
            ("3. Try to learn from them", lambda p: (p.morale + random.randint(8, 12), print("  Knowledge gained from an unexpected source."))),
            ("4. Challenge them", lambda p: (p.damage(random.randint(8, 15)), print("  The encounter turns hostile."))),
        ],
        "general": [
            ("1. Investigate carefully and take your time", lambda p: (
                (p.add_item(random.choice(["Healer's Salve", "Morale Charm", "Signal-Flare"])) if random.random() < 0.6 and len(p.inventory) < 8 else None, print("  Your careful observation pays off!")) if random.random() < 0.6 else print("  Your caution proves wise."),
                p.morale + random.randint(1, 3)
            )),
            ("2. Act boldly and seize the moment", lambda p: (
                (p.distance_travelled + random.randint(10, 20), p.morale + random.randint(10, 20), print("  Fortune favors the bold!")) if random.random() < 0.5 else (p.damage(random.randint(10, 18)), print("  Bold action backfires!")),
            )),
            ("3. Proceed cautiously, staying alert", lambda p: (p.morale + random.randint(5, 10), print("  A balanced approach serves you well."))),
            ("4. Avoid involvement and move on quickly", lambda p: (p.morale - random.randint(1, 3), print("  You slip away unnoticed."))),
        ],
    }
    
    # Use scenario-specific responses if available, otherwise use general
    options = response_options.get(scenario_type, response_options["general"])
    
    print("  How do you respond?")
    for idx, (text, _) in enumerate(options, 1):
        print(f"  {text}")
    
    choice = get_choice("  > ", range(1, len(options) + 1))
    
    # Execute outcome
    try:
        _, outcome = options[int(choice) - 1]
        outcome(player)
    except (IndexError, ValueError):
        print("  You take a moment to collect yourself.")
    
    player.try_unlock("explorer")


# ──────────────────────────────────────────────────────────────────────
# Mini-games
# ──────────────────────────────────────────────────────────────────────
def _mini_game_dice(player: Player) -> None:
    """Dice gambling mini-game."""
    print(colorize_ascii(ASCII_DICE, Fore.MAGENTA))
    print("  The trader challenges you to a dice game!")
    print(f"  Stake: 5 {player.theme.supply_names['food']} each")
    print("  Rules: both roll two dice. Highest total wins.")
    print("  1. Accept the bet")
    print("  2. Walk away")
    choice = get_choice("  > ", range(1, 3))
    if choice == "2":
        print("  You decline the gamble.")
        return

    if player.supplies["food"] < 5:
        print("  You can't afford the bet!")
        return

    lucky = StatusEffect.LUCKY in player.status_effects
    player_dice = [random.randint(1, 6), random.randint(1, 6)]
    if lucky:
        # re-roll lowest
        player_dice[player_dice.index(min(player_dice))] = random.randint(1, 6)
    trader_dice = [random.randint(1, 6), random.randint(1, 6)]

    p_total = sum(player_dice)
    t_total = sum(trader_dice)
    print(f"\n  Your roll:   [{player_dice[0]}] [{player_dice[1]}] = {p_total}")
    pause(0.5)
    print(f"  Trader roll: [{trader_dice[0]}] [{trader_dice[1]}] = {t_total}")
    pause(0.5)

    if p_total > t_total:
        print(f"\n  {Fore.GREEN}You win!{Style.RESET_ALL}")
        player.adjust_supply("food", 5)
        player.try_unlock("gambler")
    elif p_total < t_total:
        print(f"\n  {Fore.RED}You lose!{Style.RESET_ALL}")
        player.adjust_supply("food", -5)
    else:
        print("\n  It's a draw! No supplies change hands.")
    print("  Best two out of three?")
    print("  1. Yes!")
    print("  2. No, let's move on")
    again = get_choice("  > ", range(1, 3))
    if again == "1" and player.supplies["food"] >= 5:
        _mini_game_dice(player)


# Master event pool (weighted)
EVENT_POOL: list[tuple[Callable[[Player], None], int]] = [
    (_event_bandit,        14),
    (_event_river,         10),
    (_event_storm,         12),
    (_event_wildlife,      10),
    (_event_trader,        11),
    (_event_discovery,      9),
    (_event_morale,        10),
    (_event_special_item,   6),
    (_event_riddle,         7),
    (_event_companion,      5),
    (_event_ambush_elite,   4),
    (_event_weather_shift,  6),
    (_event_generated_scenario, 5),
]


def trigger_random_event(player: Player) -> None:
    funcs, weights = zip(*EVENT_POOL)
    # Night increases hostile event weight
    adjusted_weights = list(weights)
    if player.time_of_day == TimeOfDay.NIGHT:
        for i, (fn, _) in enumerate(EVENT_POOL):
            if fn in (_event_bandit, _event_ambush_elite, _event_wildlife):
                adjusted_weights[i] = int(adjusted_weights[i] * 1.5)
    chosen = random.choices(funcs, adjusted_weights, k=1)[0]
    event_name = chosen.__name__.replace("_event_", "")
    hr("~")
    print(f"  {Fore.MAGENTA}** An event unfolds... **{Style.RESET_ALL}")
    log_game("event_start", {"event": event_name, "day": player.days})
    chosen(player)
    hr("~")
    pause_for_action()
    if not TEST_MODE:
        clear_screen()


# ──────────────────────────────────────────────────────────────────────
# Use-item system (expanded)
# ──────────────────────────────────────────────────────────────────────
def use_item(player: Player) -> None:
    consumables: dict[str, Callable[[Player], None]] = {
        "Quicksilver Flask": lambda p: p.adjust_supply("water", 10),
        "Solar-Charger":     lambda p: p.adjust_supply("fuel", 15),
        "Healer's Salve":    lambda p: p.heal(25),
        "Morale Charm":      lambda p: (
            setattr(p, "morale", int(clamp(p.morale + 20, 0, 100))),
            print(f"  {Fore.GREEN}Morale +20{Style.RESET_ALL}"),
        ),
        "Elixir of Vitality": lambda p: (p.heal(40), setattr(p, "morale", int(clamp(p.morale + 30, 0, 100))),
                                          print(f"  {Fore.GREEN}Morale +30{Style.RESET_ALL}")),
        "Purified Tonic": lambda p: (p.adjust_supply("water", 15), p.heal(20)),
        "Ember Stone": lambda p: (
            print("  The Ember Stone warms you deeply."),
            p.heal(10),
            p.add_effect(StatusEffect.SHIELDED, 2),
        ),
    }
    usable = [i for i in player.inventory if i in consumables]
    if not usable:
        print("  You have no usable items right now.")
        return
    print("  Which item do you want to use?")
    for idx, item in enumerate(usable, 1):
        print(f"    {idx}. {item} — {ITEM_CATALOGUE.get(item, '')}")
    print(f"    0. Cancel")
    choice = get_choice("  > ", range(0, len(usable) + 1))
    if choice == "0":
        return
    selected = usable[int(choice) - 1]
    print()  # Blank line for separation
    consumables[selected](player)
    player.remove_item(selected)
    pause_for_action(1.0)


# ──────────────────────────────────────────────────────────────────────
# Crafting system
# ──────────────────────────────────────────────────────────────────────
def craft_menu(player: Player) -> None:
    """Show available crafting recipes and let the player craft."""
    print(colorize_ascii(ASCII_CRAFT, Fore.CYAN))
    available = []
    for a, b, result, desc in CRAFT_RECIPES:
        if player.has(a) and player.has(b) and not player.has(result):
            available.append((a, b, result, desc))

    if not available:
        print("  No recipes available. You need specific item combinations.")
        print("  Known recipes:")
        for a, b, result, desc in CRAFT_RECIPES:
            have_a = "✓" if player.has(a) else "✗"
            have_b = "✓" if player.has(b) else "✗"
            print(f"    [{have_a}] {a} + [{have_b}] {b} = {result}")
            print(f"        {desc}")
        return

    print("  Available crafting recipes:")
    for idx, (a, b, result, desc) in enumerate(available, 1):
        print(f"    {idx}. {a} + {b} → {Fore.CYAN}{result}{Style.RESET_ALL}")
        print(f"       {desc}")
    print(f"    0. Cancel")
    choice = get_choice("  > ", range(0, len(available) + 1))
    if choice == "0":
        return
    a, b, result, desc = available[int(choice) - 1]
    player.remove_item(a)
    player.remove_item(b)
    player.add_item(result)
    player.try_unlock("crafter")
    print()  # Blank line for separation
    print(f"  {Fore.GREEN}Crafted {result}!{Style.RESET_ALL}")
    pause_for_action(1.0)


# ──────────────────────────────────────────────────────────────────────
# Core game-play loop helpers
# ──────────────────────────────────────────────────────────────────────
def print_status(player: Player) -> None:
    t = player.theme
    hr()
    print(player.status_text())
    print_bar("Health", player.health, 100, Fore.RED)
    print_bar("Morale", player.morale, 100, Fore.CYAN)
    for key in ("food", "water", "fuel"):
        label = t.supply_names[key]
        cap = int(t.starting_supplies[key] * DIFFICULTY_SETTINGS[player.difficulty]["supply_mult"])
        print_bar(label[:12], player.supplies[key], cap, Fore.YELLOW)
    if player.status_effects:
        effects_str = ", ".join(f"{e.value}({d}d)" for e, d in player.status_effects.items())
        print(f"  Effects:     {effects_str}")
    if player.companion:
        print(f"  Companion:   {player.companion.name} the {player.companion.title} "
              f"(+{player.companion.bonus_value} {player.companion.bonus_type})")
    if player.inventory:
        print(f"  Inventory:   {', '.join(player.inventory)}")
    if player.has("Stormglass Vial"):
        print(f"  Forecast:    Tomorrow looks {Fore.CYAN}{random.choice(['clear', 'cloudy', 'rainy', 'stormy'])}{Style.RESET_ALL}")
    # Difficulty badge
    diff_colors = {Difficulty.EASY: Fore.GREEN, Difficulty.NORMAL: Fore.YELLOW, Difficulty.HARD: Fore.RED}
    print(f"  Difficulty:  {diff_colors[player.difficulty]}{player.difficulty.value.title()}{Style.RESET_ALL}")
    hr()


def daily_action(player: Player) -> None:
    t = player.theme
    print("\n  What would you like to do?")
    print("  1. Travel forward")
    print("  2. Rest (restore health)")
    print("  3. Scout ahead")
    print("  4. Use an item")
    print("  5. Craft items")
    print("  6. Check status & map")
    choice = get_choice("  > ", range(1, 7))
    
    action_names = {"1": "travel", "2": "rest", "3": "scout", "4": "use_item", "5": "craft", "6": "status"}
    if GAME_LOGGER:
        GAME_LOGGER.log_choice("daily_action", action_names.get(choice, choice), {"day": player.days})

    if choice == "1":
        # Travel action with narrative flavor
        travel_flavor = [
            "You press onward, the path stretching endlessly ahead.",
            "Each step brings you closer to your destination.",
            "The journey continues, one determined stride at a time.",
            "You forge ahead through the unforgiving landscape.",
            "With renewed purpose, you continue your trek.",
        ]
        print(f"  {random.choice(travel_flavor)}")
        
        bonus = 10 if (player.has("Wanderer's Compass") or player.has("Guardian's Mantle")) else 0
        if player.companion and player.companion.bonus_type == "scout":
            bonus += player.companion.bonus_value
        lo, hi = t.daily_distance
        dist = random.randint(lo, hi) + bonus
        
        # weather modifiers with flavor
        if player.weather == Weather.STORM:
            dist = max(5, dist - 15)
            print(f"  {Fore.YELLOW}Storm conditions slow your progress!{Style.RESET_ALL}")
            print("  Wind and chaos make every step a battle.")
        elif player.weather == Weather.FOG:
            dist = max(5, dist - 8)
            print(f"  {Fore.YELLOW}Fog makes navigation difficult.{Style.RESET_ALL}")
            print("  Visibility is nearly zero - you feel your way forward.")
        elif player.weather == Weather.CLEAR:
            dist += 5
            print(f"  {Fore.CYAN}Clear skies speed your journey!{Style.RESET_ALL}")
        
        # night travel
        if player.time_of_day == TimeOfDay.NIGHT:
            player.try_unlock("night_owl")
            if not player.has("Eldritch Lantern") and not player.has("Ember Stone"):
                dist = max(5, dist - 10)
                print(f"  {Fore.YELLOW}Darkness slows your travel.{Style.RESET_ALL}")
                print("  You navigate by moonlight and instinct alone.")
        
        # inspired bonus
        if StatusEffect.INSPIRED in player.status_effects:
            dist += 8
            print(f"  {Fore.GREEN}Inspiration drives you forward!{Style.RESET_ALL}")
            print("  Your spirits are high - nothing can stop you now!")

        player.distance_travelled += dist
        player.consume_daily()
        player.supplies["fuel"] = max(0, player.supplies["fuel"] - 1)
        
        # Add variety to distance announcement
        distance_messages = [
            f"  You cover {dist} {t.distance_unit}.",
            f"  Progress: {dist} {t.distance_unit} traveled.",
            f"  {dist} {t.distance_unit} lie behind you now.",
            f"  Another {dist} {t.distance_unit} closer to your goal.",
        ]
        print(f"\n{random.choice(distance_messages)}")

        # Morale drift toward 50
        if player.morale > 50:
            player.morale -= 1
        elif player.morale < 50:
            player.morale += 1

        # Random event chance (difficulty scaled)
        event_chance = DIFFICULTY_SETTINGS[player.difficulty]["event_chance"]
        
        # Apply difficulty-specific event chance tuning
        event_tuning_key = f"difficulty_{player.difficulty.value}_event_chance"
        event_chance *= get_tuned_value(event_tuning_key, 1.0)
        
        if random.random() < event_chance:
            trigger_random_event(player)

    elif choice == "2":
        # Rest action with narrative flavor
        rest_flavor = [
            "You find shelter and allow exhaustion to wash over you.",
            "Setting up a makeshift camp, you finally rest your weary bones.",
            "The weight of the journey lifts as you settle down to recover.",
            "You take refuge from the elements and tend to your wounds.",
            "For a moment, the world can wait - you need this respite.",
        ]
        print(f"  {random.choice(rest_flavor)}")
        
        heal = random.randint(8, 18)
        if player.companion and player.companion.bonus_type == "health":
            heal += player.companion.bonus_value
            print(f"  {player.companion.name} helps treat your injuries.")
        
        player.heal(heal)
        player.consume_daily()
        
        # Add some flavor to healing outcome
        if heal > 15:
            print(f"  {Fore.GREEN}You sleep deeply and wake refreshed. (+{heal} health){Style.RESET_ALL}")
        elif heal > 10:
            print(f"  {Fore.CYAN}Rest does you good. (+{heal} health){Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}A brief rest helps somewhat. (+{heal} health){Style.RESET_ALL}")
        
        # remove poison on rest
        if StatusEffect.POISONED in player.status_effects:
            if random.random() < 0.5:
                del player.status_effects[StatusEffect.POISONED]
                print(f"  {Fore.GREEN}The poison fades during your rest!{Style.RESET_ALL}")
                print("  Your body fights off the toxins naturally.")
            else:
                print(f"  {Fore.YELLOW}The poison still courses through you...{Style.RESET_ALL}")

    elif choice == "3":
        # Scout action with narrative flavor
        scout_flavor = [
            "You pause to survey the path ahead carefully.",
            "Climbing to higher ground, you scan the horizon.",
            "You take time to study your surroundings thoroughly.",
            "With keen eyes, you search for opportunities and dangers alike.",
            "You venture off the main path to explore nearby terrain.",
        ]
        print(f"  {random.choice(scout_flavor)}")
        
        player.scout_count += 1
        player.consume_daily()
        if player.scout_count >= 5:
            player.try_unlock("explorer")
        
        scout_bonus = player.companion and player.companion.bonus_type == "scout"
        if scout_bonus:
            print(f"  {player.companion.name}'s expertise guides your search.")
        
        chance = 0.65 if scout_bonus else 0.55
        if random.random() < chance:
            discovery_text = [
                "Your keen observation pays off!",
                "Something catches your eye...",
                "Your scouting reveals an unexpected find!",
                "The detour proves worthwhile!",
            ]
            print(f"\n  {Fore.CYAN}{random.choice(discovery_text)}{Style.RESET_ALL}")
            trigger_random_event(player)
        else:
            null_results = [
                "You scout the area but find nothing of note.",
                "The reconnaissance yields no significant findings.",
                "Despite your thorough search, nothing stands out.",
                "This stretch of the journey appears unremarkable.",
            ]
            print(f"\n  {random.choice(null_results)}")
            if random.random() < 0.3:
                shortcut_messages = [
                    "However, you spot a safe shortcut ahead.",
                    "Your efforts reveal an efficient alternate route.",
                    "You identify a path that will save time.",
                    "At least you found a better way forward.",
                ]
                print(f"  {random.choice(shortcut_messages)}")
                shortcut_dist = random.randint(5, 15)
                player.distance_travelled += shortcut_dist
                print(f"  You gain {shortcut_dist} {player.theme.distance_unit}!")

    elif choice == "4":
        use_item(player)
        if not TEST_MODE:
            clear_screen()
        return  # using item doesn't cost a day

    elif choice == "5":
        craft_menu(player)
        if not TEST_MODE:
            clear_screen()
        return  # crafting doesn't cost a day

    elif choice == "6":
        print_status(player)
        daily_action(player)
        if not TEST_MODE:
            clear_screen()
        return  # viewing status doesn't cost a day

    pause_for_action()
    if not TEST_MODE:
        clear_screen()
    player.days += 1
    advance_time_of_day(player)
    advance_weather(player)
    player.tick_effects()
    check_milestones(player)


# ──────────────────────────────────────────────────────────────────────
# Starvation / low-morale consequences
# ──────────────────────────────────────────────────────────────────────
def apply_penalties(player: Player) -> None:
    penalties = []
    if player.supplies["food"] <= 0:
        print(f"  {Fore.RED}You are starving! Health is dropping.{Style.RESET_ALL}")
        player.health -= 8
        penalties.append("starvation")
    if player.supplies["water"] <= 0:
        print(f"  {Fore.RED}You are dehydrated! Health is dropping fast.{Style.RESET_ALL}")
        player.health -= 12
        penalties.append("dehydration")
    if player.morale <= 10:
        print(f"  {Fore.YELLOW}Morale is critically low. Your resolve wavers.{Style.RESET_ALL}")
        player.health -= 3
        penalties.append("low_morale")
    if StatusEffect.EXHAUSTED in player.status_effects:
        print(f"  {Fore.YELLOW}Exhaustion wears you down...{Style.RESET_ALL}")
        player.health -= 2
        penalties.append("exhaustion")
    if penalties:
        log_game("penalties_applied", {"penalties": penalties, "health": player.health})


# ──────────────────────────────────────────────────────────────────────
# Final encounter & endings
# ──────────────────────────────────────────────────────────────────────
def final_encounter(player: Player) -> None:
    t = player.theme
    hr("=")
    print(f"\n  {Fore.MAGENTA}You have reached the final stretch of your journey!{Style.RESET_ALL}\n")

    if t.id == ThemeId.DESERT:
        print("  The gates of Alqarim shimmer on the horizon, but a massive")
        print("  sandstorm wall blocks the last stretch.")
    elif t.id == ThemeId.SPACE:
        print("  Erythia-4's atmosphere is visible, but a debris field")
        print("  surrounds the moon's orbit.")
    elif t.id == ThemeId.MIST:
        print("  The Forgotten Throne is within sight, but a guardian")
        print("  wraith materialises before you.")
    elif t.id == ThemeId.TIME:
        print("  The origin fracture pulses ahead, but a paradox storm")
        print("  threatens to erase you from existence.")
    elif t.id == ThemeId.CYBER:
        print("  The Omnivault core server is one firewall away, but the")
        print("  corporate AI sentinel activates.")

    print("\n  1. Charge through with brute force")
    print("  2. Use your special item (if you have it)")
    print("  3. Find a creative workaround")
    if player.companion:
        print(f"  4. Rely on {player.companion.name}'s expertise")
    max_choice = 5 if player.companion else 4
    choice = get_choice("  > ", range(1, max_choice))

    if choice == "1":
        print("\n  You charge in!")
        if player.health >= 60:
            print("  Your strength carries you through!")
            player.damage(30)
        else:
            print("  You are too weak... the obstacle overwhelms you.")
            player.damage(50)
            player.adjust_supply("food", -10)

    elif choice == "2":
        si = t.special_item
        if player.has(si):
            print(f"\n  You activate the {si}!")
            print("  It works perfectly — the obstacle is neutralised!")
            player.remove_item(si)
        else:
            print(f"\n  You don't have the {si}!")
            print("  You improvise, but take heavy damage.")
            player.damage(40)

    elif choice == "3":
        if player.morale >= 50:
            print("\n  Your high spirits inspire a clever plan!")
            print("  You bypass the obstacle with minimal losses.")
            player.adjust_supply("fuel", -5)
        else:
            print("\n  Low morale clouds your thinking. The plan fails partially.")
            player.damage(25)
            player.adjust_supply("food", -5)

    elif choice == "4" and player.companion:
        print(f"\n  {player.companion.name} steps up!")
        if player.companion.bonus_type in ("scout", "combat"):
            print(f"  With expert {player.companion.bonus_type} skills, they find a way through!")
            player.morale += 10
        else:
            print(f"  {player.companion.name} supports you through the ordeal!")
            player.heal(15)

    hr("=")
    pause_for_action(1.5)


def show_ending(player: Player) -> None:
    t = player.theme
    print()
    hr("*")

    best_signal = player.has("Signal-Flare") or player.has("Beacon Array")
    ending_type = "death"

    if player.health <= 0:
        print(colorize_ascii(ASCII_GAMEOVER, Fore.RED))
        slow_print(wrapped(
            f"  Your journey ends in tragedy.  "
            f"The {t.distance_unit} stretched too far, and the "
            f"perils of the road claimed you.  "
            f"Perhaps the next traveler will fare better..."
        ), delay=0.015)
        if GAME_LOGGER:
            cause = "combat" if player.combats_survived > 3 else "starvation" if player.supplies["food"] <= 0 else "dehydration" if player.supplies["water"] <= 0 else "unknown"
            GAME_LOGGER.log_death(cause, player)

    elif player.distance_travelled >= t.total_distance and best_signal and player.health >= 80:
        # PERFECT ENDING
        print(colorize_ascii(ASCII_VICTORY, Fore.GREEN))
        slow_print(wrapped(
            f"  A LEGENDARY victory!  You complete the journey "
            f"in peak condition with a rescue signal blazing.  "
            f"Songs will echo through the ages about this triumph. "
            f"The world will never forget your name."
        ), delay=0.015)
        player.try_unlock("best_ending")
        player.try_unlock("flawless")
        ending_type = "perfect"
        if GAME_LOGGER:
            GAME_LOGGER.log_victory(ending_type, player)

    elif player.distance_travelled >= t.total_distance and best_signal:
        print(colorize_ascii(ASCII_VICTORY, Fore.GREEN))
        slow_print(wrapped(
            f"  Against all odds, you complete the journey!  "
            f"Using the signal, a rescue party is summoned.  "
            f"Songs will be sung of your triumph for generations."
        ), delay=0.015)
        player.try_unlock("best_ending")
        ending_type = "good_signal"
        if GAME_LOGGER:
            GAME_LOGGER.log_victory(ending_type, player)

    elif player.distance_travelled >= t.total_distance and player.health >= 80:
        print(colorize_ascii(ASCII_VICTORY, Fore.GREEN))
        slow_print(wrapped(
            f"  You arrive strong and healthy!  "
            f"Though no signal was sent, the destination is reached.  "
            f"A quiet victory, but a victory nonetheless."
        ), delay=0.015)
        player.try_unlock("flawless")
        ending_type = "good_healthy"
        if GAME_LOGGER:
            GAME_LOGGER.log_victory(ending_type, player)

    elif player.distance_travelled >= t.total_distance:
        print(colorize_ascii(ASCII_VICTORY, Fore.GREEN))
        slow_print(wrapped(
            f"  You reach the destination battered but alive.  "
            f"Without a signal, survival is uncertain, "
            f"but the journey itself was the true reward."
        ), delay=0.015)
        ending_type = "arrived"
        if GAME_LOGGER:
            GAME_LOGGER.log_victory(ending_type, player)

    else:
        print(colorize_ascii(ASCII_GAMEOVER, Fore.RED))
        slow_print(wrapped(
            f"  You could not complete the journey.  "
            f"Only {player.distance_travelled} of {t.total_distance} "
            f"{t.distance_unit} were covered.  "
            f"The wilds claim another unfinished story."
        ), delay=0.015)
        ending_type = "incomplete"
        if GAME_LOGGER and player.health > 0:
            GAME_LOGGER.log_event("incomplete", {"distance_pct": int(player.distance_travelled / t.total_distance * 100)})

    if player.distance_travelled >= t.total_distance and player.is_alive():
        player.try_unlock("survivor")

    hr("*")
    print(f"\n  Final stats — Day {player.days} | Health {player.health} | Morale {player.morale}")
    print(f"  Distance: {player.distance_travelled}/{t.total_distance} {t.distance_unit}")
    print(f"  Difficulty: {player.difficulty.value.title()}")
    if player.companion:
        print(f"  Companion: {player.companion.name} the {player.companion.title}")
    if player.inventory:
        print(f"  Remaining items: {', '.join(player.inventory)}")

    # Show achievements
    unlocked = [a for a in player.achievements.values() if a.unlocked]
    if unlocked:
        print(f"\n  {Fore.YELLOW}Achievements Unlocked ({len(unlocked)}/{len(player.achievements)}):{Style.RESET_ALL}")
        for a in unlocked:
            print(f"    ★ {a.name} — {a.description}")
    locked = [a for a in player.achievements.values() if not a.unlocked]
    if locked:
        print(f"\n  Locked achievements ({len(locked)}):")
        for a in locked:
            print(f"    ○ {a.name}")
    print()


# ──────────────────────────────────────────────────────────────────────
# Theme & difficulty selection + intro
# ──────────────────────────────────────────────────────────────────────
def choose_theme() -> Theme:
    print(f"\n  {Fore.CYAN}Choose your adventure:{Style.RESET_ALL}\n")
    theme_list = list(THEMES.values())
    for idx, t in enumerate(theme_list, 1):
        print(f"  {idx}. {Fore.GREEN}{t.name}{Style.RESET_ALL}")
        print(f"     {t.tagline}")
    print()
    choice = get_choice(f"  Enter number (1-{len(theme_list)}): ", range(1, len(theme_list) + 1))
    selected_theme = theme_list[int(choice) - 1]
    
    # If AI-Generated theme selected, let user choose model
    if selected_theme.id == ThemeId.AI_GENERATED:
        select_ai_model()
    
    return selected_theme


def choose_difficulty() -> Difficulty:
    print(f"\n  {Fore.CYAN}Choose difficulty:{Style.RESET_ALL}\n")
    diffs = list(Difficulty)
    for idx, d in enumerate(diffs, 1):
        settings = DIFFICULTY_SETTINGS[d]
        marker = f" {Fore.GREEN}[DEFAULT]{Style.RESET_ALL}" if d == Difficulty.NORMAL else ""
        print(f"  {idx}. {settings['label']}{marker}")
    print()
    choice = get_choice("  Enter number (1-3, or press Enter for Normal): ", range(1, len(diffs) + 1), allow_empty=True)
    if not choice:
        return Difficulty.NORMAL
    return diffs[int(choice) - 1]


def introduction(player: Player) -> None:
    # Color theme art based on theme (generate dynamically for AI theme)
    if player.theme.id == ThemeId.AI_GENERATED:
        ascii_art = generate_ai_ascii_art()
        colored_art = colorize_ascii(ascii_art, Fore.MAGENTA)
        intro_text = generate_ai_intro_text()
    else:
        colored_art = colorize_ascii(player.theme.ascii_art, get_theme_ascii_color(player.theme.id))
        intro_text = player.theme.intro_text
    
    print(colored_art)
    hr()
    slow_print(wrapped(f"  {intro_text}"), delay=0.012)
    hr()
    print(f"\n  Special item for this theme: "
          f"{Fore.CYAN}{player.theme.special_item}{Style.RESET_ALL}")
    print(f"  \"{player.theme.special_item_desc}\"\n")
    if not TEST_MODE:
        input("  Press Enter to begin your journey... ")


# ──────────────────────────────────────────────────────────────────────
# Automated test mode
# ──────────────────────────────────────────────────────────────────────
class AutoPlayer:
    """Feeds pre-scripted or AI-driven inputs to simulate a full play-through.

    When ``strategy`` is "random", it picks valid random answers.
    When ``strategy`` is "scripted", it reads from a provided input list.
    """

    def __init__(self, strategy: str = "random", inputs: list[str] | None = None,
                 seed: int = 42):
        self.strategy = strategy
        self.input_queue: list[str] = list(inputs) if inputs else []
        self.idx = 0
        self.rng = random.Random(seed)
        self._original_input = __builtins__["input"] if isinstance(__builtins__, dict) else getattr(__builtins__, "input")  # type: ignore[index]
        self.log: list[str] = []

    def fake_input(self, prompt: str = "") -> str:
        """Replacement for built-in input()."""
        sys.stdout.write(prompt)
        if self.strategy == "scripted" and self.idx < len(self.input_queue):
            answer = self.input_queue[self.idx]
            self.idx += 1
        else:
            # "random" strategy — parse the prompt to figure out valid range
            answer = self._guess_answer(prompt)
        print(answer)  # show what was "typed"
        self.log.append(f"{prompt.strip()} → {answer}")
        return answer

    def _guess_answer(self, prompt: str) -> str:
        """Heuristic: pick a random valid answer based on common prompt patterns."""
        # look for patterns like "(1-5)" or "(1-3)" in prompt
        import re
        m = re.search(r"\((\d+)[^\d]+(\d+)\)", prompt)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            return str(self.rng.randint(lo, hi))
        # prompts that say "> " typically expect a number 1-4
        if prompt.strip() == ">":
            return str(self.rng.randint(1, 3))
        # name prompt
        lower = prompt.lower()
        if "name" in lower:
            return "TestBot"
        if "seed" in lower or "enter" in lower.split():
            return ""  # empty = random / continue
        # fallback
        return "1"

    @contextmanager
    def activate(self):
        """Context manager that patches input() and restores it on exit."""
        import builtins
        original = builtins.input
        builtins.input = self.fake_input  # type: ignore[assignment]
        try:
            yield self
        finally:
            builtins.input = original  # type: ignore[assignment]


def run_automated_test(theme_idx: int = 1, difficulty_idx: int = 2,
                       seed: int = 42, max_days: int = 200,
                       strategy: str = "random") -> dict:
    """Run a full game non-interactively and return results.

    Returns a dict with keys:
        survived, distance, days, health, morale, inventory, achievements, log
    """
    global TEST_MODE
    TEST_MODE = True

    auto = AutoPlayer(strategy=strategy, seed=seed)

    # Build scripted inputs for the intro sequence
    intro_inputs = [
        "TestBot",          # name
        str(seed),          # seed
        str(theme_idx),     # theme
        str(difficulty_idx),# difficulty
        "",                 # press Enter to begin
    ]
    auto.input_queue = intro_inputs
    auto.strategy = "scripted"  # scripted for intro, then switch to random

    rng_for_game = random.Random(seed)

    with auto.activate():
        # After intro inputs are exhausted, switch to random
        auto.strategy = "random"
        try:
            _run_game_loop(max_days=max_days)
        except SystemExit:
            pass  # game called sys.exit on death

    results = {
        "survived": True,  # will be refined below
        "distance": 0,
        "days": 0,
        "health": 0,
        "morale": 0,
        "inventory": [],
        "achievements": [],
        "log_length": len(auto.log),
    }
    TEST_MODE = False
    return results


def _run_game_loop(max_days: int = 200) -> None:
    """Internal game loop used by both interactive and test modes."""
    # Initialize logger for this session
    init_logger()
    
    # Colorize title with gradient
    title_colors = [Fore.CYAN, Fore.MAGENTA, Fore.CYAN]
    print(colorize_ascii_gradient(ASCII_TITLE, title_colors))
    print(f"  {Fore.CYAN}Terminal Adventure Quest{Style.RESET_ALL}")
    print("  A text-based survival journey\n")
    hr()

    # Start directly with theme selection
    theme = choose_theme()
    difficulty = choose_difficulty()
    
    # Use random seed automatically
    seed = random.randint(0, 999_999)
    
    player = Player(name="You", theme=theme, difficulty=difficulty, seed=seed)
    
    # Log game start
    if GAME_LOGGER:
        GAME_LOGGER.log_event("game_start", {
            "theme": theme.name,
            "difficulty": difficulty.value,
            "seed": seed,
        })
        GAME_LOGGER.log_player_state(player, "initial")
    
    # Show introduction (with unseeded random for variety in ASCII art)
    introduction(player)
    
    # NOW set the seed for gameplay randomness (reproducible events)
    random.seed(seed)

    day_count = 0
    while player.distance_travelled < theme.total_distance and player.is_alive():
        try:
            print_status(player)
            
            # Log periodic snapshots
            if GAME_LOGGER and player.days % 10 == 0:
                GAME_LOGGER.log_player_state(player, f"day_{player.days}")
            
            daily_action(player)
            apply_penalties(player)
            day_count += 1
            if day_count >= max_days:
                print(f"\n  {Fore.YELLOW}(Max days reached — ending game.){Style.RESET_ALL}")
                if GAME_LOGGER:
                    GAME_LOGGER.log_event("max_days_reached", {"days": max_days})
                break
            if not player.is_alive():
                break
        except KeyboardInterrupt:
            if GAME_LOGGER:
                GAME_LOGGER.log_error(
                    error_type="UserInterrupt",
                    message="User interrupted during game loop",
                    context={"day": player.days, "distance": player.distance_travelled}
                )
            print(f"\n\n{Fore.YELLOW}Game interrupted by user.{Style.RESET_ALL}")
            break
        except Exception as e:
            if GAME_LOGGER:
                GAME_LOGGER.log_exception(e, context={
                    "day": player.days,
                    "distance": player.distance_travelled,
                    "health": player.health,
                    "phase": "game_loop"
                })
            print(f"\n\n{Fore.RED}ERROR: {e}{Style.RESET_ALL}")
            print(f"Game crashed on day {player.days}. Check logs for details.")
            break

    if player.is_alive() and player.distance_travelled >= theme.total_distance:
        final_encounter(player)

    # Final state snapshot before ending
    if GAME_LOGGER:
        GAME_LOGGER.log_player_state(player, "final")
    
    show_ending(player)
    
    # Log session summary
    if GAME_LOGGER:
        summary = GAME_LOGGER.get_summary()
        GAME_LOGGER.log_event("session_end", summary)
        if not TEST_MODE:
            print(f"\n  {Fore.CYAN}[Session logged: {GAME_LOGGER.log_file}]{Style.RESET_ALL}")
            if summary.get("errors", 0) > 0:
                print(f"  {Fore.YELLOW}[{summary['errors']} error(s) logged during session]{Style.RESET_ALL}")

    print(f"  {Fore.CYAN}Want to play again?{Style.RESET_ALL}")
    print("  1. Yes — same seed (replay)")
    print("  2. Yes — new adventure")
    print("  3. No — quit")
    replay = get_choice("  > ", range(1, 4))
    if replay == "1":
        print(f"\n  Replaying with seed {seed}...\n")
        random.seed(seed)
        _run_game_loop(max_days=max_days)
    elif replay == "2":
        _run_game_loop(max_days=max_days)
    else:
        print(f"\n  Thank you for playing Terminal Adventure Quest!")
        print(f"  Your seed was: {seed}  (use it to replay this journey)\n")


# ──────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal Adventure Quest")
    parser.add_argument("--test", action="store_true",
                        help="Run automated test (no user input needed)")
    parser.add_argument("--test-all", action="store_true",
                        help="Run automated tests for all 5 themes")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed for the random number generator")
    parser.add_argument("--max-days", type=int, default=200,
                        help="Max days before auto-ending (test mode)")
    parser.add_argument("--fast", action="store_true",
                        help="Disable slow text printing for faster play")
    parser.add_argument("--no-log", action="store_true",
                        help="Disable gameplay logging")
    args = parser.parse_args()

    global TEST_MODE, SLOW_PRINT_DELAY, LOGGING_ENABLED
    if args.fast:
        SLOW_PRINT_DELAY = 0.0
    if args.no_log:
        LOGGING_ENABLED = False

    if args.test:
        TEST_MODE = True
        print("=" * WIDTH)
        print("  AUTOMATED TEST MODE")
        print("=" * WIDTH)
        auto = AutoPlayer(strategy="random", seed=args.seed)
        with auto.activate():
            try:
                _run_game_loop(max_days=args.max_days)
            except SystemExit:
                print("  (Game ended via sys.exit)")
        print("\n" + "=" * WIDTH)
        print(f"  Test complete. {len(auto.log)} inputs simulated.")
        print("=" * WIDTH)
        return

    if args.test_all:
        TEST_MODE = True
        results = []
        num_iterations = 3  # Run each theme/diff combo 3 times = 6 themes * 3 diff * 3 iter = 54 tests
        test_num = 0
        
        for iteration in range(num_iterations):
            for theme_idx in range(1, 7):  # All 6 themes including AI-Generated
                for diff_idx in range(1, 4):  # 3 difficulties
                    test_num += 1
                    seed = args.seed + test_num  # Vary seed for each test
                    
                    print("\n" + "=" * WIDTH)
                    print(f"  TEST {test_num}/54: Theme {theme_idx}, Difficulty {diff_idx}, Seed {seed}")
                    print("=" * WIDTH)
                    
                    # Build inputs: name, seed, theme, difficulty
                    # For AI theme (6), add model selection (2 = gemma3:4b)
                    if theme_idx == 6:
                        inputs = ["TestBot", str(seed), str(theme_idx), "2", str(diff_idx), ""]
                    else:
                        inputs = ["TestBot", str(seed), str(theme_idx), str(diff_idx), ""]
                    
                    auto = AutoPlayer(strategy="scripted", inputs=inputs, seed=seed)
                    with auto.activate():
                        auto.strategy = "random"  # after scripted intro
                        auto.idx = 0
                        # re-stock scripted inputs
                        auto.input_queue = inputs
                        auto.strategy = "scripted"
                        try:
                            _run_game_loop(max_days=args.max_days)
                        except SystemExit:
                            pass
                    
                    results.append({
                        "test_num": test_num,
                        "theme": theme_idx,
                        "difficulty": diff_idx,
                        "inputs": len(auto.log),
                        "seed": seed,
                    })
                    print(f"  → {len(auto.log)} inputs simulated")

        print("\n" + "=" * WIDTH)
        print(f"  ALL TESTS COMPLETE ({len(results)} total)")
        print("=" * WIDTH)
        
        # Summary by theme
        theme_names = {
            1: "Desert", 2: "Space", 3: "Mist", 4: "Time", 5: "Cyber", 6: "AI-Gen"
        }
        for theme_id in range(1, 7):
            theme_results = [r for r in results if r["theme"] == theme_id]
            if theme_results:
                avg_inputs = sum(r["inputs"] for r in theme_results) / len(theme_results)
                print(f"  {theme_names[theme_id]}: {len(theme_results)} tests, avg {avg_inputs:.0f} inputs")
        
        return

    # Normal interactive mode
    _run_game_loop()


if __name__ == "__main__":
    # 🧠 AUTO-TUNING: Game learns from gameplay and improves automatically
    # Runs analysis every 10 sessions and applies balance fixes
    # To disable: comment out the line below
    # To adjust frequency: change min_sessions parameter
    try:
        from auto_tune import check_and_apply_auto_tuning
        check_and_apply_auto_tuning(min_sessions=10, silent=False)
    except ImportError:
        pass  # auto_tune.py not available - skip
    except Exception as e:
        # Don't crash game if auto-tuning fails
        print(f"⚠️  Auto-tuning skipped: {e}")
    
    main()
