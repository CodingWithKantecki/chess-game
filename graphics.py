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
        
        # Intro sequence state
        self.intro_start_time = pygame.time.get_ticks()
        self.intro_jet_triggered = True  # Changed from False - start immediately
        self.intro_sound_played = False
        
        # Fire system - COMPLETELY REDESIGNED
        self.fire_zones = []  # List of fire zones that scroll with background
        self.fire_particles = []  # Active fire particles
        self.bomb_explosions = []  # Explosion animations
        self.last_parallax_offset = 0
        
        # Falling chess pieces system
        self.falling_chess_pieces = []  # Chess pieces falling from trees
        self.chess_pieces_enabled = False  # Enable after bombs drop
        
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
        
    def draw_parallax_background_with_fire(self, brightness=1.0):
        """Draw scrolling background with fire integrated at appropriate depth."""
        # Reset fire update flag for this frame
        self._fire_updated_this_frame = False
        
        # Fill screen with dark color first
        self.screen.fill((20, 20, 30))
        
        # Check if parallax layers exist and have content
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
            
        # Calculate parallax movement delta
        parallax_delta = self.parallax_offset - self.last_parallax_offset
        self.last_parallax_offset = self.parallax_offset
        
        # Slower scroll speed for better performance
        self.parallax_offset += 0.3
        
        # Skip some layers in fullscreen for performance
        layers_to_draw = self.assets.parallax_layers
        if self.scale > 1.5 and len(self.assets.parallax_layers) > 6:
            layers_to_draw = self.assets.parallax_layers[::2]
        
        # Get current time for animations
        current_time = pygame.time.get_ticks()
        
        # Reset fire update flag for this frame
        self._fire_updated_this_frame = False
        
        # Draw layers with fire and chess pieces at appropriate depths
        layers_drawn = 0
        for i, layer in enumerate(layers_to_draw):
            if not layer.get("image"):
                print(f"WARNING: Layer {i} has no image!")
                continue
            
            # Draw fire at different depths between layers
            if i == 5:
                # Draw far fire (depth 0.5)
                self._draw_fire_at_depth(current_time, 0.5)
            elif i == 6:
                # Draw middle fire (depth 0.7)
                self._draw_fire_at_depth(current_time, 0.7)
            elif i == 7:
                # Draw near fire (depth 0.9)
                self._draw_fire_at_depth(current_time, 0.9)
            
            # Determine which chess pieces to draw at this layer depth
            if i == 4 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.3)
            elif i == 5 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.5)
            elif i == 6 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.7)
            elif i == 7 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.9)
                
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
            
        # Reset the fire update flag for next frame
        self._fire_updated_this_frame = False
            
    def draw_parallax_background(self, brightness=1.0, draw_chess_callback=None):
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
            
        # Calculate parallax movement delta
        parallax_delta = self.parallax_offset - self.last_parallax_offset
        self.last_parallax_offset = self.parallax_offset
        
        # Slower scroll speed for better performance
        self.parallax_offset += 0.3
        
        # Skip some layers in fullscreen for performance
        layers_to_draw = self.assets.parallax_layers
        if self.scale > 1.5 and len(self.assets.parallax_layers) > 6:  # Only skip if we have many layers
            layers_to_draw = self.assets.parallax_layers[::2]
        
        # Draw layers with chess pieces at appropriate depths
        layers_drawn = 0
        for i, layer in enumerate(layers_to_draw):
            if not layer.get("image"):
                print(f"WARNING: Layer {i} has no image!")
                continue
            
            # Determine which chess pieces to draw at this layer depth
            # Layers 0-3: far background (no chess pieces)
            # Layers 4-7: middle ground (draw chess pieces here)
            # Layers 8-11: foreground/trees (in front of chess pieces)
            
            if i == 4 and self.chess_pieces_enabled:
                # Draw far chess pieces (layer 0.3)
                self._draw_chess_pieces_at_layer(0.3)
            elif i == 5 and self.chess_pieces_enabled:
                # Draw mid-far chess pieces (layer 0.5)
                self._draw_chess_pieces_at_layer(0.5)
            elif i == 6 and self.chess_pieces_enabled:
                # Draw middle chess pieces (layer 0.7)
                self._draw_chess_pieces_at_layer(0.7)
            elif i == 7 and self.chess_pieces_enabled:
                # Draw near chess pieces (layer 0.9)
                self._draw_chess_pieces_at_layer(0.9)
                
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
                # Make board fully opaque
                self.board_surface_cache.set_alpha(255)
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
                    
    def draw_ui(self, board, mute_button, music_muted, mouse_pos, ai=None, difficulty=None, show_captured=True):
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
        
        # Show AI difficulty and ELO if playing against AI
        if ai and difficulty:
            elo_rating = config.AI_DIFFICULTY_ELO.get(difficulty, 1200)
            diff_text = f"VS {config.AI_DIFFICULTY_NAMES[difficulty]} AI (ELO: {elo_rating})"
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
        
        # Captured pieces - only show if enabled in settings
        if show_captured:
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
            
            # Button text - REMOVED ELO from button text
            text = config.AI_DIFFICULTY_NAMES[difficulty]
            text_surface = self.pixel_fonts['large'].render(text, True, config.WHITE)
            text_rect = text_surface.get_rect(center=button.center)
            self.screen.blit(text_surface, text_rect)
            
            # Difficulty description with ELO
            descriptions = {
                "easy": f"Beginner friendly (ELO: {config.AI_DIFFICULTY_ELO['easy']})",
                "medium": f"Casual player (ELO: {config.AI_DIFFICULTY_ELO['medium']})", 
                "hard": f"Experienced player (ELO: {config.AI_DIFFICULTY_ELO['hard']})",
                "very_hard": f"Expert level (ELO: {config.AI_DIFFICULTY_ELO['very_hard']})"
            }
            
            if is_unlocked:
                # Check if this is the next level to beat - but NOT for very_hard
                difficulty_index = config.AI_DIFFICULTIES.index(difficulty)
                if difficulty_index > 0 and difficulty_index == len(unlocked) - 1 and difficulty != "very_hard":
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
        
    def draw_settings_menu(self, settings, settings_elements, back_button, mouse_pos):
        """Draw the settings menu."""
        self.draw_parallax_background(0.8)
        
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Calculate center for fullscreen compatibility
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        # Title
        title = self.pixel_fonts['huge'].render("SETTINGS", True, config.WHITE)
        title_rect = title.get_rect(center=(game_center_x, game_center_y - 220 * self.scale))
        self.screen.blit(title, title_rect)
        
        # Draw toggle switches
        for key, element in settings_elements.items():
            if key in ["animations", "show_valid_moves", "auto_queen", "show_captured", "show_timer"]:
                # Draw label
                label = self.pixel_fonts['medium'].render(element["label"], True, config.WHITE)
                label_rect = label.get_rect(midright=(element["rect"].x - 20, element["rect"].centery))
                self.screen.blit(label, label_rect)
                
                # Draw toggle switch background
                is_on = settings.get(key, True)
                bg_color = (60, 150, 60) if is_on else (100, 60, 60)
                pygame.draw.rect(self.screen, bg_color, element["rect"], border_radius=15)
                pygame.draw.rect(self.screen, config.WHITE, element["rect"], 2, border_radius=15)
                
                # Draw toggle circle
                circle_x = element["rect"].x + (element["rect"].width - 15 if is_on else 15)
                circle_y = element["rect"].centery
                circle_color = (200, 255, 200) if is_on else (255, 200, 200)
                pygame.draw.circle(self.screen, circle_color, (circle_x, circle_y), 12)
                pygame.draw.circle(self.screen, config.WHITE, (circle_x, circle_y), 12, 2)
                
                # Hover effect
                if element["rect"].collidepoint(mouse_pos):
                    hover_rect = element["rect"].inflate(4, 4)
                    pygame.draw.rect(self.screen, (255, 255, 255, 50), hover_rect, 2, border_radius=17)
                    
            elif key == "board_theme":
                # Draw board theme selector
                label = self.pixel_fonts['medium'].render(element["label"], True, config.WHITE)
                label_rect = label.get_rect(midright=(element["rect"].x - 20, element["rect"].centery))
                self.screen.blit(label, label_rect)
                
                # Draw theme button
                current_theme = element["options"][element["current"]]
                is_hover = element["rect"].collidepoint(mouse_pos)
                
                button_color = (80, 80, 100) if is_hover else (60, 60, 80)
                pygame.draw.rect(self.screen, button_color, element["rect"], border_radius=5)
                pygame.draw.rect(self.screen, config.WHITE, element["rect"], 2, border_radius=5)
                
                # Draw theme name
                theme_text = self.pixel_fonts['small'].render(current_theme, True, config.WHITE)
                theme_rect = theme_text.get_rect(center=element["rect"].center)
                self.screen.blit(theme_text, theme_rect)
                
                # Draw arrows to indicate cycling
                arrow_left = self.pixel_fonts['small'].render("◄", True, (150, 150, 150))
                arrow_right = self.pixel_fonts['small'].render("►", True, (150, 150, 150))
                arrow_left_rect = arrow_left.get_rect(midright=(element["rect"].x - 5, element["rect"].centery))
                arrow_right_rect = arrow_right.get_rect(midleft=(element["rect"].right + 5, element["rect"].centery))
                self.screen.blit(arrow_left, arrow_left_rect)
                self.screen.blit(arrow_right, arrow_right_rect)
        
        # Instructions
        instructions = [
            "Click toggles to enable/disable features",
            "Volume sliders are in the top-right corner",
            "Settings are automatically saved"
        ]
        
        y = game_center_y + 180 * self.scale
        for instruction in instructions:
            text = self.pixel_fonts['tiny'].render(instruction, True, (180, 180, 180))
            text_rect = text.get_rect(center=(game_center_x, y))
            self.screen.blit(text, text_rect)
            y += 20 * self.scale
        
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_menu(self, screen_type, buttons, mouse_pos):
        """Draw menu screens."""
        # Store current screen for chess pieces behavior
        self.current_screen = screen_type
        
        # Special handling for start screen to integrate fire with parallax layers
        if screen_type == config.SCREEN_START:
            self.draw_parallax_background_with_fire(1.2)
        else:
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
            # Check for intro jet sequence - NOW IMMEDIATE
            current_time = pygame.time.get_ticks()
            time_since_start = current_time - self.intro_start_time
            
            # Initialize high flying jets list if not exists
            if not hasattr(self, 'high_flying_jets'):
                self.high_flying_jets = []
                self.next_high_jet_spawn = current_time + random.randint(15000, 30000)  # First jet in 15-30 seconds
            
            # Spawn occasional high flying jets
            if current_time >= self.next_high_jet_spawn:
                # Create a high flying jet
                self.high_flying_jets.append({
                    'x': -100,  # Start off-screen left
                    'y': random.randint(50, 150),  # High in the sky
                    'speed': random.uniform(2, 4),  # Slower speed for high altitude
                    'scale': random.uniform(0.15, 0.25)  # Smaller for distance
                })
                # Schedule next jet
                self.next_high_jet_spawn = current_time + random.randint(20000, 40000)  # Every 20-40 seconds
            
            # Update and draw high flying jets
            jets_to_remove = []
            for jet in self.high_flying_jets:
                jet['x'] += jet['speed']
                
                # Draw the jet if we have jet frames
                if hasattr(self.assets, 'jet_frames') and self.assets.jet_frames:
                    frame_index = int((current_time / 200) % len(self.assets.jet_frames))
                    jet_frame = self.assets.jet_frames[frame_index]
                    
                    jet_width = int(jet_frame.get_width() * jet['scale'])
                    jet_height = int(jet_frame.get_height() * jet['scale'])
                    scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
                    
                    # Flip the jet so it faces right when flying left to right
                    flipped_jet = pygame.transform.flip(scaled_jet, True, False)
                    
                    # Make it slightly transparent for distance
                    flipped_jet.set_alpha(180)
                    
                    self.screen.blit(flipped_jet, (int(jet['x']), int(jet['y'])))
                
                # Remove if off screen
                if jet['x'] > config.WIDTH + 100:
                    jets_to_remove.append(jet)
            
            for jet in jets_to_remove:
                self.high_flying_jets.remove(jet)
            
            # Update chess pieces physics BEFORE drawing
            if self.chess_pieces_enabled:
                self._update_chess_pieces()
            
            # Draw jet flyby with bombs
            if self.intro_jet_triggered:
                self._draw_intro_jet_with_bombs(time_since_start)
                
            # Continue to update any remaining falling bombs even after jet is done
            if hasattr(self, 'falling_bombs') and self.falling_bombs:
                # Process any bombs that are still falling
                bombs_to_remove = []
                for bomb in self.falling_bombs:
                    if not bomb['exploded']:
                        bomb['y'] += bomb['vy']
                        bomb['vy'] += 0.5
                        
                        if bomb['y'] >= config.HEIGHT - 80:
                            bomb['exploded'] = True
                            # Create fire zones (same as in jet method)
                            world_x = bomb['world_x']
                            layers = [
                                {'depth': 0.5, 'y_offset': -10, 'size': 0.8},
                                {'depth': 0.7, 'y_offset': 0, 'size': 1.0},
                                {'depth': 0.9, 'y_offset': 10, 'size': 1.2}
                            ]
                            
                            for layer in layers:
                                self.fire_zones.append({
                                    'world_x': bomb['x'] + self.parallax_offset * layer['depth'],
                                    'y': config.HEIGHT - 80 + layer['y_offset'],
                                    'width': int(80 * layer['size']),
                                    'spawn_timer': random.randint(0, 5),
                                    'intensity': 1.0,
                                    'depth': layer['depth']
                                })
                            
                            bombs_to_remove.append(bomb)
                        elif bomb['y'] > config.HEIGHT + 100:
                            bombs_to_remove.append(bomb)
                            
                for bomb in bombs_to_remove:
                    if bomb in self.falling_bombs:
                        self.falling_bombs.remove(bomb)
                
            # Draw any remaining falling bombs on top layer
            if hasattr(self, 'falling_bombs'):
                for bomb in self.falling_bombs:
                    if not bomb['exploded']:
                        # Draw bomb
                        bomb_width = int(8 * self.scale)
                        bomb_height = int(16 * self.scale)
                        
                        # Main bomb body
                        pygame.draw.ellipse(self.screen, (60, 60, 60), 
                                          (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2, 
                                           bomb_width, bomb_height))
                        pygame.draw.ellipse(self.screen, (40, 40, 40), 
                                          (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2, 
                                           bomb_width, bomb_height), 1)
                        
                        # Nose cone
                        nose_points = [
                            (bomb['x'] - bomb_width//2, bomb['y'] + bomb_height//2 - 2),
                            (bomb['x'] + bomb_width//2, bomb['y'] + bomb_height//2 - 2),
                            (bomb['x'], bomb['y'] + bomb_height//2 + bomb_width//2)
                        ]
                        pygame.draw.polygon(self.screen, (50, 50, 50), nose_points)
                        
                        # Fins
                        fin_height = int(5 * self.scale)
                        # Left fin
                        pygame.draw.polygon(self.screen, (70, 70, 70), [
                            (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2),
                            (bomb['x'] - bomb_width//2 - 3, bomb['y'] - bomb_height//2 - fin_height),
                            (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2 + 2)
                        ])
                        # Right fin
                        pygame.draw.polygon(self.screen, (70, 70, 70), [
                            (bomb['x'] + bomb_width//2, bomb['y'] - bomb_height//2),
                            (bomb['x'] + bomb_width//2 + 3, bomb['y'] - bomb_height//2 - fin_height),
                            (bomb['x'] + bomb_width//2, bomb['y'] - bomb_height//2 + 2)
                        ])
                
            # Title
            text = self.pixel_fonts['huge'].render("CHECKMATE PROTOCOL", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, game_center_y - 150 * config.SCALE))
            self.screen.blit(text, rect)
            
            # Beta badge (displayed at top-right corner of title)
            if hasattr(self.assets, 'beta_badge') and self.assets.beta_badge:
                # Scale the beta badge appropriately
                badge_height = int(80 * config.SCALE)  # Increased size
                aspect_ratio = self.assets.beta_badge.get_width() / self.assets.beta_badge.get_height()
                badge_width = int(badge_height * aspect_ratio)
                
                # Rotate the badge slightly downward
                scaled_badge = pygame.transform.scale(self.assets.beta_badge, (badge_width, badge_height))
                rotated_badge = pygame.transform.rotate(scaled_badge, -15)  # Rotate 15 degrees clockwise
                
                # Position it closer to the corner of the title
                badge_x = rect.right - int(20 * config.SCALE)  # Closer to title
                badge_y = rect.top - int(30 * config.SCALE)  # Higher up
                
                self.screen.blit(rotated_badge, (badge_x, badge_y))
            
            # Buttons
            self._draw_button(buttons['play'], "PLAY GAME", (70, 150, 70), (100, 200, 100), mouse_pos)
            self._draw_button(buttons['settings'], "SETTINGS", (150, 70, 150), (200, 100, 200), mouse_pos)
            self._draw_button(buttons['beta'], "BETA TEST INFO", (150, 150, 70), (200, 200, 100), mouse_pos)
            self._draw_button(buttons['credits'], "CREDITS", (70, 70, 150), (100, 100, 200), mouse_pos)
            
        elif screen_type == config.SCREEN_CREDITS:
            # Title
            text = self.pixel_fonts['huge'].render("CREDITS", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, config.GAME_OFFSET_Y + 60 * config.SCALE))  # Moved up
            self.screen.blit(text, rect)
            
            # Credits - adjusted spacing and positioning
            y = config.GAME_OFFSET_Y + 140 * config.SCALE  # Start higher
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
                y += 28 * config.SCALE  # Reduced spacing from 35 to 28
                
            # Back button
            self._draw_button(buttons['back'], "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
            
        elif screen_type == config.SCREEN_BETA:
            # Title
            text = self.pixel_fonts['huge'].render("BETA TEST", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, config.GAME_OFFSET_Y + 80 * config.SCALE))
            self.screen.blit(text, rect)
            
            # Beta test information
            y = config.GAME_OFFSET_Y + 160 * config.SCALE
            beta_text = [
                "Welcome to the Checkmate Protocol Beta!",
                "",
                "This is an early test version of the game.",
                "The full game will include a complete story mode",
                "after the beta testing phase is completed.",
                "",
                "Please help us improve by:",
                "• Playing through all difficulty levels",
                "• Testing different powerups and strategies",
                "• Trying to find bugs or exploits",
                "• Providing feedback on game mechanics",
                "",
                "Your feedback is invaluable for making",
                "Checkmate Protocol the best it can be!",
                "",
                "Thank you for being a beta tester!"
            ]
            
            for line in beta_text:
                if line:
                    if line.startswith("Welcome") or line.startswith("Thank you"):
                        text_surface = self.pixel_fonts['medium'].render(line, True, (255, 215, 0))
                    elif line.startswith("•"):
                        text_surface = self.pixel_fonts['small'].render(line, True, (150, 200, 150))
                    else:
                        text_surface = self.pixel_fonts['small'].render(line, True, (200, 200, 200))
                    rect = text_surface.get_rect(center=(game_center_x, y))
                    self.screen.blit(text_surface, rect)
                y += 30 * config.SCALE
            
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
            # Use smoothscale for better quality and to reduce artifacts
            scaled_tariq = pygame.transform.smoothscale(self.assets.tariq_image, (tariq_width, tariq_height))
            
            # Position Tariq on the left side, at the very bottom
            tariq_x = int(50 * config.SCALE)
            # Position him so he's standing at the bottom edge
            tariq_y = config.HEIGHT - tariq_height  # Right at the bottom
            
            self.screen.blit(scaled_tariq, (tariq_x, tariq_y))
            
            # Store rect for click detection
            self.tariq_rect = pygame.Rect(tariq_x, tariq_y, tariq_width, tariq_height)
            
            # Draw speech bubble with dialogue - position it above Tariq's head
            if dialogues and 0 <= dialogue_index < len(dialogues):
                dialogue = dialogues[dialogue_index]
                # Position bubble directly above Tariq's head, centered on him
                # Center it over Tariq by using his center position
                bubble_width = int(300 * config.SCALE)
                tariq_center_x = tariq_x + tariq_width // 2
                bubble_x = tariq_center_x - bubble_width // 2  # Center the bubble over Tariq
                bubble_y = tariq_y - int(120 * config.SCALE)  # Well above his head
                self._draw_speech_bubble(bubble_x, bubble_y, 
                                       dialogue, bubble_width, point_down=True)
        
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
        card_width = int(120 * self.scale)  # Smaller cards
        card_height = int(160 * self.scale)
        card_spacing = int(15 * self.scale)
        
        # Calculate total width needed
        powerup_keys = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
        total_width = len(powerup_keys) * card_width + (len(powerup_keys) - 1) * card_spacing
        start_x = game_center_x - total_width // 2 + int(100 * self.scale)  # Shift right
        
        shop_buttons.clear()
        
        for i, powerup_key in enumerate(powerup_keys):
            powerup = powerup_system.powerups[powerup_key]
            price = powerup_system.powerup_prices[powerup_key]
            is_unlocked = powerup_key in unlocked
            can_afford = money >= price and not is_unlocked
            
            # Card position
            card_x = start_x + i * (card_width + card_spacing)
            card_y = game_center_y - 40 * self.scale
            
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
            icon_rect = icon_surface.get_rect(center=(card_rect.centerx, card_y + 35 * self.scale))
            self.screen.blit(icon_surface, icon_rect)
            
            # Powerup name
            name_color = config.WHITE if is_unlocked else powerup["color"]
            name_surface = self.pixel_fonts['small'].render(powerup["name"], True, name_color)
            name_rect = name_surface.get_rect(center=(card_rect.centerx, card_y + 70 * self.scale))
            self.screen.blit(name_surface, name_rect)
            
            # Description (shortened for smaller cards)
            desc_lines = self._wrap_text(powerup["description"], self.pixel_fonts['tiny'], card_width - 10)
            desc_y = card_y + 90 * self.scale
            for line in desc_lines[:2]:  # Max 2 lines
                line_surface = self.pixel_fonts['tiny'].render(line, True, (200, 200, 200))
                line_rect = line_surface.get_rect(center=(card_rect.centerx, desc_y))
                self.screen.blit(line_surface, line_rect)
                desc_y += 12 * self.scale
            
            # Price or status
            if is_unlocked:
                status_text = "OWNED"
                status_color = (100, 255, 100)
            else:
                status_text = f"${price}"
                status_color = (255, 215, 0) if can_afford else (200, 100, 100)
            
            status_surface = self.pixel_fonts['medium'].render(status_text, True, status_color)
            status_rect = status_surface.get_rect(center=(card_rect.centerx, card_rect.bottom - 15 * self.scale))
            self.screen.blit(status_surface, status_rect)
        
        # Instructions
        inst_text = "Click on items to purchase. Click Tariq for more info!"
        inst_surface = self.pixel_fonts['small'].render(inst_text, True, (200, 200, 200))
        inst_rect = inst_surface.get_rect(center=(game_center_x, game_center_y + 170 * self.scale))
        self.screen.blit(inst_surface, inst_rect)
        
        # Back button
        self._draw_button(back_button, "BACK TO GAME", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def _draw_speech_bubble(self, x, y, text, max_width, point_down=False):
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
        if point_down:
            # Tail pointing down from bottom of bubble
            tail_x = x + bubble_width // 2  # Center of bubble
            tail_points = [
                (tail_x - 15, y + bubble_height - 2),  # Left point
                (tail_x + 15, y + bubble_height - 2),  # Right point
                (tail_x, y + bubble_height + 20)        # Bottom point
            ]
            pygame.draw.polygon(self.screen, (40, 40, 40), tail_points)
            # Draw outline
            pygame.draw.lines(self.screen, (200, 200, 200), False, 
                             [(tail_x - 15, y + bubble_height - 2), (tail_x, y + bubble_height + 20)], 3)
            pygame.draw.lines(self.screen, (200, 200, 200), False, 
                             [(tail_x + 15, y + bubble_height - 2), (tail_x, y + bubble_height + 20)], 3)
        else:
            # Original tail pointing left
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
        
    def _draw_intro_jet_with_bombs(self, elapsed_time):
        """Draw jet flyby and create fire zones."""
        # Jet flies from left to right
        jet_progress = elapsed_time / 4000.0  # 4 second flyby
        jet_x = -200 + (config.WIDTH + 400) * jet_progress
        jet_y = config.HEIGHT * 0.1  # 10% from top - above the treeline
        
        # Initialize bomb list if needed
        if not hasattr(self, 'falling_bombs'):
            self.falling_bombs = []
        
        # Draw jet
        if hasattr(self.assets, 'jet_frames') and self.assets.jet_frames and jet_progress < 1.0:
            frame_index = int((elapsed_time / 100) % len(self.assets.jet_frames))
            jet_frame = self.assets.jet_frames[frame_index]
            
            jet_scale = 0.3 * self.scale
            jet_width = int(jet_frame.get_width() * jet_scale)
            jet_height = int(jet_frame.get_height() * jet_scale)
            scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
            flipped_jet = pygame.transform.flip(scaled_jet, True, False)
            
            self.screen.blit(flipped_jet, (jet_x, jet_y))
            
            # Drop bombs continuously
            if 0.05 < jet_progress < 0.95:  # Extended bombing range
                # Drop a bomb every 80 pixels
                if not hasattr(self, '_last_bomb_drop_x'):
                    self._last_bomb_drop_x = jet_x
                    
                if jet_x - self._last_bomb_drop_x > 80:
                    self._last_bomb_drop_x = jet_x
                    
                    # Create a falling bomb
                    self.falling_bombs.append({
                        'x': jet_x + jet_width // 2,
                        'y': jet_y + jet_height,
                        'vy': 2,
                        'world_x': jet_x + jet_width // 2 + self.parallax_offset * 0.6,
                        'exploded': False
                    })
        
        # Always update and process ALL falling bombs
        if hasattr(self, 'falling_bombs'):
            bombs_to_remove = []
            for bomb in self.falling_bombs:
                if not bomb['exploded']:
                    # Update bomb position
                    bomb['y'] += bomb['vy']
                    bomb['vy'] += 0.5  # Gravity
                    
                    # Check if bomb hit ground or went off screen
                    if bomb['y'] >= config.HEIGHT - 80:
                        bomb['exploded'] = True
                        
                        # Create fire zones at multiple depth layers
                        world_x = bomb['x']  # Use screen position instead of world position
                        
                        # Create fire at different depths for dimensionality
                        layers = [
                            {'depth': 0.5, 'y_offset': -10, 'size': 0.8},  # Far layer
                            {'depth': 0.7, 'y_offset': 0, 'size': 1.0},    # Middle layer
                            {'depth': 0.9, 'y_offset': 10, 'size': 1.2}    # Near layer
                        ]
                        
                        for layer in layers:
                            self.fire_zones.append({
                                'world_x': world_x + self.parallax_offset * layer['depth'],  # Convert to world coordinates
                                'y': config.HEIGHT - 80 + layer['y_offset'],
                                'width': int(80 * layer['size']),
                                'spawn_timer': random.randint(0, 5),
                                'intensity': 1.0,
                                'depth': layer['depth']  # Store depth for parallax calculation
                            })
                        
                        print(f"Bomb exploded! Created fire zones at world_x={world_x}, total zones: {len(self.fire_zones)}")
                                
                        # Create explosion effect
                        for _ in range(20):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(2, 8)
                            self.bomb_explosions.append({
                                'x': bomb['x'],
                                'y': config.HEIGHT - 80,
                                'vx': math.cos(angle) * speed,
                                'vy': math.sin(angle) * speed - 5,
                                'size': random.randint(4, 12),
                                'life': random.randint(20, 40),
                                'color': random.choice([(255, 200, 0), (255, 150, 0), (255, 100, 0)])
                            })
                        
                        # Enable chess pieces falling after first bomb
                        if not self.chess_pieces_enabled:
                            self.chess_pieces_enabled = True
                            self._spawn_initial_chess_pieces()
                            # Play sound if available
                            if hasattr(self.assets, 'explosion_sound') and self.assets.explosion_sound and not self.intro_sound_played:
                                self.assets.explosion_sound.play()
                                self.intro_sound_played = True
                        
                        bombs_to_remove.append(bomb)
                    
                    # Also remove if way off screen
                    elif bomb['y'] > config.HEIGHT + 100:
                        bomb['exploded'] = True
                        bombs_to_remove.append(bomb)
                        
            # Remove exploded bombs
            for bomb in bombs_to_remove:
                if bomb in self.falling_bombs:
                    self.falling_bombs.remove(bomb)
        
        # Once jet is done, create additional fire zones to fill the entire scrollable area
        if jet_progress >= 0.9 and not hasattr(self, '_extra_fire_zones_created'):
            self._extra_fire_zones_created = True
            
            # Only create extra zones if we have at least one fire zone from bombs
            if self.fire_zones:
                # Create fire zones extending far to the left and right
                # This ensures fire appears when scrolling
                for offset in range(-3000, 3000, 120):  # Slightly wider spacing since we have layers
                    world_x = offset + self.parallax_offset * 0.6
                    
                    # Create fire at different depths
                    layers = [
                        {'depth': 0.5, 'y_offset': -10, 'size': 0.8},  # Far layer
                        {'depth': 0.7, 'y_offset': 0, 'size': 1.0},    # Middle layer
                        {'depth': 0.9, 'y_offset': 10, 'size': 1.2}    # Near layer
                    ]
                    
                    for layer in layers:
                        self.fire_zones.append({
                            'world_x': world_x + random.randint(-40, 40),  # More variation
                            'y': config.HEIGHT - 80 + layer['y_offset'],
                            'width': int(80 * layer['size']),
                            'spawn_timer': random.randint(0, 15),  # More stagger
                            'intensity': 1.0,
                            'depth': layer['depth']
                        })
                    
    def _draw_fire_at_depth(self, current_time, target_depth):
        """Draw only fire particles at a specific depth layer."""
        # Update fire zones first if not already done
        if not hasattr(self, '_fire_updated_this_frame') or not self._fire_updated_this_frame:
            self._update_fire_zones(current_time)
            self._fire_updated_this_frame = True
        
        # Draw only particles at this depth
        particles_drawn = 0
        for particle in self.fire_particles:
            if abs(particle.get('depth', 0.7) - target_depth) < 0.1:  # Close to target depth
                life_ratio = particle['life'] / 60
                
                if particle['type'] == 'flame':
                    self._draw_16bit_fire(particle, life_ratio)
                elif particle['type'] == 'ember':
                    self._draw_pixel_ember(particle, life_ratio)
                particles_drawn += 1
        
        # Also draw explosion particles at this depth
        for exp in self.bomb_explosions:
            life_ratio = exp['life'] / 30
            color = tuple(max(0, min(255, int(c * life_ratio))) for c in exp['color'])
            pygame.draw.circle(self.screen, color, 
                             (int(exp['x']), int(exp['y'])), int(exp['size']))
    
    def _update_fire_zones(self, current_time):
        """Update fire zones and spawn particles without drawing."""
        # Update fire zones - only process visible ones for performance
        visible_buffer = 100
        
        zones_visible = 0
        particles_spawned = 0
        
        for zone in self.fire_zones:
            # Get depth for this zone
            depth = zone.get('depth', 0.7)
            
            # Calculate screen position based on parallax and depth
            screen_x = zone['world_x'] - self.parallax_offset * (0.6 * depth)
            
            # Initialize fade-in state if needed
            if 'fade_in' not in zone:
                zone['fade_in'] = 0.0
                zone['was_visible'] = False
            
            # Check if zone is potentially visible
            zone_visible = -visible_buffer < screen_x < config.WIDTH + visible_buffer
            
            # If zone just became visible, start fade-in
            if zone_visible and not zone['was_visible']:
                zone['fade_in'] = 0.0
                zone['was_visible'] = True
            elif not zone_visible:
                zone['was_visible'] = False
                continue
            
            # Gradually increase fade-in
            if zone['fade_in'] < 1.0:
                zone['fade_in'] = min(1.0, zone['fade_in'] + 0.02)
            
            zone['spawn_timer'] += 1
            
            # Spawn new particles continuously
            if zone['spawn_timer'] > 2:
                zone['spawn_timer'] = 0
                
                num_particles = int(random.randint(5, 8) * zone['fade_in'])
                if num_particles > 0:
                    for _ in range(num_particles):
                        x_offset = random.randint(-zone['width']//2, zone['width']//2)
                        
                        size_multiplier = 0.5 + 0.5 * zone['fade_in']
                        life_multiplier = 0.6 + 0.4 * zone['fade_in']
                        
                        # Adjust particle properties based on depth
                        depth_scale = 0.6 + 0.4 * depth
                        
                        self.fire_particles.append({
                            'x': screen_x + x_offset,
                            'y': zone['y'] + random.randint(-10, 10),
                            'vx': random.uniform(-0.5, 0.5) * depth_scale,
                            'vy': random.uniform(-3, -1) * (0.5 + 0.5 * zone['fade_in']) * depth_scale,
                            'size': random.randint(int(10 * size_multiplier * depth_scale), int(20 * size_multiplier * depth_scale)),
                            'life': random.randint(int(40 * life_multiplier), int(60 * life_multiplier)),
                            'type': random.choice(['flame', 'flame', 'ember']),
                            'flicker': random.randint(0, 10),
                            'opacity_modifier': zone['fade_in'] * (0.5 + 0.5 * depth),
                            'depth': depth
                        })
        
        # Update particles physics
        remaining_particles = []
        for particle in self.fire_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['flicker'] += 1
            
            if particle['type'] == 'flame':
                particle['size'] *= 0.97
                particle['vy'] -= 0.15
            elif particle['type'] == 'ember':
                particle['size'] *= 0.95
                particle['vx'] += random.uniform(-0.2, 0.2)
            
            # Gradually increase opacity modifier if it's less than 1
            if 'opacity_modifier' in particle and particle['opacity_modifier'] < 1.0:
                particle['opacity_modifier'] = min(1.0, particle['opacity_modifier'] + 0.02)
            elif 'opacity_modifier' not in particle:
                particle['opacity_modifier'] = 1.0
            
            if particle['life'] > 0 and particle['size'] > 1:
                remaining_particles.append(particle)
                
        self.fire_particles = remaining_particles
        
        # Update explosion particles
        remaining_explosions = []
        for exp in self.bomb_explosions:
            exp['x'] += exp['vx']
            exp['y'] += exp['vy']
            exp['vy'] += 0.5
            exp['life'] -= 1
            exp['size'] *= 0.95
            exp['vx'] *= 0.96
            
            if exp['life'] > 0 and exp['size'] > 1:
                life_ratio = exp['life'] / 30
                color = tuple(max(0, min(255, int(c * life_ratio))) for c in exp['color'])
                pygame.draw.circle(self.screen, color, 
                                 (int(exp['x']), int(exp['y'])), int(exp['size']))
                remaining_explosions.append(exp)
                
        self.bomb_explosions = remaining_explosions
        
        # Keep reasonable particle limits
        if len(self.fire_particles) > 500:
            self.fire_particles = self.fire_particles[-500:]
            
    def _update_and_draw_fire_system(self, current_time):
        """Update and draw the entire fire system - simplified version for non-layered drawing."""
        # This method is still used by the regular parallax background
        # Update fire zones first
        self._update_fire_zones(current_time)
        
        # Draw all particles
        for particle in self.fire_particles:
            life_ratio = particle['life'] / 60
            
            if particle['type'] == 'flame':
                self._draw_16bit_fire(particle, life_ratio)
            elif particle['type'] == 'ember':
                self._draw_pixel_ember(particle, life_ratio)
        """Update and draw the entire fire system."""
        # Update fire zones - only process visible ones for performance
        visible_buffer = 100  # Tighter buffer so fire appears closer to edge
        
        for zone in self.fire_zones:
            # Get depth for this zone
            depth = zone.get('depth', 0.7)  # Default to middle depth
            
            # Calculate screen position based on parallax and depth
            screen_x = zone['world_x'] - self.parallax_offset * (0.6 * depth)
            
            # Initialize fade-in state if needed
            if 'fade_in' not in zone:
                zone['fade_in'] = 0.0  # Start completely faded out
                zone['was_visible'] = False
            
            # Check if zone is potentially visible
            zone_visible = -visible_buffer < screen_x < config.WIDTH + visible_buffer
            
            # If zone just became visible, start fade-in
            if zone_visible and not zone['was_visible']:
                zone['fade_in'] = 0.0
                zone['was_visible'] = True
            elif not zone_visible:
                zone['was_visible'] = False
                continue
            
            # Gradually increase fade-in
            if zone['fade_in'] < 1.0:
                zone['fade_in'] = min(1.0, zone['fade_in'] + 0.02)  # Fade in over ~50 frames
            
            zone['spawn_timer'] += 1
            
            # Spawn new particles continuously - but scale by fade-in
            if zone['spawn_timer'] > 2:
                zone['spawn_timer'] = 0
                
                # Spawn fewer particles when fading in
                num_particles = int(random.randint(5, 8) * zone['fade_in'])
                if num_particles > 0:
                    # Spawn multiple particles across zone width
                    for _ in range(num_particles):
                        x_offset = random.randint(-zone['width']//2, zone['width']//2)
                        
                        # Start particles with smaller size and shorter life when fading in
                        size_multiplier = 0.5 + 0.5 * zone['fade_in']
                        life_multiplier = 0.6 + 0.4 * zone['fade_in']
                        
                        # Adjust particle properties based on depth
                        depth_scale = 0.6 + 0.4 * depth  # Smaller when further away
                        
                        self.fire_particles.append({
                            'x': screen_x + x_offset,
                            'y': zone['y'] + random.randint(-10, 10),
                            'vx': random.uniform(-0.5, 0.5) * depth_scale,
                            'vy': random.uniform(-3, -1) * (0.5 + 0.5 * zone['fade_in']) * depth_scale,
                            'size': random.randint(int(10 * size_multiplier * depth_scale), int(20 * size_multiplier * depth_scale)),
                            'life': random.randint(int(40 * life_multiplier), int(60 * life_multiplier)),
                            'type': random.choice(['flame', 'flame', 'ember']),
                            'flicker': random.randint(0, 10),
                            'opacity_modifier': zone['fade_in'] * (0.5 + 0.5 * depth),  # More transparent when further
                            'depth': depth  # Store depth for rendering order
                        })
                    
        # Update and draw particles
        remaining_particles = []
        for particle in self.fire_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['flicker'] += 1
            
            if particle['type'] == 'flame':
                particle['size'] *= 0.97
                particle['vy'] -= 0.15
            elif particle['type'] == 'ember':
                particle['size'] *= 0.95
                particle['vx'] += random.uniform(-0.2, 0.2)
            
            # Gradually increase opacity modifier if it's less than 1
            if 'opacity_modifier' in particle and particle['opacity_modifier'] < 1.0:
                particle['opacity_modifier'] = min(1.0, particle['opacity_modifier'] + 0.02)
            elif 'opacity_modifier' not in particle:
                particle['opacity_modifier'] = 1.0
            
            if particle['life'] > 0 and particle['size'] > 1:
                # Draw particle
                life_ratio = particle['life'] / 60
                
                if particle['type'] == 'flame':
                    self._draw_16bit_fire(particle, life_ratio)
                elif particle['type'] == 'ember':
                    self._draw_pixel_ember(particle, life_ratio)
                    
                remaining_particles.append(particle)
                
        self.fire_particles = remaining_particles
        
        # Update and draw explosion particles - SIMPLER
        remaining_explosions = []
        for exp in self.bomb_explosions:
            exp['x'] += exp['vx']
            exp['y'] += exp['vy']
            exp['vy'] += 0.5  # Gravity
            exp['life'] -= 1
            exp['size'] *= 0.95  # Gradual shrink
            exp['vx'] *= 0.96  # Slight air resistance
            
            if exp['life'] > 0 and exp['size'] > 1:
                # Simple fading circle
                life_ratio = exp['life'] / 30
                color = tuple(max(0, min(255, int(c * life_ratio))) for c in exp['color'])
                pygame.draw.circle(self.screen, color, 
                                 (int(exp['x']), int(exp['y'])), int(exp['size']))
                remaining_explosions.append(exp)
                
        self.bomb_explosions = remaining_explosions
        
        # Note: Chess pieces are drawn in draw_menu now, not here
        
        # Keep reasonable particle limits
        if len(self.fire_particles) > 500:
            self.fire_particles = self.fire_particles[-500:]
            
    def _draw_16bit_fire(self, particle, life_ratio):
        """Draw 16-bit style fire particle."""
        x, y = int(particle['x']), int(particle['y'])
        size = int(particle['size'])
        flicker = particle['flicker']
        
        # Get opacity modifier
        opacity = particle.get('opacity_modifier', 1.0)
        
        # Create fire shape using rectangles for that pixel art look
        if life_ratio > 0.7:
            # Hot white/yellow core
            base_color = (255, 255, 200) if flicker % 4 < 2 else (255, 255, 150)
            core_color = tuple(int(c * opacity) for c in base_color)
            # Draw diamond shape core
            for i in range(size // 3):
                w = size // 3 - i
                if w > 0:
                    pygame.draw.rect(self.screen, core_color, 
                                   (x - w, y - i, w * 2, 1))
                    pygame.draw.rect(self.screen, core_color, 
                                   (x - w, y + i, w * 2, 1))
                                   
        # Middle orange layer
        if life_ratio > 0.4:
            base_color = (255, 150, 0) if flicker % 3 < 2 else (255, 180, 0)
            mid_color = tuple(int(c * opacity) for c in base_color)
            mid_size = int(size * 0.8)
            # Draw larger diamond
            for i in range(mid_size // 2):
                w = mid_size // 2 - i
                if w > 0:
                    pygame.draw.rect(self.screen, mid_color, 
                                   (x - w, y - i - size // 6, w * 2, 1))
                    pygame.draw.rect(self.screen, mid_color, 
                                   (x - w, y + i - size // 6, w * 2, 1))
                                   
        # Outer red layer
        base_color = (200, 50, 0) if flicker % 5 < 3 else (180, 30, 0)
        outer_color = tuple(int(c * opacity) for c in base_color)
        # Draw flickering outer flames
        flame_height = int(size * 1.2)
        for i in range(0, flame_height, 2):  # Draw every other line for performance
            width = int((flame_height - i) * 0.7)
            wobble = int(math.sin(i * 0.5 + flicker * 0.3) * 2)
            if width > 0:
                pygame.draw.rect(self.screen, outer_color,
                               (x - width // 2 + wobble, y - i, width, 2))
                               
    def _draw_pixel_ember(self, particle, life_ratio):
        """Draw pixelated ember."""
        x, y = int(particle['x']), int(particle['y'])
        size = max(2, int(particle['size'] * 0.4))
        
        # Get opacity modifier
        opacity = particle.get('opacity_modifier', 1.0)
        
        # Ember colors based on heat
        if life_ratio > 0.7:
            base_color = (255, 200, 100)
        elif life_ratio > 0.4:
            base_color = (255, 100, 0)
        else:
            base_color = (150, 50, 0)
            
        color = tuple(int(c * opacity) for c in base_color)
            
        # Draw small pixel squares
        pygame.draw.rect(self.screen, color, (x - size//2, y - size//2, size, size))
        
        # Add glow effect with neighboring pixels
        if life_ratio > 0.5 and size > 2:
            glow_base = tuple(c // 2 for c in base_color)
            glow_color = tuple(int(c * opacity) for c in glow_base)
            pygame.draw.rect(self.screen, glow_color, (x - size//2 - 1, y - size//2, 1, size))
            pygame.draw.rect(self.screen, glow_color, (x + size//2, y - size//2, 1, size))
            pygame.draw.rect(self.screen, glow_color, (x - size//2, y - size//2 - 1, size, 1))
            pygame.draw.rect(self.screen, glow_color, (x - size//2, y + size//2, size, 1))
            
    def _draw_chess_pieces_at_layer(self, target_layer):
        """Draw only chess pieces at a specific layer depth."""
        for piece in self.falling_chess_pieces:
            # Only draw pieces at this specific layer
            if abs(piece['layer'] - target_layer) > 0.01:
                continue
            
            # Calculate screen position
            screen_x = piece['world_x'] - self.parallax_offset * (0.6 * piece['layer'])
            
            # Add swaying motion
            sway_x = math.sin(piece['swing']) * piece['swing_amplitude'] * piece['layer']
            screen_x += sway_x
            
            # Skip if off screen horizontally
            if screen_x < -100 or screen_x > config.WIDTH + 100:
                continue
            
            # Skip if fallen off bottom
            if piece['y'] > config.HEIGHT + 100:
                continue
                
            # Draw the piece
            if piece['piece'] in self.assets.pieces:
                # Calculate size based on distance
                base_size = int(50 * self.scale * piece['size_scale'])
                
                # Get and scale the piece image
                original = self.assets.pieces[piece['piece']]
                scaled = pygame.transform.scale(original, (base_size, base_size))
                
                # Rotate the piece
                rotated = pygame.transform.rotate(scaled, piece['rotation'])
                
                # Apply transparency based on distance and fade-in
                distance_alpha = int(255 * (0.6 + 0.4 * piece['layer']))
                fade_alpha = piece.get('opacity', 255)
                final_alpha = min(distance_alpha, fade_alpha)
                rotated.set_alpha(final_alpha)
                
                # Draw with rotation center adjustment
                rect = rotated.get_rect(center=(int(screen_x), int(piece['y'])))
                self.screen.blit(rotated, rect)
            
    def _spawn_initial_chess_pieces(self):
        """Spawn initial wave of chess pieces falling from trees."""
        # Spawn pieces across the visible area and beyond
        for i in range(50):  # Much more initial pieces (was 20)
            self._spawn_chess_piece()
            
    def _spawn_chess_piece(self):
        """Spawn a single chess piece at a random position."""
        # Chess piece types
        piece_types = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
        
        # Calculate spawn position in world space
        world_x = self.parallax_offset * 0.6 + random.randint(-config.WIDTH, config.WIDTH * 2)
        
        # Different layers for parallax effect - only use specific depths
        layer = random.choice([0.3, 0.5, 0.7, 0.9])  # Removed 1.0 to keep pieces behind trees
        
        # Spawn from tree canopy height (middle of screen) instead of above screen
        # Trees are roughly in the middle third of the screen
        tree_top = config.HEIGHT * 0.25  # Slightly below top of tree canopy
        tree_bottom = config.HEIGHT * 0.55  # Slightly above bottom of tree canopy
        spawn_y = random.uniform(tree_top, tree_bottom)
        
        self.falling_chess_pieces.append({
            'world_x': world_x,
            'y': spawn_y,  # Start at tree height
            'vy': random.uniform(0.5, 2) * layer,  # Slower initial fall speed
            'vx': random.uniform(-1, 1),  # More horizontal drift
            'rotation': random.uniform(0, 360),
            'rotation_speed': random.uniform(-8, 8),  # Faster rotation
            'piece': random.choice(piece_types),
            'layer': layer,  # Distance from camera
            'size_scale': 0.3 + 0.7 * layer,  # Smaller when further away
            'swing': random.uniform(0, 2 * math.pi),  # For swaying motion
            'swing_speed': random.uniform(0.02, 0.08),  # More varied sway
            'swing_amplitude': random.uniform(10, 40),  # Bigger sway
            'opacity': 0  # Start invisible for fade-in effect
        })
        
    def _update_chess_pieces(self):
        """Update chess pieces physics and spawning without drawing."""
        # Different spawn rates for different screens
        if hasattr(self, 'current_screen'):
            spawn_rate = 0.15 if self.current_screen == config.SCREEN_CREDITS else 0.08
        else:
            spawn_rate = 0.08
            
        # Spawn new pieces more frequently
        if random.random() < spawn_rate:  # Higher rate for credits
            self._spawn_chess_piece()
            # Sometimes spawn multiple at once for clusters
            if random.random() < 0.3:  # 30% chance of cluster
                for _ in range(random.randint(2, 5)):
                    self._spawn_chess_piece()
        
        # Update all pieces physics
        remaining_pieces = []
        for piece in self.falling_chess_pieces:
            # Update position - slower for credits page
            fall_speed = piece['vy'] * 0.3 if hasattr(self, 'current_screen') and self.current_screen == config.SCREEN_CREDITS else piece['vy']
            piece['y'] += fall_speed
            piece['world_x'] += piece['vx']
            piece['rotation'] += piece['rotation_speed']
            piece['swing'] += piece['swing_speed']
            
            # Fade in effect
            if 'opacity' in piece and piece['opacity'] < 255:
                piece['opacity'] = min(255, piece['opacity'] + 10)
            
            # Accelerate falling
            piece['vy'] += 0.1  # Gravity
            
            # Keep piece if it hasn't fallen too far off screen
            if piece['y'] <= config.HEIGHT + 200:
                remaining_pieces.append(piece)
                
        self.falling_chess_pieces = remaining_pieces
        
        # Limit max pieces for performance
        if len(self.falling_chess_pieces) > 200:
            self.falling_chess_pieces = self.falling_chess_pieces[-200:]