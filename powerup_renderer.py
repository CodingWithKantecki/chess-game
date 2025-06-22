"""
Powerup Rendering Module
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
        self.scale = 1.0
        self.explosion_frames_scaled = {}  # Cache for scaled explosion frames
        
    def update_scale(self, scale):
        """Update scale factor for fullscreen mode."""
        self.scale = scale
        
    def draw_powerup_menu(self, board, mouse_pos):
        """Draw the powerup menu on the right side of the screen."""
        # Calculate menu position (right side of board)
        board_size_scaled = int(BOARD_SIZE * self.scale)
        
        # Account for the board's border which adds extra width
        # The board has borders on all sides that we need to account for
        board_border_scaled = int((BOARD_BORDER_LEFT + BOARD_BORDER_RIGHT) * self.scale)
        
        # In fullscreen, we need even more spacing
        if self.scale > 1.0:  # Fullscreen mode
            extra_spacing = int(60 * self.scale)  # Increased to 60 pixels
        else:
            extra_spacing = int(20 * self.scale)  # Normal gap in windowed mode
            
        # Add the border width to ensure we're past the entire board
        menu_x = BOARD_OFFSET_X + board_size_scaled + extra_spacing
        menu_y = BOARD_OFFSET_Y + int(36 * self.scale)  # Move down by the board border size (36 pixels)
        menu_width = int(POWERUP_MENU_WIDTH * self.scale)
        menu_height = board_size_scaled - int(72 * self.scale)  # Subtract top and bottom borders (36 + 36)
        
        # Store position for click handling
        self.powerup_system.menu_x = menu_x
        self.powerup_system.menu_y = menu_y
        self.powerup_system.menu_width = menu_width
        self.powerup_system.menu_height = menu_height
        
        # Draw menu background - solid black background first
        # Draw a completely opaque black rectangle first
        black_bg = pygame.Surface((menu_width, menu_height))
        black_bg.fill((0, 0, 0))  # Solid black, no alpha
        self.screen.blit(black_bg, (menu_x, menu_y))
        
        # Then add a slight transparency overlay for consistency
        overlay = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 50))  # Slight transparency for depth
        self.screen.blit(overlay, (menu_x, menu_y))
        
        # Draw border (with brighter color for visibility)
        pygame.draw.rect(self.screen, (100, 100, 120), 
                        (menu_x, menu_y, menu_width, menu_height), 3)
        
        # Title - with green cyberpunk color
        title_text = "POWERUPS"
        title_surface = self.renderer.pixel_fonts['large'].render(title_text, True, (0, 255, 0))
        title_rect = title_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                           y=menu_y + int(20 * self.scale))
        self.screen.blit(title_surface, title_rect)
        
        # Player points
        player = board.current_turn
        points = self.powerup_system.points[player]
        points_text = f"POINTS: {points}"
        points_surface = self.renderer.pixel_fonts['medium'].render(points_text, True, (255, 204, 0))
        points_rect = points_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                             y=menu_y + int(60 * self.scale))
        self.screen.blit(points_surface, points_rect)
        
        # Show whose turn it is
        turn_text = f"({player.upper()}'S TURN)"
        turn_surface = self.renderer.pixel_fonts['tiny'].render(turn_text, True, (150, 150, 150))
        turn_rect = turn_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                         y=menu_y + int(85 * self.scale))
        self.screen.blit(turn_surface, turn_rect)
        
        # Get unlocked powerups
        progress = load_progress()
        unlocked_powerups = progress.get("unlocked_powerups", ["shield"])
        
        # Filter powerups to only show unlocked ones
        available_powerups = {k: v for k, v in self.powerup_system.powerups.items() 
                             if k in unlocked_powerups}
        
        # Clear button rects
        self.powerup_system.button_rects = {}
        
        # Draw powerup buttons
        button_y = menu_y + int(120 * self.scale)
        button_height = int(70 * self.scale)  # Reduced from 80
        button_spacing = int(15 * self.scale)  # Reduced from 20
        button_margin = int(20 * self.scale)
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
                button_color = (60, 60, 80)  # Slightly brighter when active
            elif is_hover:
                button_color = (50, 50, 65)  # Slightly lighter when hovering
            elif can_afford:
                button_color = (40, 40, 50)  # Dark but visible when available
            else:
                button_color = (20, 20, 25)  # Very dark when disabled
                
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
                # Use the actual revolver image for gun powerup - SMALLER SIZE
                icon_size = int(25 * self.scale)  # Reduced from 30
                scaled_revolver = pygame.transform.scale(self.renderer.assets.revolver_image, (icon_size, icon_size))
                
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
                
                icon_rect = scaled_revolver.get_rect(centerx=button_rect.centerx, 
                                                   y=button_rect.y + int(12 * self.scale))  # Adjusted position
                self.screen.blit(scaled_revolver, icon_rect)
            elif key == "chopper":
                # Draw helicopter icon
                self._draw_helicopter_icon(button_rect, can_afford)
            else:
                # Draw custom icons for other powerups
                icon_size = int(30 * self.scale)
                icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                icon_surface.fill((0, 0, 0, 0))  # Transparent background
                
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
                
                icon_rect = icon_surface.get_rect(centerx=button_rect.centerx, 
                                                 y=button_rect.y + int(10 * self.scale))
                self.screen.blit(icon_surface, icon_rect)
            
            # Draw name - with glow effect if available
            name_color = (0, 255, 0) if can_afford else (80, 80, 80)
            name_surface = self.renderer.pixel_fonts['small'].render(powerup["name"], True, name_color)
            name_rect = name_surface.get_rect(centerx=button_rect.centerx, 
                                             y=button_rect.y + int(35 * self.scale))
            self.screen.blit(name_surface, name_rect)
            
            # Draw cost
            cost_text = f"Cost: {powerup['cost']}"
            cost_color = (255, 204, 0) if can_afford else (80, 80, 80)
            cost_surface = self.renderer.pixel_fonts['tiny'].render(cost_text, True, cost_color)
            cost_rect = cost_surface.get_rect(centerx=button_rect.centerx, 
                                             y=button_rect.y + int(55 * self.scale))
            self.screen.blit(cost_surface, cost_rect)
            
            button_y += button_height + button_spacing
            
        # Draw instructions at bottom
        if self.powerup_system.active_powerup:
            instruction_text = self._get_instruction_text()
            inst_surface = self.renderer.pixel_fonts['small'].render(instruction_text, True, (255, 255, 150))
            inst_rect = inst_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                             bottom=menu_y + menu_height - int(20 * self.scale))
            self.screen.blit(inst_surface, inst_rect)
            
            # Cancel instruction
            cancel_text = "ESC to cancel"
            cancel_surface = self.renderer.pixel_fonts['tiny'].render(cancel_text, True, (200, 100, 100))
            cancel_rect = cancel_surface.get_rect(centerx=menu_x + menu_width // 2, 
                                                bottom=menu_y + menu_height - int(40 * self.scale))
            self.screen.blit(cancel_surface, cancel_rect)
            
    def _draw_helicopter_icon(self, button_rect, enabled):
        """Draw a helicopter icon for chopper gunner."""
        color = (255, 100, 100) if enabled else (80, 80, 80)
        darker_color = tuple(c // 2 for c in color)
        
        # Calculate center position
        center_x = button_rect.centerx
        center_y = button_rect.y + int(22 * self.scale)
        
        # Main body
        body_width = int(20 * self.scale)
        body_height = int(12 * self.scale)
        body_rect = pygame.Rect(center_x - body_width // 2, center_y - body_height // 2, 
                               body_width, body_height)
        pygame.draw.ellipse(self.screen, color, body_rect)
        pygame.draw.ellipse(self.screen, darker_color, body_rect, 1)
        
        # Tail
        tail_width = int(15 * self.scale)
        tail_height = int(4 * self.scale)
        pygame.draw.rect(self.screen, color, 
                        (center_x + body_width // 2 - 2, center_y - tail_height // 2, 
                         tail_width, tail_height))
        
        # Main rotor (animated)
        rotor_length = int(25 * self.scale)
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
        pygame.draw.circle(self.screen, darker_color, (tail_rotor_x, center_y), int(4 * self.scale), 1)
        
        # Landing skids
        skid_y = center_y + body_height // 2 + 2
        pygame.draw.line(self.screen, darker_color, 
                        (center_x - body_width // 2, skid_y), 
                        (center_x + body_width // 2, skid_y), 1)
            
    def _draw_missile_icon(self, surface, size, enabled):
        """Draw a horizontal missile icon for airstrike."""
        color = (255, 100, 100) if enabled else (80, 80, 80)
        darker_color = tuple(c // 2 for c in color)
        
        # Horizontal missile - smaller and cleaner
        missile_length = int(size * 0.7)  # Reduced size
        missile_height = int(size * 0.25)  # Thinner profile
        
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
        
        # Draw nose cone (pointed front)
        nose_points = [
            (missile_x, missile_y + missile_height // 2),  # Tip
            (body_x, missile_y),  # Top
            (body_x, missile_y + missile_height)  # Bottom
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
        
        # Shield shape - cleaner, more geometric
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
        # First draw a filled circle
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
        
        # Draw strings (cleaner lines)
        string_end_y = size - size // 3
        string_end_x = size // 2
        
        # Draw 3 main strings
        string_positions = [canopy_x + canopy_width // 4, size // 2, canopy_x + 3 * canopy_width // 4]
        for string_x in string_positions:
            pygame.draw.line(surface, darker_color, 
                           (string_x, canopy_y + canopy_height), 
                           (string_end_x, string_end_y), 1)
        
        # Draw simplified person/cargo as a small rectangle
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
            
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        
        # Draw 3x3 grid
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                target_row = row + dr
                target_col = col + dc
                if 0 <= target_row < 8 and 0 <= target_col < 8:
                    x, y = board.get_square_pos(target_row, target_col)
                    
                    # Draw targeting square
                    target_surface = pygame.Surface((square_size_scaled, square_size_scaled), pygame.SRCALPHA)
                    target_surface.fill((255, 0, 0, 60))
                    self.screen.blit(target_surface, (x, y))
                    
                    # Draw border
                    pygame.draw.rect(self.screen, (255, 0, 0), 
                                   (x, y, square_size_scaled, square_size_scaled), 2)
                                   
    def _draw_shield_targeting(self, board, mouse_pos):
        """Highlight valid pieces for shield."""
        player = self.powerup_system.powerup_state["player"]
        player_color = 'w' if player == "white" else 'b'
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        
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
                    highlight_surface = pygame.Surface((square_size_scaled, square_size_scaled), pygame.SRCALPHA)
                    if is_hover:
                        highlight_surface.fill((100, 200, 255, 100))
                    else:
                        highlight_surface.fill((100, 200, 255, 40))
                    self.screen.blit(highlight_surface, (x, y))
                    
                    if is_hover:
                        pygame.draw.rect(self.screen, (100, 200, 255), 
                                       (x, y, square_size_scaled, square_size_scaled), 3)
                                       
    def _draw_gun_targeting(self, board, mouse_pos):
        """Draw gun targeting based on phase."""
        if self.powerup_system.powerup_state["phase"] == "selecting":
            # Highlight player's pieces
            self._draw_shield_targeting(board, mouse_pos)
        else:
            # Show valid targets and draw gun on shooter
            square_size_scaled = int(SQUARE_SIZE * self.scale)
            valid_targets = self.powerup_system.powerup_state["data"].get("valid_targets", [])
            
            # Draw the revolver on the shooter piece
            shooter_row, shooter_col = self.powerup_system.powerup_state["data"]["shooter"]
            shooter_x, shooter_y = board.get_square_pos(shooter_row, shooter_col)
            
            # Draw the revolver if image is loaded
            if hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'revolver_image') and self.renderer.assets.revolver_image:
                # Scale the revolver to about 40% of square size
                revolver_size = int(square_size_scaled * 0.4)
                scaled_revolver = pygame.transform.scale(self.renderer.assets.revolver_image, (revolver_size, revolver_size))
                
                # Position it at the top-right of the piece
                revolver_x = shooter_x + square_size_scaled - revolver_size - int(5 * self.scale)
                revolver_y = shooter_y + int(5 * self.scale)
                
                # Draw a slight shadow/glow effect
                glow_surface = pygame.Surface((revolver_size + 4, revolver_size + 4), pygame.SRCALPHA)
                glow_surface.fill((255, 200, 100, 50))
                self.screen.blit(glow_surface, (revolver_x - 2, revolver_y - 2))
                
                # Draw the revolver
                self.screen.blit(scaled_revolver, (revolver_x, revolver_y))
            
            # Draw line from shooter to mouse
            shooter_center = (shooter_x + square_size_scaled // 2, 
                            shooter_y + square_size_scaled // 2)
            
            # Draw targeting line
            pygame.draw.line(self.screen, (255, 200, 100, 150), shooter_center, mouse_pos, 2)
            
            # Highlight valid targets
            for target_row, target_col in valid_targets:
                x, y = board.get_square_pos(target_row, target_col)
                
                # Check if mouse is over this target
                mouse_row, mouse_col = board.get_square_from_pos(mouse_pos)
                is_hover = (target_row == mouse_row and target_col == mouse_col)
                
                # Draw crosshair
                center_x = x + square_size_scaled // 2
                center_y = y + square_size_scaled // 2
                radius = int(20 * self.scale)
                
                color = (255, 0, 0) if is_hover else (200, 100, 100)
                pygame.draw.circle(self.screen, color, (center_x, center_y), radius, 2)
                pygame.draw.line(self.screen, color, 
                               (center_x - radius, center_y), (center_x + radius, center_y), 2)
                pygame.draw.line(self.screen, color, 
                               (center_x, center_y - radius), (center_x, center_y + radius), 2)
                               
    def _draw_chopper_targeting(self, board, mouse_pos):
        """Draw chopper gunner warning overlay."""
        # Draw red tint over entire board
        board_size_scaled = int(BOARD_SIZE * self.scale)
        warning_surface = pygame.Surface((board_size_scaled, board_size_scaled), pygame.SRCALPHA)
        warning_surface.fill((255, 0, 0, 30))
        self.screen.blit(warning_surface, (BOARD_OFFSET_X, BOARD_OFFSET_Y))
        
        # Draw warning text
        warning_text = "CHOPPER GUNNER - CLICK ANYWHERE TO CONFIRM"
        text_surface = self.renderer.pixel_fonts['large'].render(warning_text, True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=(BOARD_OFFSET_X + board_size_scaled // 2, 
                                                  BOARD_OFFSET_Y + board_size_scaled // 2))
        self.screen.blit(text_surface, text_rect)
        
        # Draw animated helicopter
        heli_y = BOARD_OFFSET_Y + board_size_scaled // 2 - int(50 * self.scale)
        heli_x = BOARD_OFFSET_X + board_size_scaled // 2
        
        # Helicopter body
        body_width = int(40 * self.scale)
        body_height = int(20 * self.scale)
        pygame.draw.ellipse(self.screen, (100, 100, 100), 
                           (heli_x - body_width // 2, heli_y - body_height // 2, 
                            body_width, body_height))
        
        # Animated rotor
        rotor_length = int(60 * self.scale)
        rotor_angle = (pygame.time.get_ticks() // 10) % 360
        for i in range(2):
            angle = rotor_angle + i * 180
            x1 = heli_x + int(math.cos(math.radians(angle)) * rotor_length)
            y1 = heli_y - body_height // 2 - 5 + int(math.sin(math.radians(angle)) * 3)
            x2 = heli_x - int(math.cos(math.radians(angle)) * rotor_length)
            y2 = heli_y - body_height // 2 - 5 - int(math.sin(math.radians(angle)) * 3)
            pygame.draw.line(self.screen, (80, 80, 80), (x1, y1), (x2, y2), 3)
                               
    def _draw_paratroopers_targeting(self, board, mouse_pos):
        """Draw paratrooper placement indicators."""
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        
        # Show how many pawns left to place
        placed = len(self.powerup_system.powerup_state["data"].get("placed", []))
        remaining = 3 - placed
        
        info_text = f"PLACE {remaining} MORE PAWN{'S' if remaining > 1 else ''}"
        text_surface = self.renderer.pixel_fonts['medium'].render(info_text, True, (100, 200, 100))
        text_rect = text_surface.get_rect(center=(BOARD_OFFSET_X + int(BOARD_SIZE * self.scale) // 2, 
                                                  BOARD_OFFSET_Y - int(30 * self.scale)))
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
                        zone_surface = pygame.Surface((square_size_scaled, square_size_scaled), pygame.SRCALPHA)
                        zone_surface.fill((100, 200, 100, 100))
                        self.screen.blit(zone_surface, (x, y))
                        
                        # Draw parachute icon
                        chute_text = "🪂"
                        chute_surface = self.renderer.pixel_fonts['large'].render(chute_text, True, (255, 255, 255))
                        chute_rect = chute_surface.get_rect(center=(x + square_size_scaled // 2, 
                                                                   y + square_size_scaled // 2))
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
        board_width = BOARD_SIZE * self.scale
        start_x = BOARD_OFFSET_X + board_width + 100 * self.scale  # Start off-screen right
        end_x = BOARD_OFFSET_X - 200 * self.scale  # End off-screen left
        
        # Jet flies from right to left
        jet_x = start_x + (end_x - start_x) * progress
        
        # Height arc - jet dips down at target then rises
        base_y = BOARD_OFFSET_Y - 50 * self.scale
        target_progress = abs(progress - 0.5) * 2  # 0 at middle, 1 at edges
        jet_y = base_y + (1 - target_progress) * 50 * self.scale  # Reduced dip from 100 to 50
        
        # Calculate which frame to show (4 frames total)
        frame_duration = [0.2, 0.14, 0.14, 0.2]  # Seconds for each frame
        total_duration = sum(frame_duration)
        
        # Determine current frame based on animation cycle
        cycle_progress = (progress * 3) % 1  # Repeat animation 3 times during flyby
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
        
        # Scale the jet (REDUCED from 1.5x to 0.75x)
        jet_scale = 0.75 * self.scale  # Half the previous size
        jet_width = int(jet_frame.get_width() * jet_scale)
        jet_height = int(jet_frame.get_height() * jet_scale)
        
        # Just scale the jet, no flip needed
        scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
        
        # Draw the jet
        self.screen.blit(scaled_jet, (jet_x, jet_y))
        
        # Draw bomb being dropped when jet is near target (40-60% through)
        if 0.4 <= progress <= 0.6:
            bomb_progress = (progress - 0.4) / 0.2  # 0 to 1 during bomb drop
            bomb_x = anim["target_x"] + SQUARE_SIZE * self.scale // 2
            bomb_start_y = jet_y + jet_height
            bomb_end_y = anim["target_y"] + SQUARE_SIZE * self.scale // 2
            bomb_y = bomb_start_y + (bomb_end_y - bomb_start_y) * bomb_progress
            
            # Draw a more realistic bomb
            bomb_width = int(8 * self.scale)
            bomb_height = int(20 * self.scale)
            
            # Main bomb body (dark gray cylinder)
            bomb_rect = pygame.Rect(bomb_x - bomb_width // 2, bomb_y - bomb_height // 2, 
                                   bomb_width, bomb_height)
            pygame.draw.ellipse(self.screen, (60, 60, 60), bomb_rect)
            pygame.draw.ellipse(self.screen, (40, 40, 40), bomb_rect, 1)  # Outline
            
            # Nose cone (pointed tip at bottom)
            nose_points = [
                (bomb_x - bomb_width // 2, bomb_y + bomb_height // 2 - 2),
                (bomb_x + bomb_width // 2, bomb_y + bomb_height // 2 - 2),
                (bomb_x, bomb_y + bomb_height // 2 + bomb_width)
            ]
            pygame.draw.polygon(self.screen, (50, 50, 50), nose_points)
            
            # Tail fins at top
            fin_height = int(6 * self.scale)
            fin_width = int(12 * self.scale)
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
            
        # Calculate more precise explosion timing
        # Bomb drops from 40% to 60% (0.6s to 0.9s of 1.5s animation)
        # We want explosion when bomb hits, which is at 60% progress = 0.9s
        
    def _draw_airstrike_animation(self, anim, progress, board):
        """Draw airstrike explosion using sprite frames."""
        # Skip drawing if progress is negative (animation hasn't started yet)
        if progress < 0:
            return
            
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        
        # Check if we have explosion frames loaded
        if hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'explosion_frames') and self.renderer.assets.explosion_frames:
            # Calculate which frame to show (7 frames total)
            frame_count = len(self.renderer.assets.explosion_frames)
            # FIX: Clamp progress to avoid going past the last frame
            clamped_progress = min(progress, 0.9999)
            frame_index = int(clamped_progress * frame_count)
            # Extra safety check
            frame_index = max(0, min(frame_index, frame_count - 1))
                
            # Get the explosion frame
            explosion_frame = self.renderer.assets.explosion_frames[frame_index]
            
            # Scale the explosion to cover 3x3 grid
            explosion_size = int(square_size_scaled * 3)
            
            # Cache scaled frames for performance
            cache_key = (frame_index, explosion_size)
            if cache_key not in self.explosion_frames_scaled:
                self.explosion_frames_scaled[cache_key] = pygame.transform.scale(
                    explosion_frame, (explosion_size, explosion_size))
                    
            scaled_frame = self.explosion_frames_scaled[cache_key]
            
            # Position explosion centered on the target square
            center_x = anim["x"] + square_size_scaled // 2
            center_y = anim["y"] + square_size_scaled // 2
            x = center_x - explosion_size // 2
            y = center_y - explosion_size // 2
            
            # Draw the explosion frame
            self.screen.blit(scaled_frame, (x, y))
            
        else:
            # Fallback to original animation if frames not loaded
            square_size_scaled = int(SQUARE_SIZE * self.scale)
            center_x = anim["x"] + square_size_scaled // 2
            center_y = anim["y"] + square_size_scaled // 2
            
            # Multiple explosion rings
            for i in range(3):
                phase = (progress + i * 0.2) % 1.0
                if phase < 0.7:
                    radius = int(square_size_scaled * 1.5 * phase)
                    alpha = int(255 * (1 - phase))
                    
                    if radius > 0:
                        explosion_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                        explosion_surface.fill((0, 0, 0, 0))
                        pygame.draw.circle(explosion_surface, (255, 150 - i * 30, 0), (radius, radius), radius)
                        explosion_surface.set_alpha(alpha)
                        self.screen.blit(explosion_surface, (center_x - radius, center_y - radius))
                        
    def _draw_shield_animation(self, anim, progress):
        """Draw shield activation effect."""
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        x, y = anim["x"], anim["y"]
        
        # Expanding shield bubble
        max_radius = int(square_size_scaled * 0.6)
        radius = int(max_radius * progress)
        alpha = int(200 * (1 - progress))
        
        shield_surface = pygame.Surface((square_size_scaled, square_size_scaled), pygame.SRCALPHA)
        shield_surface.fill((0, 0, 0, 0))  # Clear surface
        
        # Draw circle with color but set alpha on the surface
        if radius > 0:
            pygame.draw.circle(shield_surface, (100, 200, 255), 
                             (square_size_scaled // 2, square_size_scaled // 2), radius, 3)
        shield_surface.set_alpha(alpha)
        self.screen.blit(shield_surface, (x, y))
        
    def _draw_gunshot_animation(self, anim, progress):
        """Draw bullet/laser effect with revolver."""
        # Draw the revolver at the start position for the first part of the animation
        if progress < 0.3 and hasattr(self.renderer, 'assets') and hasattr(self.renderer.assets, 'revolver_image') and self.renderer.assets.revolver_image:
            square_size_scaled = int(SQUARE_SIZE * self.scale)
            
            # Calculate revolver position (it should appear to recoil)
            recoil = int(10 * self.scale * progress * 3)  # Quick recoil effect
            revolver_size = int(square_size_scaled * 0.4)
            scaled_revolver = pygame.transform.scale(self.renderer.assets.revolver_image, (revolver_size, revolver_size))
            
            # Position based on the starting position
            revolver_x = anim["start_x"] - revolver_size // 2 - recoil
            revolver_y = anim["start_y"] - revolver_size // 2
            
            # Add a muzzle flash effect at the tip of the gun
            if progress < 0.1:
                flash_size = int(20 * self.scale)
                flash_surface = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surface, (255, 255, 200), (flash_size, flash_size), flash_size)
                flash_surface.set_alpha(int(255 * (1 - progress * 10)))
                self.screen.blit(flash_surface, (revolver_x + revolver_size, revolver_y + revolver_size // 2 - flash_size))
            
            self.screen.blit(scaled_revolver, (revolver_x, revolver_y))
        
        # Interpolate bullet position
        x = anim["start_x"] + (anim["end_x"] - anim["start_x"]) * progress
        y = anim["start_y"] + (anim["end_y"] - anim["start_y"]) * progress
        
        # Draw trail
        trail_length = 50 * self.scale
        angle = math.atan2(anim["end_y"] - anim["start_y"], 
                          anim["end_x"] - anim["start_x"])
        trail_x = x - math.cos(angle) * trail_length * progress
        trail_y = y - math.sin(angle) * trail_length * progress
        
        # Fade out trail
        alpha = int(255 * (1 - progress * 0.5))
        pygame.draw.line(self.screen, (255, 200, 100), (trail_x, trail_y), (x, y), 
                        int(4 * self.scale))
                        
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
            particle_surface.fill((0, 0, 0, 0))  # Clear surface
            pygame.draw.circle(particle_surface, effect["color"], (size, size), size)
            particle_surface.set_alpha(alpha)
            self.screen.blit(particle_surface, (x - size, y - size))
            
    def _draw_muzzle_flash(self, effect, current_time):
        """Draw muzzle flash effect."""
        progress = (current_time - effect["start_time"]) / effect["duration"]
        
        size = int(30 * self.scale * (1 - progress))
        alpha = int(255 * (1 - progress))
        
        if size > 0:
            flash_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            flash_surface.fill((0, 0, 0, 0))  # Clear surface
            pygame.draw.circle(flash_surface, (255, 255, 200), (size, size), size)
            flash_surface.set_alpha(alpha)
            self.screen.blit(flash_surface, (effect["x"] - size, effect["y"] - size))
            
    def _draw_impact_effect(self, effect, current_time):
        """Draw impact effect at target."""
        progress = (current_time - effect["start_time"]) / effect["duration"]
        
        radius = int(20 * self.scale * (1 + progress))
        alpha = int(200 * (1 - progress))
        
        if radius > 0:
            impact_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            impact_surface.fill((0, 0, 0, 0))  # Clear surface
            pygame.draw.circle(impact_surface, (255, 100, 100), 
                             (radius, radius), radius, int(3 * self.scale))
            impact_surface.set_alpha(alpha)
            self.screen.blit(impact_surface, (effect["x"] - radius, effect["y"] - radius))
            
    def _draw_active_shields(self, board):
        """Draw shields on protected pieces."""
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        current_time = pygame.time.get_ticks()
        
        for (row, col), turns_remaining in self.powerup_system.shielded_pieces.items():
            x, y = board.get_square_pos(row, col)
            
            # Pulsing shield effect
            pulse = math.sin(current_time / 200) * 0.2 + 0.8
            radius = int(square_size_scaled * 0.4 * pulse)
            
            # Shield bubble
            shield_surface = pygame.Surface((square_size_scaled, square_size_scaled), pygame.SRCALPHA)
            shield_surface.fill((0, 0, 0, 0))  # Clear surface
            center = square_size_scaled // 2
            
            # Outer glow
            for i in range(3):
                glow_radius = radius + i * 3
                alpha = int(100 - i * 30)
                if glow_radius > 0:
                    glow_surface = pygame.Surface((square_size_scaled, square_size_scaled), pygame.SRCALPHA)
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
            return "Click anywhere to confirm"
        elif self.powerup_system.active_powerup == "paratroopers":
            placed = len(self.powerup_system.powerup_state["data"].get("placed", []))
            return f"Place pawn {placed + 1} of 3"
        return ""
        
    def _draw_paratrooper_animation(self, anim, progress):
        """Draw paratrooper drop effect."""
        square_size_scaled = int(SQUARE_SIZE * self.scale)
        x, y = anim["x"], anim["y"]
        
        # Calculate drop position (falling from above)
        start_y = y - square_size_scaled * 3
        current_y = start_y + (y - start_y) * progress
        
        # Draw parachute
        chute_size = int(square_size_scaled * 0.8)
        chute_x = x + square_size_scaled // 2
        
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
        if pawn_y < y + square_size_scaled // 2:
            pygame.draw.circle(self.screen, (100, 100, 100), 
                             (chute_x, pawn_y), int(10 * self.scale))