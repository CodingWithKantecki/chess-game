"""Test script to demonstrate typewriter effect"""

import pygame
import sys
import time
from graphics import Renderer
import config

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("Typewriter Effect Test")
clock = pygame.time.Clock()

# Create renderer with dummy assets
class DummyAssets:
    pass

assets = DummyAssets()
renderer = Renderer(screen, assets)

# Add some test texts with typewriter effect
renderer.add_typewriter_text("Welcome to Checkmate Protocol!", (config.WIDTH // 2, 100), 'huge', (255, 255, 255), center=True)
renderer.add_typewriter_text("This text appears letter by letter...", (config.WIDTH // 2, 200), 'large', (255, 215, 0), center=True)
renderer.add_typewriter_text("Just like in classic RPG games!", (config.WIDTH // 2, 250), 'medium', (100, 255, 100), center=True)

# You can also adjust the speed
renderer.typewriter_speed = 20  # Slower speed

renderer.add_typewriter_text("This text appears more slowly.", (config.WIDTH // 2, 350), 'medium', (255, 100, 100), center=True)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Clear and add new text
                renderer.clear_typewriter_texts()
                renderer.add_typewriter_text("You pressed SPACE!", (config.WIDTH // 2, 400), 'large', (255, 255, 100), center=True)
    
    # Clear screen
    screen.fill((20, 20, 30))
    
    # Update and draw typewriter texts
    renderer.update_typewriter_texts()
    renderer.draw_typewriter_texts()
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()