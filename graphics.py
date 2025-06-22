"""
Graphics and Rendering Functions - Performance Optimized
"""

import pygame
import pygame.gfxdraw
import math
import random
import config  # Import config module directly

class Renderer:
    def __init__(self, screen, assets):
        self.screen = screen
        self.assets = assets
        self.parallax_offset = 0
        self.scale = 1.0
        
        # Try to load pixel fonts
        self.pixel_fonts = self.load_pixel_fonts()
        
        # Cache surfaces for better performance
        self.board_surface_cache = None
        self.board_cache_scale = None
        
    def update_scale(self, scale):
        """Update scale factor for fullscreen mode."""
        self.scale = scale
        # Reload fonts with new sizes
        self.pixel_fonts = self.load_pixel_fonts()
        # Clear cache when scale changes
        self.board_surface_cache = None
        self.board_cache_scale = None
        
    def load_pixel_fonts(self):
        """Load pixel-style fonts with fallbacks."""
        fonts = {}
        
        # List of pixel font names to try (in order of preference)
        pixel_font_names = [
            "Courier",  # Monospace, looks decent for pixel style
            "Monaco",
            "Consolas",
            "monospace"
        ]
        
        # Calculate font sizes based on scale
        sizes = {
            'tiny': int(12 * self.scale),
            'small': int(14 * self.scale),
            'medium': int(18 * self.scale),
            'large': int(24 * self.scale),
            'huge': int(36 * self.scale)
        }
        
        # Try to load fonts
        for font_name in pixel_font_names:
            try:
                # Test if font exists
                test_font = pygame.font.SysFont(font_name, 12)
                if test_font:
                    for key, size in sizes.items():
                        fonts[key] = pygame.font.SysFont(font_name, size)
                    print(f"Loaded pixel font: {font_name}")
                    return fonts
            except:
                continue
                
        # Fallback to default font
        print("Using default monospace font")
        for key, size in sizes.items():
            fonts[key] = pygame.font.Font(pygame.font.get_default_font(), size)
        
        return fonts
        
    def draw_parallax_background(self, brightness=1.0):
        """Draw scrolling background - OPTIMIZED."""
        # Fill screen with dark color first
        self.screen.fill((20, 20, 30))
        
        # Debug: Check if parallax layers exist and have content
        if not hasattr(self.assets, 'parallax_layers') or not self.assets.parallax_layers:
            print("WARNING: No parallax layers found in assets!")
            # Draw a simple gradient background as fallback
            for y in range(0, config.HEIGHT, 10):
                color_val = int(30 + (y / config.HEIGHT) * 20)
                pygame.draw.rect(self.screen, (color_val, color_val, color_val + 10), 
                               (0, y, config.WIDTH, 10))
            
            # Apply brightness overlay
            if brightness < 1.0:
                overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
                overlay.fill(config.BLACK)
                overlay.set_alpha(int((1.0 - brightness) * 255))
                self.screen.blit(overlay, (0, 0))
            return
            
        # Slower scroll speed for better performance
        self.parallax_offset += 0.3
        
        # Skip some layers in fullscreen for performance
        layers_to_draw = self.assets.parallax_layers
        if self.scale > 1.5 and len(self.assets.parallax_layers) > 6:  # Only skip if we have many layers
            layers_to_draw = self.assets.parallax_layers[::2]
        
        # Draw each layer directly to screen
        layers_drawn = 0
        for i, layer in enumerate(layers_to_draw):
            if not layer.get("image"):
                print(f"WARNING: Layer {i} has no image!")
                continue
                
            offset = self.parallax_offset * layer["speed"]
            
            # For fullscreen, we need to scale the layers to fill the height
            if self.scale != 1.0:
                # Scale to fill screen height
                aspect = layer["image"].get_width() / layer["image"].get_height()
                new_h = config.HEIGHT
                new_w = int(new_h * aspect)
                scaled_img = pygame.transform.scale(layer["image"], (new_w, new_h))
                layer_width = new_w
            else:
                scaled_img = layer["image"]
                layer_width = layer.get("width", layer["image"].get_width())
            
            # Draw layer across the screen
            x = -(offset % layer_width)
            positions_drawn = 0
            while x < config.WIDTH:
                self.screen.blit(scaled_img, (x, 0))
                x += layer_width
                positions_drawn += 1
            layers_drawn += 1
                
        # Brightness overlay - ALWAYS APPLY THIS
        if brightness < 1.0:
            overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
            overlay.fill(config.BLACK)
            overlay.set_alpha(int((1.0 - brightness) * 255))
            self.screen.blit(overlay, (0, 0))
        elif brightness > 1.0:
            overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
            overlay.fill(config.WHITE)
            overlay.set_alpha(int((brightness - 1.0) * 128))
            self.screen.blit(overlay, (0, 0))
            
    def draw_board(self):
        """Draw chess board - CACHED FOR PERFORMANCE."""
        board_size_scaled = int(config.BOARD_SIZE * self.scale)
        
        # Check if we have a cached board surface at the current scale
        if self.board_surface_cache is None or self.board_cache_scale != self.scale:
            # Create new cache
            self.board_surface_cache = pygame.Surface((board_size_scaled, board_size_scaled), pygame.SRCALPHA)
            self.board_cache_scale = self.scale
            
            if self.assets.board_texture:
                # Scale the board texture
                scaled_texture = pygame.transform.scale(self.assets.board_texture, 
                    (board_size_scaled, board_size_scaled))
                self.board_surface_cache.blit(scaled_texture, (0, 0))
                self.board_surface_cache.set_alpha(240)
            else:
                # Fallback checkered board
                square_size_scaled = int(config.SQUARE_SIZE * self.scale)
                border_left_scaled = int(config.BOARD_BORDER_LEFT * self.scale)
                border_top_scaled = int(config.BOARD_BORDER_TOP * self.scale)
                
                for row in range(config.ROWS):
                    for col in range(config.COLS):
                        color = (*config.LIGHT_SQUARE, 230) if (row + col) % 2 == 0 else (*config.DARK_SQUARE, 230)
                        x = border_left_scaled + col * square_size_scaled
                        y = border_top_scaled + row * square_size_scaled
                        pygame.draw.rect(self.board_surface_cache, color, 
                            (x, y, square_size_scaled, square_size_scaled))
        
        # Blit the cached board
        self.screen.blit(self.board_surface_cache, (config.BOARD_OFFSET_X, config.BOARD_OFFSET_Y))
        
        # Board border
        pygame.draw.rect(self.screen, (60, 60, 60), 
                        (config.BOARD_OFFSET_X - 2, config.BOARD_OFFSET_Y - 2, 
                         board_size_scaled + 4, board_size_scaled + 4), 2)
                        
    def draw_pieces(self, board, mouse_pos):
        """Draw all pieces - OPTIMIZED."""
        current_time = pygame.time.get_ticks()
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        
        # Cache scaled pieces
        if not hasattr(self, '_scaled_pieces_cache') or self._cache_scale != self.scale:
            self._scaled_pieces_cache = {}
            self._cache_scale = self.scale
            for piece_code, piece_img in self.assets.pieces.items():
                self._scaled_pieces_cache[piece_code] = pygame.transform.scale(
                    piece_img, (square_size_scaled, square_size_scaled))
        
        # Draw static pieces
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if not piece:
                    continue
                    
                # Skip if being dragged or animated
                if board.dragging and (row, col) == board.drag_start:
                    continue
                if board.animating and (row, col) == board.animation_from:
                    continue
                    
                x, y = board.get_square_pos(row, col)
                scaled_piece = self._scaled_pieces_cache.get(piece)
                if scaled_piece:
                    self.screen.blit(scaled_piece, (x, y))
                    
        # Draw animated piece
        if board.animating and board.animation_piece:
            progress = min(1.0, (current_time - board.animation_start) / config.MOVE_ANIMATION_DURATION)
            t = progress * progress * (3.0 - 2.0 * progress)  # smoothstep
            
            from_x, from_y = board.get_square_pos(*board.animation_from)
            to_x, to_y = board.get_square_pos(*board.animation_to)
            
            current_x = from_x + (to_x - from_x) * t
            current_y = from_y + (to_y - from_y) * t
            
            scaled_piece = self._scaled_pieces_cache.get(board.animation_piece)
            if scaled_piece:
                self.screen.blit(scaled_piece, (current_x, current_y))
                
        # Draw dragged piece
        if board.dragging and board.drag_piece:
            scaled_piece = self._scaled_pieces_cache.get(board.drag_piece)
            if scaled_piece:
                rect = scaled_piece.get_rect()
                rect.center = mouse_pos
                self.screen.blit(scaled_piece, rect)
                
    def draw_highlights(self, board):
        """Draw valid move indicators with pulsing effect."""
        if not board.selected_piece:
            return
            
        current_time = pygame.time.get_ticks()
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        
        # Calculate pulse effect
        pulse = math.sin(current_time / 300) * 0.3 + 0.7  # Oscillates between 0.4 and 1.0
        
        for move_row, move_col in board.valid_moves:
            x, y = board.get_square_pos(move_row, move_col)
            center_x = x + square_size_scaled // 2
            center_y = y + square_size_scaled // 2
            
            # Pulsing dot with varying size and opacity
            base_size = int(12 * self.scale)
            size = int(base_size * pulse)
            alpha = int(180 * pulse)  # Pulsing opacity
            
            # Draw dot with pulsing effect
            dot_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, (100, 100, 100, alpha), (size, size), size)
            self.screen.blit(dot_surface, (center_x - size, center_y - size))
            
    def draw_scuffle(self, board):
        """Draw capture animation - SIMPLIFIED."""
        if not board.scuffle_active or not board.scuffle_pos:
            return
            
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - board.scuffle_start) / config.SCUFFLE_DURATION)
        
        if progress > 0.9:  # Skip near the end for performance
            return
            
        x, y = board.scuffle_pos
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        
        # Simplified dust cloud (fewer particles)
        cloud_size = int(square_size_scaled * 1.2 * (1 + progress * 0.2))
        
        for i in range(4):  # Reduced from 8
            offset_x = random.randint(-15, 15) * self.scale
            offset_y = random.randint(-15, 15) * self.scale
            size = random.randint(cloud_size // 3, cloud_size // 2)
            alpha = int(150 * (1 - progress))
            
            color = (200, 180, 100, alpha)
            pos = (int(x + offset_x), int(y + offset_y))
            pygame.draw.circle(self.screen, color[:3], pos, size)
        
        # Simplified effects (fewer elements)
        for i in range(3):  # Reduced from 5
            angle = (i / 3) * 2 * math.pi + progress * math.pi
            dist = (25 + progress * 15) * self.scale
            elem_x = x + int(math.cos(angle) * dist)
            elem_y = y + int(math.sin(angle) * dist)
            
            if i % 2 == 0:  # Simple line
                end_x = elem_x + int(math.cos(angle) * 20 * self.scale)
                end_y = elem_y + int(math.sin(angle) * 20 * self.scale)
                pygame.draw.line(self.screen, (192, 192, 192), (elem_x, elem_y), 
                    (end_x, end_y), int(2 * self.scale))
            else:  # Simple star
                pygame.draw.circle(self.screen, (255, 255, 0), (elem_x, elem_y), 
                    int(8 * self.scale))
                    
    def draw_ui(self, board, mute_button, music_muted, mouse_pos, ai=None, difficulty=None):
        """Draw UI elements - OPTIMIZED WITH TRANSPARENCY."""
        # Get scaled dimensions
        ui_width_scaled = int(config.UI_WIDTH * self.scale)
        ui_height_scaled = int(config.UI_HEIGHT * self.scale)
        board_size_scaled = int(config.BOARD_SIZE * self.scale)
        
        # Calculate UI positions based on the board position
        board_left = config.BOARD_OFFSET_X
        board_top = config.BOARD_OFFSET_Y
        board_right = config.BOARD_OFFSET_X + board_size_scaled
        board_bottom = config.BOARD_OFFSET_Y + board_size_scaled
        
        # UI background - with proper transparency
        ui_color = (0, 0, 0, 200)
        
        # Draw UI panels with transparency
        ui_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        # Top bar
        pygame.draw.rect(ui_surface, ui_color, 
            (0, 0, config.WIDTH, board_top))
        # Bottom bar
        pygame.draw.rect(ui_surface, ui_color, 
            (0, board_bottom, config.WIDTH, config.HEIGHT - board_bottom))
        # Left panel
        pygame.draw.rect(ui_surface, ui_color, 
            (0, board_top, board_left, board_size_scaled))
        # Right panel - Draw it! The powerup menu will draw over it
        pygame.draw.rect(ui_surface, ui_color, 
            (board_right, board_top, config.WIDTH - board_right, board_size_scaled))
            
        self.screen.blit(ui_surface, (0, 0))
        
        # Current turn - center it in the top bar
        if ai and board.current_turn == "black" and ai.is_thinking():
            turn_text = "AI IS THINKING..."
        else:
            turn_text = f"CURRENT TURN: {board.current_turn.upper()}"
        text = self.pixel_fonts['large'].render(turn_text, True, config.WHITE)
        rect = text.get_rect(center=(config.WIDTH // 2, board_top // 2))
        self.screen.blit(text, rect)
        
        # Show AI difficulty if playing against AI
        if ai and difficulty:
            diff_text = f"VS {config.AI_DIFFICULTY_NAMES[difficulty]} AI"
            text = self.pixel_fonts['small'].render(diff_text, True, config.AI_DIFFICULTY_COLORS[difficulty])
            rect = text.get_rect(center=(config.WIDTH // 2, board_top // 2 + 25 * self.scale))
            self.screen.blit(text, rect)
        
        # Create small pieces cache if it doesn't exist
        if not hasattr(self, '_small_pieces_cache') or getattr(self, '_small_cache_scale', None) != self.scale:
            self._small_pieces_cache = {}
            self._small_cache_scale = self.scale
            small_size = int(30 * self.scale)
            for piece_code, piece_img in self.assets.pieces.items():
                self._small_pieces_cache[piece_code] = pygame.transform.scale(
                    piece_img, (small_size, small_size))
        
        # Captured pieces - White (left side, top section)
        y_position = board_top + 10 * self.scale
        
        if board.captured_pieces["white"]:
            title = self.pixel_fonts['medium'].render("WHITE CAPTURED:", True, config.WHITE)
            self.screen.blit(title, (10 * self.scale, y_position))
            
            y_offset = y_position + 30 * self.scale
            for i, piece in enumerate(board.captured_pieces["white"][:12]):  # Show up to 12 pieces
                if piece in self._small_pieces_cache:
                    small = self._small_pieces_cache[piece]
                    if small:
                        self.screen.blit(small, 
                            (10 * self.scale + (i % 4) * 35 * self.scale, 
                             y_offset + (i // 4) * 35 * self.scale))
                             
            # Update y_position for black pieces section
            rows_used = min(3, (len(board.captured_pieces["white"]) + 3) // 4)
            y_position = y_offset + rows_used * 35 * self.scale + 20 * self.scale
        
        # Captured pieces - Black (left side, below white pieces)
        if board.captured_pieces["black"]:
            title = self.pixel_fonts['medium'].render("BLACK CAPTURED:", True, config.WHITE)
            self.screen.blit(title, (10 * self.scale, y_position))
            
            y_offset = y_position + 30 * self.scale
            for i, piece in enumerate(board.captured_pieces["black"][:12]):  # Show up to 12 pieces
                if piece in self._small_pieces_cache:
                    small = self._small_pieces_cache[piece]
                    if small:
                        self.screen.blit(small, 
                            (10 * self.scale + (i % 4) * 35 * self.scale, 
                             y_offset + (i // 4) * 35 * self.scale))
                        
        # Info text - center in bottom bar
        if ai and board.current_turn == "black":
            info_text = "AI IS PLAYING..."
        else:
            info_text = "DRAG TO MOVE - CLICK TO SELECT"
        text = self.pixel_fonts['small'].render(info_text, True, config.WHITE)
        rect = text.get_rect(center=(config.WIDTH // 2, 
            board_bottom + (config.HEIGHT - board_bottom) // 2))
        self.screen.blit(text, rect)
        
    def draw_check_indicator(self, board):
        """Draw exclamation mark above king if in check - SIMPLIFIED."""
        if not board.is_in_check():
            return
            
        king_pos = board.find_king(board.current_turn)
        if not king_pos:
            return
            
        row, col = king_pos
        x, y = board.get_square_pos(row, col)
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        
        # Position the indicator in the top-right corner of the king's square
        exc_x = x + square_size_scaled - int(15 * self.scale)
        exc_y = y + int(10 * self.scale)
        
        # Draw just a red exclamation mark
        exc_text = self.pixel_fonts['small'].render("!", True, (255, 0, 0))
        exc_rect = exc_text.get_rect(center=(exc_x, exc_y))
        self.screen.blit(exc_text, exc_rect)
        
    def draw_promotion_menu(self, board, mouse_pos):
        """Draw pawn promotion menu."""
        if not board.promoting:
            return []
            
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(config.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Menu
        menu_w = int(300 * self.scale)
        menu_h = int(100 * self.scale)
        menu_x = config.WIDTH // 2 - menu_w // 2
        menu_y = config.HEIGHT // 2 - menu_h // 2
        
        pygame.draw.rect(self.screen, (50, 50, 50), 
            (menu_x - 5, menu_y - 5, menu_w + 10, menu_h + 10))
        pygame.draw.rect(self.screen, (200, 200, 200), (menu_x, menu_y, menu_w, menu_h))
        pygame.draw.rect(self.screen, config.BLACK, (menu_x, menu_y, menu_w, menu_h), 3)
        
        # Title
        text = self.pixel_fonts['medium'].render("CHOOSE PROMOTION:", True, config.BLACK)
        rect = text.get_rect(centerx=menu_x + menu_w // 2, y=menu_y + 10 * self.scale)
        self.screen.blit(text, rect)
        
        # Pieces
        pieces = ["Q", "R", "B", "N"]
        size = int(50 * self.scale)
        spacing = int(10 * self.scale)
        total_w = len(pieces) * size + (len(pieces) - 1) * spacing
        start_x = menu_x + (menu_w - total_w) // 2
        
        # Cache promotion pieces
        if not hasattr(self, '_promo_pieces_cache') or self._promo_cache_scale != self.scale:
            self._promo_pieces_cache = {}
            self._promo_cache_scale = self.scale
            for color in ['w', 'b']:
                for piece_type in pieces:
                    piece_key = color + piece_type
                    if piece_key in self.assets.pieces:
                        self._promo_pieces_cache[piece_key] = pygame.transform.scale(
                            self.assets.pieces[piece_key], (size, size))
        
        rects = []
        for i, piece_type in enumerate(pieces):
            x = start_x + i * (size + spacing)
            y = menu_y + int(40 * self.scale)
            
            # Highlight on hover
            rect = pygame.Rect(x, y, size, size)
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (100, 200, 100), 
                    (x - 2, y - 2, size + 4, size + 4))
                
            # Draw piece
            piece_key = board.promotion_color + piece_type
            scaled = self._promo_pieces_cache.get(piece_key)
            if scaled:
                self.screen.blit(scaled, (x, y))
                
            rects.append((rect, piece_type))
            
        return rects
        
    def draw_game_over(self, board):
        """Draw game over screen."""
        if not board.game_over:
            return
            
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(config.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        winner_text = f"{board.winner.upper()} WINS!"
        text = self.pixel_fonts['huge'].render(winner_text, True, config.WHITE)
        rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 80 * self.scale))
        self.screen.blit(text, rect)
        
        # Show reward if player won
        if board.winner == "white" and hasattr(board, 'victory_reward') and board.victory_reward > 0:
            reward_text = f"EARNED ${board.victory_reward}!"
            text = self.pixel_fonts['large'].render(reward_text, True, (255, 215, 0))
            rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 30 * self.scale))
            self.screen.blit(text, rect)
        
        # Check if player won and if there's a new difficulty to unlock
        if board.winner == "white" and hasattr(board, 'selected_difficulty'):
            progress = config.load_progress()
            current_index = config.AI_DIFFICULTIES.index(board.selected_difficulty) if hasattr(board, 'selected_difficulty') and board.selected_difficulty in config.AI_DIFFICULTIES else -1
            
            if current_index >= 0 and current_index < len(config.AI_DIFFICULTIES) - 1:
                next_diff = config.AI_DIFFICULTIES[current_index + 1]
                if next_diff not in progress.get("unlocked_difficulties", []):
                    unlock_text = f"{config.AI_DIFFICULTY_NAMES[next_diff]} DIFFICULTY UNLOCKED!"
                    text = self.pixel_fonts['medium'].render(unlock_text, True, (255, 215, 0))
                    rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 20 * self.scale))
                    self.screen.blit(text, rect)
        
        restart_text = "PRESS R TO RESTART OR ESC TO MAIN MENU"
        text = self.pixel_fonts['medium'].render(restart_text, True, (200, 200, 200))
        rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 70 * self.scale))
        self.screen.blit(text, rect)
        
    def draw_difficulty_menu(self, difficulty_buttons, back_button, mouse_pos):
        """Draw difficulty selection menu."""
        self.draw_parallax_background(1.0)
        
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Calculate game area center for text positioning
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        # Title - moved up to give more space
        text = self.pixel_fonts['huge'].render("SELECT DIFFICULTY", True, config.WHITE)
        rect = text.get_rect(center=(game_center_x, game_center_y - 250 * config.SCALE))
        self.screen.blit(text, rect)
        
        # Load progress to check unlocked difficulties
        progress = config.load_progress()
        unlocked = progress.get("unlocked_difficulties", ["easy"])
        
        # Difficulty buttons
        for i, (difficulty, button) in enumerate(difficulty_buttons.items()):
            is_unlocked = difficulty in unlocked
            is_hover = button.collidepoint(mouse_pos) and is_unlocked
            
            if is_unlocked:
                color = config.AI_DIFFICULTY_COLORS[difficulty]
                hover_color = tuple(min(255, c + 50) for c in color)
                border_color = config.WHITE
            else:
                color = config.LOCKED_COLOR
                hover_color = config.LOCKED_COLOR
                border_color = (120, 120, 120)
            
            # Button background
            pygame.draw.rect(self.screen, hover_color if is_hover else color, button, border_radius=10)
            pygame.draw.rect(self.screen, border_color, button, 3, border_radius=10)
            
            # Button text - REMOVED THE EMOJI
            text = config.AI_DIFFICULTY_NAMES[difficulty]
            # No longer adding lock emoji or any prefix for locked difficulties
            text_surface = self.pixel_fonts['large'].render(text, True, config.WHITE)
            text_rect = text_surface.get_rect(center=button.center)
            self.screen.blit(text_surface, text_rect)
            
            # Difficulty description
            descriptions = {
                "easy": "Beginner friendly",
                "medium": "Casual player",
                "hard": "Experienced player",
                "very_hard": "Expert level"
            }
            
            if is_unlocked:
                # Check if this is the next level to beat
                difficulty_index = config.AI_DIFFICULTIES.index(difficulty)
                if difficulty_index > 0 and difficulty_index == len(unlocked) - 1:
                    desc_text = "★ BEAT THIS TO UNLOCK NEXT ★"
                    desc_color = (255, 215, 0)  # Gold
                else:
                    desc_text = descriptions[difficulty]
                    desc_color = (200, 200, 200)
            else:
                # Show what needs to be beaten to unlock
                difficulty_index = config.AI_DIFFICULTIES.index(difficulty)
                prev_difficulty = config.AI_DIFFICULTIES[difficulty_index - 1]
                desc_text = f"Beat {config.AI_DIFFICULTY_NAMES[prev_difficulty]} to unlock"
                desc_color = (150, 150, 150)
            
            desc = self.pixel_fonts['small'].render(desc_text, True, desc_color)
            desc_rect = desc.get_rect(center=(button.centerx, button.bottom + 10 * config.SCALE))
            self.screen.blit(desc, desc_rect)
            
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_menu(self, screen_type, buttons, mouse_pos):
        """Draw menu screens."""
        self.draw_parallax_background(1.2)
        
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80 if screen_type == config.SCREEN_START else 120))
        self.screen.blit(overlay, (0, 0))
        
        # Calculate game area center for text positioning
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        if screen_type == config.SCREEN_START:
            # Title
            text = self.pixel_fonts['huge'].render("CHECKMATE PROTOCOL", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, game_center_y - 150 * config.SCALE))
            self.screen.blit(text, rect)
            
            # Subtitle
            text = self.pixel_fonts['medium'].render("CREATED BY THOMAS KANTECKI", True, (200, 200, 200))
            rect = text.get_rect(center=(game_center_x, game_center_y - 90 * config.SCALE))
            self.screen.blit(text, rect)
            
            # Buttons
            self._draw_button(buttons['play'], "PLAY GAME", (70, 150, 70), (100, 200, 100), mouse_pos)
            self._draw_button(buttons['credits'], "CREDITS", (70, 70, 150), (100, 100, 200), mouse_pos)
            
        elif screen_type == config.SCREEN_CREDITS:
            # Title
            text = self.pixel_fonts['huge'].render("CREDITS", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, config.GAME_OFFSET_Y + 80 * config.SCALE))
            self.screen.blit(text, rect)
            
            # Credits
            y = config.GAME_OFFSET_Y + 180 * config.SCALE
            credits = [
                ("GAME DESIGN & DEVELOPMENT", "header", (255, 200, 100)),
                ("THOMAS KANTECKI", "text", (200, 200, 200)),
                ("", None, None),
                ("ARTWORK", "header", (255, 200, 100)),
                ("DANI MACCARI", "text", (200, 200, 200)),
                ("", None, None),
                ("MUSIC", "header", (255, 200, 100)),
                ("THOMAS KANTECKI", "text", (200, 200, 200)),
                ("", None, None),
                ("BACKGROUND ART", "header", (255, 200, 100)),
                ("EDER MUNIZ - FOREST BACKGROUND", "text", (200, 200, 200)),
                ("", None, None),
                ("SPECIAL THANKS", "header", (255, 200, 100)),
                ('BEN "THE CHESS MASTER" HARRISON', "text", (200, 200, 200)),
                ("KNIGHTHACKS UCF", "text", (200, 200, 200)),
            ]
            
            for text, font_type, color in credits:
                if font_type:
                    if font_type == "header":
                        surface = self.pixel_fonts['medium'].render(text, True, color)
                    else:
                        surface = self.pixel_fonts['small'].render(text, True, color)
                    rect = surface.get_rect(center=(game_center_x, y))
                    self.screen.blit(surface, rect)
                y += 35 * config.SCALE
                
            # Back button
            self._draw_button(buttons['back'], "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
            
    def draw_arms_dealer(self, powerup_system, shop_buttons, back_button, mouse_pos, dialogue_index=0, dialogues=None):
        """Draw the arms dealer shop with Tariq character."""
        # Check if arms background is loaded
        if hasattr(self.assets, 'arms_background') and self.assets.arms_background:
            # Scale background to fill screen
            scaled_bg = pygame.transform.scale(self.assets.arms_background, (config.WIDTH, config.HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
        else:
            # Fallback: darker parallax background
            self.draw_parallax_background(0.6)
            
        # Semi-transparent overlay for better text visibility
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Calculate layout
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        # Draw Tariq character
        if hasattr(self.assets, 'tariq_image') and self.assets.tariq_image:
            # Scale Tariq to appropriate size
            tariq_height = int(450 * config.SCALE)  # Even taller
            aspect_ratio = self.assets.tariq_image.get_width() / self.assets.tariq_image.get_height()
            tariq_width = int(tariq_height * aspect_ratio)
            scaled_tariq = pygame.transform.scale(self.assets.tariq_image, (tariq_width, tariq_height))
            
            # Position Tariq on the left side, at the very bottom
            tariq_x = int(50 * config.SCALE)
            # Position him so he's standing at the bottom edge
            tariq_y = config.HEIGHT - tariq_height  # Right at the bottom
            
            self.screen.blit(scaled_tariq, (tariq_x, tariq_y))
            
            # Store rect for click detection
            self.tariq_rect = pygame.Rect(tariq_x, tariq_y, tariq_width, tariq_height)
            
            # Draw speech bubble with dialogue - position it higher up near his head
            if dialogues and 0 <= dialogue_index < len(dialogues):
                dialogue = dialogues[dialogue_index]
                # Position bubble near Tariq's head/upper body
                bubble_y = tariq_y + int(80 * config.SCALE)  # Near top of character
                self._draw_speech_bubble(tariq_x + tariq_width + int(20 * config.SCALE), 
                                       bubble_y, 
                                       dialogue, int(300 * config.SCALE))
        
        # Title
        title = self.pixel_fonts['huge'].render("ARMS DEALER", True, (255, 100, 100))
        title_rect = title.get_rect(center=(game_center_x, game_center_y - 280 * config.SCALE))
        self.screen.blit(title, title_rect)
        
        # Player's money
        progress = config.load_progress()
        money = progress.get("money", 0)
        money_text = self.pixel_fonts['large'].render(f"FUNDS: ${money}", True, (255, 215, 0))
        money_rect = money_text.get_rect(center=(game_center_x, game_center_y - 220 * config.SCALE))
        self.screen.blit(money_text, money_rect)
        
        # Get unlocked powerups
        unlocked = progress.get("unlocked_powerups", ["shield"])
        
        # Draw powerup cards (shifted right to make room for Tariq)
        card_width = int(120 * config.SCALE)  # Smaller cards
        card_height = int(160 * config.SCALE)
        card_spacing = int(15 * config.SCALE)
        
        # Calculate total width needed
        powerup_keys = ["shield", "gun", "airstrike", "paratroopers", "nuke"]
        total_width = len(powerup_keys) * card_width + (len(powerup_keys) - 1) * card_spacing
        start_x = game_center_x - total_width // 2 + int(100 * config.SCALE)  # Shift right
        
        shop_buttons.clear()
        
        for i, powerup_key in enumerate(powerup_keys):
            powerup = powerup_system.powerups[powerup_key]
            price = powerup_system.powerup_prices[powerup_key]
            is_unlocked = powerup_key in unlocked
            can_afford = money >= price and not is_unlocked
            
            # Card position
            card_x = start_x + i * (card_width + card_spacing)
            card_y = game_center_y - 40 * config.SCALE
            
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            shop_buttons[powerup_key] = card_rect
            
            # Card background
            if is_unlocked:
                card_color = (50, 100, 50)  # Green for owned
                border_color = (100, 255, 100)
            elif can_afford:
                card_color = (70, 70, 40)  # Yellow tint for affordable
                border_color = (255, 215, 0)
            else:
                card_color = (40, 40, 40)  # Dark for unaffordable
                border_color = (80, 80, 80)
            
            # Hover effect
            if card_rect.collidepoint(mouse_pos) and not is_unlocked:
                card_color = tuple(min(255, c + 20) for c in card_color)
            
            pygame.draw.rect(self.screen, card_color, card_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, card_rect, 3, border_radius=10)
            
            # Powerup icon
            icon_text = powerup["icon"]
            icon_surface = self.pixel_fonts['large'].render(icon_text, True, config.WHITE)
            icon_rect = icon_surface.get_rect(center=(card_rect.centerx, card_y + 35 * config.SCALE))
            self.screen.blit(icon_surface, icon_rect)
            
            # Powerup name
            name_color = config.WHITE if is_unlocked else powerup["color"]
            name_surface = self.pixel_fonts['small'].render(powerup["name"], True, name_color)
            name_rect = name_surface.get_rect(center=(card_rect.centerx, card_y + 70 * config.SCALE))
            self.screen.blit(name_surface, name_rect)
            
            # Description (shortened for smaller cards)
            desc_lines = self._wrap_text(powerup["description"], self.pixel_fonts['tiny'], card_width - 10)
            desc_y = card_y + 90 * config.SCALE
            for line in desc_lines[:2]:  # Max 2 lines
                line_surface = self.pixel_fonts['tiny'].render(line, True, (200, 200, 200))
                line_rect = line_surface.get_rect(center=(card_rect.centerx, desc_y))
                self.screen.blit(line_surface, line_rect)
                desc_y += 12 * config.SCALE
            
            # Price or status
            if is_unlocked:
                status_text = "OWNED"
                status_color = (100, 255, 100)
            else:
                status_text = f"${price}"
                status_color = (255, 215, 0) if can_afford else (200, 100, 100)
            
            status_surface = self.pixel_fonts['medium'].render(status_text, True, status_color)
            status_rect = status_surface.get_rect(center=(card_rect.centerx, card_rect.bottom - 15 * config.SCALE))
            self.screen.blit(status_surface, status_rect)
        
        # Instructions
        inst_text = "Click on items to purchase. Click Tariq for more info!"
        inst_surface = self.pixel_fonts['small'].render(inst_text, True, (200, 200, 200))
        inst_rect = inst_surface.get_rect(center=(game_center_x, game_center_y + 170 * config.SCALE))
        self.screen.blit(inst_surface, inst_rect)
        
        # Back button
        self._draw_button(back_button, "BACK TO GAME", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def _draw_speech_bubble(self, x, y, text, max_width):
        """Draw a speech bubble with text."""
        # Wrap text
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.pixel_fonts['small'].size(test_line)[0] <= max_width - 40:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate bubble size
        line_height = self.pixel_fonts['small'].get_height() + 5
        bubble_height = len(lines) * line_height + 30
        bubble_width = max_width
        
        # Draw bubble background
        bubble_rect = pygame.Rect(x, y, bubble_width, bubble_height)
        pygame.draw.rect(self.screen, (40, 40, 40), bubble_rect, border_radius=15)
        pygame.draw.rect(self.screen, (200, 200, 200), bubble_rect, 3, border_radius=15)
        
        # Draw tail
        tail_points = [
            (x - 10, y + 30),
            (x + 10, y + 20),
            (x + 10, y + 40)
        ]
        pygame.draw.polygon(self.screen, (40, 40, 40), tail_points)
        pygame.draw.lines(self.screen, (200, 200, 200), False, 
                         [(x - 10, y + 30), (x + 10, y + 20)], 3)
        pygame.draw.lines(self.screen, (200, 200, 200), False, 
                         [(x - 10, y + 30), (x + 10, y + 40)], 3)
        
        # Draw text
        text_y = y + 15
        for line in lines:
            text_surface = self.pixel_fonts['small'].render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(centerx=x + bubble_width // 2, y=text_y)
            self.screen.blit(text_surface, text_rect)
            text_y += line_height

    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line_text = ' '.join(current_line)
            if font.size(line_text)[0] > max_width:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
            
    def _draw_button(self, rect, text, color, hover_color, mouse_pos):
        """Draw a button."""
        is_hover = rect.collidepoint(mouse_pos)
        
        pygame.draw.rect(self.screen, hover_color if is_hover else color, rect, border_radius=10)
        pygame.draw.rect(self.screen, config.WHITE, rect, 3, border_radius=10)
        
        text_surface = self.pixel_fonts['large'].render(text, True, config.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)