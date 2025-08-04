"""
Chess Game Configuration FINAL
All game constants and settings in one place
"""

import pygame
import json
import os

# Window settings
BOARD_SIZE = 640
UI_WIDTH = 200
UI_HEIGHT = 100
POWERUP_MENU_WIDTH = 250  # Width of powerup menu
WIDTH = BOARD_SIZE + UI_WIDTH * 2 + POWERUP_MENU_WIDTH
HEIGHT = BOARD_SIZE + UI_HEIGHT * 2

# Rows and columns
ROWS = 8
COLS = 8

# These will be dynamically calculated
BOARD_OFFSET_X = UI_WIDTH
BOARD_OFFSET_Y = UI_HEIGHT
GAME_OFFSET_X = 0
GAME_OFFSET_Y = 0

# Board borders
BOARD_BORDER_LEFT = 36
BOARD_BORDER_TOP = 36
BOARD_BORDER_RIGHT = 36
BOARD_BORDER_BOTTOM = 36

# Calculate square size
PLAYING_AREA_WIDTH = BOARD_SIZE - BOARD_BORDER_LEFT - BOARD_BORDER_RIGHT
PLAYING_AREA_HEIGHT = BOARD_SIZE - BOARD_BORDER_TOP - BOARD_BORDER_BOTTOM
SQUARE_SIZE = PLAYING_AREA_WIDTH // 8

# Scaling and display settings
SCALE = 1.0  # Default scale (1.0 = no scaling)
BASE_WIDTH = WIDTH
BASE_HEIGHT = HEIGHT
GAME_OFFSET_X = 0
GAME_OFFSET_Y = 0

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (212, 175, 55)
HIGHLIGHT = (186, 202, 43, 150)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
LOCKED_COLOR = (80, 80, 80)  # Gray for locked difficulties

# Powerup colors
POWERUP_MENU_BG = (40, 40, 50, 230)
POWERUP_BUTTON_BG = (60, 60, 70)
POWERUP_BUTTON_HOVER = (80, 80, 90)
POWERUP_BUTTON_ACTIVE = (100, 100, 120)
POWERUP_DISABLED = (40, 40, 40)

# Animation settings
MOVE_ANIMATION_DURATION = 300
SCUFFLE_DURATION = 800
FADE_DURATION = 1000

# Game settings
STARTING_PLAYER = "white"
FPS = 60

# Screen states
SCREEN_START = "start"
SCREEN_BAR_INTRO = "bar_intro"
SCREEN_DIFFICULTY = "difficulty"
SCREEN_GAME = "game"
SCREEN_CREDITS = "credits"
SCREEN_ARMS_DEALER = "arms_dealer"
SCREEN_BETA = "beta"

# AI Difficulty levels with ELO ratings
AI_DIFFICULTIES = ["easy", "medium", "hard", "very_hard"]
AI_DIFFICULTY_NAMES = {
    "easy": "EASY",
    "medium": "MEDIUM", 
    "hard": "HARD",
    "very_hard": "VERY HARD"
}
AI_DIFFICULTY_COLORS = {
    "easy": (100, 200, 100),
    "medium": (200, 200, 100),
    "hard": (200, 150, 100),
    "very_hard": (200, 100, 100)
}
AI_DIFFICULTY_ELO = {
    "easy": 800,
    "medium": 1200,
    "hard": 1600,
    "very_hard": 2000
}

# Currency rewards for winning
VICTORY_REWARDS = {
    "easy": 100,
    "medium": 200,
    "hard": 400,
    "very_hard": 800
}

# Save file for progress
SAVE_FILE = "chess_progress.json"

# Asset paths
ASSETS_DIR = "assets"
PIECE_IMAGES = {
    "bR": "B_Rook.png",
    "bN": "B_Knight.png", 
    "bB": "B_Bishop.png",
    "bQ": "B_Queen.png",
    "bK": "B_King.png",
    "bP": "B_Pawn.png",
    "wR": "W_Rook.png",
    "wN": "W_Knight.png",
    "wB": "W_Bishop.png", 
    "wQ": "W_Queen.png",
    "wK": "W_King.png",
    "wP": "W_Pawn.png",
}

# Board textures
BOARD_TEXTURES = ["board.png", "board_plain_05.png"]

# Sound files
MUSIC_FILE = "music.mp3"
TARIQ_MUSIC_FILE = "tariq.mp3"
CAPTURE_SOUND = "slash.mp3"

# Parallax layers - UPDATED TO MATCH YOUR FILES
PARALLAX_LAYERS = [
    {"file": "Layer_0011_0.png", "speed": 0.05},
    {"file": "Layer_0010_1.png", "speed": 0.1},
    {"file": "Layer_0009_2.png", "speed": 0.15},
    {"file": "Layer_0008_3.png", "speed": 0.2},
    {"file": "Layer_0007_Lights.png", "speed": 0.25},
    {"file": "Layer_0006_4.png", "speed": 0.3},
    {"file": "Layer_0005_5.png", "speed": 0.35},
    {"file": "Layer_0004_Lights.png", "speed": 0.4},
    {"file": "Layer_0003_6.png", "speed": 0.45},
    {"file": "Layer_0002_7.png", "speed": 0.5},
    {"file": "Layer_0001_8.png", "speed": 0.55},
    {"file": "Layer_0000_9.png", "speed": 0.6},
]

# Initial board setup
INITIAL_BOARD = [
    ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
    ["bP"] * 8,
    [""] * 8,
    [""] * 8,
    [""] * 8,
    [""] * 8,
    ["wP"] * 8,
    ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
]

# Progress tracking functions
# Tutorial state - global variable to track tutorial unlocks
tutorial_unlocked_powerups = []

# Track actual money and unlocks separately
_player_money = 0
_unlocked_powerups = ["shield"]  # Start with only shield unlocked
_in_tutorial = False

# Story mode state - PERSISTENT IN MEMORY
_story_state = {
    "completed_battles": [],
    "unlocked_chapters": [True, False, False, False, False],
    "current_chapter": 0,
    "current_battle": 0
}

def set_tutorial_mode(enabled):
    """Enable/disable tutorial mode."""
    global _in_tutorial
    print(f"set_tutorial_mode called: enabled={enabled}, was={_in_tutorial}")
    _in_tutorial = enabled

def load_progress():
    """Load player progress from save file."""
    global _player_money, _unlocked_powerups
    
    # Default progress structure
    default_progress = {
        "unlocked_difficulties": ["easy", "medium", "hard", "very_hard"],
        "money": 0,
        "unlocked_powerups": ["shield"],
        "settings": {
            "music_volume": 0.4,
            "sfx_volume": 0.75
        },
        "story": {
            "current_chapter": 0,
            "current_battle": 0,
            "completed_battles": [],
            "unlocked_chapters": [True, False, False, False, False]
        }
    }
    
    # Try to load from file first
    try:
        if os.path.exists("player_progress.json"):
            with open("player_progress.json", "r") as f:
                saved_data = json.load(f)
            
            # Update global variables
            _player_money = saved_data.get("money", 0)
            _unlocked_powerups = saved_data.get("unlocked_powerups", ["shield"])
            
            # Merge with defaults to ensure all fields exist
            progress = default_progress.copy()
            progress.update(saved_data)
            
            # Ensure story section exists with all required fields
            if "story" not in progress:
                progress["story"] = default_progress["story"]
            else:
                story_defaults = default_progress["story"]
                for key, value in story_defaults.items():
                    if key not in progress["story"]:
                        progress["story"][key] = value
            
            # Ensure settings section exists with all required fields
            if "settings" not in progress:
                progress["settings"] = default_progress["settings"]
            else:
                settings_defaults = default_progress["settings"]
                for key, value in settings_defaults.items():
                    if key not in progress["settings"]:
                        progress["settings"][key] = value
            
            print(f"Progress loaded: money=${_player_money}, powerups={_unlocked_powerups}")
            return progress
    except Exception as e:
        print(f"Error loading progress: {e}")
    
    # Return default progress
    _player_money = default_progress["money"]
    _unlocked_powerups = default_progress["unlocked_powerups"][:]
    return default_progress

def save_progress(progress):
    """Save disabled - keeping in memory only."""
    global _player_money, _unlocked_powerups
    # Update global variables from progress
    _player_money = progress.get("money", 0)
    _unlocked_powerups = progress.get("unlocked_powerups", ["shield"])
    print(f"[SAVE DISABLED] In-memory: money=${_player_money}, powerups={_unlocked_powerups}")
    # NO FILE WRITES

def save_story_progress(current_chapter, current_battle, completed_battles, unlocked_chapters):
    """Save story progress to file."""
    global _story_state
    try:
        # Read existing progress
        if os.path.exists("player_progress.json"):
            with open("player_progress.json", "r") as f:
                progress = json.load(f)
        else:
            progress = {
                "unlocked_difficulties": ["easy", "medium", "hard", "very_hard"],
                "money": _player_money,
                "unlocked_powerups": _unlocked_powerups,
                "settings": {
                    "music_volume": 0.4,
                    "sfx_volume": 0.75
                },
                "story": {
                    "current_chapter": 0,
                    "current_battle": 0,
                    "completed_battles": [],
                    "unlocked_chapters": [True, False, False, False, False]
                }
            }
        
        # Update story progress
        progress["story"]["current_chapter"] = current_chapter
        progress["story"]["current_battle"] = current_battle
        progress["story"]["completed_battles"] = completed_battles
        progress["story"]["unlocked_chapters"] = unlocked_chapters
        
        # Also update in-memory state
        _story_state["current_chapter"] = current_chapter
        _story_state["current_battle"] = current_battle
        _story_state["completed_battles"] = completed_battles
        _story_state["unlocked_chapters"] = unlocked_chapters
        
        # Save to file
        with open("player_progress.json", "w") as f:
            json.dump(progress, f, indent=2)
            
        print(f"Story progress saved: chapter={current_chapter}, battles={completed_battles}")
    except Exception as e:
        print(f"Error saving story progress: {e}")

def get_story_progress():
    """Get story progress from memory."""
    global _story_state
    print(f"[GET STORY] Returning in-memory state: {_story_state}")
    return _story_state.copy()

def complete_story_battle(battle_id):
    """Mark a battle as complete and save to file."""
    global _story_state
    if battle_id not in _story_state["completed_battles"]:
        _story_state["completed_battles"].append(battle_id)
        print(f"[COMPLETE BATTLE] Added {battle_id} to completed battles")
        print(f"[COMPLETE BATTLE] Current state: {_story_state}")
        
        # Save the updated story progress
        save_story_progress(
            _story_state["current_chapter"],
            _story_state["current_battle"],
            _story_state["completed_battles"],
            _story_state["unlocked_chapters"]
        )
    return _story_state["completed_battles"]

def unlock_story_chapter(chapter_index):
    """Unlock a chapter and save to file."""
    global _story_state
    if 0 <= chapter_index < len(_story_state["unlocked_chapters"]):
        _story_state["unlocked_chapters"][chapter_index] = True
        print(f"[UNLOCK CHAPTER] Unlocked chapter {chapter_index + 1}")
        
        # Save the updated story progress
        save_story_progress(
            _story_state["current_chapter"],
            _story_state["current_battle"],
            _story_state["completed_battles"],
            _story_state["unlocked_chapters"]
        )
    return _story_state["unlocked_chapters"]

def save_volume_settings(music_volume, sfx_volume):
    """Save volume settings to the unified progress file."""
    try:
        # Read the file directly to avoid load_progress overwriting globals
        if os.path.exists("player_progress.json"):
            with open("player_progress.json", "r") as f:
                progress = json.load(f)
        else:
            progress = {
                "unlocked_difficulties": ["easy", "medium", "hard", "very_hard"],
                "money": 0,
                "unlocked_powerups": ["shield"],
                "settings": {
                    "music_volume": 0.4,
                    "sfx_volume": 0.75
                },
                "story": {
                    "current_chapter": 0,
                    "current_battle": 0,
                    "completed_battles": [],
                    "unlocked_chapters": [True, False, False, False, False]
                }
            }
        
        # Ensure settings section exists
        if "settings" not in progress:
            progress["settings"] = {}
        
        # Update volume settings
        progress["settings"]["music_volume"] = music_volume
        progress["settings"]["sfx_volume"] = sfx_volume
        
        # Save directly to file
        with open("player_progress.json", "w") as f:
            json.dump(progress, f, indent=2)
            
        print(f"Volume settings saved: music={int(music_volume*100)}%, sfx={int(sfx_volume*100)}%")
    except Exception as e:
        print(f"Error saving volume settings: {e}")

def get_volume_settings():
    """Get volume settings from the unified progress file."""
    try:
        progress = load_progress()
        settings = progress.get("settings", {})
        return {
            "music_volume": settings.get("music_volume", 0.4),
            "sfx_volume": settings.get("sfx_volume", 0.75)
        }
    except Exception as e:
        print(f"Error getting volume settings: {e}")
        return {"music_volume": 0.4, "sfx_volume": 0.75}

def unlock_next_difficulty(current_difficulty):
    """Unlock the next difficulty level - DISABLED."""
    # Always return None (no progression saving)
    return None

def save_money_to_file():
    """Save current money value to the progress file."""
    global _player_money
    try:
        # Read existing progress
        if os.path.exists("player_progress.json"):
            with open("player_progress.json", "r") as f:
                progress = json.load(f)
        else:
            # Create default progress if file doesn't exist
            progress = {
                "unlocked_difficulties": ["easy", "medium", "hard", "very_hard"],
                "money": 0,
                "unlocked_powerups": ["shield"],
                "settings": {
                    "music_volume": 0.4,
                    "sfx_volume": 0.75
                },
                "story": {
                    "current_chapter": 0,
                    "current_battle": 0,
                    "completed_battles": [],
                    "unlocked_chapters": [True, False, False, False, False]
                }
            }
        
        # Update money in progress
        progress["money"] = _player_money
        
        # Save to file
        with open("player_progress.json", "w") as f:
            json.dump(progress, f, indent=2)
            
        print(f"Money saved to file: ${_player_money}")
    except Exception as e:
        print(f"Error saving money: {e}")

def add_money(amount):
    """Add money to player's account."""
    global _player_money
    print(f"\n{'='*50}")
    print(f"ADD MONEY CALLED")
    print(f"Amount: ${amount}")
    print(f"Tutorial mode: {_in_tutorial}")
    print(f"Current money: ${_player_money}")
    print(f"{'='*50}\n")
    
    if not _in_tutorial:  # Only track money outside tutorial
        old_money = _player_money
        _player_money += amount
        print(f"✓ MONEY ADDED! ${old_money} + ${amount} = ${_player_money}")
        # Save money to file immediately after adding
        save_money_to_file()
    else:
        print("✗ MONEY NOT ADDED - in tutorial mode!")
    
    return _player_money

def get_money():
    """Get current money balance."""
    global _player_money
    return _player_money

def spend_money(amount):
    """Spend money if player has enough."""
    global _player_money
    if _in_tutorial:
        return True  # Unlimited money in tutorial
    if _player_money >= amount:
        _player_money -= amount
        # Save money to file after spending
        save_money_to_file()
        return True
    return False

def get_player_money():
    """Get current player money."""
    return 9999 if _in_tutorial else _player_money

def get_unlocked_powerups():
    """Get list of unlocked powerups."""
    global _unlocked_powerups
    return _unlocked_powerups[:]  # Return a copy

def unlock_powerup(powerup_key):
    """Unlock a powerup permanently."""
    global _unlocked_powerups
    if not _in_tutorial and powerup_key not in _unlocked_powerups:
        _unlocked_powerups.append(powerup_key)
        
        # Save the updated unlocked powerups directly to file
        try:
            # Read the file directly to avoid load_progress overwriting globals
            if os.path.exists("player_progress.json"):
                with open("player_progress.json", "r") as f:
                    progress = json.load(f)
            else:
                progress = {
                    "unlocked_difficulties": ["easy", "medium", "hard", "very_hard"],
                    "money": _player_money,
                    "unlocked_powerups": ["shield"],
                    "story": {
                        "current_chapter": 0,
                        "current_battle": 0,
                        "completed_battles": [],
                        "unlocked_chapters": [True, False, False, False, False]
                    }
                }
            
            # Update the unlocked powerups and money in the file data
            progress["unlocked_powerups"] = _unlocked_powerups[:]
            progress["money"] = _player_money  # Also save current money
            
            # Save directly to file
            with open("player_progress.json", "w") as f:
                json.dump(progress, f, indent=2)
                
            print(f"Unlocked powerup: {powerup_key}. Total unlocked: {_unlocked_powerups}")
            print(f"Progress saved: money=${progress.get('money', 0)}, powerups={progress['unlocked_powerups']}")
        except Exception as e:
            print(f"Error saving unlocked powerup: {e}")
    return True

def reset_after_tutorial():
    """Reset money and powerups after tutorial completion."""
    global _player_money, _unlocked_powerups
    
    # Set the tutorial completion rewards
    _player_money = 100  # Start with $100 from tutorial reward
    _unlocked_powerups = ["shield"]  # Reset to only shield unlocked
    print(f"[TUTORIAL RESET] Money set to ${_player_money}")
    
    # Save money to file
    save_money_to_file()
    
    # Also update story progress to mark tutorial as completed
    try:
        if os.path.exists("player_progress.json"):
            with open("player_progress.json", "r") as f:
                progress = json.load(f)
        else:
            progress = {
                "unlocked_difficulties": ["easy", "medium", "hard", "very_hard"],
                "money": 100,
                "unlocked_powerups": ["shield"],
                "story": {
                    "current_chapter": 0,
                    "current_battle": 0,
                    "completed_battles": [],
                    "unlocked_chapters": [True, False, False, False, False]
                }
            }
        
        # Update tutorial completion
        if "story" in progress and "completed_battles" not in progress["story"]:
            progress["story"]["completed_battles"] = []
        if "tutorial_bot" not in progress["story"]["completed_battles"]:
            progress["story"]["completed_battles"].append("tutorial_bot")
        
        # Save progress
        with open("player_progress.json", "w") as f:
            json.dump(progress, f, indent=2)
            
        print(f"Tutorial completion saved")
    except Exception as e:
        print(f"Error saving tutorial completion: {e}")

def unlock_all_powerups_for_tutorial():
    """Unlock all powerups for tutorial."""
    global tutorial_unlocked_powerups
    tutorial_unlocked_powerups = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
    pass
    return True

def reset_tutorial_powerups():
    """Reset powerups to empty list for tutorial start."""
    global tutorial_unlocked_powerups
    tutorial_unlocked_powerups = []
    pass
    return True
