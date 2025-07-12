"""
Checkmate Protocol - Powerup Edition FINAL
A chess game with special abilities by Thomas Kantecki
Enhanced with powerup system
"""

import pygame
import sys
from game import ChessGame

def main():
    """Main entry point for the enhanced chess game."""
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    
    # Print game info
    print("=" * 50)
    print("CHECKMATE PROTOCOL - POWERUP EDITION")
    print("=" * 50)
    print("\nPOWERUP SYSTEM:")
    print("- Capture enemy pieces to earn points")
    print("- Spend points to activate special abilities:")
    print("  • AIRSTRIKE (10 pts): Bomb a 3x3 area")
    print("  • SHIELD (5 pts): Protect a piece for 3 turns")
    print("  • GUN (7 pts): Shoot an enemy in range")
    print("\nPIECE VALUES:")
    print("  Pawn = 1 pt, Knight/Bishop = 3 pts")
    print("  Rook = 5 pts, Queen = 9 pts")
    print("\nCONTROLS:")
    print("- Click powerup buttons when you have enough points")
    print("- ESC to cancel active powerup")
    print("- F for fullscreen mode")
    print("=" * 50)
    
    # Create and run the game
    game = ChessGame()
    game.run()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
