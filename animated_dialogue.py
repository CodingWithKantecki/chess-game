"""
Animated Dialogue Box for Story Mode
Provides smooth animation from a thin line to a full dialogue box
"""

import pygame
import math
import config


class AnimatedDialogueBox:
    """Handles animated dialogue box with line-to-rectangle expansion and typewriter text."""
    
    def __init__(self, renderer):
        self.renderer = renderer
        
        # Box dimensions
        self.box_width = 600
        self.box_height = 120
        self.box_x = (config.WIDTH - self.box_width) // 2
        self.box_y = config.HEIGHT - 200
        
        # Animation state
        self.animation_state = "idle"  # idle, expanding, expanded, typewriting, complete
        self.animation_start_time = 0
        self.expand_duration = 600  # milliseconds for box expansion
        self.current_height = 2  # Start as a thin line
        self.initialized = False  # Track if first update has happened
        self.animation_count = 0  # Track how many times we've animated
        
        # Text properties
        self.current_text = ""
        self.wrapped_lines = []
        self.typewriter_progress = 0
        self.typewriter_speed = 30  # characters per second
        self.text_start_time = 0
        
        # Visual properties
        self.border_color = (0, 150, 200)
        self.bg_color = (10, 15, 25)
        self.text_color = config.WHITE
        self.glow_alpha = 0
        self.glow_pulse_time = 0
        
        # Corner decoration
        self.corner_size = 15
        self.corner_alpha = 0
        
        # Store previous dialogue to detect changes
        self.previous_text = ""
        self.current_dialogue_index = -1
        
        # Delta time for frame-rate independent animation
        self.last_update_time = 0
        
        # Track if we've shown this dialogue already
        self.shown_dialogues = set()
        
        # Track when we last completed an animation
        self.last_completion_time = 0
        
    def start_dialogue(self, text):
        """Start a new dialogue animation."""
        current_time = pygame.time.get_ticks()
        
        # If we just completed an animation, don't start a new one immediately
        if self.last_completion_time > 0 and current_time - self.last_completion_time < 500:
            return
        
        # For the first dialogue (index 0), use a simple flag
        if self.current_dialogue_index == 0:
            if hasattr(self, '_first_dialogue_shown') and self._first_dialogue_shown:
                if self.animation_state != "idle":
                    return
            else:
                self._first_dialogue_shown = True
        
        # Create a unique key for this dialogue
        dialogue_key = f"{self.current_dialogue_index}:{text[:20]}"
        
        # If we've already shown this exact dialogue at this index, don't restart
        if dialogue_key in self.shown_dialogues and self.animation_state != "idle":
            return
            
        # Prevent restarting if we're already animating this text
        if self.current_text == text and self.animation_state not in ["idle"]:
            return
        
        # Don't restart if we just started animating
        if self.animation_state == "expanding" and current_time - self.animation_start_time < 300:
            return
        
        # Mark this dialogue as shown
        self.shown_dialogues.add(dialogue_key)
        self.animation_count += 1
            
        self.previous_text = self.current_text
        self.current_text = text
        self.wrapped_lines = self._wrap_text(text)
        self.animation_state = "expanding"
        self.animation_start_time = current_time
        self.last_update_time = self.animation_start_time
        self.current_height = 2
        self.typewriter_progress = 0
        self.corner_alpha = 0
        self.glow_alpha = 0
        self.glow_pulse_time = 0
        self.initialized = True
        
    def _wrap_text(self, text):
        """Wrap text to fit in the dialogue box."""
        if hasattr(self.renderer, '_wrap_text'):
            return self.renderer._wrap_text(text, self.renderer.pixel_fonts['medium'], self.box_width - 40)
        else:
            # Simple fallback wrapping
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                
                # Simple character limit fallback
                if len(test_line) > 60:
                    if len(current_line) > 1:
                        current_line.pop()
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(test_line)
                        current_line = []
            
            if current_line:
                lines.append(' '.join(current_line))
                
            return lines
    
    def update(self):
        """Update animation state."""
        if self.animation_state == "idle":
            return
            
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_update_time) / 1000.0 if self.last_update_time > 0 else 0
        self.last_update_time = current_time
        
        if self.animation_state == "expanding":
            # Calculate expansion progress
            elapsed = current_time - self.animation_start_time
            progress = min(elapsed / self.expand_duration, 1.0)
            
            # Smooth easing function (ease-out cubic)
            eased_progress = 1 - pow(1 - progress, 3)
            
            # Update height with smoother interpolation
            target_height = 2 + (self.box_height - 2) * eased_progress
            self.current_height = target_height
            
            # Fade in corners and glow during expansion
            self.corner_alpha = int(255 * eased_progress)
            self.glow_alpha = int(80 * eased_progress)
            
            # Check if expansion is complete
            if progress >= 1.0:
                self.animation_state = "expanded"
                self.text_start_time = current_time + 100  # Small delay before text
                self.current_height = self.box_height  # Ensure exact height
                
        elif self.animation_state == "expanded":
            # Wait a moment before starting typewriter
            if current_time >= self.text_start_time:
                self.animation_state = "typewriting"
                self.text_start_time = current_time
                
        elif self.animation_state == "typewriting":
            # Update typewriter progress
            elapsed = (current_time - self.text_start_time) / 1000.0
            total_chars = sum(len(line) for line in self.wrapped_lines)
            self.typewriter_progress = min(int(elapsed * self.typewriter_speed), total_chars)
            
            # Check if typewriter is complete
            if self.typewriter_progress >= total_chars:
                self.animation_state = "complete"
                self.typewriter_progress = total_chars  # Ensure all text is shown
                self.last_completion_time = current_time
                
        # Update glow pulse effect with delta time
        if delta_time > 0:
            self.glow_pulse_time += delta_time * 3
        
    def draw(self, screen):
        """Draw the animated dialogue box."""
        if self.animation_state == "idle":
            return
        
        # Ensure we have a valid start time
        if self.animation_start_time == 0:
            return
            
        # Skip drawing for the first few frames to prevent flash
        if pygame.time.get_ticks() - self.animation_start_time < 32:
            return
            
        # Calculate current box dimensions with proper rounding
        current_box_height = max(2, int(round(self.current_height)))
        box_y_offset = (self.box_height - current_box_height) // 2
        current_box_y = self.box_y + box_y_offset
        
        # Draw glow effect
        if self.glow_alpha > 0 and current_box_height > 4:  # Only draw glow when box has some height
            glow_intensity = self.glow_alpha + int(math.sin(self.glow_pulse_time) * 20)
            for i in range(3):
                glow_surf = pygame.Surface((self.box_width + i*6, current_box_height + i*6), pygame.SRCALPHA)
                glow_color = (*self.border_color, max(0, min(255, glow_intensity - i * 25)))
                pygame.draw.rect(glow_surf, glow_color,
                               (0, 0, self.box_width + i*6, current_box_height + i*6),
                               3, border_radius=10)
                screen.blit(glow_surf, (self.box_x - i*3, current_box_y - i*3))
        
        # Draw main box background
        pygame.draw.rect(screen, self.bg_color,
                        (self.box_x, current_box_y, self.box_width, current_box_height),
                        border_radius=10)
        
        # Draw border
        pygame.draw.rect(screen, self.border_color,
                        (self.box_x, current_box_y, self.box_width, current_box_height),
                        2, border_radius=10)
        
        # Draw tech corner decorations (only if box is expanded enough)
        if current_box_height > 30 and self.corner_alpha > 0:
            corner_color = (*self.border_color, self.corner_alpha)
            
            # Create a surface for corners with alpha
            corner_surf = pygame.Surface((self.box_width, current_box_height), pygame.SRCALPHA)
            
            # Top left corner
            pygame.draw.lines(corner_surf, corner_color, False,
                            [(10, 10 + self.corner_size),
                             (10, 10),
                             (10 + self.corner_size, 10)], 2)
            
            # Top right corner
            pygame.draw.lines(corner_surf, corner_color, False,
                            [(self.box_width - 10 - self.corner_size, 10),
                             (self.box_width - 10, 10),
                             (self.box_width - 10, 10 + self.corner_size)], 2)
            
            # Bottom left corner (only if fully expanded)
            if current_box_height >= self.box_height - 5:
                pygame.draw.lines(corner_surf, corner_color, False,
                                [(10, current_box_height - 10 - self.corner_size),
                                 (10, current_box_height - 10),
                                 (10 + self.corner_size, current_box_height - 10)], 2)
                
                # Bottom right corner
                pygame.draw.lines(corner_surf, corner_color, False,
                                [(self.box_width - 10 - self.corner_size, current_box_height - 10),
                                 (self.box_width - 10, current_box_height - 10),
                                 (self.box_width - 10, current_box_height - 10 - self.corner_size)], 2)
            
            screen.blit(corner_surf, (self.box_x, current_box_y))
        
        # Draw text (only after box is mostly expanded)
        if self.animation_state in ["typewriting", "complete"] and current_box_height > self.box_height * 0.8:
            self._draw_typewriter_text(screen, current_box_y)
            
    def _draw_typewriter_text(self, screen, box_y):
        """Draw text with typewriter effect."""
        chars_drawn = 0
        text_y = box_y + 20
        
        for line in self.wrapped_lines:
            if chars_drawn >= self.typewriter_progress:
                break
                
            # Calculate how many characters of this line to show
            chars_remaining = self.typewriter_progress - chars_drawn
            visible_chars = min(len(line), chars_remaining)
            visible_text = line[:visible_chars]
            
            if visible_text:
                # Render the visible portion
                text_surface = self.renderer.pixel_fonts['medium'].render(visible_text, True, self.text_color)
                text_rect = text_surface.get_rect(center=(config.WIDTH // 2, text_y))
                screen.blit(text_surface, text_rect)
            
            chars_drawn += len(line)
            text_y += 25
            
    def is_complete(self):
        """Check if the dialogue animation is complete."""
        return self.animation_state == "complete"
    
    def skip_animation(self):
        """Skip to the end of the animation."""
        if self.animation_state in ["expanding", "expanded"]:
            self.animation_state = "typewriting"
            self.current_height = self.box_height
            self.corner_alpha = 255
            self.glow_alpha = 80
            self.text_start_time = pygame.time.get_ticks() - 1000  # Start typewriter immediately
        elif self.animation_state == "typewriting":
            self.animation_state = "complete"
            self.typewriter_progress = sum(len(line) for line in self.wrapped_lines)
            
    def reset(self):
        """Reset the dialogue box to idle state."""
        self.animation_state = "idle"
        self.current_height = 2
        self.typewriter_progress = 0
        self.corner_alpha = 0
        self.glow_alpha = 0
        self.previous_text = ""
        self.current_dialogue_index = -1
        self.shown_dialogues.clear()
        self.animation_count = 0
        self.last_completion_time = 0
        if hasattr(self, '_first_dialogue_shown'):
            delattr(self, '_first_dialogue_shown')