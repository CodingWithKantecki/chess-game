"""
Checkmate Protocol - Main Entry Point
A chess game with special abilities by Thomas Kantecki
"""

import pygame
import sys
from game import ChessGame

def print_game_info():
    """Print game information and controls."""
    print("=" * 50)
    print("CHECKMATE PROTOCOL")
    print("=" * 50)
    print("\nPOWERUP SYSTEM:")
    print("- Capture enemy pieces to earn points")
    print("- Spend points to activate special abilities:")
    print("  • AIRSTRIKE (10 pts): Bomb a 3x3 area")
    print("  • SHIELD (5 pts): Protect a piece for 3 turns")
    print("  • GUN (7 pts): Shoot an enemy in range")
    print("  • PARATROOPERS (15 pts): Deploy tactical pawns")
    print("  • CHOPPER GUNNER (25 pts): First-person minigun mode")
    print("\nPIECE VALUES:")
    print("  Pawn = 1 pt, Knight/Bishop = 3 pts")
    print("  Rook = 5 pts, Queen = 9 pts")
    print("\nCONTROLS:")
    print("- Click powerup buttons when you have enough points")
    print("- ESC to cancel active powerup")
    print("- F for fullscreen mode")
    print("- Shift+T for test mode (cheat)")
    print("=" * 50)

def main(show_info=True):
    """Main entry point for the chess game.
    
    Args:
        show_info: Whether to display game information at startup
    """
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    
    # Print game info if requested
    if show_info:
        print_game_info()
    
    # Create and run the game
    game = ChessGame()
    game.run()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Check command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Checkmate Protocol - Chess with Powerups')
    parser.add_argument('--no-info', action='store_true', help='Skip displaying game info at startup')
    args = parser.parse_args()
    
    main(show_info=not args.no_info)