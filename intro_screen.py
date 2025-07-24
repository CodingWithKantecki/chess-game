"""
Intro Screen Implementation for Checkmate Protocol
Displays credits with fade in/out sequences FINAL
Total duration: 9.7 seconds
"""

import pygame
import config

class IntroScreen:
    def __init__(self, screen, renderer):
        self.screen = screen
        self.renderer = renderer
        self.active = True
        self.complete = False
        
        # Timing configuration (10 seconds total)
        self.fade_duration = 800  # 0.8 second fade in/out
        self.display_duration = 1500  # 1.5 seconds display time
        self.between_fade = 400  # 0.4 seconds between screens
        
        # Credit screens
        self.credits = [
            {
                "text": "GAME CREATED BY",
                "name": "THOMAS KANTECKI",
                "start_time": 0
            },
            {
                "text": "MUSIC CREATED BY",
                "name": "THOMAS KANTECKI",
                "start_time": 3300  # Start at 3.3 seconds
            },
            {
                "text": "ART CREATED BY",
                "name": "EDER MUNIZ AND DANI MACCARI",
                "start_time": 6600  # Start at 6.6 seconds
            }
        ]
        
        # Start time
        self.start_time = pygame.time.get_ticks()
        
        # Track if we've started the final fade
        self.final_fade_started = False
        
        # Font sizes
        self.credit_font = None
        self.name_font = None
        self._load_fonts()
        
    def _load_fonts(self):
        """Load fonts for credits."""
        if hasattr(self.renderer, 'pixel_fonts'):
            self.credit_font = self.renderer.pixel_fonts['large']  # Changed from 'medium' to 'large'
            self.name_font = self.renderer.pixel_fonts['huge']     # Changed from 'large' to 'huge'
        else:
            # Fallback fonts - also made bigger
            self.credit_font = pygame.font.Font(None, 48)  # Increased from 36
            self.name_font = pygame.font.Font(None, 64)    # Increased from 48
            
    def update(self):
        """Update intro screen state."""
        if not self.active:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # Check if we should start the fade to menu
        # The last credit starts at 6600ms and lasts 3100ms (0.8s fade in + 1.5s display + 0.8s fade out)
        # So we complete at 9700ms (9.7 seconds)
        if elapsed >= 9700 and not self.final_fade_started:
            self.final_fade_started = True
            self.complete = True
            
    def draw(self):
        """Draw the intro screen."""
        if not self.active:
            return
            
        # Black background
        self.screen.fill(config.BLACK)
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # Draw each credit screen
        for credit in self.credits:
            credit_elapsed = elapsed - credit["start_time"]
            
            if credit_elapsed >= 0 and credit_elapsed < self.fade_duration + self.display_duration + self.fade_duration:
                self._draw_credit_screen(credit, credit_elapsed)
                
    def _draw_credit_screen(self, credit, elapsed):
        """Draw individual credit screen with fade."""
        # Calculate alpha based on elapsed time
        if elapsed < self.fade_duration:
            # Fade in
            alpha = int(255 * (elapsed / self.fade_duration))
        elif elapsed < self.fade_duration + self.display_duration:
            # Full display
            alpha = 255
        else:
            # Fade out
            fade_out_progress = (elapsed - self.fade_duration - self.display_duration) / self.fade_duration
            alpha = int(255 * (1 - fade_out_progress))
            
        # Create text surfaces
        credit_text = self.credit_font.render(credit["text"], True, config.WHITE)
        name_text = self.name_font.render(credit["name"], True, config.WHITE)
        
        # Calculate positions (centered)
        screen_center_x = self.screen.get_width() // 2
        screen_center_y = self.screen.get_height() // 2
        
        credit_rect = credit_text.get_rect(center=(screen_center_x, screen_center_y - 30))
        name_rect = name_text.get_rect(center=(screen_center_x, screen_center_y + 20))
        
        # Apply alpha
        credit_text.set_alpha(alpha)
        name_text.set_alpha(alpha)
        
        # Draw text
        self.screen.blit(credit_text, credit_rect)
        self.screen.blit(name_text, name_rect)
        
    def skip(self):
        """Skip the intro."""
        self.final_fade_started = True
        self.complete = True
