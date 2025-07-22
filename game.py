"""
Main Game Class - Enhanced with Tutorial, Victory Screen, Killstreaks, Emotes, Story Mode
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
from intro_screen import IntroScreen
from emotes import EmoteSystem
from story_mode import StoryMode

class ChessGame:
    def __init__(self):
        # Get screen info before creating display
        self.screen_info = pygame.display.Info()
        
        # Create screen (windowed mode only)
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
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
        
        # NEW: Emote system
        self.emote_system = EmoteSystem(self.screen, self.renderer)
        
        # NEW: Story mode
        self.story_mode = StoryMode()
        self.current_story_battle = None
        
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
                "title": "BASIC CHESS RULES",
                "content": [
                    "• Click a piece to select it",
                    "• Valid moves will be highlighted",
                    "• Click a highlighted square to move",
                    "• Capture enemy pieces by moving to their square",
                    "",
                    "SPECIAL MOVES:",
                    "• Pawns can move 2 squares on first move",
                    "• Pawns promote when reaching the end",
                    "• Protect your King at all costs!"
                ]
            },
            {
                "title": "EARNING POINTS",
                "content": [
                    "Capture enemy pieces to earn powerup points:",
                    "",
                    "• Pawn = 1 point",
                    "• Knight/Bishop = 3 points",
                    "• Rook = 5 points",
                    "• Queen = 9 points",
                    "",
                    "Points are shown in the powerup menu",
                    "on the right side of the game board."
                ]
            },
            {
                "title": "POWERUPS",
                "content": [
                    "SHIELD (5 pts): Protects a piece for 3 turns",
                    "",
                    "GUN (7 pts): Shoot any enemy in line of sight",
                    "",
                    "AIRSTRIKE (10 pts): Bomb a 3x3 area",
                    "",
                    "PARATROOPERS (10 pts): Drop 3 pawns anywhere",
                    "",
                    "CHOPPER GUNNER (25 pts): Ultimate destruction!"
                ]
            },
            {
                "title": "KILLSTREAKS",
                "content": [
                    "NEW! Capture pieces without losing any to build streaks:",
                    "",
                    "• 3 KILLS: Free Shield",
                    "• 5 KILLS: Free Gun", 
                    "• 7 KILLS: Free Airstrike",
                    "• 10 KILLS: Free Chopper Gunner",
                    "• 15 KILLS: TACTICAL NUKE!",
                    "",
                    "Lose a piece and your streak resets!"
                ]
            },
            {
                "title": "PROGRESSION",
                "content": [
                    "Beat AI opponents to progress:",
                    "",
                    "• Win to unlock the next difficulty",
                    "• Earn money based on difficulty",
                    "• Visit the Arms Dealer to buy powerups",
                    "",
                    "REWARDS:",
                    "Easy: $100 | Medium: $200",
                    "Hard: $400 | Very Hard: $800"
                ]
            }
        ]
        
        # Story mode UI - Initialize these dictionaries
        self.story_chapter_buttons = {}
        self.story_battle_buttons = {}
        self.story_back_button = None  # Will be initialized in update_ui_positions()
        
        # UI elements
        self.update_ui_positions()
        
        # Volume control
        self.music_volume = 0.75
        self.sfx_volume = 0.75
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
        
        # Track last capture for emotes
        self.last_captured_piece = None
        
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
            "killstreaks": {
                "white": self.powerup_system.current_streak["white"],
                "black": self.powerup_system.current_streak["black"]
            },
            "shielded_pieces": dict(self.powerup_system.shielded_pieces),
            "game_over": self.board.game_over,
            "winner": self.board.winner,
            "ai": self.ai,
            "selected_difficulty": self.selected_difficulty,
            "current_mode": self.current_mode,
            "current_story_battle": self.current_story_battle
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
            self.powerup_system.current_streak = dict(self.stored_game_state["killstreaks"])
            self.powerup_system.shielded_pieces = dict(self.stored_game_state["shielded_pieces"])
            
            # Restore AI and mode
            self.ai = self.stored_game_state["ai"]
            self.selected_difficulty = self.stored_game_state["selected_difficulty"]
            self.current_mode = self.stored_game_state["current_mode"]
            self.current_story_battle = self.stored_game_state["current_story_battle"]
            
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
        # Deduct points unless it's from killstreak
        is_free = self.powerup_system.has_pending_streak_reward("black", powerup_key)
        
        if is_free:
            # Find and remove the streak reward
            for reward in self.powerup_system.pending_streak_rewards["black"]:
                if reward["powerup"] == powerup_key:
                    self.powerup_system.pending_streak_rewards["black"].remove(reward)
                    break
        else:
            self.powerup_system.points["black"] -= self.powerup_system.powerups[powerup_key]["cost"]
        
        # Trigger emote for powerup use
        self.emote_system.trigger_emote("ai_powerup", self.selected_difficulty)
        
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
            
    def _check_and_trigger_game_emotes(self):
        """Check game state and trigger appropriate emotes."""
        if not self.ai or not self.emote_system:
            return
            
        # Check for check
        if self.board.is_in_check():
            if self.board.current_turn == "white":
                self.emote_system.trigger_emote("player_check", self.selected_difficulty)
                
        # Check material balance for winning/losing
        white_material = 0
        black_material = 0
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece:
                    value = self.ai.piece_values.get(piece[1], 0)
                    if piece[0] == 'w':
                        white_material += value
                    else:
                        black_material += value
                        
        balance = black_material - white_material
        if balance > 500:
            self.emote_system.trigger_emote("ai_winning", self.selected_difficulty)
        elif balance < -500:
            self.emote_system.trigger_emote("ai_losing", self.selected_difficulty)
                
    def handle_events(self):
        """Handle all events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Handle intro screen events
            if self.current_screen == "intro":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        # Skip intro
                        self.intro_screen.skip()
                        if not self.fade_active:
                            self.start_fade("intro", config.SCREEN_START)
                        
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
        if 'click' in self.assets.sounds:
            self.assets.sounds['click'].set_volume(self.sfx_volume * 0.5)  # Click at 50% of SFX volume
                
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
                    print(f"Error playing click sound: {e}")
            
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
                        print(f"Mode {mode_key} coming soon!")
                        
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
                    play_click_sound()
                    self.story_mode.current_battle = battle_index
                    battle_data = self.story_mode.get_current_battle()
                    if battle_data:
                        self.current_story_battle = battle_data
                        self.selected_difficulty = battle_data["difficulty"]
                        self.ai = ChessAI(self.selected_difficulty)
                        self.start_fade("story_chapter", "story_dialogue")
                        
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
            # Check purchase buttons
            for powerup_key, button_rect in self.shop_buttons.items():
                if button_rect.collidepoint(pos):
                    progress = config.load_progress()
                    unlocked = progress.get("unlocked_powerups", ["shield"])
                    
                    if powerup_key not in unlocked:
                        price = self.powerup_system.powerup_prices[powerup_key]
                        if config.spend_money(price):
                            play_click_sound()
                            config.unlock_powerup(powerup_key)
                            print(f"Purchased {powerup_key}!")
                        else:
                            # Different sound for insufficient funds could go here
                            print("Not enough money!")
            
            # Click on Tariq to cycle dialogue
            if hasattr(self.renderer, 'tariq_rect') and self.renderer.tariq_rect.collidepoint(pos):
                play_click_sound()
                self.tariq_dialogue_index = (self.tariq_dialogue_index + 1) % len(self.tariq_dialogues)
            
            # Back button - restore game state instead of starting new game
            if self.back_button.collidepoint(pos):
                play_click_sound()
                if self.stored_game_state:
                    # Restore the game state
                    self.restore_game_state()
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
                    
                    # Trigger game start emote
                    self.emote_system.trigger_emote("game_start", difficulty)
                    
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
            # Check Arms Dealer button
            if self.arms_dealer_game_button and self.arms_dealer_game_button.collidepoint(pos):
                play_click_sound()
                # Store current game state before going to shop
                self.store_game_state()
                self.start_fade(config.SCREEN_GAME, config.SCREEN_ARMS_DEALER)
                return
                
            # Check powerup menu buttons first
            if self.board.current_turn == "white":  # Only player can use powerups
                for powerup_key, button_rect in self.powerup_system.button_rects.items():
                    if button_rect.collidepoint(pos):
                        if self.powerup_system.activate_powerup("white", powerup_key):
                            play_click_sound()
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
                        play_click_sound()
                        self.board.promote_pawn(piece_type)
                        if 'capture' in self.assets.sounds:
                            self.assets.sounds['capture'].play()
                        return
                        
            # Normal game clicks (piece movement) - no click sound for these
            if not self.board.animating and not self.board.promoting:
                row, col = self.board.get_square_from_pos(pos)
                if row >= 0 and col >= 0 and self.board.is_valid_selection(row, col):
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
                if hasattr(self, 'victory_processed'):
                    delattr(self, 'victory_processed')  # Reset victory flag
                self.victory_reward = 0  # Reset reward display
                # Clear chopper mode
                self.chopper_mode = None
                # Clear emotes
                self.emote_system.clear()
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
        
    def update(self):
        """Update game logic."""
        current_time = pygame.time.get_ticks()
        
        # Update intro screen
        if self.current_screen == "intro" and not self.fade_active:
            self.intro_screen.update()
            if self.intro_screen.complete and not self.intro_complete:
                # Start fade transition to main menu
                self.start_fade("intro", config.SCREEN_START)
                self.intro_complete = True  # Prevent multiple fade starts
        
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
                if self.fade_to == config.SCREEN_GAME:
                    if not self.stored_game_state:
                        # Only reset if we're not returning from shop
                        self.board.reset()
                        self.powerup_system = PowerupSystem()  # Reset powerup system
                        self.powerup_system.assets = self.assets  # Pass assets reference
                        self.board.set_powerup_system(self.powerup_system)
                        self.powerup_renderer.powerup_system = self.powerup_system
                        
                        # Apply story mode rules if in story mode
                        if self.current_mode == "story" and self.current_story_battle:
                            self.story_mode.apply_battle_rules(
                                self.current_story_battle,
                                self.board,
                                self.powerup_system,
                                self.ai
                            )
                elif self.fade_to == "story_dialogue":
                    # Initialize dialogue state
                    self.current_dialogue_index = 0
                    self.dialogue_complete = False
                    
        # Update emote system
        if self.emote_system:
            self.emote_system.update()
        
        # Check if chopper gunner was requested
        if self.powerup_system.chopper_gunner_requested:
            self.powerup_system.chopper_gunner_requested = False
            # Create and start chopper mode
            self.chopper_mode = ChopperGunnerMode(self.screen, self.assets, self.board)
            self.chopper_mode.start()
            
        # Check if nuke was requested
        if self.powerup_system.nuke_requested:
            self.powerup_system.nuke_requested = False
            # Nuke explosion will be handled by powerup system animations
            
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
                        
                        # Track capture for killstreaks and emotes
                        self.last_captured_piece = captured
                        capturing_player = "black" if self.board.current_turn == "white" else "white"
                        
                        # Reset opposing player's streak
                        if capturing_player == "white":
                            self.powerup_system.reset_streak("black")
                        else:
                            self.powerup_system.reset_streak("white")
                            
                        # Trigger emotes based on capture
                        if captured[1] in ['Q', 'R', 'B', 'N']:
                            if capturing_player == "black":
                                self.emote_system.trigger_emote("ai_captures", self.selected_difficulty)
                            else:
                                self.emote_system.trigger_emote("capture_major", self.selected_difficulty)
                        elif captured[1] == 'P':
                            if capturing_player == "white":
                                self.emote_system.trigger_emote("capture_pawn", self.selected_difficulty)
                                
                    # Check for streaks after move completes
                    self._check_for_streak_emotes()
                        
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
                            # Always use animation
                            self.board.start_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                        self.ai.start_thinking = None
                        
            # Check for game state emotes
            if not self.board.animating:
                self._check_and_trigger_game_emotes()
                        
            # Check for player victory and unlock next difficulty
            if self.board.game_over and self.board.winner == "white" and self.selected_difficulty:
                if not hasattr(self, 'victory_processed'):
                    self.victory_processed = True
                    
                    # Award money for victory
                    reward = config.VICTORY_REWARDS[self.selected_difficulty]
                    new_total = config.add_money(reward)
                    self.victory_reward = reward  # Store for display
                    print(f"Victory! Earned ${reward}. Total: ${new_total}")
                    
                    # Handle story mode victory
                    if self.current_mode == "story" and self.current_story_battle:
                        # Mark battle as complete
                        self.story_mode.complete_battle(self.current_story_battle["id"], won=True)
                        
                        # Award story rewards
                        if "reward_money" in self.current_story_battle:
                            story_reward = self.current_story_battle["reward_money"]
                            config.add_money(story_reward)
                            self.victory_reward += story_reward
                            
                        if "reward_unlocks" in self.current_story_battle:
                            for unlock in self.current_story_battle["reward_unlocks"]:
                                config.unlock_powerup(unlock)
                    else:
                        # Classic mode - unlock next difficulty
                        next_difficulty = config.unlock_next_difficulty(self.selected_difficulty)
                        if next_difficulty:
                            print(f"Congratulations! You've unlocked {config.AI_DIFFICULTY_NAMES[next_difficulty]} difficulty!")
                    
                    # Trigger victory emote
                    self.emote_system.trigger_emote("checkmate", self.selected_difficulty)
                    
            elif self.board.game_over and self.board.winner == "black":
                # AI victory
                if not hasattr(self, 'defeat_processed'):
                    self.defeat_processed = True
                    
                    # Handle story mode defeat
                    if self.current_mode == "story" and self.current_story_battle:
                        self.story_mode.complete_battle(self.current_story_battle["id"], won=False)
                        
                    # Trigger defeat emote
                    self.emote_system.trigger_emote("checkmate", self.selected_difficulty)
                    
    def _check_for_streak_emotes(self):
        """Check for killstreak milestones and trigger emotes."""
        if not self.ai or not self.emote_system:
            return
            
        # Check player streak
        player_streak = self.powerup_system.current_streak["white"]
        if player_streak == 3:
            self.emote_system.trigger_emote("player_streak_3", self.selected_difficulty)
        elif player_streak == 5:
            self.emote_system.trigger_emote("player_streak_5", self.selected_difficulty)
            
        # Check AI streak
        ai_streak = self.powerup_system.current_streak["black"]
        if ai_streak == 3:
            self.emote_system.trigger_emote("ai_streak_3", self.selected_difficulty)
            
        # Check for broken streaks
        if self.powerup_system.streak_popup and self.powerup_system.streak_popup.get("type") == "broken":
            if self.powerup_system.streak_popup["player"] == "white":
                self.emote_system.trigger_emote("player_streak_broken", self.selected_difficulty)
                    
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
        
        # Create a temporary surface for the game content
        if shake_x != 0 or shake_y != 0:
            game_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
            original_screen = self.screen
            self.screen = game_surface
            self.renderer.screen = game_surface
            self.powerup_renderer.screen = game_surface
        
        # Handle fade transitions
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
            # Normal drawing (no fade)
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
                
            # UI with AI info (always show captured pieces)
            self.renderer.draw_ui(self.board, None, False, self.mouse_pos, 
                                 self.ai, self.selected_difficulty,
                                 show_captured=True)
            self.draw_volume_sliders()
            
            # Add Arms Dealer button in game
            self.draw_arms_dealer_button()
            
            # Powerup menu with killstreak indicator
            self.powerup_renderer.draw_powerup_menu(self.board, self.mouse_pos)
            
            # Draw killstreak UI
            self.draw_killstreak_ui()
            
            # Powerup effects
            self.powerup_renderer.draw_effects(self.board)
            
            # Powerup targeting
            self.powerup_renderer.draw_powerup_targeting(self.board, self.mouse_pos)
            
            # Draw emotes
            if self.emote_system:
                self.emote_system.draw()
            
            # Draw story mode UI if in story mode
            if self.current_mode == "story" and self.current_story_battle:
                self.renderer.draw_story_battle_ui(self.current_story_battle)
            
            # Overlays
            if self.board.promoting:
                self.promotion_rects = self.renderer.draw_promotion_menu(self.board, self.mouse_pos)
            
            # Pass selected difficulty and victory reward to renderer
            if self.board.game_over and self.selected_difficulty:
                if not hasattr(self.board, 'selected_difficulty'):
                    self.board.selected_difficulty = self.selected_difficulty
                if not hasattr(self.board, 'victory_reward'):
                    self.board.victory_reward = self.victory_reward
                if self.current_mode == "story":
                    self.board.is_story_mode = True
                    self.board.story_battle = self.current_story_battle
            self.renderer.draw_game_over(self.board)
            
    def draw_killstreak_ui(self):
        """Draw killstreak counter and notifications."""
        # Draw current streak for player in top-left corner
        player_streak = self.powerup_system.current_streak["white"]
        if player_streak > 0:
            # Position in top-left, below volume controls
            streak_x = 20
            streak_y = 100  # Below the SFX slider
            
            # Get color based on streak level
            bg_color = self.powerup_system._get_streak_color(player_streak)
            dark_color = tuple(c // 3 for c in bg_color)
            
            # Create text
            streak_text = f"KILLSTREAK: {player_streak}"
            font = self.renderer.pixel_fonts['small']
            text_surface = font.render(streak_text, True, config.WHITE)
            
            # Create background box
            padding = 8
            bg_rect = pygame.Rect(streak_x - padding, streak_y - padding,
                                text_surface.get_width() + padding * 2,
                                text_surface.get_height() + padding * 2)
            
            # Draw background
            pygame.draw.rect(self.screen, dark_color, bg_rect, border_radius=5)
            pygame.draw.rect(self.screen, bg_color, bg_rect, 2, border_radius=5)
            
            # Draw text
            self.screen.blit(text_surface, (streak_x, streak_y))
            
            # Show next reward info below
            next_rewards = []
            for streak_num in [3, 5, 7, 10, 15]:
                if player_streak < streak_num and not self.powerup_system.killstreak_rewards[streak_num]["claimed"]["white"]:
                    next_rewards.append((streak_num, self.powerup_system.killstreak_rewards[streak_num]))
                    break
                    
            if next_rewards:
                streak_num, reward_data = next_rewards[0]
                next_text = f"Next: {reward_data['reward'].upper()} at {streak_num}"
                next_font = self.renderer.pixel_fonts['tiny']
                next_surface = next_font.render(next_text, True, (180, 180, 180))
                self.screen.blit(next_surface, (streak_x, streak_y + 25))
        
        # Draw streak popup notification
        if self.powerup_system.streak_popup:
            popup = self.powerup_system.streak_popup
            elapsed = pygame.time.get_ticks() - popup["start_time"]
            
            if elapsed < 3000:  # Show for 3 seconds
                # Position in upper middle area, away from game elements
                popup_x = config.WIDTH // 2
                popup_y = 150  # Below the top UI elements
                
                # Fade in/out
                alpha = 255
                if elapsed < 300:
                    alpha = int(255 * (elapsed / 300))
                elif elapsed > 2700:
                    alpha = int(255 * ((3000 - elapsed) / 300))
                
                # Scale animation for impact
                scale = 1.0
                if elapsed < 200:
                    scale = 0.5 + (elapsed / 200) * 0.5
                
                # Main text
                main_font_size = int(36 * scale)
                main_font = pygame.font.Font(None, main_font_size)
                main_text = main_font.render(popup["text"], True, popup["color"])
                main_text.set_alpha(alpha)
                main_rect = main_text.get_rect(center=(popup_x, popup_y))
                
                # Draw background box
                padding = 15
                bg_rect = main_rect.inflate(padding * 2, padding)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((*config.BLACK, min(200, alpha)))
                self.screen.blit(bg_surface, bg_rect)
                
                # Draw border
                if popup.get("type") == "reward":
                    pygame.draw.rect(self.screen, popup["color"], bg_rect, 2, border_radius=5)
                
                self.screen.blit(main_text, main_rect)
                
                # Subtext
                if "subtext" in popup:
                    sub_font_size = int(20 * scale)
                    sub_font = pygame.font.Font(None, sub_font_size)
                    sub_text = sub_font.render(popup["subtext"], True, (200, 200, 200))
                    sub_text.set_alpha(alpha)
                    sub_rect = sub_text.get_rect(center=(popup_x, popup_y + 30))
                    self.screen.blit(sub_text, sub_rect)
            else:
                # Clear popup after 3 seconds
                self.powerup_system.streak_popup = None
                
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