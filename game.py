"""
Main Game Class - Enhanced with Powerup System and Arms Dealer
"""

import pygame
import config
from assets import AssetManager
from board import ChessBoard
from graphics import Renderer
from ai import ChessAI
from powerups import PowerupSystem
from powerup_renderer import PowerupRenderer
from chopper_gunner import ChopperGunnerMode

class ChessGame:
    def __init__(self):
        # Get screen info before creating display
        self.screen_info = pygame.display.Info()
        
        # Create screen (windowed mode initially)
        self.fullscreen = False
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Checkmate Protocol - Powerup Edition")
        self.clock = pygame.time.Clock()
        
        # Load assets
        self.assets = AssetManager()
        self.assets.load_all()
        
        # Create components
        self.board = ChessBoard()
        self.renderer = Renderer(self.screen, self.assets)
        self.ai = None  # Will be created when difficulty is selected
        
        # Create powerup system
        self.powerup_system = PowerupSystem()
        self.powerup_renderer = PowerupRenderer(self.screen, self.renderer, self.powerup_system)
        
        # Pass assets reference to powerup system
        self.powerup_system.assets = self.assets
        
        # Pass assets reference to renderer
        self.renderer.assets = self.assets
        
        # Connect powerup system to board
        self.board.set_powerup_system(self.powerup_system)
        
        # Chopper gunner mode
        self.chopper_mode = None
        
        # Game state
        self.running = True
        self.current_screen = config.SCREEN_START
        self.mouse_pos = (0, 0)
        self.selected_difficulty = None
        
        # Arms dealer
        self.shop_buttons = {}
        self.arms_dealer_game_button = None
        
        # Arms dealer dialogue state
        self.tariq_dialogue_index = 0
        self.tariq_dialogues = [
            "Welcome, my friend! I am Tariq, the finest arms dealer in the kingdom.",
            "I have powerful tools that can turn the tide of battle...",
            "Each powerup has its price, but victory is priceless!",
            "Shield your pieces, rain fire from above, or unleash total destruction!",
            "What will it be today?"
        ]
        
        # UI elements - will be updated for scaling
        self.update_ui_positions()
        
        # Volume control - NOW WITH SEPARATE MUSIC AND SFX
        self.music_volume = 0.25  # Default music volume at 25%
        self.sfx_volume = 0.7     # Default sound effects volume at 70%
        self.dragging_music_slider = False
        self.dragging_sfx_slider = False
        pygame.mixer.music.set_volume(self.music_volume)
        
        # Apply initial SFX volume to all loaded sounds
        self.update_sfx_volumes()
        
        # Transition state
        self.fade_active = False
        self.fade_start = 0
        self.fade_from = None
        self.fade_to = None
        
        # Promotion menu
        self.promotion_rects = []
        
        # Victory reward tracking
        self.victory_reward = 0
        
        # Start music
        pygame.mixer.music.play(-1)
            
    def update_ui_positions(self):
        """Update UI element positions based on current scale."""
        # Import config to get current values
        import config
        
        # Calculate game area center (accounting for letterboxing in fullscreen)
        if self.fullscreen and config.SCALE != 1.0:
            # In fullscreen, center relative to the scaled game area
            game_width = config.BASE_WIDTH * config.SCALE
            game_height = config.BASE_HEIGHT * config.SCALE
            center_x = config.WIDTH // 2  # Use screen center, which is where the game is centered
            center_y = config.HEIGHT // 2
            
            # Volume sliders - stacked vertically in top right
            slider_width = int(140 * config.SCALE)
            slider_height = int(20 * config.SCALE)
            slider_spacing = int(35 * config.SCALE)
            slider_x = config.GAME_OFFSET_X + game_width - int(160 * config.SCALE)
            
            # Music slider
            self.music_slider_rect = pygame.Rect(
                slider_x, 
                config.GAME_OFFSET_Y + int(10 * config.SCALE), 
                slider_width, 
                slider_height
            )
            
            # SFX slider (below music)
            self.sfx_slider_rect = pygame.Rect(
                slider_x, 
                config.GAME_OFFSET_Y + int(10 * config.SCALE) + slider_spacing, 
                slider_width, 
                slider_height
            )
            
            self.volume_knob_radius = int(10 * config.SCALE)
        else:
            # In windowed mode, use normal positioning
            center_x = config.WIDTH // 2
            center_y = config.HEIGHT // 2
            
            # Volume sliders - stacked vertically in top right
            slider_width = int(140 * config.SCALE)
            slider_height = int(20 * config.SCALE)
            slider_spacing = int(35 * config.SCALE)
            slider_x = config.WIDTH - int(160 * config.SCALE)
            
            # Music slider
            self.music_slider_rect = pygame.Rect(
                slider_x, 
                int(10 * config.SCALE), 
                slider_width, 
                slider_height
            )
            
            # SFX slider (below music)
            self.sfx_slider_rect = pygame.Rect(
                slider_x, 
                int(10 * config.SCALE) + slider_spacing, 
                slider_width, 
                slider_height
            )
            
            self.volume_knob_radius = int(10 * config.SCALE)
        
        # Menu buttons - centered in game area
        self.play_button = pygame.Rect(
            center_x - int(100 * config.SCALE), 
            center_y - int(60 * config.SCALE), 
            int(200 * config.SCALE), 
            int(60 * config.SCALE)
        )
        self.beta_button = pygame.Rect(
            center_x - int(100 * config.SCALE), 
            center_y + int(20 * config.SCALE), 
            int(200 * config.SCALE), 
            int(60 * config.SCALE)
        )
        self.credits_button = pygame.Rect(
            center_x - int(100 * config.SCALE), 
            center_y + int(100 * config.SCALE), 
            int(200 * config.SCALE), 
            int(60 * config.SCALE)
        )
        self.back_button = pygame.Rect(
            center_x - int(100 * config.SCALE), 
            center_y + int(250 * config.SCALE), 
            int(200 * config.SCALE), 
            int(50 * config.SCALE)
        )
        
        # Difficulty buttons
        self.difficulty_buttons = {}
        button_height = int(60 * config.SCALE)
        button_spacing = int(20 * config.SCALE)
        total_height = len(config.AI_DIFFICULTIES) * button_height + (len(config.AI_DIFFICULTIES) - 1) * button_spacing
        start_y = center_y - total_height // 2
        
        for i, difficulty in enumerate(config.AI_DIFFICULTIES):
            y = start_y + i * (button_height + button_spacing)
            self.difficulty_buttons[difficulty] = pygame.Rect(
                center_x - int(150 * config.SCALE), 
                y, 
                int(300 * config.SCALE), 
                button_height
            )
            
    def _handle_ai_powerup(self, powerup_key, action):
        """Handle AI powerup usage."""
        # Deduct points
        self.powerup_system.points["black"] -= self.powerup_system.powerups[powerup_key]["cost"]
        
        if action["type"] == "shield":
            # AI shields a piece
            row, col = action["target"]
            self.powerup_system.shielded_pieces[(row, col)] = 3
            self.powerup_system._create_shield_effect(row, col, self.board)
            
        elif action["type"] == "gun":
            # AI shoots a piece
            shooter_pos = action["shooter"]
            target_pos = action["target"]
            self.powerup_system._create_gun_effect(shooter_pos, target_pos, self.board)
            
            # Destroy target
            target = self.board.get_piece(*target_pos)
            if target and target[1] != 'K' and target_pos not in self.powerup_system.shielded_pieces:
                self.board.set_piece(target_pos[0], target_pos[1], "")
                
        elif action["type"] == "airstrike":
            # AI airstrikes an area
            row, col = action["target"]
            self.powerup_system._create_airstrike_effect(row, col, self.board)
            
            # Schedule destruction
            current_time = pygame.time.get_ticks()
            self.powerup_system.animations.append({
                "type": "delayed_destruction",
                "row": row,
                "col": col,
                "start_time": current_time + 900,
                "duration": 1,
                "board": self.board
            })
            
        elif action["type"] == "paratroopers":
            # AI drops paratroopers
            for target in action["targets"]:
                row, col = target
                self.powerup_system._create_paratrooper_effect(row, col, self.board)
                
                # Schedule pawn placement
                current_time = pygame.time.get_ticks()
                self.powerup_system.animations.append({
                    "type": "delayed_pawn_placement",
                    "row": row,
                    "col": col,
                    "pawn": "bP",  # Black pawn
                    "start_time": current_time + 1500,
                    "duration": 1,
                    "board": self.board
                })
                
        elif action["type"] == "chopper" and action.get("confirm"):
            # AI uses chopper gunner
            # For now, we'll just destroy all white pieces (except king)
            # In a full implementation, you might want a different AI chopper mode
            for row in range(8):
                for col in range(8):
                    piece = self.board.get_piece(row, col)
                    if piece and piece[0] == 'w' and piece[1] != 'K':
                        if not self.powerup_system.is_piece_shielded(row, col):
                            self.board.set_piece(row, col, "")
                            
            # Add explosion effects
            current_time = pygame.time.get_ticks()
            self.powerup_system.start_screen_shake(20, 1000)
            
        # Play sound effect
        if 'capture' in self.assets.sounds:
            self.assets.sounds['capture'].play()
            
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        
        # Update dimensions
        from config import update_screen_dimensions
        update_screen_dimensions(self.fullscreen, self.screen_info)
        
        # Recreate screen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
            
        # Update renderer with new screen
        self.renderer.screen = self.screen
        self.renderer.update_scale(config.SCALE)
        self.powerup_renderer.screen = self.screen
        self.powerup_renderer.update_scale(config.SCALE)
        
        # Update board scaling
        self.board.update_scale(config.SCALE)
        
        # Update chopper mode if it exists
        if self.chopper_mode:
            self.chopper_mode.screen = self.screen
        
        # IMPORTANT: Update UI positions AFTER everything else
        # This ensures we use the correct config values
        self.update_ui_positions()
        
    def handle_events(self):
        """Handle all events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                
                # Handle chopper mode mouse movement
                if self.chopper_mode and self.chopper_mode.active:
                    self.chopper_mode.handle_mouse(event.pos)
                # Handle volume slider dragging
                elif self.dragging_music_slider:
                    self.update_music_volume_from_mouse(event.pos)
                elif self.dragging_sfx_slider:
                    self.update_sfx_volume_from_mouse(event.pos)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Handle chopper mode clicks
                    if self.chopper_mode and self.chopper_mode.active:
                        self.chopper_mode.handle_click(event.pos)
                    else:
                        # Check music slider first
                        music_knob_x = self.music_slider_rect.x + int(self.music_volume * self.music_slider_rect.width)
                        music_knob_rect = pygame.Rect(music_knob_x - self.volume_knob_radius, 
                                              self.music_slider_rect.centery - self.volume_knob_radius,
                                              self.volume_knob_radius * 2, self.volume_knob_radius * 2)
                        
                        # Check SFX slider
                        sfx_knob_x = self.sfx_slider_rect.x + int(self.sfx_volume * self.sfx_slider_rect.width)
                        sfx_knob_rect = pygame.Rect(sfx_knob_x - self.volume_knob_radius, 
                                              self.sfx_slider_rect.centery - self.volume_knob_radius,
                                              self.volume_knob_radius * 2, self.volume_knob_radius * 2)
                        
                        if music_knob_rect.collidepoint(event.pos) or self.music_slider_rect.collidepoint(event.pos):
                            self.dragging_music_slider = True
                            self.update_music_volume_from_mouse(event.pos)
                        elif sfx_knob_rect.collidepoint(event.pos) or self.sfx_slider_rect.collidepoint(event.pos):
                            self.dragging_sfx_slider = True
                            self.update_sfx_volume_from_mouse(event.pos)
                        else:
                            self.handle_click(event.pos)
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left release
                    if self.chopper_mode and self.chopper_mode.active:
                        self.chopper_mode.handle_release()
                    elif self.dragging_music_slider:
                        self.dragging_music_slider = False
                    elif self.dragging_sfx_slider:
                        self.dragging_sfx_slider = False
                    else:
                        self.handle_release(event.pos)
                    
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
                
    def update_music_volume_from_mouse(self, mouse_pos):
        """Update music volume based on mouse position."""
        # Calculate volume from mouse x position relative to slider
        rel_x = mouse_pos[0] - self.music_slider_rect.x
        self.music_volume = max(0, min(1, rel_x / self.music_slider_rect.width))
        pygame.mixer.music.set_volume(self.music_volume)
        
    def update_sfx_volume_from_mouse(self, mouse_pos):
        """Update SFX volume based on mouse position."""
        # Calculate volume from mouse x position relative to slider
        rel_x = mouse_pos[0] - self.sfx_slider_rect.x
        self.sfx_volume = max(0, min(1, rel_x / self.sfx_slider_rect.width))
        self.update_sfx_volumes()
        
    def update_sfx_volumes(self):
        """Update volume for all sound effects."""
        # Update all loaded sound effects
        if 'capture' in self.assets.sounds:
            self.assets.sounds['capture'].set_volume(self.sfx_volume * 0.7)  # Capture sound at 70% of SFX volume
        if 'bomb' in self.assets.sounds:
            self.assets.sounds['bomb'].set_volume(self.sfx_volume * 0.8)  # Bomb sound at 80% of SFX volume
        if 'minigun' in self.assets.sounds:
            self.assets.sounds['minigun'].set_volume(self.sfx_volume * 0.6)  # Minigun at 60% of SFX volume
        if 'helicopter' in self.assets.sounds:
            self.assets.sounds['helicopter'].set_volume(self.sfx_volume * 0.5)  # Helicopter at 50% of SFX volume
        if 'helicopter_blade' in self.assets.sounds:
            self.assets.sounds['helicopter_blade'].set_volume(self.sfx_volume * 0.8)  # Helicopter blade at 80% of SFX volume
                
    def handle_click(self, pos):
        """Handle mouse click."""
        # Don't process other clicks during fade
        if self.fade_active:
            return
            
        if self.current_screen == config.SCREEN_START:
            if self.play_button.collidepoint(pos):
                self.start_fade(config.SCREEN_START, config.SCREEN_DIFFICULTY)
            elif self.beta_button.collidepoint(pos):
                self.start_fade(config.SCREEN_START, config.SCREEN_BETA)
            elif self.credits_button.collidepoint(pos):
                self.start_fade(config.SCREEN_START, config.SCREEN_CREDITS)
                
        elif self.current_screen == config.SCREEN_ARMS_DEALER:
            # Check purchase buttons
            for powerup_key, button_rect in self.shop_buttons.items():
                if button_rect.collidepoint(pos):
                    progress = config.load_progress()
                    unlocked = progress.get("unlocked_powerups", ["shield"])
                    
                    if powerup_key not in unlocked:
                        price = self.powerup_system.powerup_prices[powerup_key]
                        if config.spend_money(price):
                            config.unlock_powerup(powerup_key)
                            print(f"Purchased {powerup_key}!")
                        else:
                            print("Not enough money!")
            
            # Click on Tariq to cycle dialogue
            if hasattr(self.renderer, 'tariq_rect') and self.renderer.tariq_rect.collidepoint(pos):
                self.tariq_dialogue_index = (self.tariq_dialogue_index + 1) % len(self.tariq_dialogues)
            
            # Back button
            if self.back_button.collidepoint(pos):
                self.start_fade(config.SCREEN_ARMS_DEALER, config.SCREEN_GAME)
                
        elif self.current_screen == config.SCREEN_DIFFICULTY:
            # Load progress to check unlocked difficulties
            progress = config.load_progress()
            unlocked = progress.get("unlocked_difficulties", ["easy"])
            
            # Check difficulty buttons
            for difficulty, button in self.difficulty_buttons.items():
                if button.collidepoint(pos) and difficulty in unlocked:
                    self.selected_difficulty = difficulty
                    self.ai = ChessAI(difficulty)
                    self.start_fade(config.SCREEN_DIFFICULTY, config.SCREEN_GAME)
                    return
                    
            # Back button
            if self.back_button.collidepoint(pos):
                self.start_fade(config.SCREEN_DIFFICULTY, config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_CREDITS:
            if self.back_button.collidepoint(pos):
                self.start_fade(config.SCREEN_CREDITS, config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_BETA:
            if self.back_button.collidepoint(pos):
                self.start_fade(config.SCREEN_BETA, config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_GAME:
            # Check Arms Dealer button
            if self.arms_dealer_game_button and self.arms_dealer_game_button.collidepoint(pos):
                self.start_fade(config.SCREEN_GAME, config.SCREEN_ARMS_DEALER)
                return
                
            # Check powerup menu buttons first
            if self.board.current_turn == "white":  # Only player can use powerups
                for powerup_key, button_rect in self.powerup_system.button_rects.items():
                    if button_rect.collidepoint(pos):
                        if self.powerup_system.activate_powerup("white", powerup_key):
                            return
                            
            # Handle active powerup clicks
            if self.powerup_system.active_powerup:
                if self.powerup_system.handle_click(pos, self.board):
                    # Powerup was used, play sound effect
                    if 'capture' in self.assets.sounds:
                        self.assets.sounds['capture'].play()
                    return
                    
            # Only allow player moves during white's turn
            if self.board.current_turn != "white":
                return
                
            # Check promotion menu
            if self.board.promoting:
                for rect, piece_type in self.promotion_rects:
                    if rect.collidepoint(pos):
                        self.board.promote_pawn(piece_type)
                        if 'capture' in self.assets.sounds:
                            self.assets.sounds['capture'].play()
                        return
                        
            # Normal game clicks
            if not self.board.animating and not self.board.promoting:
                row, col = self.board.get_square_from_pos(pos)
                if row >= 0 and col >= 0 and self.board.is_valid_selection(row, col):
                    self.board.selected_piece = (row, col)
                    self.board.valid_moves = self.board.get_valid_moves(row, col)
                    self.board.dragging = True
                    self.board.drag_piece = self.board.get_piece(row, col)
                    self.board.drag_start = (row, col)
                    
    def handle_release(self, pos):
        """Handle mouse release."""
        if self.current_screen != config.SCREEN_GAME or not self.board.dragging:
            return
            
        # Only allow player moves during white's turn
        if self.board.current_turn != "white":
            self.board.dragging = False
            self.board.drag_piece = None
            self.board.drag_start = None
            return
            
        row, col = self.board.get_square_from_pos(pos)
        
        if (row, col) in self.board.valid_moves:
            # Make move
            from_row, from_col = self.board.selected_piece
            self.board.start_move(from_row, from_col, row, col)
            self.board.selected_piece = None
            self.board.valid_moves = []
        else:
            # Check if selecting new piece
            if row >= 0 and col >= 0 and self.board.is_valid_selection(row, col):
                self.board.selected_piece = (row, col)
                self.board.valid_moves = self.board.get_valid_moves(row, col)
            else:
                self.board.selected_piece = None
                self.board.valid_moves = []
                
        self.board.dragging = False
        self.board.drag_piece = None
        self.board.drag_start = None
        
    def handle_key(self, key):
        """Handle keyboard input."""
        # F key toggles fullscreen on any screen
        if key == pygame.K_f:
            self.toggle_fullscreen()
            return
            
        # CHEAT CODE: Press 'T' for TEST MODE - unlocks everything and gives money
        if key == pygame.K_t:
            # Check if SHIFT is also held for the cheat
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                print("CHEAT CODE ACTIVATED! TEST MODE ENABLED!")
                
                # Load progress
                progress = config.load_progress()
                
                # Unlock all difficulties
                progress["unlocked_difficulties"] = ["easy", "medium", "hard", "very_hard"]
                
                # Unlock all powerups
                progress["unlocked_powerups"] = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
                
                # Give lots of money
                progress["money"] = 99999
                
                # Save progress
                config.save_progress(progress)
                
                # Also give current player lots of points if in game
                if self.current_screen == config.SCREEN_GAME:
                    self.powerup_system.points["white"] = 999
                    self.powerup_system.points["black"] = 999
                    
                print("✓ All difficulties unlocked!")
                print("✓ All powerups unlocked!")
                print("✓ Money set to $99,999!")
                print("✓ Both players have 999 powerup points!")
                
                # Visual feedback - flash the screen green
                flash_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
                flash_surface.fill((0, 255, 0))
                flash_surface.set_alpha(100)
                self.screen.blit(flash_surface, (0, 0))
                pygame.display.flip()
                pygame.time.wait(200)
                
                return
            
        if self.current_screen == config.SCREEN_GAME:
            if key == pygame.K_ESCAPE:
                # Exit chopper mode if active
                if self.chopper_mode and self.chopper_mode.active:
                    self.chopper_mode.stop()
                    self.chopper_mode = None
                # Cancel active powerup
                elif self.powerup_system.active_powerup:
                    self.powerup_system.cancel_powerup()
                # If in fullscreen, exit fullscreen first
                elif self.fullscreen:
                    self.toggle_fullscreen()
                else:
                    self.start_fade(config.SCREEN_GAME, config.SCREEN_START)
            elif key == pygame.K_r and self.board.game_over:
                self.board.reset()
                self.powerup_system = PowerupSystem()  # Reset powerup system
                self.powerup_system.assets = self.assets  # Pass assets reference
                self.board.set_powerup_system(self.powerup_system)
                self.powerup_renderer.powerup_system = self.powerup_system
                if hasattr(self, 'victory_processed'):
                    delattr(self, 'victory_processed')  # Reset victory flag
                self.victory_reward = 0  # Reset reward display
                # Clear chopper mode
                self.chopper_mode = None
        elif self.current_screen == config.SCREEN_DIFFICULTY:
            if key == pygame.K_ESCAPE:
                self.start_fade(config.SCREEN_DIFFICULTY, config.SCREEN_START)
        elif self.current_screen in [config.SCREEN_START, config.SCREEN_CREDITS, config.SCREEN_ARMS_DEALER, config.SCREEN_BETA]:
            if key == pygame.K_ESCAPE and self.fullscreen:
                self.toggle_fullscreen()
                
    def start_fade(self, from_screen, to_screen):
        """Start fade transition."""
        self.fade_active = True
        self.fade_start = pygame.time.get_ticks()
        self.fade_from = from_screen
        self.fade_to = to_screen
        
    def update(self):
        """Update game logic."""
        current_time = pygame.time.get_ticks()
        
        # Update fade
        if self.fade_active:
            if current_time - self.fade_start >= config.FADE_DURATION:
                self.fade_active = False
                self.current_screen = self.fade_to
                if self.fade_to == config.SCREEN_GAME:
                    self.board.reset()
                    self.powerup_system = PowerupSystem()  # Reset powerup system
                    self.powerup_system.assets = self.assets  # Pass assets reference
                    self.board.set_powerup_system(self.powerup_system)
                    self.powerup_renderer.powerup_system = self.powerup_system
                    
        # Check if chopper gunner was requested
        if self.powerup_system.chopper_gunner_requested:
            self.powerup_system.chopper_gunner_requested = False
            # Create and start chopper mode
            self.chopper_mode = ChopperGunnerMode(self.screen, self.assets, self.board)
            self.chopper_mode.start()
            
        # Update chopper mode if active
        if self.chopper_mode and self.chopper_mode.active:
            self.chopper_mode.update()
            # Don't update other game logic while in chopper mode
            return
                    
        # Update board
        if self.current_screen == config.SCREEN_GAME:
            # Update powerup effects
            self.powerup_system.update_effects(current_time)
            
            # Check animation complete
            if self.board.animating:
                if current_time - self.board.animation_start >= config.MOVE_ANIMATION_DURATION:
                    captured = self.board.complete_move()
                    # Play capture sound immediately when capture happens
                    if captured and 'capture' in self.assets.sounds:
                        try:
                            self.assets.sounds['capture'].play()
                        except Exception as e:
                            print(f"Error playing capture sound: {e}")
                        
            # AI turn
            if self.board.current_turn == "black" and not self.board.game_over and not self.board.animating:
                if self.ai:
                    # Start thinking if not already
                    if not self.ai.is_thinking() and self.ai.start_thinking is None:
                        self.ai.start_turn()
                    
                    # Make move when done thinking
                    if not self.ai.is_thinking():
                        # First check if AI wants to use a powerup
                        ai_powerup = self.ai.should_use_powerup(self.board, self.powerup_system)
                        if ai_powerup:
                            powerup_action = self.ai.execute_powerup(self.board, self.powerup_system, ai_powerup)
                            if powerup_action:
                                self._handle_ai_powerup(ai_powerup, powerup_action)
                                self.ai.start_thinking = None
                                return  # Skip normal move if powerup was used
                        
                        # Otherwise make a normal move
                        ai_move = self.ai.get_move(self.board)
                        if ai_move:
                            from_pos, to_pos = ai_move
                            self.board.start_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                        self.ai.start_thinking = None
                        
            # Check for player victory and unlock next difficulty
            if self.board.game_over and self.board.winner == "white" and self.selected_difficulty:
                if not hasattr(self, 'victory_processed'):
                    self.victory_processed = True
                    
                    # Award money for victory
                    reward = config.VICTORY_REWARDS[self.selected_difficulty]
                    new_total = config.add_money(reward)
                    self.victory_reward = reward  # Store for display
                    print(f"Victory! Earned ${reward}. Total: ${new_total}")
                    
                    # Unlock next difficulty
                    next_difficulty = config.unlock_next_difficulty(self.selected_difficulty)
                    if next_difficulty:
                        print(f"Congratulations! You've unlocked {config.AI_DIFFICULTY_NAMES[next_difficulty]} difficulty!")
                    
    def draw(self):
        """Draw everything."""
        # Handle chopper mode drawing separately
        if self.chopper_mode and self.chopper_mode.active:
            self.chopper_mode.draw()
            pygame.display.flip()
            return
            
        # Get screen shake offset
        shake_x, shake_y = self.powerup_system.get_screen_shake_offset()
        
        # Create a temporary surface for the game content
        if shake_x != 0 or shake_y != 0:
            game_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
            original_screen = self.screen
            self.screen = game_surface
            self.renderer.screen = game_surface
            self.powerup_renderer.screen = game_surface
        
        # Don't fill the screen here - let each screen handle its own background
        
        if self.fade_active:
            # Draw fade transition
            progress = min(1.0, (pygame.time.get_ticks() - self.fade_start) / config.FADE_DURATION)
            
            if progress < 0.5:
                # Fade out
                self.draw_screen(self.fade_from)
                alpha = int(255 * (progress * 2))
                fade_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
                fade_surface.fill(config.BLACK)
                fade_surface.set_alpha(alpha)
                self.screen.blit(fade_surface, (0, 0))
            else:
                # Fade in
                self.draw_screen(self.fade_to)
                alpha = int(255 * (2 - progress * 2))
                fade_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
                fade_surface.fill(config.BLACK)
                fade_surface.set_alpha(alpha)
                self.screen.blit(fade_surface, (0, 0))
        else:
            self.draw_screen(self.current_screen)
            
        # Apply screen shake if active
        if shake_x != 0 or shake_y != 0:
            # Restore original screen
            self.screen = original_screen
            self.renderer.screen = original_screen
            self.powerup_renderer.screen = original_screen
            
            # Clear the screen with black
            self.screen.fill(config.BLACK)
            
            # Blit the game surface with shake offset
            self.screen.blit(game_surface, (shake_x, shake_y))
            
    def draw_screen(self, screen_type):
        """Draw specific screen."""
        if screen_type == config.SCREEN_START:
            buttons = {
                'play': self.play_button,
                'beta': self.beta_button, 
                'credits': self.credits_button
            }
            self.renderer.draw_menu(config.SCREEN_START, buttons, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == config.SCREEN_ARMS_DEALER:
            self.renderer.draw_arms_dealer(self.powerup_system, self.shop_buttons, 
                                          self.back_button, self.mouse_pos, 
                                          self.tariq_dialogue_index, self.tariq_dialogues)
            self.draw_volume_sliders()
            
        elif screen_type == config.SCREEN_DIFFICULTY:
            self.renderer.draw_difficulty_menu(self.difficulty_buttons, self.back_button, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == config.SCREEN_CREDITS:
            buttons = {'back': self.back_button}
            self.renderer.draw_menu(config.SCREEN_CREDITS, buttons, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == config.SCREEN_BETA:
            buttons = {'back': self.back_button}
            self.renderer.draw_menu(config.SCREEN_BETA, buttons, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == config.SCREEN_GAME:
            # Background
            self.renderer.draw_parallax_background(1.0)
            
            # Board and pieces
            self.renderer.draw_board()
            self.renderer.draw_pieces(self.board, self.mouse_pos)
            
            # Game elements
            if not self.board.game_over:
                self.renderer.draw_highlights(self.board)
                self.renderer.draw_check_indicator(self.board)
                
            # UI with AI info (modified to not include mute button)
            self.renderer.draw_ui(self.board, None, False, self.mouse_pos, 
                                 self.ai, self.selected_difficulty)
            self.draw_volume_sliders()
            
            # Add Arms Dealer button in game
            self.draw_arms_dealer_button()
            
            # Powerup menu
            self.powerup_renderer.draw_powerup_menu(self.board, self.mouse_pos)
            
            # Powerup effects
            self.powerup_renderer.draw_effects(self.board)
            
            # Powerup targeting
            self.powerup_renderer.draw_powerup_targeting(self.board, self.mouse_pos)
            
            # Overlays
            if self.board.promoting:
                self.promotion_rects = self.renderer.draw_promotion_menu(self.board, self.mouse_pos)
            
            # Pass selected difficulty and victory reward to renderer
            if self.board.game_over and self.selected_difficulty:
                if not hasattr(self.board, 'selected_difficulty'):
                    self.board.selected_difficulty = self.selected_difficulty
                if not hasattr(self.board, 'victory_reward'):
                    self.board.victory_reward = self.victory_reward
            self.renderer.draw_game_over(self.board)
            
        # Draw fullscreen indicator (small 'F' in corner)
        if self.fullscreen:
            text = self.renderer.pixel_fonts['tiny'].render("Press F to exit fullscreen", True, (150, 150, 150))
            self.screen.blit(text, (10, config.HEIGHT - 20))
        else:
            text = self.renderer.pixel_fonts['tiny'].render("Press F for fullscreen", True, (150, 150, 150))
            self.screen.blit(text, (10, config.HEIGHT - 20))
            
    def draw_volume_sliders(self):
        """Draw both volume sliders."""
        # MUSIC SLIDER
        # Background of slider track
        pygame.draw.rect(self.screen, (60, 60, 60), self.music_slider_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), self.music_slider_rect, 2)
        
        # Fill portion representing current volume
        fill_width = int(self.music_volume * self.music_slider_rect.width)
        fill_rect = pygame.Rect(self.music_slider_rect.x, self.music_slider_rect.y,
                               fill_width, self.music_slider_rect.height)
        pygame.draw.rect(self.screen, (100, 200, 100), fill_rect)
        
        # Draw the slider knob
        knob_x = self.music_slider_rect.x + fill_width
        knob_y = self.music_slider_rect.centery
        
        # Knob hover effect
        knob_rect = pygame.Rect(knob_x - self.volume_knob_radius, 
                               knob_y - self.volume_knob_radius,
                               self.volume_knob_radius * 2, self.volume_knob_radius * 2)
        knob_color = (200, 200, 200) if knob_rect.collidepoint(self.mouse_pos) or self.dragging_music_slider else (150, 150, 150)
        
        pygame.draw.circle(self.screen, knob_color, (knob_x, knob_y), self.volume_knob_radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (knob_x, knob_y), self.volume_knob_radius, 2)
        
        # Music label
        music_text = f"Music: {int(self.music_volume * 100)}%"
        text_surface = self.renderer.pixel_fonts['tiny'].render(music_text, True, config.WHITE)
        text_rect = text_surface.get_rect(midright=(self.music_slider_rect.x - 10, self.music_slider_rect.centery))
        self.screen.blit(text_surface, text_rect)
        
        # SFX SLIDER
        # Background of slider track
        pygame.draw.rect(self.screen, (60, 60, 60), self.sfx_slider_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), self.sfx_slider_rect, 2)
        
        # Fill portion representing current volume
        sfx_fill_width = int(self.sfx_volume * self.sfx_slider_rect.width)
        sfx_fill_rect = pygame.Rect(self.sfx_slider_rect.x, self.sfx_slider_rect.y,
                                   sfx_fill_width, self.sfx_slider_rect.height)
        pygame.draw.rect(self.screen, (100, 150, 200), sfx_fill_rect)
        
        # Draw the slider knob
        sfx_knob_x = self.sfx_slider_rect.x + sfx_fill_width
        sfx_knob_y = self.sfx_slider_rect.centery
        
        # Knob hover effect
        sfx_knob_rect = pygame.Rect(sfx_knob_x - self.volume_knob_radius, 
                                   sfx_knob_y - self.volume_knob_radius,
                                   self.volume_knob_radius * 2, self.volume_knob_radius * 2)
        sfx_knob_color = (200, 200, 200) if sfx_knob_rect.collidepoint(self.mouse_pos) or self.dragging_sfx_slider else (150, 150, 150)
        
        pygame.draw.circle(self.screen, sfx_knob_color, (sfx_knob_x, sfx_knob_y), self.volume_knob_radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (sfx_knob_x, sfx_knob_y), self.volume_knob_radius, 2)
        
        # SFX label
        sfx_text = f"SFX: {int(self.sfx_volume * 100)}%"
        text_surface = self.renderer.pixel_fonts['tiny'].render(sfx_text, True, config.WHITE)
        text_rect = text_surface.get_rect(midright=(self.sfx_slider_rect.x - 10, self.sfx_slider_rect.centery))
        self.screen.blit(text_surface, text_rect)
            
    def draw_arms_dealer_button(self):
        """Draw the Arms Dealer button in the game screen."""
        # Position it in the middle left side of the screen
        button_width = int(150 * config.SCALE)
        button_height = int(40 * config.SCALE)
        button_x = int(20 * config.SCALE)
        button_y = config.HEIGHT // 2 - button_height // 2  # Center vertically
        
        self.arms_dealer_game_button = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # Check if hovering
        is_hover = self.arms_dealer_game_button.collidepoint(self.mouse_pos)
        
        # Draw button
        button_color = (150, 100, 50) if is_hover else (120, 80, 40)
        pygame.draw.rect(self.screen, button_color, self.arms_dealer_game_button, border_radius=10)
        pygame.draw.rect(self.screen, (200, 150, 100), self.arms_dealer_game_button, 3, border_radius=10)
        
        # Draw text
        text = self.renderer.pixel_fonts['small'].render("VISIT ARMS DEALER", True, config.WHITE)
        text_rect = text.get_rect(center=self.arms_dealer_game_button.center)
        self.screen.blit(text, text_rect)
            
    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)