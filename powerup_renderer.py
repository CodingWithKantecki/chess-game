"""
Powerup Rendering Module FINAL
Handles all visual aspects of the powerup system
"""

import pygame
import math
from config import *

class PowerupRenderer:
    def __init__(self, screen, renderer, powerup_system):
        self.screen = screen
        self.renderer = renderer  # Reference to main renderer for fonts
        self.powerup_system = powerup_system
        self.explosion_frames_scaled = {}  # Cache for scaled explosion frames
        # Performance: Cache progress to avoid file I/O every frame
        self._cached_progress = None
        self._progress_cache_time = 0
        self._progress_cache_duration = 1000  # Refresh cache every second
        # Cache scaled revolver image
        self._scaled_revolver_cache = {}
        
    def _get_cached_progress(self):
        """Get cached progress data to avoid file I/O every frame."""
        current_time = pygame.time.get_ticks()
        if (self._cached_progress is None or 
            current_time - self._progress_cache_time > self._progress_cache_duration):
            self._cached_progress = load_progress()
            self._progress_cache_time = current_time
        return self._cached_progress
        
    def draw_powerup_menu(self, board, mouse_pos):
        """Draw the powerup menu on the right side of the screen."""
        # Calculate menu position (right side of board)
        extra_spacing = 20  # Normal gap in windowed mode
            
        # Add the border width to ensure we're past the entire board
        menu_x = BOARD_OFFSET_X + BOARD_SIZE + extra_spacing
        menu_y = BOARD_OFFSET_Y + 36  # Move down by the board border size
        menu_width = POWERUP_MENU_WIDTH
        menu_height = BOARD_SIZE - 72  # Subtract top and bottom borders
        
        # Store position for click handling
        self.powerup_system.menu_x = menu_x
        self.powerup_system.menu_y = menu_y
        self.powerup_system.menu_width = menu_width
        self.powerup_system.menu_height = menu_height
        
        # Draw menu background - solid black background first
        # Draw a completely opaque black rectangle first
        black_bg = pygame.Surface((menu_width, menu_height))
        black_bg.fill((0, 0, 0))
        self.screen.blit(black_bg, (menu_x, menu_y))
        
        # Then add a slight transparency overlay for consistency
        overlay = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 50))
        self.screen.blit(overlay, (menu_x, menu_y))
        
        # Draw border
        pygame.draw.rect(self.screen, (100, 100, 120), 
                        (menu_x, menu_y, menu_width, menu_height), 3)
        
        # Title
        title_text = "POWERUPS"
        title_surface = self.renderer.pixel_fonts['large'].render(title_text, True, (180, 200, 180))
        title_rect = title_surface.get_rect(centerx=menu_x + menu_width // 2, y=menu_y + 20)
        self.screen.blit(title_surface, title_rect)
        
        # Player points
        player = board.current_turn
        points = self.powerup_system.points[player]
        points_text = f"POINTS: {points}"
        points_surface = self.renderer.pixel_fonts['medium'].render(points_text, True, (220, 190, 130))
        points_rect = points_surface.get_rect(centerx=menu_x + menu_width // 2, y=menu_y + 60)
        self.screen.blit(points_surface, points_rect)
        
        # Show whose turn it is
        turn_text = f"({player.upper()}'S TURN)"
        turn_surface = self.renderer.pixel_fonts['tiny'].render(turn_text, True, (150, 150, 150))
        turn_rect = turn_surface.get_rect(centerx=menu_x + menu_width // 2, y=menu_y + 85)
        self.screen.blit(turn_surface, turn_rect)
        
        # Get unlocked powerups - use cached version
        progress = self._get_cached_progress()
        unlocked_powerups = progress.get("unlocked_powerups", ["shield"])
        
        # Check if we're in tutorial mode
        in_tutorial = hasattr(self.powerup_system, 'in_tutorial') and self.powerup_system.in_tutorial
        
        # Filter powerups to only show unlocked ones (or all in tutorial)
        if in_tutorial:
            available_powerups = self.powerup_system.powerups
        else:
            available_powerups = {k: v for k, v in self.powerup_system.powerups.items() 
                                 if k in unlocked_powerups}
        
        # Clear button rects
        self.powerup_system.button_rects = {}
        
        # Draw powerup buttons
        button_y = menu_y + 120
        button_height = 70
        button_spacing = 15
        button_margin = 20
        button_width = menu_width - 2 * button_margin
        
        # If no powerups unlocked, show message
        if not available_powerups:
            no_powerups_text = "No powerups unlocked!"
            no_powerups_surface = self.renderer.pixel_fonts['small'].render(no_powerups_text, True, (200, 200, 200))
            no_powerups_rect = no_powerups_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                                           centery=menu_y + menu_height // 2)
            self.screen.blit(no_powerups_surface, no_powerups_rect)
            
            hint_text = "Visit Arms Dealer"
            hint_surface = self.renderer.pixel_fonts['tiny'].render(hint_text, True, (150, 150, 150))
            hint_rect = hint_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                             y=no_powerups_rect.bottom + 10)
            self.screen.blit(hint_surface, hint_rect)
            return
        
        for key, powerup in available_powerups.items():
            # Create button rect
            button_rect = pygame.Rect(menu_x + button_margin, button_y, 
                                     button_width, button_height)
            self.powerup_system.button_rects[key] = button_rect
            
            # Determine button state
            can_afford = self.powerup_system.can_afford_powerup(player, key)
            is_active = self.powerup_system.active_powerup == key
            is_hover = button_rect.collidepoint(mouse_pos) and can_afford
            
            # Choose button color - DARKER COLORS
            if is_active:
                button_color = (60, 60, 80)
            elif is_hover:
                button_color = (50, 50, 65)
            elif can_afford:
                button_color = (40, 40, 50)
            else:
                button_color = (20, 20, 25)
                
            # Draw button
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
            
            # Border color changes based on state
            if can_afford:
                # Use powerup color but dimmed
                border_color = tuple(c // 2 for c in powerup["color"])
            else:
                border_color = (40, 40, 40)
                
            pygame.draw.rect(self.screen, border_color, button_rect, 3, border_radius=10)
            
            # Glow effect when hovering
            if is_hover:
                glow_rect = button_rect.inflate(4, 4)
                pygame.draw.rect(self.screen, powerup["color"], glow_rect, 2, border_radius=12)
            
            # Draw icon
            if key == "gun" and hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'revolver_image') and self.renderer.assets.revolver_image:
                # Use the actual revolver image for gun powerup
                icon_size = 25
                # Cache scaled revolver to avoid scaling every frame
                cache_key = (icon_size, icon_size)
                if cache_key not in self._scaled_revolver_cache:
                    self._scaled_revolver_cache[cache_key] = pygame.transform.scale(self.renderer.assets.revolver_image, cache_key)
                scaled_revolver = self._scaled_revolver_cache[cache_key]
                
                # Apply grayscale effect if can't afford
                if not can_afford:
                    # Convert to grayscale
                    gray_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                    for x in range(icon_size):
                        for y in range(icon_size):
                            r, g, b, a = scaled_revolver.get_at((x, y))
                            gray = int(0.3 * r + 0.59 * g + 0.11 * b)
                            gray_surface.set_at((x, y), (gray, gray, gray, a))
                    scaled_revolver = gray_surface
                
                icon_rect = scaled_revolver.get_rect(centerx=button_rect.centerx, y=button_rect.y + 12)
                self.screen.blit(scaled_revolver, icon_rect)
            elif key == "chopper":
                # Draw helicopter icon
                self._draw_helicopter_icon(button_rect, can_afford)
            else:
                # Draw custom icons for other powerups
                icon_size = 30
                icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                icon_surface.fill((0, 0, 0, 0))
                
                if key == "airstrike":
                    # Draw missile icon
                    self._draw_missile_icon(icon_surface, icon_size, can_afford)
                elif key == "shield":
                    # Draw shield icon
                    self._draw_shield_icon(icon_surface, icon_size, can_afford)
                elif key == "paratroopers":
                    # Draw parachute icon
                    self._draw_parachute_icon(icon_surface, icon_size, can_afford)
                else:
                    # Fallback to text icon
                    icon_color = WHITE if can_afford else (80, 80, 80)
                    icon_surface = self.renderer.pixel_fonts['large'].render(powerup["icon"], True, icon_color)
                
                icon_rect = icon_surface.get_rect(centerx=button_rect.centerx, y=button_rect.y + 10)
                self.screen.blit(icon_surface, icon_rect)
            
            # Draw name
            name_color = (200, 220, 200) if can_afford else (80, 80, 80)
            name_surface = self.renderer.pixel_fonts['small'].render(powerup["name"], True, name_color)
            name_rect = name_surface.get_rect(centerx=button_rect.centerx, y=button_rect.y + 35)
            self.screen.blit(name_surface, name_rect)
            
            # Draw cost
            cost_text = f"Cost: {powerup['cost']}"
            cost_color = (200, 180, 140) if can_afford else (80, 80, 80)
            cost_surface = self.renderer.pixel_fonts['tiny'].render(cost_text, True, cost_color)
            cost_rect = cost_surface.get_rect(centerx=button_rect.centerx, y=button_rect.y + 55)
            self.screen.blit(cost_surface, cost_rect)
            
            button_y += button_height + button_spacing
            
        # Draw instructions at bottom
        if self.powerup_system.active_powerup:
            instruction_text = self._get_instruction_text()
            inst_surface = self.renderer.pixel_fonts['small'].render(instruction_text, True, (220, 220, 180))
            inst_rect = inst_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                             bottom=menu_y + menu_height - 20)
            self.screen.blit(inst_surface, inst_rect)
            
            # Cancel instruction
            cancel_text = "ESC to cancel"
            cancel_surface = self.renderer.pixel_fonts['tiny'].render(cancel_text, True, (200, 100, 100))
            cancel_rect = cancel_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                                bottom=menu_y + menu_height - 40)
            self.screen.blit(cancel_surface, cancel_rect)
            
    def _draw_helicopter_icon(self, button_rect, enabled):
        """Draw a helicopter icon for chopper gunner."""
        color = (255, 100, 100) if enabled else (80, 80, 80)
        darker_color = tuple(c // 2 for c in color)
        
        # Calculate center position
        center_x = button_rect.centerx
        center_y = button_rect.y + 22
        
        # Main body
        body_width = 20
        body_height = 12
        body_rect = pygame.Rect(center_x - body_width // 2, center_y - body_height // 2, 
                               body_width, body_height)
        pygame.draw.ellipse(self.screen, color, body_rect)
        pygame.draw.ellipse(self.screen, darker_color, body_rect, 1)
        
        # Tail
        tail_width = 15
        tail_height = 4
        pygame.draw.rect(self.screen, color, 
                        (center_x + body_width // 2 - 2, center_y - tail_height // 2, 
                         tail_width, tail_height))
        
        # Main rotor (animated)
        rotor_length = 25
        rotor_angle = (pygame.time.get_ticks() // 20) % 360
        for i in range(2):
            angle = rotor_angle + i * 180
            x1 = center_x + math.cos(math.radians(angle)) * rotor_length
            y1 = center_y - body_height // 2 - 3 + math.sin(math.radians(angle)) * 2
            x2 = center_x - math.cos(math.radians(angle)) * rotor_length
            y2 = center_y - body_height // 2 - 3 - math.sin(math.radians(angle)) * 2
            pygame.draw.line(self.screen, darker_color, (x1, y1), (x2, y2), 2)
            
        # Tail rotor
        tail_rotor_x = center_x + body_width // 2 + tail_width - 3
        pygame.draw.circle(self.screen, darker_color, (tail_rotor_x, center_y), 4, 1)
        
        # Landing skids
        skid_y = center_y + body_height // 2 + 2
        pygame.draw.line(self.screen, darker_color, 
                        (center_x - body_width // 2, skid_y), 
                        (center_x + body_width // 2, skid_y), 1)
            
    def _draw_missile_icon(self, surface, size, enabled):
        """Draw a horizontal missile icon for airstrike."""
        color = (255, 100, 100) if enabled else (80, 80, 80)
        darker_color = tuple(c // 2 for c in color)
        
        # Horizontal missile
        missile_length = int(size * 0.7)
        missile_height = int(size * 0.25)
        
        # Center the missile
        missile_x = (size - missile_length) // 2
        missile_y = (size - missile_height) // 2
        
        # Draw main body
        body_x = missile_x + missile_length // 4
        body_width = missile_length // 2
        pygame.draw.rect(surface, color, 
                        (body_x, missile_y, body_width, missile_height))
        
        # Add highlight for 3D effect
        pygame.draw.line(surface, tuple(min(255, c + 50) for c in color),
                        (body_x, missile_y + 1), 
                        (body_x + body_width, missile_y + 1), 1)
        
        # Draw nose cone
        nose_points = [
            (missile_x, missile_y + missile_height // 2),
            (body_x, missile_y),
            (body_x, missile_y + missile_height)
        ]
        pygame.draw.polygon(surface, color, nose_points)
        
        # Draw tail fins
        fin_x = body_x + body_width
        fin_width = missile_length // 4
        
        # Top fin
        pygame.draw.polygon(surface, darker_color, [
            (fin_x, missile_y),
            (fin_x + fin_width, missile_y - missile_height // 3),
            (fin_x + fin_width, missile_y + missile_height // 3),
            (fin_x, missile_y + missile_height // 3)
        ])
        
        # Bottom fin
        pygame.draw.polygon(surface, darker_color, [
            (fin_x, missile_y + missile_height),
            (fin_x + fin_width, missile_y + missile_height + missile_height // 3),
            (fin_x + fin_width, missile_y + missile_height * 2 // 3),
            (fin_x, missile_y + missile_height * 2 // 3)
        ])
        
        # Small center fin
        pygame.draw.rect(surface, darker_color,
                        (fin_x, missile_y + missile_height // 3, 
                         fin_width // 2, missile_height // 3))
                                   
    def _draw_shield_icon(self, surface, size, enabled):
        """Draw a shield icon."""
        color = (100, 200, 255) if enabled else (80, 80, 80)
        darker_color = tuple(int(c * 0.7) for c in color)
        lighter_color = tuple(min(255, int(c * 1.3)) for c in color)
        
        # Shield shape
        width = int(size * 0.6)
        height = int(size * 0.7)
        x = (size - width) // 2
        y = size // 6
        
        # Main shield body
        shield_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, shield_rect)
        
        # Top curved part
        pygame.draw.ellipse(surface, color, (x - 2, y - height // 4, width + 4, height // 2))
        
        # Inner border for depth
        inner_rect = pygame.Rect(x + 3, y + 3, width - 6, height - 6)
        pygame.draw.rect(surface, darker_color, inner_rect, 2)
        
        # Simple cross design
        cross_thickness = 4
        # Vertical line
        pygame.draw.rect(surface, lighter_color, 
                        (size // 2 - cross_thickness // 2, y + height // 5, 
                         cross_thickness, height * 3 // 5))
        # Horizontal line
        pygame.draw.rect(surface, lighter_color, 
                        (x + width // 5, y + height // 2 - cross_thickness // 2, 
                         width * 3 // 5, cross_thickness))
            
    def _draw_parachute_icon(self, surface, size, enabled):
        """Draw a parachute icon."""
        color = (100, 200, 100) if enabled else (80, 80, 80)
        darker_color = tuple(int(c * 0.7) for c in color)
        
        # Cleaner parachute design
        canopy_width = int(size * 0.7)
        canopy_height = int(size * 0.35)
        canopy_x = (size - canopy_width) // 2
        canopy_y = size // 5
        
        # Draw canopy as filled semi-circle
        canopy_center_x = size // 2
        canopy_center_y = canopy_y + canopy_height // 2
        
        # Draw the canopy segments
        segment_count = 5
        for i in range(segment_count):
            angle_start = math.pi + (math.pi * i / segment_count)
            angle_end = math.pi + (math.pi * (i + 1) / segment_count)
            
            # Calculate points for the segment
            points = [(canopy_center_x, canopy_center_y)]
            for angle in [angle_start, angle_end]:
                x = canopy_center_x + int(canopy_width // 2 * math.cos(angle))
                y = canopy_center_y + int(canopy_height * math.sin(angle))
                points.append((x, y))
            
            # Alternate colors for segments
            segment_color = color if i % 2 == 0 else darker_color
            pygame.draw.polygon(surface, segment_color, points)
        
        # Draw strings
        string_end_y = size - size // 3
        string_end_x = size // 2
        
        # Draw 3 main strings
        string_positions = [canopy_x + canopy_width // 4, size // 2, canopy_x + 3 * canopy_width // 4]
        for string_x in string_positions:
            pygame.draw.line(surface, darker_color, 
                           (string_x, canopy_y + canopy_height), 
                           (string_end_x, string_end_y), 1)
        
        # Draw simplified person/cargo
        cargo_size = size // 8
        pygame.draw.rect(surface, color, 
                        (string_end_x - cargo_size // 2, string_end_y, 
                         cargo_size, cargo_size))
            
    def draw_powerup_targeting(self, board, mouse_pos):
        """Draw targeting indicators for active powerups."""
        if not self.powerup_system.active_powerup:
            return
            
        if self.powerup_system.active_powerup == "airstrike":
            self._draw_airstrike_targeting(board, mouse_pos)
        elif self.powerup_system.active_powerup == "shield":
            self._draw_shield_targeting(board, mouse_pos)
        elif self.powerup_system.active_powerup == "gun":
            self._draw_gun_targeting(board, mouse_pos)
        elif self.powerup_system.active_powerup == "chopper":
            self._draw_chopper_targeting(board, mouse_pos)
        elif self.powerup_system.active_powerup == "paratroopers":
            self._draw_paratroopers_targeting(board, mouse_pos)
            
    def _draw_airstrike_targeting(self, board, mouse_pos):
        """Draw 3x3 targeting grid for airstrike."""
        row, col = board.get_square_from_pos(mouse_pos)
        if row < 0 or col < 0:
            return
            
        # Draw 3x3 grid
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                target_row = row + dr
                target_col = col + dc
                if 0 <= target_row < 8 and 0 <= target_col < 8:
                    x, y = board.get_square_pos(target_row, target_col)
                    
                    # Draw targeting square
                    target_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    target_surface.fill((255, 0, 0, 60))
                    self.screen.blit(target_surface, (x, y))
                    
                    # Draw border
                    pygame.draw.rect(self.screen, (255, 0, 0), 
                                   (x, y, SQUARE_SIZE, SQUARE_SIZE), 2)
                                   
    def _draw_shield_targeting(self, board, mouse_pos):
        """Highlight valid pieces for shield."""
        player = self.powerup_system.powerup_state["player"]
        player_color = 'w' if player == "white" else 'b'
        
        # Highlight all player's pieces
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == player_color:
                    x, y = board.get_square_pos(row, col)
                    
                    # Check if mouse is over this piece
                    mouse_row, mouse_col = board.get_square_from_pos(mouse_pos)
                    is_hover = (row == mouse_row and col == mouse_col)
                    
                    # Draw highlight
                    highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    if is_hover:
                        highlight_surface.fill((100, 200, 255, 100))
                    else:
                        highlight_surface.fill((100, 200, 255, 40))
                    self.screen.blit(highlight_surface, (x, y))
                    
                    if is_hover:
                        pygame.draw.rect(self.screen, (100, 200, 255), 
                                       (x, y, SQUARE_SIZE, SQUARE_SIZE), 3)
                                       
    def _draw_gun_targeting(self, board, mouse_pos):
        """Draw gun targeting based on phase."""
        if self.powerup_system.powerup_state["phase"] == "selecting":
            # Highlight player's pieces
            self._draw_shield_targeting(board, mouse_pos)
        else:
            # Show valid targets and draw gun on shooter
            valid_targets = self.powerup_system.powerup_state["data"].get("valid_targets", [])
            
            # Draw the revolver on the shooter piece
            shooter_row, shooter_col = self.powerup_system.powerup_state["data"]["shooter"]
            shooter_x, shooter_y = board.get_square_pos(shooter_row, shooter_col)
            
            # Draw the revolver if image is loaded
            if hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'revolver_image') and self.renderer.assets.revolver_image:
                # Scale the revolver
                revolver_size = int(SQUARE_SIZE * 0.4)
                # Cache scaled revolver to avoid scaling every frame
                cache_key = (revolver_size, revolver_size)
                if cache_key not in self._scaled_revolver_cache:
                    self._scaled_revolver_cache[cache_key] = pygame.transform.scale(self.renderer.assets.revolver_image, cache_key)
                scaled_revolver = self._scaled_revolver_cache[cache_key]
                
                # Position it at the top-right of the piece
                revolver_x = shooter_x + SQUARE_SIZE - revolver_size - 5
                revolver_y = shooter_y + 5
                
                # Draw a slight shadow/glow effect
                glow_surface = pygame.Surface((revolver_size + 4, revolver_size + 4), pygame.SRCALPHA)
                glow_surface.fill((255, 200, 100, 50))
                self.screen.blit(glow_surface, (revolver_x - 2, revolver_y - 2))
                
                # Draw the revolver
                self.screen.blit(scaled_revolver, (revolver_x, revolver_y))
            
            # Draw line from shooter to mouse
            shooter_center = (shooter_x + SQUARE_SIZE // 2, 
                            shooter_y + SQUARE_SIZE // 2)
            
            # Draw targeting line
            pygame.draw.line(self.screen, (255, 200, 100, 150), shooter_center, mouse_pos, 2)
            
            # Highlight valid targets
            for target_row, target_col in valid_targets:
                x, y = board.get_square_pos(target_row, target_col)
                
                # Check if mouse is over this target
                mouse_row, mouse_col = board.get_square_from_pos(mouse_pos)
                is_hover = (target_row == mouse_row and target_col == mouse_col)
                
                # Draw crosshair
                center_x = x + SQUARE_SIZE // 2
                center_y = y + SQUARE_SIZE // 2
                radius = 20
                
                color = (255, 0, 0) if is_hover else (200, 100, 100)
                pygame.draw.circle(self.screen, color, (center_x, center_y), radius, 2)
                pygame.draw.line(self.screen, color, 
                               (center_x - radius, center_y), (center_x + radius, center_y), 2)
                pygame.draw.line(self.screen, color, 
                               (center_x, center_y - radius), (center_x, center_y + radius), 2)
                               
    def _draw_chopper_targeting(self, board, mouse_pos):
        """Draw chopper gunner confirmation dialog."""
        # Dim the entire screen
        dim_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim_surface.fill((0, 0, 0, 180))
        self.screen.blit(dim_surface, (0, 0))
        
        # Dialog box dimensions
        dialog_width = 400
        dialog_height = 200
        dialog_x = (WIDTH - dialog_width) // 2
        dialog_y = (HEIGHT - dialog_height) // 2
        
        # Draw dialog background
        pygame.draw.rect(self.screen, (30, 30, 30), 
                        (dialog_x, dialog_y, dialog_width, dialog_height), 
                        border_radius=10)
        pygame.draw.rect(self.screen, (200, 50, 50), 
                        (dialog_x, dialog_y, dialog_width, dialog_height), 
                        3, border_radius=10)
        
        # Warning text
        warning_text = "WARNING!"
        warning_surface = self.renderer.pixel_fonts['large'].render(warning_text, True, (255, 50, 50))
        warning_rect = warning_surface.get_rect(centerx=WIDTH // 2, y=dialog_y + 20)
        self.screen.blit(warning_surface, warning_rect)
        
        # Message text
        message = "This will destroy all enemy pieces!"
        message_surface = self.renderer.pixel_fonts['medium'].render(message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(centerx=WIDTH // 2, y=dialog_y + 60)
        self.screen.blit(message_surface, message_rect)
        
        question = "Are you sure you want to continue?"
        question_surface = self.renderer.pixel_fonts['medium'].render(question, True, (200, 200, 200))
        question_rect = question_surface.get_rect(centerx=WIDTH // 2, y=dialog_y + 90)
        self.screen.blit(question_surface, question_rect)
        
        # Store button positions for click handling
        button_width = 100
        button_height = 40
        button_spacing = 20
        buttons_total_width = button_width * 2 + button_spacing
        button_y = dialog_y + dialog_height - 60
        
        # YES button
        yes_x = (WIDTH - buttons_total_width) // 2
        self.powerup_system.chopper_yes_button = pygame.Rect(yes_x, button_y, button_width, button_height)
        
        # NO button
        no_x = yes_x + button_width + button_spacing
        self.powerup_system.chopper_no_button = pygame.Rect(no_x, button_y, button_width, button_height)
        
        # Draw buttons with hover effect
        # YES button
        yes_hover = self.powerup_system.chopper_yes_button.collidepoint(mouse_pos)
        yes_color = (50, 150, 50) if yes_hover else (30, 100, 30)
        pygame.draw.rect(self.screen, yes_color, self.powerup_system.chopper_yes_button, border_radius=5)
        pygame.draw.rect(self.screen, (100, 255, 100), self.powerup_system.chopper_yes_button, 2, border_radius=5)
        
        yes_text = self.renderer.pixel_fonts['medium'].render("YES", True, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=self.powerup_system.chopper_yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # NO button
        no_hover = self.powerup_system.chopper_no_button.collidepoint(mouse_pos)
        no_color = (150, 50, 50) if no_hover else (100, 30, 30)
        pygame.draw.rect(self.screen, no_color, self.powerup_system.chopper_no_button, border_radius=5)
        pygame.draw.rect(self.screen, (255, 100, 100), self.powerup_system.chopper_no_button, 2, border_radius=5)
        
        no_text = self.renderer.pixel_fonts['medium'].render("NO", True, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=self.powerup_system.chopper_no_button.center)
        self.screen.blit(no_text, no_text_rect)
                               
    def _draw_paratroopers_targeting(self, board, mouse_pos):
        """Draw paratrooper placement indicators."""
        # Show how many pawns left to place
        placed = len(self.powerup_system.powerup_state["data"].get("placed", []))
        remaining = 3 - placed
        
        info_text = f"PLACE {remaining} MORE PAWN{'S' if remaining > 1 else ''}"
        text_surface = self.renderer.pixel_fonts['medium'].render(info_text, True, (100, 200, 100))
        text_rect = text_surface.get_rect(center=(BOARD_OFFSET_X + BOARD_SIZE // 2, 
                                                  BOARD_OFFSET_Y - 30))
        self.screen.blit(text_surface, text_rect)
        
        # Highlight empty squares
        for row in range(8):
            for col in range(8):
                if board.get_piece(row, col) == "":
                    x, y = board.get_square_pos(row, col)
                    
                    # Check if mouse is over this square
                    mouse_row, mouse_col = board.get_square_from_pos(mouse_pos)
                    is_hover = (row == mouse_row and col == mouse_col)
                    
                    # Draw parachute preview
                    if is_hover:
                        # Draw landing zone
                        zone_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                        zone_surface.fill((100, 200, 100, 100))
                        self.screen.blit(zone_surface, (x, y))
                        
                        # Draw parachute icon
                        chute_text = "🪂"
                        chute_surface = self.renderer.pixel_fonts['large'].render(chute_text, True, (255, 255, 255))
                        chute_rect = chute_surface.get_rect(center=(x + SQUARE_SIZE // 2, 
                                                                   y + SQUARE_SIZE // 2))
                        self.screen.blit(chute_surface, chute_rect)
                               
    def draw_effects(self, board):
        """Draw visual effects."""
        current_time = pygame.time.get_ticks()
        
        # Draw animations
        for anim in self.powerup_system.animations:
            progress = (current_time - anim["start_time"]) / anim["duration"]
            
            if anim["type"] == "jet_flyby":
                self._draw_jet_flyby_animation(anim, progress, board)
            elif anim["type"] == "airstrike":
                self._draw_airstrike_animation(anim, progress, board)
            elif anim["type"] == "shield":
                self._draw_shield_animation(anim, progress)
            elif anim["type"] == "lightning":
                self._draw_lightning_animation(anim, progress)
            elif anim["type"] == "gunshot":
                self._draw_gunshot_animation(anim, progress)
            elif anim["type"] == "paratrooper":
                self._draw_paratrooper_animation(anim, progress)
                
        # Draw particle effects
        for effect in self.powerup_system.effects:
            if effect["type"] == "explosion_particle":
                self._draw_explosion_particle(effect, current_time)
            elif effect["type"] == "muzzle_flash":
                self._draw_muzzle_flash(effect, current_time)
            elif effect["type"] == "impact":
                self._draw_impact_effect(effect, current_time)
                
        # Draw persistent shield indicators
        self._draw_active_shields(board)
        
    def _draw_jet_flyby_animation(self, anim, progress, board):
        """Draw jet flying across screen and dropping bomb."""
        if not hasattr(self.renderer, 'assets') or not hasattr(self.renderer.assets, 'jet_frames') or not self.renderer.assets.jet_frames:
            return
            
        # Calculate jet position (flying from RIGHT to LEFT)
        start_x = BOARD_OFFSET_X + BOARD_SIZE + 100
        end_x = BOARD_OFFSET_X - 200
        
        # Jet flies from right to left
        jet_x = start_x + (end_x - start_x) * progress
        
        # Height arc - jet dips down at target then rises
        base_y = BOARD_OFFSET_Y - 50
        target_progress = abs(progress - 0.5) * 2
        jet_y = base_y + (1 - target_progress) * 50
        
        # Calculate which frame to show
        frame_duration = [0.2, 0.14, 0.14, 0.2]
        total_duration = sum(frame_duration)
        
        # Determine current frame based on animation cycle
        cycle_progress = (progress * 3) % 1
        current_time = cycle_progress * total_duration
        
        frame_index = 0
        accumulated_time = 0
        for i, duration in enumerate(frame_duration):
            accumulated_time += duration
            if current_time <= accumulated_time:
                frame_index = i
                break
                
        if frame_index >= len(self.renderer.assets.jet_frames):
            frame_index = len(self.renderer.assets.jet_frames) - 1
            
        # Get the jet frame
        jet_frame = self.renderer.assets.jet_frames[frame_index]
        
        # Scale the jet
        jet_scale = 0.75
        jet_width = int(jet_frame.get_width() * jet_scale)
        jet_height = int(jet_frame.get_height() * jet_scale)
        
        # Just scale the jet, no flip needed
        scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
        
        # Draw the jet
        self.screen.blit(scaled_jet, (jet_x, jet_y))
        
        # Draw bomb being dropped when jet is near target
        if 0.4 <= progress <= 0.6:
            bomb_progress = (progress - 0.4) / 0.2
            bomb_x = anim["target_x"] + SQUARE_SIZE // 2
            bomb_start_y = jet_y + jet_height
            bomb_end_y = anim["target_y"] + SQUARE_SIZE // 2
            bomb_y = bomb_start_y + (bomb_end_y - bomb_start_y) * bomb_progress
            
            # Draw a realistic bomb
            bomb_width = 8
            bomb_height = 20
            
            # Main bomb body
            bomb_rect = pygame.Rect(bomb_x - bomb_width // 2, bomb_y - bomb_height // 2, 
                                   bomb_width, bomb_height)
            pygame.draw.ellipse(self.screen, (60, 60, 60), bomb_rect)
            pygame.draw.ellipse(self.screen, (40, 40, 40), bomb_rect, 1)
            
            # Nose cone
            nose_points = [
                (bomb_x - bomb_width // 2, bomb_y + bomb_height // 2 - 2),
                (bomb_x + bomb_width // 2, bomb_y + bomb_height // 2 - 2),
                (bomb_x, bomb_y + bomb_height // 2 + bomb_width)
            ]
            pygame.draw.polygon(self.screen, (50, 50, 50), nose_points)
            
            # Tail fins at top
            fin_height = 6
            fin_width = 12
            # Left fin
            pygame.draw.polygon(self.screen, (70, 70, 70), [
                (bomb_x - bomb_width // 2, bomb_y - bomb_height // 2),
                (bomb_x - bomb_width // 2 - fin_width // 3, bomb_y - bomb_height // 2 - fin_height),
                (bomb_x - bomb_width // 2, bomb_y - bomb_height // 2 + 2)
            ])
            # Right fin
            pygame.draw.polygon(self.screen, (70, 70, 70), [
                (bomb_x + bomb_width // 2, bomb_y - bomb_height // 2),
                (bomb_x + bomb_width // 2 + fin_width // 3, bomb_y - bomb_height // 2 - fin_height),
                (bomb_x + bomb_width // 2, bomb_y - bomb_height // 2 + 2)
            ])
            # Center fin
            pygame.draw.rect(self.screen, (70, 70, 70), 
                           (bomb_x - 1, bomb_y - bomb_height // 2 - fin_height, 
                            2, fin_height))
    
    def _draw_airstrike_animation(self, anim, progress, board):
        """Draw airstrike explosion using sprite frames."""
        # Skip drawing if progress is negative
        if progress < 0:
            return
            
        # Check if we have explosion frames loaded
        if hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'explosion_frames') and self.renderer.assets.explosion_frames:
            # Calculate which frame to show
            frame_count = len(self.renderer.assets.explosion_frames)
            clamped_progress = min(progress, 0.9999)
            frame_index = int(clamped_progress * frame_count)
            frame_index = max(0, min(frame_index, frame_count - 1))
                
            # Get the explosion frame
            explosion_frame = self.renderer.assets.explosion_frames[frame_index]
            
            # Scale the explosion to cover 3x3 grid
            explosion_size = SQUARE_SIZE * 3
            
            # Cache scaled frames for performance
            cache_key = (frame_index, explosion_size)
            if cache_key not in self.explosion_frames_scaled:
                self.explosion_frames_scaled[cache_key] = pygame.transform.scale(
                    explosion_frame, (explosion_size, explosion_size))
                    
            scaled_frame = self.explosion_frames_scaled[cache_key]
            
            # Position explosion centered on the target square
            center_x = anim["x"] + SQUARE_SIZE // 2
            center_y = anim["y"] + SQUARE_SIZE // 2
            x = center_x - explosion_size // 2
            y = center_y - explosion_size // 2
            
            # Draw the explosion frame
            self.screen.blit(scaled_frame, (x, y))
            
        else:
            # Fallback to original animation if frames not loaded
            center_x = anim["x"] + SQUARE_SIZE // 2
            center_y = anim["y"] + SQUARE_SIZE // 2
            
            # Multiple explosion rings
            for i in range(3):
                phase = (progress + i * 0.2) % 1.0
                if phase < 0.7:
                    radius = int(SQUARE_SIZE * 1.5 * phase)
                    alpha = int(255 * (1 - phase))
                    
                    if radius > 0:
                        explosion_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                        explosion_surface.fill((0, 0, 0, 0))
                        pygame.draw.circle(explosion_surface, (255, 150 - i * 30, 0), (radius, radius), radius)
                        explosion_surface.set_alpha(alpha)
                        self.screen.blit(explosion_surface, (center_x - radius, center_y - radius))
                        
    def _draw_shield_animation(self, anim, progress):
        """Draw shield activation effect."""
        x, y = anim["x"], anim["y"]
        
        # Expanding shield bubble
        max_radius = int(SQUARE_SIZE * 0.6)
        radius = int(max_radius * progress)
        alpha = int(200 * (1 - progress))
        
        shield_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        shield_surface.fill((0, 0, 0, 0))
        
        # Draw circle with color but set alpha on the surface
        if radius > 0:
            pygame.draw.circle(shield_surface, (100, 200, 255), 
                             (SQUARE_SIZE // 2, SQUARE_SIZE // 2), radius, 3)
        shield_surface.set_alpha(alpha)
        self.screen.blit(shield_surface, (x, y))
        
    def _draw_lightning_animation(self, anim, progress):
        """Draw lightning strike effect before shield."""
        x, y = anim["x"], anim["y"]
        center_x = x + SQUARE_SIZE // 2
        center_y = y + SQUARE_SIZE // 2
        
        # Lightning comes from above
        start_y = y - SQUARE_SIZE * 2
        
        # Create multiple lightning bolts for dramatic effect
        if progress < 0.7:  # Lightning strikes phase
            # Main lightning bolt
            segments = 8
            bolt_x = center_x
            bolt_y = start_y
            
            # Generate jagged lightning path
            import random
            random.seed(int(anim["start_time"]))  # Consistent randomness for this bolt
            
            points = [(center_x, start_y)]
            for i in range(segments):
                progress_segment = (i + 1) / segments
                next_y = start_y + (center_y - start_y) * progress_segment
                # Zigzag left and right
                offset = random.randint(-20, 20)
                next_x = center_x + offset
                points.append((next_x, next_y))
            
            # Draw the lightning bolt with glow effect
            for width, color, alpha_mult in [(8, (255, 255, 255), 0.3), 
                                            (5, (200, 200, 255), 0.5), 
                                            (2, (255, 255, 255), 1.0)]:
                if len(points) > 1:
                    # Create surface for this lightning layer
                    bolt_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
                    bolt_surface.fill((0, 0, 0, 0))
                    
                    # Draw connected segments
                    visible_points = points[:int(len(points) * (progress / 0.7))]
                    if len(visible_points) > 1:
                        for i in range(len(visible_points) - 1):
                            pygame.draw.line(bolt_surface, color, visible_points[i], visible_points[i + 1], width)
                    
                    # Apply alpha
                    alpha = int(255 * alpha_mult * (1 - progress / 0.7))
                    bolt_surface.set_alpha(alpha)
                    self.screen.blit(bolt_surface, (0, 0))
            
            # Add smaller branch bolts
            if progress > 0.2 and len(visible_points) > 2:
                for _ in range(2):
                    max_idx = len(visible_points) - 1
                    if max_idx > 2:
                        branch_start_idx = random.randint(2, min(5, max_idx))
                        if branch_start_idx < len(visible_points):
                            branch_start = visible_points[branch_start_idx]
                            branch_end_x = branch_start[0] + random.randint(-30, 30)
                            branch_end_y = branch_start[1] + random.randint(20, 40)
                            pygame.draw.line(self.screen, (200, 200, 255), branch_start, (branch_end_x, branch_end_y), 2)
        
        # Flash effect at impact point
        if 0.5 < progress < 0.9:
            flash_alpha = int(255 * (1 - (progress - 0.5) / 0.4))
            flash_radius = int(SQUARE_SIZE * 0.8)
            flash_surface = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            flash_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(flash_surface, (255, 255, 255), (flash_radius, flash_radius), flash_radius)
            flash_surface.set_alpha(flash_alpha)
            self.screen.blit(flash_surface, (center_x - flash_radius, center_y - flash_radius))
        
    def _draw_gunshot_animation(self, anim, progress):
        """Draw bullet/laser effect with revolver."""
        # Draw the revolver at the start position for the first part of the animation
        if progress < 0.3 and hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'revolver_image') and self.renderer.assets.revolver_image:
            # Calculate revolver position (it should appear to recoil)
            recoil = int(10 * progress * 3)  # Quick recoil effect
            revolver_size = int(SQUARE_SIZE * 0.4)
            # Cache scaled revolver to avoid scaling every frame
            cache_key = (revolver_size, revolver_size)
            if cache_key not in self._scaled_revolver_cache:
                self._scaled_revolver_cache[cache_key] = pygame.transform.scale(self.renderer.assets.revolver_image, cache_key)
            scaled_revolver = self._scaled_revolver_cache[cache_key]
            
            # Position based on the starting position
            revolver_x = anim["start_x"] - revolver_size // 2 - recoil
            revolver_y = anim["start_y"] - revolver_size // 2
            
            # Add a muzzle flash effect at the tip of the gun
            if progress < 0.1:
                flash_size = 20
                flash_surface = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surface, (255, 255, 200), (flash_size, flash_size), flash_size)
                flash_surface.set_alpha(int(255 * (1 - progress * 10)))
                self.screen.blit(flash_surface, (revolver_x + revolver_size, revolver_y + revolver_size // 2 - flash_size))
            
            self.screen.blit(scaled_revolver, (revolver_x, revolver_y))
        
        # Interpolate bullet position
        x = anim["start_x"] + (anim["end_x"] - anim["start_x"]) * progress
        y = anim["start_y"] + (anim["end_y"] - anim["start_y"]) * progress
        
        # Draw trail
        trail_length = 50
        angle = math.atan2(anim["end_y"] - anim["start_y"], 
                          anim["end_x"] - anim["start_x"])
        trail_x = x - math.cos(angle) * trail_length * progress
        trail_y = y - math.sin(angle) * trail_length * progress
        
        # Fade out trail
        alpha = int(255 * (1 - progress * 0.5))
        pygame.draw.line(self.screen, (255, 200, 100), (trail_x, trail_y), (x, y), 4)
                        
    def _draw_explosion_particle(self, effect, current_time):
        """Draw explosion particle."""
        elapsed = current_time - effect["start_time"]
        progress = elapsed / effect["duration"]
        
        # Update position with gravity
        x = effect["x"] + effect["vx"] * elapsed / 1000
        y = effect["y"] + effect["vy"] * elapsed / 1000 + 0.5 * 300 * (elapsed / 1000) ** 2
        
        # Fade out
        alpha = int(255 * (1 - progress))
        size = int(effect["size"] * (1 - progress * 0.5))
        
        if size > 0:
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            particle_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(particle_surface, effect["color"], (size, size), size)
            particle_surface.set_alpha(alpha)
            self.screen.blit(particle_surface, (x - size, y - size))
            
    def _draw_muzzle_flash(self, effect, current_time):
        """Draw muzzle flash effect."""
        progress = (current_time - effect["start_time"]) / effect["duration"]
        
        size = int(30 * (1 - progress))
        alpha = int(255 * (1 - progress))
        
        if size > 0:
            flash_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            flash_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(flash_surface, (255, 255, 200), (size, size), size)
            flash_surface.set_alpha(alpha)
            self.screen.blit(flash_surface, (effect["x"] - size, effect["y"] - size))
            
    def _draw_impact_effect(self, effect, current_time):
        """Draw impact effect at target."""
        progress = (current_time - effect["start_time"]) / effect["duration"]
        
        radius = int(20 * (1 + progress))
        alpha = int(200 * (1 - progress))
        
        if radius > 0:
            impact_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            impact_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(impact_surface, (255, 100, 100), 
                             (radius, radius), radius, 3)
            impact_surface.set_alpha(alpha)
            self.screen.blit(impact_surface, (effect["x"] - radius, effect["y"] - radius))
            
    def _draw_active_shields(self, board):
        """Draw shields on protected pieces."""
        current_time = pygame.time.get_ticks()
        
        for (row, col), turns_remaining in self.powerup_system.shielded_pieces.items():
            x, y = board.get_square_pos(row, col)
            
            # Pulsing shield effect
            pulse = math.sin(current_time / 200) * 0.2 + 0.8
            radius = int(SQUARE_SIZE * 0.4 * pulse)
            
            # Shield bubble
            shield_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            shield_surface.fill((0, 0, 0, 0))
            center = SQUARE_SIZE // 2
            
            # Outer glow
            for i in range(3):
                glow_radius = radius + i * 3
                alpha = int(100 - i * 30)
                if glow_radius > 0:
                    glow_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    glow_surface.fill((0, 0, 0, 0))
                    pygame.draw.circle(glow_surface, (100, 200, 255), 
                                     (center, center), glow_radius, 1)
                    glow_surface.set_alpha(alpha)
                    shield_surface.blit(glow_surface, (0, 0))
                                 
            # Inner shield
            if radius > 0:
                pygame.draw.circle(shield_surface, (150, 220, 255), 
                                 (center, center), radius, 2)
                             
            # Turns remaining indicator
            turns_text = str(turns_remaining)
            text_surface = self.renderer.pixel_fonts['tiny'].render(turns_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(center, center))
            shield_surface.blit(text_surface, text_rect)
            
            shield_surface.set_alpha(150)
            self.screen.blit(shield_surface, (x, y))
            
    def _get_instruction_text(self):
        """Get instruction text for active powerup."""
        if self.powerup_system.active_powerup == "airstrike":
            return "Click to target 3x3 area"
        elif self.powerup_system.active_powerup == "shield":
            return "Click your piece to shield"
        elif self.powerup_system.active_powerup == "gun":
            if self.powerup_system.powerup_state["phase"] == "selecting":
                return "Select piece to shoot with"
            else:
                return "Click enemy to shoot"
        elif self.powerup_system.active_powerup == "chopper":
            return "Confirm activation"
        elif self.powerup_system.active_powerup == "paratroopers":
            placed = len(self.powerup_system.powerup_state["data"].get("placed", []))
            return f"Place pawn {placed + 1} of 3"
        return ""
        
    def _draw_paratrooper_animation(self, anim, progress):
        """Draw paratrooper drop effect."""
        x, y = anim["x"], anim["y"]
        
        # Calculate drop position (falling from above)
        start_y = y - SQUARE_SIZE * 3
        current_y = start_y + (y - start_y) * progress
        
        # Draw parachute
        chute_size = int(SQUARE_SIZE * 0.8)
        chute_x = x + SQUARE_SIZE // 2
        
        # Parachute canopy
        pygame.draw.arc(self.screen, (200, 200, 200), 
                       (chute_x - chute_size // 2, current_y - chute_size // 2, 
                        chute_size, chute_size), 0, math.pi, 3)
        
        # Parachute lines
        for i in range(3):
            line_x = chute_x - chute_size // 3 + i * chute_size // 3
            pygame.draw.line(self.screen, (150, 150, 150), 
                           (line_x, current_y), 
                           (chute_x, current_y + chute_size // 2), 1)
        
        # Pawn dangling below
        pawn_y = current_y + chute_size // 2
        if pawn_y < y + SQUARE_SIZE // 2:
            pygame.draw.circle(self.screen, (100, 100, 100), 
                             (chute_x, pawn_y), 10)
