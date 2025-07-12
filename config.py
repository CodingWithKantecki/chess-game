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
def load_progress():
    """Load player progress from save file."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all fields exist
                if "money" not in data:
                    data["money"] = 0
                if "unlocked_powerups" not in data:
                    data["unlocked_powerups"] = ["shield"]  # Start with shield only
                if "unlocked_difficulties" not in data:
                    data["unlocked_difficulties"] = ["easy"]
                return data
        except:
            return {
                "unlocked_difficulties": ["easy"],
                "money": 0,
                "unlocked_powerups": ["shield"]
            }
    return {
        "unlocked_difficulties": ["easy"],
        "money": 0,
        "unlocked_powerups": ["shield"]
    }

def save_progress(progress):
    """Save player progress to file."""
    with open(SAVE_FILE, 'w') as f:
        json.dump(progress, f)

def unlock_next_difficulty(current_difficulty):
    """Unlock the next difficulty level."""
    progress = load_progress()
    
    # Find the next difficulty
    current_index = AI_DIFFICULTIES.index(current_difficulty)
    if current_index < len(AI_DIFFICULTIES) - 1:
        next_difficulty = AI_DIFFICULTIES[current_index + 1]
        if next_difficulty not in progress["unlocked_difficulties"]:
            progress["unlocked_difficulties"].append(next_difficulty)
            save_progress(progress)
            return next_difficulty
    return None

def add_money(amount):
    """Add money to player's account."""
    progress = load_progress()
    progress["money"] = progress.get("money", 0) + amount
    save_progress(progress)
    return progress["money"]

def spend_money(amount):
    """Spend money if player has enough."""
    progress = load_progress()
    current_money = progress.get("money", 0)
    if current_money >= amount:
        progress["money"] = current_money - amount
        save_progress(progress)
        return True
    return False

def unlock_powerup(powerup_key):
    """Unlock a powerup."""
    progress = load_progress()
    if powerup_key not in progress.get("unlocked_powerups", []):
        progress["unlocked_powerups"].append(powerup_key)
        save_progress(progress)
        return True
    return False
