# Chess Game with Powerups

A unique chess game built with Pygame featuring military-themed powerups, AI opponents, and an immersive story mode.

## Features

- **Classic Chess Gameplay**: Full chess rules implementation with drag-and-drop piece movement
- **Military Powerups**: 
  - Airstrike: Call in aerial support to clear enemy pieces
  - Chopper Gunner: Take direct control of attack helicopter
  - Additional tactical powerups
- **Game Modes**:
  - Story Mode with cutscenes and narrative
  - Tutorial Mode for beginners
  - VS AI Mode with intelligent computer opponent
  - Free Play Mode
- **Visual Effects**:
  - Parallax scrolling backgrounds
  - Explosion animations
  - Smooth piece animations
  - Custom military-themed UI
- **Audio**:
  - Background music
  - Sound effects for moves, captures, and powerups
  - Voice acting in story mode

## Requirements

- Python 3.8 or higher
- Pygame 2.0 or higher

## Installation

1. Clone the repository:
```bash
git clone https://github.com/KentuckyToThe/chess-game.git
cd chess-game
```

2. Install required dependencies:
```bash
pip install pygame
```

## How to Play

Run the game:
```bash
python main.py
```

### Controls

- **Mouse**: Click and drag to move pieces
- **ESC**: Return to menu / Exit
- **Space**: Skip cutscenes (in story mode)
- **1-3**: Activate powerups (when available)

### Game Rules

Standard chess rules apply with the addition of powerup mechanics:
- Capture enemy pieces to charge your powerup meter
- Once charged, activate devastating military strikes
- Use powerups strategically to turn the tide of battle

## Project Structure

- `main.py` - Entry point
- `game.py` - Core game logic and state management
- `board.py` - Chess board representation and move validation
- `ai.py` - AI opponent implementation
- `powerups.py` - Powerup system logic
- `story_mode.py` - Story mode campaign
- `assets/` - Game sprites, sounds, and music

## Development

This game was created as a creative take on classical chess, adding modern military elements while maintaining the strategic depth of the original game.

### Recent Updates

- Replaced jet flyby animation with title fade-in effect
- Fixed typewriter text issues between screen transitions
- Windows compatibility improvements for console output

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

You are free to use, modify, and share this code for non-commercial purposes. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Chess piece sprites and board textures
- Pygame community for the excellent game development framework
- Beta testers for feedback and bug reports