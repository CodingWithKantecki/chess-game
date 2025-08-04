"""
Main Game Class - Enhanced with Tutorial, Victory Screen, and Story Mode
"""

import pygame
import os
import config
from assets import AssetManager
from board import ChessBoard
from graphics import Renderer
from ai import ChessAI
from powerups import PowerupSystem
from powerup_renderer import PowerupRenderer
from chopper_gunner import ChopperGunnerMode
from cinematics import IntroScreen, PostIntroCutscene
from story_mode import StoryMode
from tutorial_system import TutorialSystem

class ChessGame:
    def __init__(self):
        # Get screen info before creating display
        self.screen_info = pygame.display.Info()
        
        # Create screen (windowed mode only)
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.DOUBLEBUF)
        pygame.display.set_caption("Checkmate Protocol - BETA")
        self.clock = pygame.time.Clock()
        
        # Load assets
        self.assets = AssetManager()
        self.assets.load_all()
        
        # Create components
        self.board = ChessBoard()
        self.renderer = Renderer(self.screen, self.assets)
        self.ai = None  # Will be created when difficulty is selected
        
        # Intro screen
        self.intro_screen = IntroScreen(self.screen, self.renderer)
        self.intro_complete = False
        self.intro_screen.start()  # Start the intro immediately
        
        # Post-intro cutscene
        self.post_intro_cutscene = PostIntroCutscene(self.screen, self.assets, self.renderer)
        self.post_intro_complete = False
        
        # Cache fade surface for performance
        self._fade_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
        self._fade_surface.fill(config.BLACK)
        
        # Cache game surface for screen shake
        self._shake_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
        
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
        
        # NEW: Story mode
        self.story_mode = StoryMode()
        self.current_story_battle = None
        
        # Story Tutorial System
        self.tutorial = TutorialSystem(self, self.board, self.powerup_system)
        self.in_tutorial_battle = False
        
        
        # Game state - start with intro
        self.running = True
        self.current_screen = "intro"  # Start with intro screen
        self.mouse_pos = (0, 0)
        self.selected_difficulty = None
        
        # NEW: Game mode
        self.current_mode = None  # "classic", "story", "survival", etc.
        self.mode_buttons = {}
        
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
        
        # Tutorial page state
        self.tutorial_page = 0
        self.tutorial_pages = [
            {
                "title": "WELCOME TO CHECKMATE PROTOCOL",
                "content": [
                    "This is not your ordinary chess game!",
                    "",
                    "In addition to standard chess rules, you can",
                    "earn points by capturing enemy pieces and",
                    "spend them on powerful abilities.",
                    "",
                    "Defeat increasingly difficult AI opponents",
                    "to unlock new challenges and earn money",
                    "for purchasing more devastating powerups!"
                ]
            },
            {
                "title": "HOW TO PLAY CHESS",
                "content": [
                    "MOVING PIECES:",
                    "• Click a piece to select it",
                    "• Valid moves will be highlighted in green",
                    "• Click a highlighted square to move there",
                    "• Capture enemy pieces by moving to their square",
                    "",
                    "WINNING THE GAME:",
                    "• Checkmate the enemy King to win",
                    "• Protect your King at all costs!"
                ]
            },
            {
                "title": "HOW PIECES MOVE - PART 1",
                "content": [
                    "PAWN: Moves forward 1 square (2 on first move)",
                    "       Captures diagonally forward",
                    "",
                    "ROOK: Moves any distance horizontally or vertically",
                    "",
                    "BISHOP: Moves any distance diagonally",
                    "",
                    "KNIGHT: Moves in an 'L' shape (2+1 squares)",
                    "        Can jump over other pieces"
                ]
            },
            {
                "title": "HOW PIECES MOVE - PART 2",
                "content": [
                    "QUEEN: Moves like Rook + Bishop combined",
                    "       Most powerful piece!",
                    "",
                    "KING: Moves 1 square in any direction",
                    "      Must be protected!",
                    "",
                    "SPECIAL MOVES:",
                    "• Castling: King + Rook special move",
                    "• En Passant: Special pawn capture",
                    "• Promotion: Pawn reaches end = Queen"
                ]
            },
            {
                "title": "EARNING POWERUP POINTS",
                "content": [
                    "Capture enemy pieces to earn points:",
                    "",
                    "• Pawn = 1 point",
                    "• Knight/Bishop = 3 points",
                    "• Rook = 5 points",
                    "• Queen = 9 points",
                    "",
                    "Your points appear in the powerup menu",
                    "on the right side of the game board.",
                    "",
                    "Click powerups to activate them!"
                ]
            },
            {
                "title": "POWERUPS EXPLAINED",
                "content": [
                    "SHIELD (5 pts):",
                    "• Protects a piece for 3 turns",
                    "• Shielded pieces cannot be captured",
                    "",
                    "GUN (7 pts):",
                    "• Click shooter, then click target",
                    "• Must have clear line of sight",
                    "• One-shot kill on any piece"
                ]
            },
            {
                "title": "MORE POWERUPS",
                "content": [
                    "AIRSTRIKE (10 pts):",
                    "• Click to target a 3x3 area",
                    "• Destroys all pieces in the zone",
                    "• Even your own pieces!",
                    "",
                    "PARATROOPERS (10 pts):",
                    "• Drop 3 pawns on empty squares",
                    "• Click 3 times to place them",
                    "• Great for surprise attacks!"
                ]
            },
            {
                "title": "ULTIMATE POWERUP",
                "content": [
                    "CHOPPER GUNNER (25 pts):",
                    "• Enter helicopter minigame",
                    "• Use mouse to aim",
                    "• Left click to fire minigun",
                    "• Destroy pieces to damage the board",
                    "",
                    "This is the most devastating powerup!",
                    "Save your points for maximum destruction!"
                ]
            },
            {
                "title": "GAME PROGRESSION",
                "content": [
                    "1. Start with EASY difficulty",
                    "2. Win to unlock harder difficulties",
                    "3. Earn money for each victory:",
                    "   • Easy: $100",
                    "   • Medium: $200", 
                    "   • Hard: $400",
                    "   • Very Hard: $800",
                    "",
                    "4. Visit Arms Dealer to buy powerups",
                    "5. Use 'R' key to restart if needed"
                ]
            },
            {
                "title": "TIPS FOR SUCCESS",
                "content": [
                    "• Control the center of the board",
                    "• Develop knights before bishops",
                    "• Castle early for King safety",
                    "• Don't move the same piece twice early",
                    "",
                    "• Save powerups for critical moments",
                    "• Combine powerups for combos",
                    "• Shield your important pieces",
                    "",
                    "Good luck, Commander!"
                ]
            }
        ]
        
        # Story mode UI - Initialize these dictionaries
        self.story_chapter_buttons = {}
        self.story_battle_buttons = {}
        self.story_back_button = None  # Will be initialized in update_ui_positions()
        
        # UI elements
        self.update_ui_positions()
        
        # Volume control - load from saved settings
        volume_settings = config.get_volume_settings()
        self.music_volume = volume_settings["music_volume"]
        self.sfx_volume = volume_settings["sfx_volume"]
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
        
        # Store game state when entering shop mid-game
        self.stored_game_state = None
        self.returning_from_shop = False
        
        # Track last capture
        self.last_captured_piece = None
        
        # Story dialogue state
        self.current_dialogue_index = 0
        self.dialogue_complete = False
        
        # Music fade state
        self.music_fade_active = False
        self.music_fade_start_time = 0
        self.music_fade_duration = 1000  # 1 second fade
        self.music_fade_out = False  # True for fade out, False for fade in
        self.music_fade_target_volume = 0
        self.music_fade_start_volume = 0
        self.switching_to_tariq = False
        self.current_music = "main"  # "main" or "tariq"
        
        # Music position tracking
        self.main_music_position = 0
        self.tariq_music_position = 0
        self.music_start_time = pygame.time.get_ticks()
        
        # Start music immediately when game loads
        pygame.mixer.music.play(-1)
        
    def update_ui_positions(self):
        """Update UI element positions."""
        # Center coordinates
        center_x = config.WIDTH // 2
        center_y = config.HEIGHT // 2
        
        # Volume sliders - stacked vertically in top right
        slider_width = 140
        slider_height = 20
        slider_spacing = 35
        slider_x = config.WIDTH - 160
        
        # Music slider
        self.music_slider_rect = pygame.Rect(
            slider_x, 
            10, 
            slider_width, 
            slider_height
        )
        
        # SFX slider (below music)
        self.sfx_slider_rect = pygame.Rect(
            slider_x, 
            10 + slider_spacing, 
            slider_width, 
            slider_height
        )
        
        self.volume_knob_radius = 10
        
        # Menu buttons - centered (added tutorial button)
        button_spacing = 80
        self.play_button = pygame.Rect(
            center_x - 100, 
            center_y - 120, 
            200, 
            60
        )
        self.tutorial_button = pygame.Rect(
            center_x - 100, 
            center_y - 40, 
            200, 
            60
        )
        self.beta_button = pygame.Rect(
            center_x - 100, 
            center_y + 40, 
            200, 
            60
        )
        self.credits_button = pygame.Rect(
            center_x - 100, 
            center_y + 120, 
            200, 
            60
        )
        self.back_button = pygame.Rect(
            center_x - 100, 
            center_y + 250, 
            200, 
            50
        )
        
        # Tutorial navigation buttons
        self.prev_button = pygame.Rect(
            50,
            center_y + 200,
            120,
            50
        )
        self.next_button = pygame.Rect(
            config.WIDTH - 170,
            center_y + 200,
            120,
            50
        )
        
        # Difficulty buttons
        self.difficulty_buttons = {}
        button_height = 60
        button_spacing = 20
        total_height = len(config.AI_DIFFICULTIES) * button_height + (len(config.AI_DIFFICULTIES) - 1) * button_spacing
        start_y = center_y - total_height // 2
        
        for i, difficulty in enumerate(config.AI_DIFFICULTIES):
            y = start_y + i * (button_height + button_spacing)
            self.difficulty_buttons[difficulty] = pygame.Rect(
                center_x - 150, 
                y, 
                300, 
                button_height
            )
            
        # Story mode back button
        self.story_back_button = pygame.Rect(
            center_x - 100, 
            config.HEIGHT - 100, 
            200, 
            50
        )
            
    def store_game_state(self):
        """Store the current game state before entering shop."""
        self.stored_game_state = {
            "board": [row[:] for row in self.board.board],  # Deep copy of board
            "current_turn": self.board.current_turn,
            "captured_pieces": {
                "white": self.board.captured_pieces["white"][:],
                "black": self.board.captured_pieces["black"][:]
            },
            "powerup_points": {
                "white": self.powerup_system.points["white"],
                "black": self.powerup_system.points["black"]
            },
            "shielded_pieces": dict(self.powerup_system.shielded_pieces),
            "game_over": self.board.game_over,
            "winner": self.board.winner,
            "ai": self.ai,
            "selected_difficulty": self.selected_difficulty,
            "current_mode": self.current_mode,
            "current_story_battle": self.current_story_battle,
            # Store tutorial state
            "in_tutorial_battle": self.in_tutorial_battle,
            "tutorial_state": {
                "active": self.tutorial.active if hasattr(self.tutorial, 'active') else False,
                "current_step": self.tutorial.current_step if hasattr(self.tutorial, 'current_step') else 0,
                "steps_completed": self.tutorial.steps_completed[:] if hasattr(self.tutorial, 'steps_completed') else [],
                "waiting_for": self.tutorial.waiting_for if hasattr(self.tutorial, 'waiting_for') else None
            }
        }
        
    def restore_game_state(self):
        """Restore the game state after returning from shop."""
        if self.stored_game_state:
            # Restore board state
            self.board.board = [row[:] for row in self.stored_game_state["board"]]
            self.board.current_turn = self.stored_game_state["current_turn"]
            self.board.captured_pieces = {
                "white": self.stored_game_state["captured_pieces"]["white"][:],
                "black": self.stored_game_state["captured_pieces"]["black"][:]
            }
            self.board.game_over = self.stored_game_state["game_over"]
            self.board.winner = self.stored_game_state["winner"]
            
            # Restore powerup state
            self.powerup_system.points = dict(self.stored_game_state["powerup_points"])
            self.powerup_system.shielded_pieces = dict(self.stored_game_state["shielded_pieces"])
            
            # Special case: ensure tutorial has points
            if self.in_tutorial_battle and self.tutorial.active:
                if self.powerup_system.points["white"] < 100:
                    self.powerup_system.points["white"] = 999
                    pass
            
            # Restore AI and mode
            self.ai = self.stored_game_state["ai"]
            self.selected_difficulty = self.stored_game_state["selected_difficulty"]
            self.current_mode = self.stored_game_state["current_mode"]
            self.current_story_battle = self.stored_game_state["current_story_battle"]
            
            # Restore tutorial state
            if "in_tutorial_battle" in self.stored_game_state:
                self.in_tutorial_battle = self.stored_game_state["in_tutorial_battle"]
                
                # Restore tutorial system state - but NOT the current step if we're in tutorial
                # This prevents the tutorial from going backwards when returning from arms dealer
                if "tutorial_state" in self.stored_game_state:
                    tutorial_state = self.stored_game_state["tutorial_state"]
                    if hasattr(self.tutorial, 'active'):
                        self.tutorial.active = tutorial_state["active"]
                    # Don't restore current_step during active tutorial - it should have advanced
                    if not self.tutorial.active:
                        if hasattr(self.tutorial, 'current_step'):
                            self.tutorial.current_step = tutorial_state["current_step"]
                    if hasattr(self.tutorial, 'steps_completed'):
                        self.tutorial.steps_completed = tutorial_state["steps_completed"][:]
                    if hasattr(self.tutorial, 'waiting_for'):
                        self.tutorial.waiting_for = tutorial_state["waiting_for"]
            
            # Clear stored state
            self.stored_game_state = None
            
            # Clear any active animations or selections
            self.board.selected_piece = None
            self.board.valid_moves = []
            self.board.animating = False
            self.board.dragging = False
            self.board.promoting = False
            
    def _handle_ai_powerup(self, powerup_key, action):
        """Handle AI powerup usage."""
        # Deduct points
        self.powerup_system.points["black"] -= self.powerup_system.powerups[powerup_key]["cost"]
        
        if action["type"] == "shield":
            # AI shields a piece
            row, col = action["target"]
            # Create lightning strike animation first
            self.powerup_system._create_lightning_effect(row, col, self.board)
            self.powerup_system.shielded_pieces[(row, col)] = 3
            self.powerup_system._create_shield_effect(row, col, self.board, delay=500)
            
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
            for row in range(8):
                for col in range(8):
                    piece = self.board.get_piece(row, col)
                    if piece and piece[0] == 'w' and piece[1] != 'K':
                        if not self.powerup_system.is_piece_shielded(row, col):
                            self.board.set_piece(row, col, "")
                            
            # Add explosion effects
            current_time = pygame.time.get_ticks()
            self.powerup_system.start_screen_shake(20, 1000)
            
        # Play appropriate sound effect based on powerup type
        if action["type"] in ["gun", "airstrike", "chopper"]:
            # Destructive powerups use capture sound
            if 'capture' in self.assets.sounds:
                self.assets.sounds['capture'].play()
        elif action["type"] == "shield":
            # Shield uses click sound
            if 'click' in self.assets.sounds:
                self.assets.sounds['click'].play()
        # Paratroopers don't need a sound here as they have their own animation sounds
                
    def handle_events(self):
        """Handle all events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Handle tutorial timer events
            if event.type == pygame.USEREVENT + 1:
                if self.in_tutorial_battle and self.tutorial.active:
                    self.tutorial.handle_timer_event()
                    
            # Handle AI move completion timer
            if event.type == pygame.USEREVENT + 2:
                if self.in_tutorial_battle and self.tutorial.active:
                    self.tutorial.handle_ai_move_complete()
                
            # Handle intro screen events
            if self.current_screen == "intro":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        # Skip intro
                        self.intro_screen.skip()
                        if not self.fade_active:
                            self.start_fade("intro", "post_intro")
                            
            # Handle post-intro cutscene events
            if self.current_screen == "post_intro":
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    # Skip cutscene on any key or click
                    self.post_intro_cutscene.skip()
                    if not self.fade_active:
                        self.start_fade("post_intro", config.SCREEN_START)
                        
            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                
                # Handle chopper mode mouse movement
                if self.chopper_mode and self.chopper_mode.active:
                    self.chopper_mode.handle_mouse(event.pos)
                # Handle volume slider dragging
                elif self.dragging_music_slider:
                    self.update_music_volume_from_mouse(event.pos)
                elif self.dragging_sfx_slider:
                    self.update_sfx_volume_from_mouse(event.pos)
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
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
                    
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left release
                    if self.chopper_mode and self.chopper_mode.active:
                        self.chopper_mode.handle_release()
                    elif self.dragging_music_slider:
                        self.dragging_music_slider = False
                    elif self.dragging_sfx_slider:
                        self.dragging_sfx_slider = False
                    else:
                        self.handle_release(event.pos)
                    
            if event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
                
    def update_music_volume_from_mouse(self, mouse_pos):
        """Update music volume based on mouse position."""
        # Calculate volume from mouse x position relative to slider
        rel_x = mouse_pos[0] - self.music_slider_rect.x
        self.music_volume = max(0, min(1, rel_x / self.music_slider_rect.width))
        pygame.mixer.music.set_volume(self.music_volume)
        # Save volume settings
        config.save_volume_settings(self.music_volume, self.sfx_volume)
        
    def update_sfx_volume_from_mouse(self, mouse_pos):
        """Update SFX volume based on mouse position."""
        # Calculate volume from mouse x position relative to slider
        rel_x = mouse_pos[0] - self.sfx_slider_rect.x
        self.sfx_volume = max(0, min(1, rel_x / self.sfx_slider_rect.width))
        self.update_sfx_volumes()
        # Save volume settings
        config.save_volume_settings(self.music_volume, self.sfx_volume)
        
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
        if 'click' in self.assets.sounds:
            self.assets.sounds['click'].set_volume(self.sfx_volume * 0.5)  # Click at 50% of SFX volume
    
    def update_music_fade(self):
        """Update music fade in/out."""
        if not self.music_fade_active:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.music_fade_start_time
        
        if elapsed >= self.music_fade_duration:
            # Fade complete
            self.music_fade_active = False
            pygame.mixer.music.set_volume(self.music_fade_target_volume * self.music_volume)
            
            # If we were switching to tariq music, load and play it now
            if self.switching_to_tariq and self.music_fade_out:
                # Store current position of main music
                self.main_music_position = pygame.mixer.music.get_pos()
                if self.main_music_position == -1:  # Music not playing
                    self.main_music_position = 0
                else:
                    # Add elapsed time since music started
                    self.main_music_position += (pygame.time.get_ticks() - self.music_start_time)
                
                tariq_path = os.path.join(config.ASSETS_DIR, config.TARIQ_MUSIC_FILE)
                if os.path.exists(tariq_path):
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(tariq_path)
                    # Start from saved position or beginning
                    start_pos = self.tariq_music_position / 1000.0  # Convert to seconds
                    pygame.mixer.music.play(-1, start_pos)
                    self.current_music = "tariq"
                    self.music_start_time = pygame.time.get_ticks() - self.tariq_music_position
                    # Start fade in
                    self.start_music_fade(0, 1, 1000)
                    self.switching_to_tariq = False
            # If we were switching back to main music
            elif not self.switching_to_tariq and self.music_fade_out and self.current_music == "tariq":
                # Store current position of tariq music
                self.tariq_music_position = pygame.mixer.music.get_pos()
                if self.tariq_music_position == -1:  # Music not playing
                    self.tariq_music_position = 0
                else:
                    # Add elapsed time since music started
                    self.tariq_music_position += (pygame.time.get_ticks() - self.music_start_time)
                
                main_path = os.path.join(config.ASSETS_DIR, config.MUSIC_FILE)
                if os.path.exists(main_path):
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(main_path)
                    # Start from saved position or beginning
                    start_pos = self.main_music_position / 1000.0  # Convert to seconds
                    pygame.mixer.music.play(-1, start_pos)
                    self.current_music = "main"
                    self.music_start_time = pygame.time.get_ticks() - self.main_music_position
                    # Start fade in
                    self.start_music_fade(0, 1, 1000)
        else:
            # Calculate current volume
            progress = elapsed / self.music_fade_duration
            if self.music_fade_out:
                current_volume = self.music_fade_start_volume * (1 - progress)
            else:
                current_volume = self.music_fade_target_volume * progress
            
            pygame.mixer.music.set_volume(current_volume * self.music_volume)
    
    def start_music_fade(self, start_volume, target_volume, duration):
        """Start a music fade."""
        self.music_fade_active = True
        self.music_fade_start_time = pygame.time.get_ticks()
        self.music_fade_duration = duration
        self.music_fade_start_volume = start_volume
        self.music_fade_target_volume = target_volume
        self.music_fade_out = target_volume < start_volume
                
    def handle_click(self, pos):
        """Handle mouse click."""
        # Don't process other clicks during fade
        if self.fade_active:
            return
        
        # Helper function to play click sound
        def play_click_sound():
            if 'click' in self.assets.sounds:
                try:
                    # Apply SFX volume to click sound
                    self.assets.sounds['click'].set_volume(self.sfx_volume * 0.5)  # 50% of SFX volume
                    self.assets.sounds['click'].play()
                except Exception as e:
                    pass
            
        if self.current_screen == config.SCREEN_START:
            if self.play_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_START, "mode_select")
            elif self.tutorial_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_START, "tutorial")
            elif self.beta_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_START, config.SCREEN_BETA)
            elif self.credits_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_START, config.SCREEN_CREDITS)
                
        elif self.current_screen == "mode_select":
            # Handle mode selection
            for mode_key, button_rect in self.mode_buttons.items():
                if button_rect.collidepoint(pos):
                    play_click_sound()
                    self.current_mode = mode_key
                    
                    if mode_key == "classic":
                        self.start_fade("mode_select", config.SCREEN_DIFFICULTY)
                    elif mode_key == "story":
                        self.start_fade("mode_select", "story_select")
                    else:
                        # Other modes not implemented yet
                        pass
                        
            if self.back_button.collidepoint(pos):
                play_click_sound()
                self.start_fade("mode_select", config.SCREEN_START)
                
        elif self.current_screen == "story_select":
            # Handle story chapter selection
            for chapter_index, button_rect in self.story_chapter_buttons.items():
                if button_rect.collidepoint(pos) and self.story_mode.unlocked_chapters[chapter_index]:
                    play_click_sound()
                    self.story_mode.current_chapter = chapter_index
                    self.story_mode.current_battle = 0
                    self.start_fade("story_select", "story_chapter")
                    
            if self.story_back_button and self.story_back_button.collidepoint(pos):
                play_click_sound()
                self.start_fade("story_select", "mode_select")
                
        elif self.current_screen == "story_chapter":
            # Handle battle selection within chapter
            for battle_index, button_rect in self.story_battle_buttons.items():
                if button_rect.collidepoint(pos):
                    # Check if battle is unlocked
                    chapter_index = next((idx for idx, ch in enumerate(self.story_mode.chapters) 
                                        if ch["id"] == self.story_mode.get_current_chapter()["id"]), 0)
                    if self.story_mode.is_battle_unlocked(chapter_index, battle_index):
                        play_click_sound()
                        print(f"\n=== SELECTING BATTLE ===")
                        print(f"Battle index clicked: {battle_index}")
                        print(f"Chapter index: {chapter_index}")
                        print(f"Story mode current chapter before: {self.story_mode.current_chapter}")
                        
                        # Make sure we're on the right chapter
                        if self.story_mode.current_chapter != chapter_index:
                            print(f"Switching from chapter {self.story_mode.current_chapter} to {chapter_index}")
                            self.story_mode.current_chapter = chapter_index
                            
                        self.story_mode.current_battle = battle_index
                        battle_data = self.story_mode.get_current_battle()
                        print(f"Selected battle: {battle_data['id'] if battle_data else 'None'}")
                        print(f"Story mode state - chapter: {self.story_mode.current_chapter}, battle: {self.story_mode.current_battle}")
                        print("=== END SELECTING BATTLE ===\n")
                        if battle_data:
                            self.current_story_battle = battle_data
                            self.current_mode = "story"  # Set the game mode to story
                            self.selected_difficulty = battle_data["difficulty"]
                            
                            # Ensure tutorial is disabled for non-tutorial battles
                            if battle_data.get("id") != "tutorial_bot":
                                self.in_tutorial_battle = False
                                if hasattr(self, 'tutorial') and self.tutorial:
                                    self.tutorial.active = False
                                    self.tutorial.completed = True
                                config.set_tutorial_mode(False)
                            
                            self.ai = ChessAI(self.selected_difficulty)
                            self.start_fade("story_chapter", "story_dialogue")
                    else:
                        # Play error sound for locked battle
                        if 'click' in self.assets.sounds:
                            self.assets.sounds['click'].play()
                        
            if self.story_back_button and self.story_back_button.collidepoint(pos):
                play_click_sound()
                self.start_fade("story_chapter", "story_select")
                
        elif self.current_screen == "story_dialogue":
            # Click to advance dialogue or start battle
            if hasattr(self, 'dialogue_complete') and self.dialogue_complete:
                play_click_sound()
                self.start_fade("story_dialogue", config.SCREEN_GAME)
            else:
                # Advance dialogue
                if hasattr(self, 'current_dialogue_index'):
                    play_click_sound()
                    self.current_dialogue_index += 1
                    
        elif self.current_screen == "tutorial":
            # Handle tutorial navigation
            if self.prev_button.collidepoint(pos) and self.tutorial_page > 0:
                play_click_sound()
                self.tutorial_page -= 1
            elif self.next_button.collidepoint(pos) and self.tutorial_page < len(self.tutorial_pages) - 1:
                play_click_sound()
                self.tutorial_page += 1
            elif self.back_button.collidepoint(pos):
                play_click_sound()
                self.tutorial_page = 0  # Reset to first page
                self.start_fade("tutorial", config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_ARMS_DEALER:
            # Handle tutorial progression in arms dealer
            if self.in_tutorial_battle and self.tutorial.active:
                # Get current step, handling both SimpleTutorial and StoryTutorial
                if hasattr(self.tutorial, 'steps'):
                    # SimpleTutorial
                    if self.tutorial.current_step < len(self.tutorial.steps):
                        step = self.tutorial.steps[self.tutorial.current_step]
                    else:
                        step = {}
                else:
                    # StoryTutorial
                    step = self.tutorial.tutorial_steps[self.tutorial.current_step]
                
                # Check if waiting for tutorial specific actions
                if step.get("wait_for") == "arms_dealer_continue":
                    play_click_sound()
                    self.tutorial._advance_step()
                    return
                elif step.get("wait_for") == "tutorial_gift_complete":
                    # For SimpleTutorial, just advance past this step
                    play_click_sound()
                    if hasattr(self.tutorial, 'handle_tutorial_gift_complete'):
                        self.tutorial.handle_tutorial_gift_complete()
                    else:
                        self.tutorial._advance_step()
                    return
                elif step.get("wait_for") == "powerup_purchase":
                    # Handle tutorial powerup purchases
                    target_powerup = step.get("target_powerup")
                    for powerup_key, button_rect in self.shop_buttons.items():
                        if button_rect.collidepoint(pos) and powerup_key == target_powerup:
                            play_click_sound()
                            config.unlock_powerup(powerup_key)
                            pass
                            
                            # After purchasing shield, unlock all powerups for tutorial
                            if target_powerup == "shield":
                                config.tutorial_unlocked_powerups = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
                                pass
                            
                            # Advance tutorial step
                            self.tutorial._advance_step()
                            return
                elif step.get("wait_for") == "return_to_game":
                    # Handle "BACK TO GAME" during tutorial
                    if self.back_button.collidepoint(pos):
                        play_click_sound()
                        pass
                        # For SimpleTutorial, call handle_back_to_game
                        if hasattr(self.tutorial, 'handle_back_to_game'):
                            self.tutorial.handle_back_to_game()
                        else:
                            self.tutorial._advance_step()
                        # Don't return here - let the back button logic continue
                        # Fall through to normal back button handling
            
            # Check purchase buttons (only for non-tutorial mode)
            if not self.in_tutorial_battle:
                for powerup_key, button_rect in self.shop_buttons.items():
                    if button_rect.collidepoint(pos):
                        progress = config.load_progress()
                        unlocked = progress.get("unlocked_powerups", ["shield"])
                        
                        if powerup_key not in unlocked:
                            price = self.powerup_system.powerup_prices[powerup_key]
                            if config.spend_money(price):
                                play_click_sound()
                                config.unlock_powerup(powerup_key)
                                pass
                            else:
                                # Different sound for insufficient funds could go here
                                pass
            
            # Click on Tariq to cycle dialogue
            if hasattr(self.renderer, 'tariq_rect') and self.renderer.tariq_rect.collidepoint(pos):
                play_click_sound()
                # Clear ALL typewriter texts to prevent overlap
                self.renderer.clear_typewriter_texts()
                self.tariq_dialogue_index = (self.tariq_dialogue_index + 1) % len(self.tariq_dialogues)
            
            # Back button - restore game state instead of starting new game
            if self.back_button.collidepoint(pos):
                play_click_sound()
                if self.stored_game_state:
                    # Handle tutorial gift completion when returning to game
                    if self.in_tutorial_battle:
                        step = self.tutorial.tutorial_steps[self.tutorial.current_step] if self.tutorial.active else None
                        if step and step.get("wait_for") == "tutorial_gift_complete":
                            self.tutorial.handle_tutorial_gift_complete()
                    
                    # Restore the game state and set flag
                    self.restore_game_state()
                    self.returning_from_shop = True
                    self.start_fade(config.SCREEN_ARMS_DEALER, config.SCREEN_GAME)
                else:
                    # No stored state, go to main menu
                    self.start_fade(config.SCREEN_ARMS_DEALER, config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_DIFFICULTY:
            # Load progress to check unlocked difficulties
            progress = config.load_progress()
            unlocked = progress.get("unlocked_difficulties", ["easy"])
            
            # Check difficulty buttons
            for difficulty, button in self.difficulty_buttons.items():
                if button.collidepoint(pos) and difficulty in unlocked:
                    play_click_sound()
                    self.selected_difficulty = difficulty
                    self.ai = ChessAI(difficulty)
                    
                    self.start_fade(config.SCREEN_DIFFICULTY, config.SCREEN_GAME)
                    return
                    
            # Back button
            if self.back_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_DIFFICULTY, "mode_select")
                
        elif self.current_screen == config.SCREEN_CREDITS:
            if self.back_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_CREDITS, config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_BETA:
            if self.back_button.collidepoint(pos):
                play_click_sound()
                self.start_fade(config.SCREEN_BETA, config.SCREEN_START)
                
        elif self.current_screen == config.SCREEN_GAME:
            # Check if tutorial is waiting for click anywhere
            if self.in_tutorial_battle and self.tutorial.active:
                if hasattr(self.tutorial, 'steps'):
                    if self.tutorial.current_step < len(self.tutorial.steps):
                        step = self.tutorial.steps[self.tutorial.current_step]
                        if step.get("wait_for") == "click_anywhere":
                            play_click_sound()
                            self.tutorial.handle_click_anywhere()
                            return
            
            # Check game over buttons first
            if self.board.game_over and hasattr(self, 'game_over_buttons') and self.game_over_buttons:
                restart_rect, menu_rect = self.game_over_buttons
                if restart_rect and restart_rect.collidepoint(pos):
                    play_click_sound()
                    # Restart game
                    self.board.reset()
                    self.powerup_system = PowerupSystem()  # Reset powerup system
                    self.powerup_system.assets = self.assets  # Pass assets reference
                    self.board.set_powerup_system(self.powerup_system)
                    self.powerup_renderer.powerup_system = self.powerup_system
                    self.victory_processed = False  # Reset victory flag
                    self.victory_reward = 0  # Reset reward display
                    # Clear chopper mode
                    self.chopper_mode = None
                    return
                elif menu_rect and menu_rect.collidepoint(pos):
                    play_click_sound()
                    # CRITICAL: Reset victory flag when returning to menu
                    self.victory_processed = False
                    print("Reset victory_processed flag to False")
                    # Ensure story mode progress is saved before leaving
                    if self.current_mode == "story" and hasattr(self.story_mode, 'save_progress'):
                        self.story_mode.save_progress()
                        print(f"Saved story progress before returning to menu")
                    if self.current_mode == "story":
                        self.start_fade(config.SCREEN_GAME, "story_chapter")
                    else:
                        self.start_fade(config.SCREEN_GAME, config.SCREEN_START)
                    return
            
            # Check Arms Dealer button
            if self.arms_dealer_game_button and self.arms_dealer_game_button.collidepoint(pos):
                play_click_sound()
                
                # Handle tutorial arms dealer visit
                if self.in_tutorial_battle:
                    self.tutorial.handle_arms_dealer_visit()
                
                # Store current game state before going to shop
                self.store_game_state()
                self.start_fade(config.SCREEN_GAME, config.SCREEN_ARMS_DEALER)
                return
                
            # Check powerup menu buttons first
            if self.board.current_turn == "white":  # Only player can use powerups
                for powerup_key, button_rect in self.powerup_system.button_rects.items():
                    if button_rect.collidepoint(pos):
                        # Handle tutorial powerup selection
                        if self.in_tutorial_battle:
                            self.tutorial.handle_powerup_select(powerup_key)
                            
                        if self.powerup_system.activate_powerup("white", powerup_key):
                            play_click_sound()
                            return
                            
            # Handle active powerup clicks
            if self.powerup_system.active_powerup:
                # Store the active powerup before it gets cleared
                active_powerup_type = self.powerup_system.active_powerup
                if self.powerup_system.handle_click(pos, self.board):
                    # Handle tutorial powerup usage
                    if self.in_tutorial_battle:
                        row, col = self.board.get_square_from_pos(pos)
                        if row >= 0 and col >= 0:
                            self.tutorial.handle_powerup_use(
                                active_powerup_type, row, col)
                    
                    # Only play capture sound for destructive powerups
                    active_powerup = self.powerup_system.active_powerup
                    if active_powerup in ["gun", "airstrike"] and 'capture' in self.assets.sounds:
                        self.assets.sounds['capture'].play()
                    elif active_powerup == "shield" and 'click' in self.assets.sounds:
                        # Play a softer sound for shield
                        self.assets.sounds['click'].play()
                    # Paratroopers and chopper have their own sounds
                    return
                    
            # Only allow player moves during white's turn
            if self.board.current_turn != "white":
                return
                
            # Check promotion menu
            if self.board.promoting:
                for rect, piece_type in self.promotion_rects:
                    if rect.collidepoint(pos):
                        play_click_sound()
                        self.board.promote_pawn(piece_type)
                        if 'capture' in self.assets.sounds:
                            self.assets.sounds['capture'].play()
                        return
                        
            # Handle tutorial click to continue
            if self.in_tutorial_battle:
                if self.tutorial.handle_click(pos):
                    play_click_sound()
                    return
                        
            # Normal game clicks (piece movement) - no click sound for these
            if not self.board.animating and not self.board.promoting:
                row, col = self.board.get_square_from_pos(pos)
                if row >= 0 and col >= 0 and self.board.is_valid_selection(row, col):
                    # In tutorial mode, extra check to prevent selecting during black's turn
                    if self.in_tutorial_battle and self.board.current_turn != "white":
                        return
                    
                    # Handle tutorial piece selection and move start
                    if self.in_tutorial_battle:
                        self.tutorial.handle_piece_select(row, col)
                        self.tutorial.handle_move_start(row, col)
                    
                    self.board.selected_piece = (row, col)
                    # Always show valid moves
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
            
            # Validate tutorial move first
            if self.in_tutorial_battle:
                if not self.tutorial.validate_player_move(from_row, from_col, row, col):
                    # Invalid tutorial move - don't allow it
                    self.board.selected_piece = None
                    self.board.valid_moves = []
                    return
                    
                # Handle tutorial move
                self.tutorial.handle_move(from_row, from_col, row, col)
                
                # TUTORIAL FIX: Move shield immediately in tutorial mode (but only if not capturing)
                if self.powerup_system and self.powerup_system.is_piece_shielded(from_row, from_col):
                    # Check if this is a capture move
                    target_piece = self.board.get_piece(row, col)
                    if not target_piece:  # Only move shield if not capturing
                        print(f"\nTUTORIAL: Moving shield from ({from_row}, {from_col}) to ({row}, {col})")
                        self.powerup_system.move_shield((from_row, from_col), (row, col))
                    else:
                        print(f"\nTUTORIAL: Not moving shield - capturing at ({row}, {col})")
                        # Remove shield from source position since piece is capturing
                        self.powerup_system.remove_shield_at(from_row, from_col)
                        print(f"\nTUTORIAL: Removed shield from source position ({from_row}, {from_col})")
                    
                # Note: Shield countdown will happen when turn switches in complete_move()
            
            # Always use animation
            self.board.start_move(from_row, from_col, row, col)
            self.board.selected_piece = None
            self.board.valid_moves = []
        else:
            # Check if selecting new piece
            if row >= 0 and col >= 0 and self.board.is_valid_selection(row, col):
                self.board.selected_piece = (row, col)
                # Always show valid moves
                self.board.valid_moves = self.board.get_valid_moves(row, col)
            else:
                self.board.selected_piece = None
                self.board.valid_moves = []
                
        self.board.dragging = False
        self.board.drag_piece = None
        self.board.drag_start = None
        
    def handle_key(self, key):
        """Handle keyboard input."""
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
                else:
                    if self.current_mode == "story":
                        self.start_fade(config.SCREEN_GAME, "story_chapter")
                    else:
                        self.start_fade(config.SCREEN_GAME, config.SCREEN_START)
            elif key == pygame.K_r and self.board.game_over:
                self.board.reset()
                self.powerup_system = PowerupSystem()  # Reset powerup system
                self.powerup_system.assets = self.assets  # Pass assets reference
                self.board.set_powerup_system(self.powerup_system)
                self.powerup_renderer.powerup_system = self.powerup_system
                self.victory_processed = False  # Reset victory flag
                self.victory_reward = 0  # Reset reward display
                # Clear chopper mode
                self.chopper_mode = None
        elif self.current_screen == config.SCREEN_DIFFICULTY:
            if key == pygame.K_ESCAPE:
                self.start_fade(config.SCREEN_DIFFICULTY, "mode_select")
        elif self.current_screen == "mode_select":
            if key == pygame.K_ESCAPE:
                self.start_fade("mode_select", config.SCREEN_START)
        elif self.current_screen == "story_select":
            if key == pygame.K_ESCAPE:
                self.start_fade("story_select", "mode_select")
        elif self.current_screen == "story_chapter":
            if key == pygame.K_ESCAPE:
                self.start_fade("story_chapter", "story_select")
        elif self.current_screen == "tutorial":
            if key == pygame.K_ESCAPE:
                self.tutorial_page = 0  # Reset to first page
                self.start_fade("tutorial", config.SCREEN_START)
            elif key == pygame.K_LEFT and self.tutorial_page > 0:
                self.tutorial_page -= 1
            elif key == pygame.K_RIGHT and self.tutorial_page < len(self.tutorial_pages) - 1:
                self.tutorial_page += 1
        elif self.current_screen in [config.SCREEN_START, config.SCREEN_CREDITS, config.SCREEN_ARMS_DEALER, config.SCREEN_BETA]:
            pass  # No special key handling for these screens
                
    def start_fade(self, from_screen, to_screen):
        """Start fade transition."""
        self.fade_active = True
        self.fade_start = pygame.time.get_ticks()
        self.fade_from = from_screen
        self.fade_to = to_screen
        
        # Handle music transitions
        if to_screen == config.SCREEN_ARMS_DEALER and self.current_music == "main":
            # Fade out main music when entering arms dealer
            self.switching_to_tariq = True
            self.start_music_fade(1, 0, 1000)
        elif from_screen == config.SCREEN_ARMS_DEALER and to_screen in [config.SCREEN_GAME, config.SCREEN_START] and self.current_music == "tariq":
            # Fade out tariq music when leaving arms dealer
            self.switching_to_tariq = False
            self.start_music_fade(1, 0, 1000)
        # Always clear ALL typewriter texts when switching screens
        # Each screen will re-add its own texts when drawn
        self.renderer.clear_typewriter_texts()
        
    def update(self):
        """Update game logic."""
        current_time = pygame.time.get_ticks()
        
        # Update music fade
        self.update_music_fade()
        
        # Update intro screen
        if self.current_screen == "intro" and not self.fade_active:
            self.intro_screen.update()
            if self.intro_screen.complete and not self.intro_complete:
                # Start fade transition to post-intro cutscene
                self.start_fade("intro", "post_intro")
                self.intro_complete = True  # Prevent multiple fade starts
                
        # Update post-intro cutscene
        if self.current_screen == "post_intro" and not self.fade_active:
            self.post_intro_cutscene.update()
            if self.post_intro_cutscene.complete and not self.post_intro_complete:
                # Start fade transition to main menu
                self.start_fade("post_intro", config.SCREEN_START)
                self.post_intro_complete = True  # Prevent multiple fade starts
        
        # Update fade
        if self.fade_active:
            elapsed = current_time - self.fade_start
            if elapsed >= config.FADE_DURATION:
                self.fade_active = False
                self.current_screen = self.fade_to
                # Special handling for fade from intro
                if self.fade_from == "intro":
                    self.intro_screen.active = False
                    self.intro_complete = True  # Mark intro as complete
                    # Start the post-intro cutscene
                    if self.fade_to == "post_intro":
                        self.post_intro_cutscene.start()
                elif self.fade_from == "post_intro":
                    self.post_intro_cutscene.active = False
                    self.post_intro_complete = True
                elif self.fade_to == config.SCREEN_ARMS_DEALER:
                    # Auto-advance tutorial when reaching arms dealer
                    if self.in_tutorial_battle and self.tutorial.active:
                        self.tutorial.handle_at_arms_dealer()
                        # Ensure tutorial has points
                        if self.powerup_system.points["white"] < 100:
                            self.powerup_system.points["white"] = 999
                            pass
                if self.fade_to == config.SCREEN_GAME:
                    if not self.returning_from_shop:
                        # Only reset if we're not returning from shop
                        self.board.reset()
                        self.powerup_system = PowerupSystem()  # Reset powerup system
                        self.powerup_system.assets = self.assets  # Pass assets reference
                        self.board.set_powerup_system(self.powerup_system)
                        self.powerup_renderer.powerup_system = self.powerup_system
                        
                        # CRITICAL: Reset victory flag when starting new game
                        self.victory_processed = False
                        self.victory_reward = 0  # Reset victory reward
                        self.board.victory_reward = 0  # Reset board victory reward
                        print("Reset victory_processed flag to False for new game")
                        
                        # Apply story mode rules if in story mode
                        if self.current_mode == "story" and self.current_story_battle:
                            self.story_mode.apply_battle_rules(
                                self.current_story_battle,
                                self.board,
                                self.powerup_system,
                                self.ai
                            )
                            
                            # Check if this is the tutorial battle (Chapter 1, Battle 1)
                            if self.current_story_battle.get("id") == "tutorial_bot":
                                self.in_tutorial_battle = True
                                config.set_tutorial_mode(True)  # Enable tutorial mode
                                self.powerup_system.in_tutorial = True  # Enable all powerups for tutorial
                                
                                # CRITICAL FIX: Update tutorial references to current board and powerup system
                                self.tutorial.board = self.board
                                self.tutorial.powerup_system = self.powerup_system
                                print(f"Tutorial: Updated references - board powerup_system: {self.board.powerup_system is not None}")
                                
                                self.tutorial.start("story")
                            else:
                                self.in_tutorial_battle = False
                                config.set_tutorial_mode(False)  # Disable tutorial mode
                                self.powerup_system.in_tutorial = False
                                # Force disable tutorial system
                                if hasattr(self, 'tutorial'):
                                    self.tutorial.active = False
                                    self.tutorial.completed = True
                                    self.tutorial.current_step = 999  # Set to beyond any valid step
                                print(f"Tutorial forcefully disabled for non-tutorial battle: {self.current_story_battle.get('id')}")
                        else:
                            # Not in story mode - ensure tutorial is disabled
                            self.in_tutorial_battle = False
                    else:
                        # Returning from shop - game state already restored, just clear flag
                        self.returning_from_shop = False
                        
                        # Handle tutorial continuation after returning from shop
                        if self.in_tutorial_battle and self.tutorial.active:
                            pass
                            self.tutorial.handle_back_to_game()
                            pass
                            # Force refresh of tutorial text
                            if hasattr(self.tutorial, 'get_current_instruction'):
                                current_text = self.tutorial.get_current_instruction()
                                pass
                elif self.fade_to == "story_dialogue":
                    # Initialize dialogue state
                    self.current_dialogue_index = 0
                    self.dialogue_complete = False
                    # Clear any story dialogue typewriter texts when starting new dialogue
                    story_dialogue_ids = {key for key in self.renderer.typewriter_added_texts if key.startswith("story_dialogue_")}
                    for text_id in story_dialogue_ids:
                        self.renderer.typewriter_added_texts.discard(text_id)
        
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
            
            
            # Multiple bulletproof checks for AI moves in tutorial
            if self.in_tutorial_battle:
                # Method 1: Check turn changes
                if hasattr(self, '_last_turn'):
                    if self._last_turn == "black" and self.board.current_turn == "white":
                        # AI just finished its turn
                        self.tutorial.handle_ai_move()
                        self.tutorial.force_check_ai_move()  # Backup check
                        
                # Method 2: Force check every frame if waiting for AI move
                self.tutorial.force_check_ai_move()
                
                # Method 3: Timeout safety net
                self.tutorial.check_timeout()
                
            self._last_turn = self.board.current_turn
            
            # Check animation complete
            if self.board.animating:
                if current_time - self.board.animation_start >= config.MOVE_ANIMATION_DURATION:
                    if self.in_tutorial_battle:
                        print(f"\n=== TUTORIAL ANIMATION COMPLETE ===")
                        print(f"About to call complete_move()")
                    captured = self.board.complete_move()
                    
                    # Bulletproof AI move detection when animation completes
                    if self.in_tutorial_battle:
                        self.tutorial.force_check_ai_move()
                    
                    # Play capture sound immediately when capture happens
                    if captured and 'capture' in self.assets.sounds:
                        try:
                            self.assets.sounds['capture'].play()
                        except Exception as e:
                            pass
                        
                        # Track last capture
                        self.last_captured_piece = captured
                        
                        # Handle tutorial progression for captures by white player
                        if self.in_tutorial_battle and captured and captured.islower():  # White captured black piece
                            self.tutorial.handle_points_gained()
                        
                        
            # AI turn
            if (self.board.current_turn == "black" and 
                not self.board.game_over and 
                not self.board.animating and
                self.current_mode in ["vs_ai", "story"]):
                if self.ai:
                    # Start thinking if not already
                    if not self.ai.is_thinking() and self.ai.start_thinking is None:
                        if self.in_tutorial_battle:
                            print(f"\n=== AI STARTING TURN ===\nTutorial active: {self.tutorial.active}\nMode: {self.tutorial.current_mode}\nStep: {self.tutorial.current_step}")
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
                        # Check if tutorial should override AI move
                        print(f"\nAI Move Check: in_tutorial_battle={self.in_tutorial_battle}, tutorial_active={self.tutorial.active if hasattr(self, 'tutorial') else 'No tutorial'}")
                        should_override = self.tutorial.should_override_ai() if self.in_tutorial_battle else False
                        print(f"Should override AI: {should_override}")
                        
                        # SPECIAL CASE: Force e7-e5 in tutorial ONLY for first AI move
                        if (self.in_tutorial_battle and 
                            self.tutorial.ai_move_index == 0 and
                            self.board.get_piece(1, 4) == 'bP' and
                            self.board.get_piece(3, 4) == ""):
                                print("TUTORIAL OVERRIDE: Forcing e7-e5 move for tutorial (first AI move only)")
                                tutorial_move = ((4, 1), (4, 3))  # e7 to e5
                                # Increment AI move index
                                self.tutorial.ai_move_index += 1
                                # Handle tutorial AI move
                                if hasattr(self.tutorial, 'handle_ai_move'):
                                    self.tutorial.handle_ai_move()
                                # Execute the move
                                self.board.start_move(1, 4, 3, 4)  # row, col format
                                self.ai.start_thinking = None
                                return
                        
                        if self.in_tutorial_battle and should_override:
                            tutorial_move = self.tutorial.get_next_ai_move()
                            if tutorial_move:
                                from_pos, to_pos = tutorial_move
                                
                                # Debug: Check what piece is at the from position
                                # Note: from_pos is (col, row) but get_piece expects (row, col)
                                piece_at_from = self.board.get_piece(from_pos[1], from_pos[0])
                                piece_at_to = self.board.get_piece(to_pos[1], to_pos[0])
                                
                                print(f"Tutorial AI: Moving {piece_at_from} from {from_pos} to {to_pos}")
                                print(f"Piece at destination: {piece_at_to}")
                                
                                # Verify it's a valid black piece
                                if not piece_at_from or piece_at_from[0] != 'b':
                                    print(f"ERROR: Invalid piece at source position! Expected black piece, got: {piece_at_from}")
                                    # Try to find e7 pawn and force the move
                                    e7_piece = self.board.get_piece(1, 4)  # e7 = row 1, col 4
                                    if e7_piece == 'bP':
                                        print("Found black pawn at e7, forcing e7-e5 move")
                                        from_pos = (4, 1)
                                        to_pos = (4, 3)
                                
                                # Handle tutorial AI move (do this before the move)
                                self.tutorial.handle_ai_move()
                                
                                # Always use animation
                                # Fixed: start_move expects (from_row, from_col, to_row, to_col)
                                # but tutorial stores moves as ((from_col, from_row), (to_col, to_row))
                                self.board.start_move(from_pos[1], from_pos[0], to_pos[1], to_pos[0])
                        else:
                            # Normal AI move
                            ai_move = self.ai.get_move(self.board)
                            
                            # TUTORIAL SAFETY: Don't let AI capture critical pieces during tutorial
                            if self.in_tutorial_battle and ai_move:
                                from_pos, to_pos = ai_move
                                target_piece = self.board.get_piece(to_pos[1], to_pos[0])
                                
                                # Check if AI is trying to capture any white knight during tutorial
                                if (target_piece == 'wN' and 
                                    self.tutorial.current_step >= 7 and self.tutorial.current_step <= 14):  # During/after capture phase
                                    print(f"Tutorial: Preventing AI from capturing knight at {to_pos}")
                                    # Find a safe pawn move instead
                                    safe_moves = [
                                        ((0, 1), (0, 2)),  # a7-a6
                                        ((7, 1), (7, 2)),  # h7-h6
                                        ((2, 1), (2, 2)),  # c7-c6
                                        ((5, 1), (5, 2)),  # f7-f6
                                    ]
                                    for move in safe_moves:
                                        piece = self.board.get_piece(move[0][1], move[0][0])
                                        target = self.board.get_piece(move[1][1], move[1][0])
                                        if piece == 'bP' and target == "":
                                            ai_move = move
                                            print(f"Tutorial: Redirecting AI to safe move {move}")
                                            break
                                    
                                    # If no safe pawn moves, just skip the AI turn
                                    if ai_move == old_ai_move:
                                        print("Tutorial: No safe moves found, skipping AI turn")
                                        self.ai.start_thinking = None
                                        return
                            
                            if ai_move:
                                from_pos, to_pos = ai_move
                                
                                # Handle tutorial AI move (do this before the move)
                                if self.in_tutorial_battle:
                                    self.tutorial.handle_ai_move()
                                    
                                # Check if target is shielded (final safety check)
                                target_piece = self.board.get_piece(to_pos[0], to_pos[1])
                                if (target_piece and self.powerup_system and 
                                    self.powerup_system.is_piece_shielded(to_pos[0], to_pos[1])):
                                    print(f"ERROR: AI trying to capture shielded piece at {to_pos}!")
                                    # This shouldn't happen - skip the AI turn
                                    self.ai.start_thinking = None
                                else:
                                    # Always use animation
                                    self.board.start_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                        self.ai.start_thinking = None
                        
            # Check for player victory and unlock next difficulty
            if self.board.game_over and self.board.winner == "white":
                print(f"Game Over! Winner: {self.board.winner}, Mode: {self.current_mode}, Selected Difficulty: {self.selected_difficulty}")
                print(f"Victory processing check - has victory_processed: {hasattr(self, 'victory_processed')}")
                print(f"Current story battle: {getattr(self, 'current_story_battle', None)}")
                print(f"Tutorial mode: {getattr(config, '_in_tutorial', 'Unknown')}")
                if not hasattr(self, 'victory_processed') or not self.victory_processed:
                    self.victory_processed = True
                    print("PROCESSING VICTORY NOW!")
                    
                    # Handle story mode victory first (story mode has its own reward system)
                    if self.current_mode == "story":
                        print(f"Story mode check - current_mode: {self.current_mode}")
                        print(f"Story mode check - current_story_battle: {self.current_story_battle}")
                        print(f"Story mode instance id: {id(self.story_mode)}")
                        print(f"Story mode state before: completed_battles={self.story_mode.completed_battles}")
                        if self.current_story_battle:
                            battle_id = self.current_story_battle['id']
                            print(f"\n{'='*50}")
                            print(f"STORY MODE VICTORY PROCESSING")
                            print(f"Battle: {battle_id}")
                            print(f"Battle data: {self.current_story_battle}")
                            print(f"{'='*50}\n")
                            
                            # Get chapter index for this battle
                            chapter_index = None
                            for idx, chapter in enumerate(self.story_mode.chapters):
                                for battle in chapter["battles"]:
                                    if battle["id"] == battle_id:
                                        chapter_index = idx
                                        break
                                if chapter_index is not None:
                                    break
                            
                            # Use story mode's robust completion system
                            self.story_mode.complete_battle(battle_id, won=True)
                            
                            print(f"Story mode state: completed_battles={self.story_mode.completed_battles}")
                            print(f"Story mode state: unlocked_chapters={self.story_mode.unlocked_chapters}")
                            
                            # Award story mode cash rewards on EVERY victory (not just first time)
                            print(f"\nChecking for reward_money in battle data...")
                            if "reward_money" in self.current_story_battle:
                                story_reward = self.current_story_battle["reward_money"]
                                print(f"Found reward_money: ${story_reward}")
                                
                                # Handle tutorial bot completion specially
                                if self.current_story_battle["id"] == "tutorial_bot":
                                    print("Special handling for tutorial_bot")
                                    config.set_tutorial_mode(False)
                                    self.powerup_system.in_tutorial = False
                                    config.reset_after_tutorial()  # This sets money to $100
                                    self.victory_reward = 100  # Display the reward
                                    self.board.victory_reward = 100  # Set it on board immediately
                                    print("Tutorial completed! Starting with $100")
                                else:
                                    # Regular story battle rewards
                                    print(f"Processing regular battle reward: ${story_reward}")
                                    print(f"Current money before: ${config.get_money()}")
                                    new_money = config.add_money(story_reward)
                                    self.victory_reward = story_reward  # Display the correct reward
                                    self.board.victory_reward = story_reward  # Set it on board immediately
                                    print(f"Story mode victory reward: ${story_reward}")
                                    print(f"Current money after: ${config.get_money()}")
                                    print(f"add_money returned: ${new_money}")
                                    print(f"self.victory_reward set to: ${self.victory_reward}")
                                    print(f"self.board.victory_reward set to: ${self.board.victory_reward}")
                            else:
                                print("ERROR: No reward_money found in battle data!")
                    else:
                        # Classic mode - award difficulty-based money and unlock next difficulty
                        if self.selected_difficulty:
                            reward = config.VICTORY_REWARDS[self.selected_difficulty]
                            new_total = config.add_money(reward)
                            self.victory_reward = reward  # Store for display
                            self.board.victory_reward = reward  # Set it on board immediately
                            print(f"Victory! Earned ${reward}. Total: ${new_total}")
                        
                        # Unlock next difficulty
                        next_difficulty = config.unlock_next_difficulty(self.selected_difficulty)
                        if next_difficulty:
                            print(f"Congratulations! You've unlocked {config.AI_DIFFICULTY_NAMES[next_difficulty]} difficulty!")
                    
            elif self.board.game_over and self.board.winner == "black":
                # AI victory
                if not hasattr(self, 'defeat_processed'):
                    self.defeat_processed = True
                    
                    # Handle story mode defeat
                    if self.current_mode == "story" and self.current_story_battle:
                        self.story_mode.complete_battle(self.current_story_battle["id"], won=False)
                    
    def draw(self):
        """Draw everything."""
        # Handle chopper mode drawing separately
        if self.chopper_mode and self.chopper_mode.active:
            self.chopper_mode.draw()
            pygame.display.flip()
            return
            
        # Get screen shake offset - only apply during actual gameplay, not during fades or menus
        shake_x, shake_y = 0, 0
        if self.current_screen == config.SCREEN_GAME and not self.fade_active:
            shake_x, shake_y = self.powerup_system.get_screen_shake_offset()
        
        # Use cached surface for screen shake
        if shake_x != 0 or shake_y != 0:
            original_screen = self.screen
            self.screen = self._shake_surface
            self.renderer.screen = self._shake_surface
            self.powerup_renderer.screen = self._shake_surface
        
        # Handle fade transitions
        if self.fade_active:
            # Disable typewriter additions during fade
            self.renderer.allow_typewriter_additions = False
            
            # Draw fade transition
            progress = min(1.0, (pygame.time.get_ticks() - self.fade_start) / config.FADE_DURATION)
            
            if progress < 0.5:
                # Fade out
                self.draw_screen(self.fade_from)
                alpha = int(255 * (progress * 2))
                self._fade_surface.set_alpha(alpha)
                self.screen.blit(self._fade_surface, (0, 0))
            else:
                # Fade in
                self.draw_screen(self.fade_to)
                alpha = int(255 * (2 - progress * 2))
                self._fade_surface.set_alpha(alpha)
                self.screen.blit(self._fade_surface, (0, 0))
                
            # Re-enable typewriter additions
            self.renderer.allow_typewriter_additions = True
        else:
            # Normal drawing (no fade)
            self.draw_screen(self.current_screen)
            
        # Update and draw typewriter texts only on appropriate screens
        # Don't draw typewriter texts during fade transitions
        if not self.fade_active and self.current_screen in [config.SCREEN_START, "mode_select", "story_dialogue", config.SCREEN_ARMS_DEALER]:
            self.renderer.update_typewriter_texts()
            self.renderer.draw_typewriter_texts()
            
        # Apply screen shake if active
        if shake_x != 0 or shake_y != 0:
            # Restore original screen
            self.screen = original_screen
            self.renderer.screen = original_screen
            self.powerup_renderer.screen = original_screen
            
            # Clear the screen with black
            self.screen.fill(config.BLACK)
            
            # Blit the game surface with shake offset
            self.screen.blit(self._shake_surface, (shake_x, shake_y))
            
        pygame.display.flip()
            
    def draw_screen(self, screen_type):
        """Draw specific screen."""
        if screen_type == "intro":
            self.intro_screen.draw()
            
            # Draw skip instruction
            if hasattr(self.intro_screen, 'credit_font'):
                skip_text = self.renderer.pixel_fonts['small'].render("Press SPACE or ESC to skip", True, (100, 100, 100))
                skip_rect = skip_text.get_rect(bottomright=(config.WIDTH - 20, config.HEIGHT - 20))
                skip_text.set_alpha(150)
                self.screen.blit(skip_text, skip_rect)
                
        elif screen_type == "post_intro":
            self.post_intro_cutscene.draw()
                
        elif screen_type == config.SCREEN_START:
            buttons = {
                'play': self.play_button,
                'tutorial': self.tutorial_button,
                'beta': self.beta_button, 
                'credits': self.credits_button
            }
            self.renderer.draw_menu(config.SCREEN_START, buttons, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == "mode_select":
            self.renderer.draw_mode_select(self.mode_buttons, self.back_button, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == "story_select":
            self.renderer.draw_story_chapters(self.story_mode, self.story_chapter_buttons, 
                                            self.story_back_button, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == "story_chapter":
            chapter = self.story_mode.get_current_chapter()
            if chapter:
                self.renderer.draw_story_battles(chapter, self.story_mode, 
                                               self.story_battle_buttons, 
                                               self.story_back_button, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == "story_dialogue":
            if self.current_story_battle:
                self.renderer.draw_story_dialogue(self.current_story_battle, 
                                                self.current_dialogue_index,
                                                self.dialogue_complete)
                
                # Check if dialogue is complete
                dialogue_lines = self.current_story_battle.get("pre_battle", [])
                if self.current_dialogue_index >= len(dialogue_lines) - 1:
                    self.dialogue_complete = True
                    
        elif screen_type == "tutorial":
            # Create tutorial buttons dictionary
            tutorial_buttons = {
                'prev': self.prev_button,
                'next': self.next_button,
                'back': self.back_button
            }
            # Pass the tutorial page data with additional info
            tutorial_page_data = {
                'page': self.tutorial_pages[self.tutorial_page],
                'current_index': self.tutorial_page,
                'total_pages': len(self.tutorial_pages)
            }
            self.renderer.draw_tutorial(tutorial_page_data, tutorial_buttons, self.mouse_pos)
            self.draw_volume_sliders()
            
        elif screen_type == config.SCREEN_ARMS_DEALER:
            self.renderer.draw_arms_dealer(self.powerup_system, self.shop_buttons, 
                                          self.back_button, self.mouse_pos, 
                                          self.tariq_dialogue_index, self.tariq_dialogues,
                                          self.tutorial if self.in_tutorial_battle else None)
            
            # Draw tutorial hints if in tutorial battle
            if self.in_tutorial_battle and self.tutorial.active:
                self.renderer.draw_tutorial_hints(self.tutorial)
                
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
                
            # UI with AI info (always show captured pieces)
            self.renderer.draw_ui(self.board, None, False, self.mouse_pos, 
                                 self.ai, self.selected_difficulty,
                                 show_captured=True)
            self.draw_volume_sliders()
            
            # Add Arms Dealer button in game
            self.draw_arms_dealer_button()
            
            # Powerup menu
            self.powerup_renderer.draw_powerup_menu(self.board, self.mouse_pos)
            
            # Powerup effects
            self.powerup_renderer.draw_effects(self.board)
            
            # Powerup targeting
            self.powerup_renderer.draw_powerup_targeting(self.board, self.mouse_pos)
            
            # Draw story mode UI if in story mode
            if self.current_mode == "story" and self.current_story_battle:
                self.renderer.draw_story_battle_ui(self.current_story_battle)
                
            # Draw tutorial hints if in tutorial battle
            if self.in_tutorial_battle and self.tutorial.active:
                self.renderer.draw_tutorial_hints(self.tutorial)
            
            
            # Overlays
            if self.board.promoting:
                self.promotion_rects = self.renderer.draw_promotion_menu(self.board, self.mouse_pos)
            
            # Pass selected difficulty and victory reward to renderer
            if self.board.game_over and self.selected_difficulty:
                if not hasattr(self.board, 'selected_difficulty'):
                    self.board.selected_difficulty = self.selected_difficulty
                if not hasattr(self.board, 'victory_reward'):
                    self.board.victory_reward = self.victory_reward
                    print(f"[VICTORY SCREEN] Set board.victory_reward = {self.board.victory_reward}")
                else:
                    print(f"[VICTORY SCREEN] board.victory_reward already = {self.board.victory_reward}")
                if self.current_mode == "story":
                    self.board.is_story_mode = True
                    self.board.story_battle = self.current_story_battle
            self.game_over_buttons = self.renderer.draw_game_over(self.board)
            
    def draw_killstreak_ui(self):
        """Placeholder for removed killstreak UI."""
        pass
        
    def _calculate_material_advantage(self):
        """Calculate material advantage for white player."""
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        white_value = 0
        black_value = 0
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(col, row)
                if piece:
                    value = piece_values.get(piece[1], 0)
                    if piece[0] == 'w':
                        white_value += value
                    else:
                        black_value += value
                        
        return white_value - black_value
                
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
        button_width = 150
        button_height = 40
        button_x = 20
        button_y = config.HEIGHT // 2 - button_height // 2  # Center vertically
        
        self.arms_dealer_game_button = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # Check if tutorial is highlighting this button
        should_highlight = False
        if self.in_tutorial_battle and self.tutorial and self.tutorial.active:
            if self.tutorial.current_step < len(self.tutorial.steps):
                current_step = self.tutorial.steps[self.tutorial.current_step]
                if current_step.get("wait_for") == "arms_dealer_visit":
                    should_highlight = True
        
        # Check if hovering
        is_hover = self.arms_dealer_game_button.collidepoint(self.mouse_pos)
        
        # Draw highlighting effect if needed
        if should_highlight:
            # Draw pulsing glow effect
            pulse = (pygame.time.get_ticks() // 200) % 10
            glow_size = 10 + pulse
            
            # Draw multiple layers of glow
            for i in range(3):
                glow_rect = self.arms_dealer_game_button.inflate(glow_size * 2 - i * 6, glow_size * 2 - i * 6)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 215, 0, 100 - i * 30), glow_surf.get_rect(), border_radius=15)
                self.screen.blit(glow_surf, glow_rect)
            
        
        # Draw button
        button_color = (150, 100, 50) if is_hover else (120, 80, 40)
        if should_highlight:
            button_color = (200, 150, 100)  # Brighter when highlighted
        pygame.draw.rect(self.screen, button_color, self.arms_dealer_game_button, border_radius=10)
        
        # Draw border (thicker and brighter if highlighted)
        border_color = (255, 215, 0) if should_highlight else (200, 150, 100)
        border_width = 5 if should_highlight else 3
        pygame.draw.rect(self.screen, border_color, self.arms_dealer_game_button, border_width, border_radius=10)
        
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