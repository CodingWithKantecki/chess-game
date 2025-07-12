""" FINAL
Checkmate Protocol - Main Entry Point
A chess game by Thomas Kantecki
"""

import pygame
import sys
from game import ChessGame

def main():
    """Main entry point for the chess game."""
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    
    # Create and run the game
    game = ChessGame()
    game.run()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
