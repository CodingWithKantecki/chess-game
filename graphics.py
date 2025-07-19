"""
Graphics and Rendering Functions - Enhanced with Mode Selection and Story UI
"""

import pygame
import pygame.gfxdraw
import math
import random
import config

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
        self.intro_start_time = None
        self.intro_jet_triggered = False
        self.intro_sound_played = False
        
        # Fire system
        self.fire_zones = []
        self.fire_particles = []
        self.bomb_explosions = []
        self.last_parallax_offset = 0
        
        # Falling chess pieces system
        self.falling_chess_pieces = []
        self.chess_pieces_enabled = False
        
        # Add missing attributes
        self._fire_updated_this_frame = False
        self.current_screen = None
        self.falling_bombs = []
        self.smoke_particles = []
        
    def update_scale(self, scale):
        """Update scale factor for fullscreen mode."""
        self.scale = scale
        self.pixel_fonts = self.load_pixel_fonts()
        self.board_surface_cache = None
        self.board_cache_scale = None
        
    def load_pixel_fonts(self):
        """Load pixel-style fonts with fallbacks."""
        fonts = {}
        
        pixel_font_names = [
            "Courier",
            "Monaco",
            "Consolas",
            "monospace"
        ]
        
        sizes = {
            'tiny': int(12 * self.scale),
            'small': int(14 * self.scale),
            'medium': int(18 * self.scale),
            'large': int(24 * self.scale),
            'huge': int(36 * self.scale)
        }
        
        for font_name in pixel_font_names:
            try:
                test_font = pygame.font.SysFont(font_name, 12)
                if test_font:
                    for key, size in sizes.items():
                        fonts[key] = pygame.font.SysFont(font_name, size)
                    print(f"Loaded pixel font: {font_name}")
                    return fonts
            except:
                continue
                
        print("Using default monospace font")
        for key, size in sizes.items():
            fonts[key] = pygame.font.Font(pygame.font.get_default_font(), size)
        
        return fonts
        
    def draw_mode_select(self, mode_buttons, back_button, mouse_pos):
        """Draw game mode selection screen."""
        self.draw_parallax_background(1.0)
        
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.pixel_fonts['huge'].render("SELECT GAME MODE", True, config.WHITE)
        title_rect = title.get_rect(center=(config.WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Mode cards - removed blitz and puzzle
        modes = [
            {
                "key": "classic",
                "name": "CLASSIC",
                "desc": "Traditional chess with powerups",
                "icon": "C",
                "color": (70, 150, 70)
            },
            {
                "key": "story",
                "name": "STORY MODE",
                "desc": "Epic campaign with special battles",
                "icon": "S",
                "color": (150, 100, 50)
            },
            {
                "key": "survival",
                "name": "SURVIVAL",
                "desc": "Endless waves of enemies",
                "icon": "X",
                "color": (150, 70, 70)
            }
        ]
        
        # Draw mode buttons as cards
        card_width = 200
        card_height = 250
        cards_per_row = 3
        spacing = 30
        
        start_x = (config.WIDTH - (cards_per_row * card_width + (cards_per_row - 1) * spacing)) // 2
        start_y = 200
        
        mode_buttons.clear()
        
        for i, mode in enumerate(modes):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = start_x + col * (card_width + spacing)
            y = start_y + row * (card_height + spacing)
            
            rect = pygame.Rect(x, y, card_width, card_height)
            mode_buttons[mode["key"]] = rect
            
            # Check hover
            is_hover = rect.collidepoint(mouse_pos)
            
            # Draw card
            card_color = mode["color"] if not is_hover else tuple(min(255, c + 30) for c in mode["color"])
            pygame.draw.rect(self.screen, card_color, rect, border_radius=15)
            pygame.draw.rect(self.screen, config.WHITE, rect, 3, border_radius=15)
            
            # Icon (using text instead of emoji)
            icon_text = self.pixel_fonts['huge'].render(mode["icon"], True, config.WHITE)
            icon_rect = icon_text.get_rect(center=(rect.centerx, rect.y + 60))
            self.screen.blit(icon_text, icon_rect)
            
            # Name
            name_text = self.pixel_fonts['medium'].render(mode["name"], True, config.WHITE)
            name_rect = name_text.get_rect(center=(rect.centerx, rect.y + 120))
            self.screen.blit(name_text, name_rect)
            
            # Description (word wrap)
            desc_lines = self._wrap_text(mode["desc"], self.pixel_fonts['small'], card_width - 20)
            y_offset = rect.y + 160
            for line in desc_lines:
                line_surface = self.pixel_fonts['small'].render(line, True, (200, 200, 200))
                line_rect = line_surface.get_rect(center=(rect.centerx, y_offset))
                self.screen.blit(line_surface, line_rect)
                y_offset += 25
                
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_story_chapters(self, story_mode, chapter_buttons, back_button, mouse_pos):
        """Draw story mode chapter selection."""
        self.draw_parallax_background(0.8)
        
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.pixel_fonts['huge'].render("STORY MODE", True, config.WHITE)
        title_rect = title.get_rect(center=(config.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Overall progress
        total_progress = story_mode.get_total_progress()
        progress_text = f"Campaign Progress: {total_progress}%"
        progress_surface = self.pixel_fonts['medium'].render(progress_text, True, (255, 215, 0))
        progress_rect = progress_surface.get_rect(center=(config.WIDTH // 2, 100))
        self.screen.blit(progress_surface, progress_rect)
        
        # Chapter list
        chapter_buttons.clear()
        y_offset = 150
        
        for i, chapter in enumerate(story_mode.chapters):
            if not chapter.get("battles"):  # Skip epilogue
                continue
                
            # Chapter button
            button_width = 600
            button_height = 80
            button_x = (config.WIDTH - button_width) // 2
            button_y = y_offset
            
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            chapter_buttons[i] = button_rect
            
            # Check if unlocked
            is_unlocked = story_mode.unlocked_chapters[i]
            is_hover = button_rect.collidepoint(mouse_pos) and is_unlocked
            
            # Button color
            if is_unlocked:
                button_color = (50, 50, 70) if not is_hover else (70, 70, 90)
                border_color = (255, 215, 0)
            else:
                button_color = (30, 30, 30)
                border_color = (80, 80, 80)
                
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, button_rect, 3, border_radius=10)
            
            # Chapter number and title
            chapter_text = f"Chapter {i + 1}: {chapter['title']}"
            text_color = config.WHITE if is_unlocked else (100, 100, 100)
            text_surface = self.pixel_fonts['large'].render(chapter_text, True, text_color)
            text_rect = text_surface.get_rect(midleft=(button_x + 20, button_rect.centery - 10))
            self.screen.blit(text_surface, text_rect)
            
            # Progress bar
            progress = story_mode.get_chapter_progress(i)
            bar_width = 200
            bar_height = 10
            bar_x = button_x + button_width - bar_width - 20
            bar_y = button_rect.centery - bar_height // 2
            
            # Background
            pygame.draw.rect(self.screen, (40, 40, 40), 
                           (bar_x, bar_y, bar_width, bar_height), 
                           border_radius=5)
            
            # Progress fill
            if progress > 0:
                fill_width = int(bar_width * progress / 100)
                pygame.draw.rect(self.screen, (100, 200, 100), 
                               (bar_x, bar_y, fill_width, bar_height), 
                               border_radius=5)
                               
            # Progress text
            progress_text = f"{progress}%"
            prog_surface = self.pixel_fonts['tiny'].render(progress_text, True, (200, 200, 200))
            prog_rect = prog_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height + 15))
            self.screen.blit(prog_surface, prog_rect)
            
            # Lock icon if locked
            if not is_unlocked:
                lock_text = "LOCKED"
                lock_surface = self.pixel_fonts['small'].render(lock_text, True, (150, 150, 150))
                lock_rect = lock_surface.get_rect(center=(button_x + 40, button_rect.centery))
                self.screen.blit(lock_surface, lock_rect)
                
            y_offset += button_height + 20
            
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_story_battles(self, chapter, story_mode, battle_buttons, back_button, mouse_pos):
        """Draw battle selection within a chapter."""
        self.draw_parallax_background(0.8)
        
        # Overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Chapter title
        title = self.pixel_fonts['huge'].render(chapter["title"], True, config.WHITE)
        title_rect = title.get_rect(center=(config.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Chapter intro text
        intro_y = 100
        for line in chapter.get("intro", []):
            if line:
                line_surface = self.pixel_fonts['small'].render(line, True, (200, 200, 200))
                line_rect = line_surface.get_rect(center=(config.WIDTH // 2, intro_y))
                self.screen.blit(line_surface, line_rect)
            intro_y += 25
            
        # Battle list
        battle_buttons.clear()
        y_offset = intro_y + 40
        
        for i, battle in enumerate(chapter["battles"]):
            # Battle card
            card_width = 500
            card_height = 120
            card_x = (config.WIDTH - card_width) // 2
            card_y = y_offset
            
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            battle_buttons[i] = card_rect
            
            # Check if completed
            is_completed = story_mode.is_battle_completed(battle["id"])
            is_hover = card_rect.collidepoint(mouse_pos)
            
            # Card color
            if is_completed:
                card_color = (40, 60, 40)  # Green tint
                border_color = (100, 200, 100)
            else:
                card_color = (50, 50, 70) if not is_hover else (70, 70, 90)
                border_color = (200, 200, 200)
                
            pygame.draw.rect(self.screen, card_color, card_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, card_rect, 3, border_radius=10)
            
            # Portrait
            portrait_text = battle.get("portrait", "X")
            portrait_surface = self.pixel_fonts['huge'].render(portrait_text, True, config.WHITE)
            portrait_rect = portrait_surface.get_rect(center=(card_x + 60, card_rect.centery))
            self.screen.blit(portrait_surface, portrait_rect)
            
            # Battle name
            name_text = battle["opponent"]
            name_surface = self.pixel_fonts['large'].render(name_text, True, config.WHITE)
            name_rect = name_surface.get_rect(midleft=(card_x + 100, card_rect.centery - 20))
            self.screen.blit(name_surface, name_rect)
            
            # Difficulty
            diff_text = f"Difficulty: {battle['difficulty'].upper()}"
            diff_color = config.AI_DIFFICULTY_COLORS.get(battle['difficulty'], (200, 200, 200))
            diff_surface = self.pixel_fonts['small'].render(diff_text, True, diff_color)
            diff_rect = diff_surface.get_rect(midleft=(card_x + 100, card_rect.centery + 10))
            self.screen.blit(diff_surface, diff_rect)
            
            # Reward
            reward_text = f"Reward: ${battle.get('reward_money', 0)}"
            reward_surface = self.pixel_fonts['small'].render(reward_text, True, (255, 215, 0))
            reward_rect = reward_surface.get_rect(midleft=(card_x + 100, card_rect.centery + 30))
            self.screen.blit(reward_surface, reward_rect)
            
            # Completion status
            if is_completed:
                complete_text = "✓ COMPLETE"
                complete_surface = self.pixel_fonts['medium'].render(complete_text, True, (100, 255, 100))
                complete_rect = complete_surface.get_rect(midright=(card_x + card_width - 20, card_rect.centery))
                self.screen.blit(complete_surface, complete_rect)
                
            y_offset += card_height + 20
            
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_story_dialogue(self, battle_data, dialogue_index, dialogue_complete):
        """Draw pre-battle dialogue screen."""
        self.draw_parallax_background(0.6)
        
        # Dark overlay
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Character portrait
        portrait_size = 200
        portrait_x = config.WIDTH // 2 - portrait_size // 2
        portrait_y = 100
        
        # Portrait background
        pygame.draw.rect(self.screen, (40, 40, 40), 
                       (portrait_x - 10, portrait_y - 10, portrait_size + 20, portrait_size + 20), 
                       border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 200), 
                       (portrait_x - 10, portrait_y - 10, portrait_size + 20, portrait_size + 20), 
                       3, border_radius=10)
        
        # Portrait emoji/text
        portrait_text = battle_data.get("portrait", "X")
        portrait_surface = pygame.font.Font(None, 120).render(portrait_text, True, config.WHITE)
        portrait_rect = portrait_surface.get_rect(center=(portrait_x + portrait_size // 2, portrait_y + portrait_size // 2))
        self.screen.blit(portrait_surface, portrait_rect)
        
        # Character name
        name_text = battle_data["opponent"]
        name_surface = self.pixel_fonts['large'].render(name_text, True, (255, 215, 0))
        name_rect = name_surface.get_rect(center=(config.WIDTH // 2, portrait_y + portrait_size + 40))
        self.screen.blit(name_surface, name_rect)
        
        # Dialogue box
        dialogue_lines = battle_data.get("pre_battle", [])
        if 0 <= dialogue_index < len(dialogue_lines):
            # Dialogue background
            dialogue_width = 600
            dialogue_height = 150
            dialogue_x = (config.WIDTH - dialogue_width) // 2
            dialogue_y = config.HEIGHT - 250
            
            pygame.draw.rect(self.screen, (20, 20, 30), 
                           (dialogue_x, dialogue_y, dialogue_width, dialogue_height), 
                           border_radius=10)
            pygame.draw.rect(self.screen, (100, 100, 120), 
                           (dialogue_x, dialogue_y, dialogue_width, dialogue_height), 
                           3, border_radius=10)
            
            # Dialogue text
            current_line = dialogue_lines[dialogue_index]
            wrapped_lines = self._wrap_text(current_line, self.pixel_fonts['medium'], dialogue_width - 40)
            
            text_y = dialogue_y + 20
            for line in wrapped_lines:
                line_surface = self.pixel_fonts['medium'].render(line, True, config.WHITE)
                line_rect = line_surface.get_rect(center=(config.WIDTH // 2, text_y))
                self.screen.blit(line_surface, line_rect)
                text_y += 30
                
        # Instructions
        if dialogue_complete:
            inst_text = "Click to start battle!"
            inst_color = (100, 255, 100)
        else:
            inst_text = "Click to continue..."
            inst_color = (200, 200, 200)
            
        inst_surface = self.pixel_fonts['small'].render(inst_text, True, inst_color)
        inst_rect = inst_surface.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 50))
        self.screen.blit(inst_surface, inst_rect)
        
    def draw_story_battle_ui(self, battle_data):
        """Draw UI elements specific to story battles."""
        # Battle name in top left
        battle_text = f"BATTLE: {battle_data['opponent']}"
        battle_surface = self.pixel_fonts['medium'].render(battle_text, True, (255, 215, 0))
        self.screen.blit(battle_surface, (20, 20))
        
        # Special rules indicator
        if battle_data.get("special_rules"):
            rules_text = "SPECIAL RULES ACTIVE"
            rules_surface = self.pixel_fonts['small'].render(rules_text, True, (255, 100, 100))
            self.screen.blit(rules_surface, (20, 50))
            
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, config.WHITE)
            if test_surface.get_width() > max_width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
        
    def _draw_button(self, rect, text, base_color, hover_color, mouse_pos):
        """Helper method to draw a button."""
        is_hover = rect.collidepoint(mouse_pos)
        color = hover_color if is_hover else base_color
        
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, config.WHITE, rect, 3, border_radius=10)
        
        text_surface = self.pixel_fonts['medium'].render(text, True, config.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
        
    def draw_parallax_background(self, brightness=1.0):
        """Draw scrolling background."""
        self.screen.fill((20, 20, 30))
        
        if not hasattr(self.assets, 'parallax_layers') or not self.assets.parallax_layers:
            for y in range(0, config.HEIGHT, 10):
                color_val = int(30 + (y / config.HEIGHT) * 20)
                pygame.draw.rect(self.screen, (color_val, color_val, color_val + 10), 
                               (0, y, config.WIDTH, 10))
            return
            
        self.parallax_offset += 0.3
        
        layers_to_draw = self.assets.parallax_layers
        if self.scale > 1.5 and len(self.assets.parallax_layers) > 6:
            layers_to_draw = self.assets.parallax_layers[::2]
        
        for i, layer in enumerate(layers_to_draw):
            if not layer.get("image"):
                continue
                
            offset = self.parallax_offset * layer["speed"]
            
            if self.scale != 1.0:
                aspect = layer["image"].get_width() / layer["image"].get_height()
                new_h = config.HEIGHT
                new_w = int(new_h * aspect)
                scaled_img = pygame.transform.scale(layer["image"], (new_w, new_h))
                layer_width = new_w
            else:
                scaled_img = layer["image"]
                layer_width = layer.get("width", layer["image"].get_width())
            
            x = -(offset % layer_width)
            while x < config.WIDTH:
                self.screen.blit(scaled_img, (x, 0))
                x += layer_width
                
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
            
    def draw_parallax_background_with_fire(self, brightness=1.0):
        """Draw scrolling background with fire integrated at appropriate depth."""
        self._fire_updated_this_frame = False
        self.screen.fill((20, 20, 30))
        
        if not hasattr(self.assets, 'parallax_layers') or not self.assets.parallax_layers:
            print("WARNING: No parallax layers found in assets!")
            for y in range(0, config.HEIGHT, 10):
                color_val = int(30 + (y / config.HEIGHT) * 20)
                pygame.draw.rect(self.screen, (color_val, color_val, color_val + 10), 
                               (0, y, config.WIDTH, 10))
            
            if brightness < 1.0:
                overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
                overlay.fill(config.BLACK)
                overlay.set_alpha(int((1.0 - brightness) * 255))
                self.screen.blit(overlay, (0, 0))
            return
            
        parallax_delta = self.parallax_offset - self.last_parallax_offset
        self.last_parallax_offset = self.parallax_offset
        self.parallax_offset += 0.3
        
        layers_to_draw = self.assets.parallax_layers
        if self.scale > 1.5 and len(self.assets.parallax_layers) > 6:
            layers_to_draw = self.assets.parallax_layers[::2]
        
        current_time = pygame.time.get_ticks()
        self._fire_updated_this_frame = False
        
        layers_drawn = 0
        for i, layer in enumerate(layers_to_draw):
            if not layer.get("image"):
                print(f"WARNING: Layer {i} has no image!")
                continue
            
            if i == 5:
                self._draw_fire_at_depth(current_time, 0.5)
            elif i == 6:
                self._draw_fire_at_depth(current_time, 0.7)
            elif i == 7:
                self._draw_fire_at_depth(current_time, 0.9)
            
            if i == 4 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.3)
            elif i == 5 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.5)
            elif i == 6 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.7)
            elif i == 7 and self.chess_pieces_enabled:
                self._draw_chess_pieces_at_layer(0.9)
                
            offset = self.parallax_offset * layer["speed"]
            
            if self.scale != 1.0:
                aspect = layer["image"].get_width() / layer["image"].get_height()
                new_h = config.HEIGHT
                new_w = int(new_h * aspect)
                scaled_img = pygame.transform.scale(layer["image"], (new_w, new_h))
                layer_width = new_w
            else:
                scaled_img = layer["image"]
                layer_width = layer.get("width", layer["image"].get_width())
            
            x = -(offset % layer_width)
            positions_drawn = 0
            while x < config.WIDTH:
                self.screen.blit(scaled_img, (x, 0))
                x += layer_width
                positions_drawn += 1
            layers_drawn += 1
                
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
            
        self._fire_updated_this_frame = False
        
    def _draw_fire_at_depth(self, current_time, depth):
        """Draw fire particles at a specific depth layer."""
        if self._fire_updated_this_frame:
            return
            
        if not hasattr(self, 'smoke_particles'):
            self.smoke_particles = []
            
        zones_to_remove = []
        for zone in self.fire_zones:
            zone_screen_x = zone['world_x'] - self.parallax_offset * zone['depth']
            if zone_screen_x < -500:
                zones_to_remove.append(zone)
        
        for zone in zones_to_remove:
            if zone in self.fire_zones:
                self.fire_zones.remove(zone)
            
        for zone in self.fire_zones:
            if zone['depth'] == depth:
                if 'creation_time' in zone:
                    zone_age = (current_time - zone['creation_time']) / 1000.0
                    
                    if zone_age < 10:
                        if zone_age > 5:
                            zone['intensity'] = max(0, 1.0 - (zone_age - 5) / 5.0)
                        else:
                            zone['intensity'] = 1.0
                    else:
                        zone['intensity'] = 0
                        
                    if zone_age > 3 and zone_age < 15 and zone['spawn_timer'] <= 0:
                        smoke_intensity = max(0, 1.0 - (zone_age - 10) / 5.0) if zone_age > 10 else 1.0
                        if random.random() < 0.3 * smoke_intensity:
                            smoke_particle = {
                                'x': zone['world_x'] - self.parallax_offset * depth + random.randint(-zone['width']//2, zone['width']//2),
                                'y': zone['y'] + random.randint(-20, 0),
                                'vx': random.uniform(-0.3, 0.3),
                                'vy': random.uniform(-0.8, -0.3),
                                'size': random.randint(15, 30),
                                'life': 1.0,
                                'depth': depth,
                                'opacity': random.uniform(0.2, 0.4) * smoke_intensity
                            }
                            self.smoke_particles.append(smoke_particle)
                
                if zone['spawn_timer'] <= 0 and zone['intensity'] > 0:
                    num_particles = int(2 * zone['intensity'])
                    for _ in range(max(1, num_particles)):
                        particle = {
                            'x': zone['world_x'] - self.parallax_offset * depth + random.randint(-zone['width']//3, zone['width']//3),
                            'y': zone['y'] + random.randint(0, 10),
                            'vx': random.uniform(-0.5, 0.5),
                            'vy': random.uniform(-1.5, -0.5) * zone['intensity'],
                            'size': random.randint(8, 20) * zone['intensity'],
                            'life': zone['intensity'],
                            'depth': depth,
                            'spike_height': random.uniform(0.5, 1.5),
                            'flicker': random.uniform(0, 6.28)
                        }
                        self.fire_particles.append(particle)
                    zone['spawn_timer'] = random.randint(1, 3)
                else:
                    zone['spawn_timer'] -= 1
        
        fire_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        
        smoke_to_remove = []
        if len(self.smoke_particles) > 50:
            self.smoke_particles = self.smoke_particles[-50:]
            
        for smoke in self.smoke_particles:
            if smoke['depth'] == depth:
                smoke['x'] += smoke['vx']
                smoke['y'] += smoke['vy']
                smoke['vy'] -= 0.02
                smoke['life'] -= 0.008
                smoke['size'] += 0.3
                smoke['vx'] += random.uniform(-0.05, 0.05)
                
                if smoke['life'] <= 0 or smoke['y'] < -100:
                    smoke_to_remove.append(smoke)
                else:
                    screen_x = int(smoke['x'] - self.parallax_offset * depth)
                    screen_y = int(smoke['y'])
                    
                    if 0 <= screen_x <= config.WIDTH:
                        gray_value = int(50 + (1 - smoke['life']) * 100)
                        smoke_color = (gray_value, gray_value, gray_value)
                        alpha = int(smoke['life'] * smoke['opacity'] * 120)
                        size = int(smoke['size'] * self.scale)
                        
                        smoke_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                        for i in range(2):
                            offset_x = random.randint(-3, 3)
                            offset_y = random.randint(-3, 3)
                            pygame.draw.circle(smoke_surf, (*smoke_color, alpha // 2), 
                                             (size + offset_x, size + offset_y), size)
                        fire_surface.blit(smoke_surf, (screen_x - size, screen_y - size))
        
        for smoke in smoke_to_remove:
            if smoke in self.smoke_particles:
                self.smoke_particles.remove(smoke)
        
        particles_to_remove = []
        for particle in self.fire_particles:
            if particle['depth'] == depth:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vy'] -= 0.08
                particle['life'] -= 0.035
                particle['size'] = max(1, particle['size'] - 0.3)
                particle['flicker'] += 0.3
                
                flicker_offset = math.sin(particle['flicker']) * 2
                particle['vx'] += random.uniform(-0.1, 0.1) + flicker_offset * 0.1
                
                if particle['life'] <= 0 or particle['y'] < zone['y'] - 60:
                    particles_to_remove.append(particle)
                else:
                    screen_x = int(particle['x'] - self.parallax_offset * depth)
                    screen_y = int(particle['y'])
                    
                    if particle['life'] > 0.85:
                        base_color = (255, 240, 100)
                        glow_color = (255, 180, 50)
                    elif particle['life'] > 0.6:
                        base_color = (255, 180, 0)
                        glow_color = (255, 120, 0)
                    elif particle['life'] > 0.3:
                        base_color = (255, 100, 0)
                        glow_color = (200, 50, 0)
                    else:
                        base_color = (150, 30, 0)
                        glow_color = (80, 20, 0)
                    
                    alpha = int(particle['life'] * 180)
                    size = int(particle['size'] * self.scale)
                    
                    if 0 <= screen_x <= config.WIDTH and particle['life'] > 0.3:
                        flame_height = int(size * particle['spike_height'])
                        
                        glow_size = int(size * 1.2)
                        glow_surf = pygame.Surface((glow_size * 2, flame_height * 2), pygame.SRCALPHA)
                        glow_alpha = int(alpha * 0.4)
                        
                        for i in range(3):
                            offset_y = i * flame_height // 3
                            radius = glow_size - (i * glow_size // 4)
                            if radius > 0:
                                pygame.draw.circle(glow_surf, (*glow_color, glow_alpha // (i + 1)), 
                                                 (glow_size, glow_size + offset_y), radius)
                        
                        fire_surface.blit(glow_surf, (screen_x - glow_size, screen_y - glow_size), 
                                        special_flags=pygame.BLEND_ADD)
                        
                        particle_surf = pygame.Surface((size * 2, flame_height * 2), pygame.SRCALPHA)
                        for i in range(3):
                            offset_y = i * flame_height // 4
                            radius = size - (i * size // 3)
                            if radius > 0:
                                flame_alpha = max(0, alpha - (i * 30))
                                pygame.draw.circle(particle_surf, (*base_color, flame_alpha), 
                                                 (size, size + offset_y), radius)
                        
                        fire_surface.blit(particle_surf, (screen_x - size, screen_y - size), 
                                        special_flags=pygame.BLEND_ADD)
        
        self.screen.blit(fire_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        for particle in particles_to_remove:
            if particle in self.fire_particles:
                self.fire_particles.remove(particle)
                
    def _draw_chess_pieces_at_layer(self, depth):
        """Draw falling chess pieces at a specific depth layer."""
        for piece in self.falling_chess_pieces:
            if abs(piece['depth'] - depth) < 0.1:
                screen_x = int(piece['x'] - self.parallax_offset * piece['depth'])
                screen_y = int(piece['y'])
                
                if -50 <= screen_x <= config.WIDTH + 50:
                    piece_key = piece['piece']
                    if piece_key in self.assets.pieces:
                        piece_img = self.assets.pieces[piece_key]
                        
                        scale_factor = 0.3 + (piece['depth'] * 0.7)
                        piece_size = int(50 * self.scale * scale_factor)
                        scaled_piece = pygame.transform.scale(piece_img, (piece_size, piece_size))
                        
                        rotated_piece = pygame.transform.rotate(scaled_piece, piece['rotation'])
                        
                        alpha = int(100 + piece['depth'] * 155)
                        rotated_piece.set_alpha(alpha)
                        
                        piece_rect = rotated_piece.get_rect(center=(screen_x, screen_y))
                        self.screen.blit(rotated_piece, piece_rect)
                        
    def _update_chess_pieces(self):
        """Update physics for falling chess pieces."""
        pieces_to_remove = []
        current_time = pygame.time.get_ticks()
        
        if not hasattr(self, 'next_piece_spawn'):
            self.next_piece_spawn = current_time + random.randint(500, 2000)
        
        if current_time >= self.next_piece_spawn and len(self.falling_chess_pieces) < 20:
            piece_types = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
            
            new_piece = {
                'x': random.randint(0, config.WIDTH) + self.parallax_offset * 0.7,
                'y': random.randint(config.HEIGHT // 3, config.HEIGHT // 2),
                'vy': random.uniform(0.5, 1.5),
                'vx': random.uniform(-0.3, 0.3),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-2, 2),
                'piece': random.choice(piece_types),
                'depth': random.choice([0.3, 0.5, 0.7, 0.9])
            }
            self.falling_chess_pieces.append(new_piece)
            self.next_piece_spawn = current_time + random.randint(500, 2000)
        
        for piece in self.falling_chess_pieces:
            piece['x'] += piece['vx']
            piece['y'] += piece['vy']
            piece['rotation'] += piece['rotation_speed']
            
            piece['vy'] += 0.03
            piece['vy'] = min(piece['vy'], 4)
            
            if piece['y'] > config.HEIGHT + 100:
                pieces_to_remove.append(piece)
        
        for piece in pieces_to_remove:
            if piece in self.falling_chess_pieces:
                self.falling_chess_pieces.remove(piece)
                
    def _draw_intro_jet_with_bombs(self, time_elapsed):
        """Draw the intro jet sequence with bomb drops."""
        if not hasattr(self.assets, 'jet_frames') or not self.assets.jet_frames:
            return
            
        jet_start_time = 0
        jet_duration = 4000
        
        if time_elapsed < jet_start_time + jet_duration:
            progress = (time_elapsed - jet_start_time) / jet_duration
            jet_x = -200 + (config.WIDTH + 400) * progress
            jet_y = 100
            
            if not self.intro_sound_played and hasattr(self.assets, 'jet_sound') and self.assets.jet_sound:
                self.assets.jet_sound.play()
                self.intro_sound_played = True
            
            frame_index = int((time_elapsed / 100) % len(self.assets.jet_frames))
            jet_frame = self.assets.jet_frames[frame_index]
            
            jet_scale = 0.3 * self.scale
            jet_width = int(jet_frame.get_width() * jet_scale)
            jet_height = int(jet_frame.get_height() * jet_scale)
            scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
            
            flipped_jet = pygame.transform.flip(scaled_jet, True, False)
            
            self.screen.blit(flipped_jet, (int(jet_x), int(jet_y)))
            
            if not hasattr(self, 'falling_bombs'):
                self.falling_bombs = []
            
            bomb_drop_times = [500, 800, 1100, 1400, 1700, 2000, 2300, 2600, 2900, 3200, 3500]
            
            for drop_time in bomb_drop_times:
                if jet_start_time + drop_time <= time_elapsed < jet_start_time + drop_time + 50:
                    already_dropped = any(b['drop_time'] == drop_time for b in self.falling_bombs)
                    
                    if not already_dropped:
                        bomb_progress = drop_time / jet_duration
                        bomb_x = -200 + (config.WIDTH + 400) * bomb_progress + jet_width // 2
                        
                        self.falling_bombs.append({
                            'x': bomb_x,
                            'y': jet_y + jet_height // 2,
                            'vy': 2,
                            'world_x': bomb_x + self.parallax_offset,
                            'exploded': False,
                            'drop_time': drop_time
                        })
                        
                        if hasattr(self.assets, 'bomb_sound') and self.assets.bomb_sound:
                            self.assets.bomb_sound.play()
        
        if time_elapsed > 1500 and not self.chess_pieces_enabled:
            self.chess_pieces_enabled = True
            
    def draw_board(self):
        """Draw chess board."""
        board_size_scaled = int(config.BOARD_SIZE * self.scale)
        
        if self.board_surface_cache is None or self.board_cache_scale != self.scale:
            self.board_surface_cache = pygame.Surface((board_size_scaled, board_size_scaled), pygame.SRCALPHA)
            self.board_cache_scale = self.scale
            
            if self.assets.board_texture:
                scaled_texture = pygame.transform.scale(self.assets.board_texture, 
                    (board_size_scaled, board_size_scaled))
                self.board_surface_cache.blit(scaled_texture, (0, 0))
                self.board_surface_cache.set_alpha(255)
            else:
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
        
        self.screen.blit(self.board_surface_cache, (config.BOARD_OFFSET_X, config.BOARD_OFFSET_Y))
        pygame.draw.rect(self.screen, (60, 60, 60), 
                        (config.BOARD_OFFSET_X - 2, config.BOARD_OFFSET_Y - 2, 
                         board_size_scaled + 4, board_size_scaled + 4), 2)
                         
    def draw_pieces(self, board, mouse_pos):
        """Draw all pieces."""
        current_time = pygame.time.get_ticks()
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        
        if not hasattr(self, '_scaled_pieces_cache') or self._cache_scale != self.scale:
            self._scaled_pieces_cache = {}
            self._cache_scale = self.scale
            for piece_code, piece_img in self.assets.pieces.items():
                self._scaled_pieces_cache[piece_code] = pygame.transform.scale(
                    piece_img, (square_size_scaled, square_size_scaled))
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if not piece:
                    continue
                    
                if board.dragging and (row, col) == board.drag_start:
                    continue
                if board.animating and (row, col) == board.animation_from:
                    continue
                    
                x, y = board.get_square_pos(row, col)
                scaled_piece = self._scaled_pieces_cache.get(piece)
                if scaled_piece:
                    self.screen.blit(scaled_piece, (x, y))
                    
        if board.animating and board.animation_piece:
            progress = min(1.0, (current_time - board.animation_start) / config.MOVE_ANIMATION_DURATION)
            t = progress * progress * (3.0 - 2.0 * progress)
            
            from_x, from_y = board.get_square_pos(*board.animation_from)
            to_x, to_y = board.get_square_pos(*board.animation_to)
            
            current_x = from_x + (to_x - from_x) * t
            current_y = from_y + (to_y - from_y) * t
            
            scaled_piece = self._scaled_pieces_cache.get(board.animation_piece)
            if scaled_piece:
                self.screen.blit(scaled_piece, (current_x, current_y))
                
        if board.dragging and board.drag_piece:
            scaled_piece = self._scaled_pieces_cache.get(board.drag_piece)
            if scaled_piece:
                rect = scaled_piece.get_rect()
                rect.center = mouse_pos
                self.screen.blit(scaled_piece, rect)
                
    def draw_highlights(self, board):
        """Draw valid move indicators."""
        if not board.selected_piece:
            return
            
        current_time = pygame.time.get_ticks()
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        pulse = math.sin(current_time / 300) * 0.3 + 0.7
        
        for move_row, move_col in board.valid_moves:
            x, y = board.get_square_pos(move_row, move_col)
            center_x = x + square_size_scaled // 2
            center_y = y + square_size_scaled // 2
            
            base_size = int(12 * self.scale)
            size = int(base_size * pulse)
            alpha = int(180 * pulse)
            
            dot_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, (100, 100, 100, alpha), (size, size), size)
            self.screen.blit(dot_surface, (center_x - size, center_y - size))
            
    def draw_ui(self, board, mute_button, music_muted, mouse_pos, ai=None, difficulty=None, show_captured=True):
        """Draw UI elements."""
        ui_width_scaled = int(config.UI_WIDTH * self.scale)
        ui_height_scaled = int(config.UI_HEIGHT * self.scale)
        board_size_scaled = int(config.BOARD_SIZE * self.scale)
        
        board_left = config.BOARD_OFFSET_X
        board_top = config.BOARD_OFFSET_Y
        board_right = config.BOARD_OFFSET_X + board_size_scaled
        board_bottom = config.BOARD_OFFSET_Y + board_size_scaled
        
        ui_color = (0, 0, 0, 200)
        
        ui_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, ui_color, (0, 0, config.WIDTH, board_top))
        pygame.draw.rect(ui_surface, ui_color, (0, board_bottom, config.WIDTH, config.HEIGHT - board_bottom))
        pygame.draw.rect(ui_surface, ui_color, (0, board_top, board_left, board_size_scaled))
        pygame.draw.rect(ui_surface, ui_color, (board_right, board_top, config.WIDTH - board_right, board_size_scaled))
        self.screen.blit(ui_surface, (0, 0))
        
        if ai and board.current_turn == "black" and ai.is_thinking():
            turn_text = "AI IS THINKING..."
        else:
            turn_text = f"CURRENT TURN: {board.current_turn.upper()}"
        text = self.pixel_fonts['large'].render(turn_text, True, config.WHITE)
        rect = text.get_rect(center=(config.WIDTH // 2, board_top // 2))
        self.screen.blit(text, rect)
        
        if ai and difficulty:
            elo_rating = config.AI_DIFFICULTY_ELO.get(difficulty, 1200)
            diff_text = f"VS {config.AI_DIFFICULTY_NAMES[difficulty]} AI (ELO: {elo_rating})"
            text = self.pixel_fonts['small'].render(diff_text, True, config.AI_DIFFICULTY_COLORS[difficulty])
            rect = text.get_rect(center=(config.WIDTH // 2, board_top // 2 + 25 * self.scale))
            self.screen.blit(text, rect)
        
        if not hasattr(self, '_small_pieces_cache') or getattr(self, '_small_cache_scale', None) != self.scale:
            self._small_pieces_cache = {}
            self._small_cache_scale = self.scale
            small_size = int(30 * self.scale)
            for piece_code, piece_img in self.assets.pieces.items():
                self._small_pieces_cache[piece_code] = pygame.transform.scale(
                    piece_img, (small_size, small_size))
        
        if show_captured:
            y_position = board_top + 10 * self.scale
            
            if board.captured_pieces["white"]:
                title = self.pixel_fonts['medium'].render("WHITE CAPTURED:", True, config.WHITE)
                self.screen.blit(title, (10 * self.scale, y_position))
                
                y_offset = y_position + 30 * self.scale
                for i, piece in enumerate(board.captured_pieces["white"][:12]):
                    if piece in self._small_pieces_cache:
                        small = self._small_pieces_cache[piece]
                        if small:
                            self.screen.blit(small, 
                                (10 * self.scale + (i % 4) * 35 * self.scale, 
                                 y_offset + (i // 4) * 35 * self.scale))
                                 
                rows_used = min(3, (len(board.captured_pieces["white"]) + 3) // 4)
                y_position = y_offset + rows_used * 35 * self.scale + 20 * self.scale
            
            if board.captured_pieces["black"]:
                title = self.pixel_fonts['medium'].render("BLACK CAPTURED:", True, config.WHITE)
                self.screen.blit(title, (10 * self.scale, y_position))
                
                y_offset = y_position + 30 * self.scale
                for i, piece in enumerate(board.captured_pieces["black"][:12]):
                    if piece in self._small_pieces_cache:
                        small = self._small_pieces_cache[piece]
                        if small:
                            self.screen.blit(small, 
                                (10 * self.scale + (i % 4) * 35 * self.scale, 
                                 y_offset + (i // 4) * 35 * self.scale))
                        
        if ai and board.current_turn == "black":
            info_text = "AI IS PLAYING..."
        else:
            info_text = "DRAG TO MOVE - CLICK TO SELECT"
        text = self.pixel_fonts['small'].render(info_text, True, config.WHITE)
        rect = text.get_rect(center=(config.WIDTH // 2, 
            board_bottom + (config.HEIGHT - board_bottom) // 2))
        self.screen.blit(text, rect)
        
    def draw_check_indicator(self, board):
        """Draw exclamation mark above king if in check."""
        if not board.is_in_check():
            return
            
        king_pos = board.find_king(board.current_turn)
        if not king_pos:
            return
            
        row, col = king_pos
        x, y = board.get_square_pos(row, col)
        square_size_scaled = int(config.SQUARE_SIZE * self.scale)
        
        exc_x = x + square_size_scaled - int(15 * self.scale)
        exc_y = y + int(10 * self.scale)
        
        exc_text = self.pixel_fonts['small'].render("!", True, (255, 0, 0))
        exc_rect = exc_text.get_rect(center=(exc_x, exc_y))
        self.screen.blit(exc_text, exc_rect)
        
    def draw_promotion_menu(self, board, mouse_pos):
        """Draw pawn promotion menu."""
        if not board.promoting:
            return []
            
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(config.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        menu_w = int(300 * self.scale)
        menu_h = int(100 * self.scale)
        menu_x = config.WIDTH // 2 - menu_w // 2
        menu_y = config.HEIGHT // 2 - menu_h // 2
        
        pygame.draw.rect(self.screen, (50, 50, 50), 
            (menu_x - 5, menu_y - 5, menu_w + 10, menu_h + 10))
        pygame.draw.rect(self.screen, (200, 200, 200), (menu_x, menu_y, menu_w, menu_h))
        pygame.draw.rect(self.screen, config.BLACK, (menu_x, menu_y, menu_w, menu_h), 3)
        
        text = self.pixel_fonts['medium'].render("CHOOSE PROMOTION:", True, config.BLACK)
        rect = text.get_rect(centerx=menu_x + menu_w // 2, y=menu_y + 10 * self.scale)
        self.screen.blit(text, rect)
        
        pieces = ["Q", "R", "B", "N"]
        size = int(50 * self.scale)
        spacing = int(10 * self.scale)
        total_w = len(pieces) * size + (len(pieces) - 1) * spacing
        start_x = menu_x + (menu_w - total_w) // 2
        
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
            
            rect = pygame.Rect(x, y, size, size)
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (100, 200, 100), 
                    (x - 2, y - 2, size + 4, size + 4))
                
            piece_key = board.promotion_color + piece_type
            scaled = self._promo_pieces_cache.get(piece_key)
            if scaled:
                self.screen.blit(scaled, (x, y))
                
            rects.append((rect, piece_type))
            
        return rects
        
    def draw_game_over(self, board):
        """Draw game over screen with story mode support."""
        if not board.game_over:
            return
            
        current_time = pygame.time.get_ticks()
        
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(config.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if board.winner == "white":
            pulse = math.sin(current_time / 200) * 0.1 + 0.9
            victory_size = int(48 * self.scale * pulse)
            victory_font = pygame.font.SysFont("Courier", victory_size)
            victory_text = victory_font.render("VICTORY!", True, (255, 215, 0))
            victory_rect = victory_text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 120 * self.scale))
            self.screen.blit(victory_text, victory_rect)
            
            star_count = 8
            star_radius = 80 * self.scale
            for i in range(star_count):
                angle = (i / star_count) * 2 * math.pi + current_time / 1000
                star_x = victory_rect.centerx + math.cos(angle) * star_radius
                star_y = victory_rect.centery + math.sin(angle) * star_radius
                self._draw_star(star_x, star_y, 15 * self.scale, (255, 255, 100))
            
            if hasattr(board, 'victory_reward') and board.victory_reward > 0:
                coin_y = config.HEIGHT // 2 - 40 * self.scale
                coin_x = config.WIDTH // 2 - 80 * self.scale
                pygame.draw.circle(self.screen, (255, 215, 0), (int(coin_x), int(coin_y)), int(20 * self.scale))
                pygame.draw.circle(self.screen, (255, 255, 100), (int(coin_x), int(coin_y)), int(20 * self.scale), 2)
                coin_text = self.pixel_fonts['large'].render("$", True, (180, 150, 0))
                coin_rect = coin_text.get_rect(center=(coin_x, coin_y))
                self.screen.blit(coin_text, coin_rect)
                
                reward_text = f"EARNED ${board.victory_reward}!"
                text = self.pixel_fonts['large'].render(reward_text, True, (255, 255, 255))
                rect = text.get_rect(center=(config.WIDTH // 2 + 20 * self.scale, coin_y))
                self.screen.blit(text, rect)
            
            if hasattr(board, 'is_story_mode') and board.is_story_mode and hasattr(board, 'story_battle'):
                battle = board.story_battle
                if "victory" in battle:
                    victory_dialogue_y = config.HEIGHT // 2
                    for line in battle["victory"]:
                        if line:
                            line_surface = self.pixel_fonts['small'].render(line, True, (200, 200, 200))
                            line_rect = line_surface.get_rect(center=(config.WIDTH // 2, victory_dialogue_y))
                            self.screen.blit(line_surface, line_rect)
                            victory_dialogue_y += 25
            
            if hasattr(board, 'selected_difficulty') and not hasattr(board, 'is_story_mode'):
                progress = config.load_progress()
                current_index = config.AI_DIFFICULTIES.index(board.selected_difficulty) if board.selected_difficulty in config.AI_DIFFICULTIES else -1
                
                if current_index >= 0 and current_index < len(config.AI_DIFFICULTIES) - 1:
                    next_diff = config.AI_DIFFICULTIES[current_index + 1]
                    if next_diff not in progress.get("unlocked_difficulties", []):
                        unlock_y = config.HEIGHT // 2 + 20 * self.scale
                        self._draw_unlock_icon(config.WIDTH // 2 - 100 * self.scale, unlock_y)
                        
                        unlock_text = f"{config.AI_DIFFICULTY_NAMES[next_diff]} DIFFICULTY UNLOCKED!"
                        text = self.pixel_fonts['medium'].render(unlock_text, True, (255, 215, 0))
                        rect = text.get_rect(center=(config.WIDTH // 2 + 20 * self.scale, unlock_y))
                        self.screen.blit(text, rect)
            
            stats_y = config.HEIGHT // 2 + 80 * self.scale
            stats_width = 300 * self.scale
            stats_height = 80 * self.scale
            stats_x = config.WIDTH // 2 - stats_width // 2
            
            pygame.draw.rect(self.screen, (40, 40, 40), 
                           (stats_x, stats_y, stats_width, stats_height), 
                           border_radius=10)
            pygame.draw.rect(self.screen, (255, 215, 0), 
                           (stats_x, stats_y, stats_width, stats_height), 2, 
                           border_radius=10)
            
            pieces_captured = len(board.captured_pieces["black"])
            pieces_lost = len(board.captured_pieces["white"])
            
            stats_text = [
                f"Pieces Captured: {pieces_captured}",
                f"Pieces Lost: {pieces_lost}"
            ]
            
            y_offset = stats_y + 20 * self.scale
            for stat in stats_text:
                text = self.pixel_fonts['small'].render(stat, True, (200, 200, 200))
                rect = text.get_rect(center=(config.WIDTH // 2, y_offset))
                self.screen.blit(text, rect)
                y_offset += 25 * self.scale
                
        else:
            defeat_text = "DEFEAT"
            text = self.pixel_fonts['huge'].render(defeat_text, True, (200, 50, 50))
            rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 80 * self.scale))
            self.screen.blit(text, rect)
            
            if hasattr(board, 'is_story_mode') and board.is_story_mode and hasattr(board, 'story_battle'):
                battle = board.story_battle
                if "defeat" in battle:
                    defeat_dialogue_y = config.HEIGHT // 2 - 20 * self.scale
                    for line in battle["defeat"]:
                        if line:
                            line_surface = self.pixel_fonts['small'].render(line, True, (200, 200, 200))
                            line_rect = line_surface.get_rect(center=(config.WIDTH // 2, defeat_dialogue_y))
                            self.screen.blit(line_surface, line_rect)
                            defeat_dialogue_y += 25
                else:
                    encourage_text = "Better luck next time!"
                    text = self.pixel_fonts['medium'].render(encourage_text, True, (150, 150, 150))
                    rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 20 * self.scale))
                    self.screen.blit(text, rect)
        
        button_y = config.HEIGHT // 2 + 160 * self.scale
        button_width = 140 * self.scale
        button_height = 40 * self.scale
        button_spacing = 20 * self.scale
        
        restart_x = config.WIDTH // 2 - button_width - button_spacing // 2
        restart_rect = pygame.Rect(restart_x, button_y, button_width, button_height)
        restart_color = (70, 150, 70) if restart_rect.collidepoint(pygame.mouse.get_pos()) else (50, 100, 50)
        pygame.draw.rect(self.screen, restart_color, restart_rect, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), restart_rect, 2, border_radius=5)
        
        restart_text = self.pixel_fonts['small'].render("RESTART (R)", True, (255, 255, 255))
        restart_text_rect = restart_text.get_rect(center=restart_rect.center)
        self.screen.blit(restart_text, restart_text_rect)
        
        menu_x = config.WIDTH // 2 + button_spacing // 2
        menu_rect = pygame.Rect(menu_x, button_y, button_width, button_height)
        menu_color = (150, 70, 70) if menu_rect.collidepoint(pygame.mouse.get_pos()) else (100, 50, 50)
        pygame.draw.rect(self.screen, menu_color, menu_rect, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), menu_rect, 2, border_radius=5)
        
        menu_text = self.pixel_fonts['small'].render("MENU (ESC)", True, (255, 255, 255))
        menu_text_rect = menu_text.get_rect(center=menu_rect.center)
        self.screen.blit(menu_text, menu_text_rect)
        
    def _draw_star(self, x, y, size, color):
        """Helper method to draw a star."""
        points = []
        for i in range(10):
            angle = (i * math.pi / 5) - math.pi / 2
            if i % 2 == 0:
                r = size
            else:
                r = size * 0.5
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(self.screen, color, points)
        
    def _draw_unlock_icon(self, x, y):
        """Helper method to draw an unlock padlock icon."""
        pygame.draw.rect(self.screen, (255, 215, 0), 
                        (x - 15, y - 10, 30, 20), 
                        border_radius=3)
        pygame.draw.arc(self.screen, (255, 215, 0), 
                       (x - 12, y - 20, 24, 20), 
                       0, math.pi, 3)
        pygame.draw.circle(self.screen, (40, 40, 40), (int(x), int(y)), 3)
        
    def draw_difficulty_menu(self, difficulty_buttons, back_button, mouse_pos):
        """Draw difficulty selection menu."""
        self.draw_parallax_background(1.0)
        
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        text = self.pixel_fonts['huge'].render("SELECT DIFFICULTY", True, config.WHITE)
        rect = text.get_rect(center=(game_center_x, game_center_y - 250 * config.SCALE))
        self.screen.blit(text, rect)
        
        progress = config.load_progress()
        unlocked = progress.get("unlocked_difficulties", ["easy"])
        
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
            
            pygame.draw.rect(self.screen, hover_color if is_hover else color, button, border_radius=10)
            pygame.draw.rect(self.screen, border_color, button, 3, border_radius=10)
            
            text = config.AI_DIFFICULTY_NAMES[difficulty]
            text_surface = self.pixel_fonts['large'].render(text, True, config.WHITE)
            text_rect = text_surface.get_rect(center=button.center)
            self.screen.blit(text_surface, text_rect)
            
            descriptions = {
                "easy": f"Beginner friendly (ELO: {config.AI_DIFFICULTY_ELO['easy']})",
                "medium": f"Casual player (ELO: {config.AI_DIFFICULTY_ELO['medium']})", 
                "hard": f"Experienced player (ELO: {config.AI_DIFFICULTY_ELO['hard']})",
                "very_hard": f"Expert level (ELO: {config.AI_DIFFICULTY_ELO['very_hard']})"
            }
            
            if is_unlocked:
                difficulty_index = config.AI_DIFFICULTIES.index(difficulty)
                if difficulty_index > 0 and difficulty_index == len(unlocked) - 1 and difficulty != "very_hard":
                    desc_text = "★ BEAT THIS TO UNLOCK NEXT ★"
                    desc_color = (255, 215, 0)
                else:
                    desc_text = descriptions[difficulty]
                    desc_color = (200, 200, 200)
            else:
                difficulty_index = config.AI_DIFFICULTIES.index(difficulty)
                prev_difficulty = config.AI_DIFFICULTIES[difficulty_index - 1]
                desc_text = f"Beat {config.AI_DIFFICULTY_NAMES[prev_difficulty]} to unlock"
                desc_color = (150, 150, 150)
            
            desc = self.pixel_fonts['small'].render(desc_text, True, desc_color)
            desc_rect = desc.get_rect(center=(button.centerx, button.bottom + 10 * config.SCALE))
            self.screen.blit(desc, desc_rect)
            
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_menu(self, screen_type, buttons, mouse_pos):
        """Draw menu screens."""
        self.current_screen = screen_type
        
        if screen_type == config.SCREEN_START:
            self.draw_parallax_background_with_fire(1.2)
        else:
            self.draw_parallax_background(1.2)
        
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80 if screen_type == config.SCREEN_START else 120))
        self.screen.blit(overlay, (0, 0))
        
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        if screen_type == config.SCREEN_START:
            if self.intro_start_time is None:
                self.intro_start_time = pygame.time.get_ticks()
                self.intro_jet_triggered = True
                
            current_time = pygame.time.get_ticks()
            time_since_start = current_time - self.intro_start_time
            
            if not hasattr(self, 'high_flying_jets'):
                self.high_flying_jets = []
                self.next_high_jet_spawn = current_time + random.randint(15000, 30000)
            
            if current_time >= self.next_high_jet_spawn:
                self.high_flying_jets.append({
                    'x': -100,
                    'y': random.randint(50, 150),
                    'speed': random.uniform(5, 8),
                    'scale': random.uniform(0.15, 0.25)
                })
                self.next_high_jet_spawn = current_time + random.randint(20000, 40000)
            
            jets_to_remove = []
            for jet in self.high_flying_jets:
                jet['x'] += jet['speed']
                
                if hasattr(self.assets, 'jet_frames') and self.assets.jet_frames:
                    frame_index = int((current_time / 200) % len(self.assets.jet_frames))
                    jet_frame = self.assets.jet_frames[frame_index]
                    
                    jet_width = int(jet_frame.get_width() * jet['scale'])
                    jet_height = int(jet_frame.get_height() * jet['scale'])
                    scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
                    
                    flipped_jet = pygame.transform.flip(scaled_jet, True, False)
                    flipped_jet.set_alpha(180)
                    
                    self.screen.blit(flipped_jet, (int(jet['x']), int(jet['y'])))
                
                if jet['x'] > config.WIDTH + 100:
                    jets_to_remove.append(jet)
            
            for jet in jets_to_remove:
                self.high_flying_jets.remove(jet)
            
            if self.chess_pieces_enabled:
                self._update_chess_pieces()
            
            if self.intro_jet_triggered:
                self._draw_intro_jet_with_bombs(time_since_start)
                
            if hasattr(self, 'falling_bombs') and self.falling_bombs:
                bombs_to_remove = []
                for bomb in self.falling_bombs:
                    if not bomb['exploded']:
                        bomb['y'] += bomb['vy']
                        bomb['vy'] += 0.5
                        
                        if bomb['y'] >= config.HEIGHT - 80:
                            bomb['exploded'] = True
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
                                    'depth': layer['depth'],
                                    'creation_time': pygame.time.get_ticks()
                                })
                            
                            bombs_to_remove.append(bomb)
                        elif bomb['y'] > config.HEIGHT + 100:
                            bombs_to_remove.append(bomb)
                            
                for bomb in bombs_to_remove:
                    if bomb in self.falling_bombs:
                        self.falling_bombs.remove(bomb)
                
            if hasattr(self, 'falling_bombs'):
                for bomb in self.falling_bombs:
                    if not bomb['exploded']:
                        bomb_width = int(8 * self.scale)
                        bomb_height = int(16 * self.scale)
                        
                        pygame.draw.ellipse(self.screen, (60, 60, 60), 
                                          (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2, 
                                           bomb_width, bomb_height))
                        pygame.draw.ellipse(self.screen, (40, 40, 40), 
                                          (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2, 
                                           bomb_width, bomb_height), 1)
                        
                        nose_points = [
                            (bomb['x'] - bomb_width//2, bomb['y'] + bomb_height//2 - 2),
                            (bomb['x'] + bomb_width//2, bomb['y'] + bomb_height//2 - 2),
                            (bomb['x'], bomb['y'] + bomb_height//2 + bomb_width//2)
                        ]
                        pygame.draw.polygon(self.screen, (50, 50, 50), nose_points)
                        
                        fin_height = int(5 * self.scale)
                        pygame.draw.polygon(self.screen, (70, 70, 70), [
                            (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2),
                            (bomb['x'] - bomb_width//2 - 3, bomb['y'] - bomb_height//2 - fin_height),
                            (bomb['x'] - bomb_width//2, bomb['y'] - bomb_height//2 + 2)
                        ])
                        pygame.draw.polygon(self.screen, (70, 70, 70), [
                            (bomb['x'] + bomb_width//2, bomb['y'] - bomb_height//2),
                            (bomb['x'] + bomb_width//2 + 3, bomb['y'] - bomb_height//2 - fin_height),
                            (bomb['x'] + bomb_width//2, bomb['y'] - bomb_height//2 + 2)
                        ])
                
            text = self.pixel_fonts['huge'].render("CHECKMATE PROTOCOL", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, game_center_y - 150 * config.SCALE))
            self.screen.blit(text, rect)
            
            if hasattr(self.assets, 'beta_badge') and self.assets.beta_badge:
                badge_height = int(80 * config.SCALE)
                aspect_ratio = self.assets.beta_badge.get_width() / self.assets.beta_badge.get_height()
                badge_width = int(badge_height * aspect_ratio)
                
                scaled_badge = pygame.transform.scale(self.assets.beta_badge, (badge_width, badge_height))
                rotated_badge = pygame.transform.rotate(scaled_badge, -15)
                
                badge_x = rect.right - int(20 * config.SCALE)
                badge_y = rect.top - int(70 * config.SCALE)
                
                self.screen.blit(rotated_badge, (badge_x, badge_y))
            
            self._draw_button(buttons['play'], "PLAY GAME", (70, 150, 70), (100, 200, 100), mouse_pos)
            self._draw_button(buttons['tutorial'], "TUTORIAL", (70, 100, 150), (100, 130, 200), mouse_pos)
            self._draw_button(buttons['beta'], "BETA TEST INFO", (150, 150, 70), (200, 200, 100), mouse_pos)
            self._draw_button(buttons['credits'], "CREDITS", (70, 70, 150), (100, 100, 200), mouse_pos)
            
        elif screen_type == config.SCREEN_CREDITS:
            text = self.pixel_fonts['huge'].render("CREDITS", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, config.GAME_OFFSET_Y + 60 * config.SCALE))
            self.screen.blit(text, rect)
            
            y = config.GAME_OFFSET_Y + 140 * config.SCALE
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
                y += 28 * config.SCALE
                
            self._draw_button(buttons['back'], "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
            
        elif screen_type == config.SCREEN_BETA:
            text = self.pixel_fonts['huge'].render("BETA TEST", True, config.WHITE)
            rect = text.get_rect(center=(game_center_x, config.GAME_OFFSET_Y + 80 * config.SCALE))
            self.screen.blit(text, rect)
            
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
            
            self._draw_button(buttons['back'], "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
            
    def draw_tutorial(self, tutorial_page_data, tutorial_buttons, mouse_pos):
        """Draw tutorial screen with navigation."""
        self.draw_parallax_background(1.0)
        
        tutorial_page = tutorial_page_data['page']
        current_index = tutorial_page_data['current_index']
        total_pages = tutorial_page_data['total_pages']
        
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        text = self.pixel_fonts['huge'].render("TUTORIAL", True, config.WHITE)
        rect = text.get_rect(center=(game_center_x, game_center_y - 250 * config.SCALE))
        self.screen.blit(text, rect)
        
        page_text = f"Page {current_index + 1}/{total_pages}"
        page_surface = self.pixel_fonts['small'].render(page_text, True, (200, 200, 200))
        page_rect = page_surface.get_rect(center=(game_center_x, game_center_y - 200 * config.SCALE))
        self.screen.blit(page_surface, page_rect)
        
        y = game_center_y - 150 * config.SCALE
        
        if "title" in tutorial_page:
            title_surface = self.pixel_fonts['large'].render(tutorial_page["title"], True, (255, 215, 0))
            title_rect = title_surface.get_rect(center=(game_center_x, y))
            self.screen.blit(title_surface, title_rect)
            y += 50 * config.SCALE
        
        if "content" in tutorial_page:
            for line in tutorial_page["content"]:
                if line:
                    if line.startswith("•"):
                        color = (200, 200, 200)
                    elif "=" in line:
                        color = (255, 215, 0)
                    else:
                        color = (200, 200, 200)
                    
                    text_surface = self.pixel_fonts['medium'].render(line, True, color)
                    text_rect = text_surface.get_rect(center=(game_center_x, y))
                    self.screen.blit(text_surface, text_rect)
                y += 35 * config.SCALE
        
        if current_index > 0:
            self._draw_button(tutorial_buttons['prev'], "PREVIOUS", (100, 100, 100), (150, 150, 150), mouse_pos)
        
        if current_index < total_pages - 1:
            self._draw_button(tutorial_buttons['next'], "NEXT", (100, 100, 100), (150, 150, 150), mouse_pos)
        
        self._draw_button(tutorial_buttons['back'], "BACK TO MENU", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_arms_dealer(self, powerup_system, shop_buttons, back_button, mouse_pos, dialogue_index=0, dialogues=None):
        """Draw the arms dealer shop with Tariq character."""
        if hasattr(self.assets, 'arms_background') and self.assets.arms_background:
            scaled_bg = pygame.transform.scale(self.assets.arms_background, (config.WIDTH, config.HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
        else:
            self.draw_parallax_background(0.6)
            
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        if hasattr(self.assets, 'tariq_image') and self.assets.tariq_image:
            tariq_height = int(450 * config.SCALE)
            aspect_ratio = self.assets.tariq_image.get_width() / self.assets.tariq_image.get_height()
            tariq_width = int(tariq_height * aspect_ratio)
            scaled_tariq = pygame.transform.smoothscale(self.assets.tariq_image, (tariq_width, tariq_height))
            
            tariq_x = int(50 * config.SCALE)
            tariq_y = config.HEIGHT - tariq_height
            
            self.screen.blit(scaled_tariq, (tariq_x, tariq_y))
            
            self.tariq_rect = pygame.Rect(tariq_x, tariq_y, tariq_width, tariq_height)
            
            if dialogues and 0 <= dialogue_index < len(dialogues):
                dialogue = dialogues[dialogue_index]
                bubble_width = int(300 * config.SCALE)
                tariq_center_x = tariq_x + tariq_width // 2
                bubble_x = tariq_center_x - bubble_width // 2
                bubble_y = tariq_y - int(120 * config.SCALE)
                self._draw_speech_bubble(bubble_x, bubble_y, 
                                       dialogue, bubble_width, point_down=True)
        
        title = self.pixel_fonts['huge'].render("ARMS DEALER", True, (255, 100, 100))
        title_rect = title.get_rect(center=(game_center_x, game_center_y - 280 * config.SCALE))
        self.screen.blit(title, title_rect)
        
        progress = config.load_progress()
        money = progress.get("money", 0)
        money_text = self.pixel_fonts['large'].render(f"FUNDS: ${money}", True, (255, 215, 0))
        money_rect = money_text.get_rect(center=(game_center_x, game_center_y - 220 * config.SCALE))
        self.screen.blit(money_text, money_rect)
        
        unlocked = progress.get("unlocked_powerups", ["shield"])
        
        card_width = int(120 * self.scale)
        card_height = int(160 * self.scale)
        card_spacing = int(15 * self.scale)
        
        powerup_keys = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
        total_width = len(powerup_keys) * card_width + (len(powerup_keys) - 1) * card_spacing
        start_x = game_center_x - total_width // 2 + int(100 * self.scale)
        
        shop_buttons.clear()
        
        for i, powerup_key in enumerate(powerup_keys):
            powerup = powerup_system.powerups[powerup_key]
            price = powerup_system.powerup_prices[powerup_key]
            is_unlocked = powerup_key in unlocked
            can_afford = money >= price and not is_unlocked
            
            card_x = start_x + i * (card_width + card_spacing)
            card_y = game_center_y - 40 * self.scale
            
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            shop_buttons[powerup_key] = card_rect
            
            if is_unlocked:
                card_color = (50, 100, 50)
                border_color = (100, 255, 100)
            elif can_afford:
                card_color = (70, 70, 40)
                border_color = (255, 215, 0)
            else:
                card_color = (40, 40, 40)
                border_color = (80, 80, 80)
            
            if card_rect.collidepoint(mouse_pos) and not is_unlocked:
                card_color = tuple(min(255, c + 20) for c in card_color)
            
            pygame.draw.rect(self.screen, card_color, card_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, card_rect, 3, border_radius=10)
            
            if powerup_key == "gun" and hasattr(self, 'assets') and hasattr(self.assets, 'revolver_image') and self.assets.revolver_image:
                icon_size = 25
                scaled_revolver = pygame.transform.scale(self.assets.revolver_image, (icon_size, icon_size))
                
                if not can_afford:
                    gray_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                    for x in range(icon_size):
                        for y in range(icon_size):
                            r, g, b, a = scaled_revolver.get_at((x, y))
                            gray = int(0.3 * r + 0.59 * g + 0.11 * b)
                            gray_surface.set_at((x, y), (gray, gray, gray, a))
                    scaled_revolver = gray_surface
                
                icon_rect = scaled_revolver.get_rect(centerx=card_rect.centerx, y=card_rect.y + 12)
                self.screen.blit(scaled_revolver, icon_rect)
            elif powerup_key == "chopper":
                self._draw_helicopter_icon(card_rect, can_afford)
            else:
                icon_size = 30
                icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                icon_surface.fill((0, 0, 0, 0))
                
                if powerup_key == "airstrike":
                    self._draw_missile_icon(icon_surface, icon_size, can_afford)
                elif powerup_key == "shield":
                    self._draw_shield_icon(icon_surface, icon_size, can_afford)
                elif powerup_key == "paratroopers":
                    self._draw_parachute_icon(icon_surface, icon_size, can_afford)
                else:
                    icon_color = config.WHITE if can_afford else (80, 80, 80)
                    icon_surface = self.pixel_fonts['large'].render(powerup["icon"], True, icon_color)
                
                icon_rect = icon_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 10)
                self.screen.blit(icon_surface, icon_rect)
            
            name_color = (0, 255, 0) if can_afford else (80, 80, 80)
            name_surface = self.pixel_fonts['small'].render(powerup["name"], True, name_color)
            name_rect = name_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 35)
            self.screen.blit(name_surface, name_rect)
            
            cost_text = f"Cost: {powerup['cost']}"
            cost_color = (255, 204, 0) if can_afford else (80, 80, 80)
            cost_surface = self.pixel_fonts['tiny'].render(cost_text, True, cost_color)
            cost_rect = cost_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 55)
            self.screen.blit(cost_surface, cost_rect)
            
            if is_unlocked:
                status_text = "OWNED"
                status_color = (100, 255, 100)
            else:
                status_text = f"${price}"
                status_color = (255, 215, 0) if can_afford else (200, 100, 100)
            
            status_surface = self.pixel_fonts['medium'].render(status_text, True, status_color)
            status_rect = status_surface.get_rect(center=(card_rect.centerx, card_rect.bottom - 15 * self.scale))
            self.screen.blit(status_surface, status_rect)
        
        inst_text = "Click on items to purchase. Click Tariq for more info!"
        inst_surface = self.pixel_fonts['small'].render(inst_text, True, (200, 200, 200))
        inst_rect = inst_surface.get_rect(center=(game_center_x, game_center_y + 170 * self.scale))
        self.screen.blit(inst_surface, inst_rect)
        
        self._draw_button(back_button, "BACK TO GAME", (150, 70, 70), (200, 100, 100), mouse_pos)

    def _draw_speech_bubble(self, x, y, text, width, point_down=False):
        """Draw a speech bubble with text."""
        padding = int(20 * self.scale)
        line_height = int(20 * self.scale)
        
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_surface = self.pixel_fonts['small'].render(test_line, True, config.BLACK)
            if text_surface.get_width() > width - 2 * padding:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        height = len(lines) * line_height + 2 * padding
        
        bubble_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (255, 255, 255), bubble_rect, border_radius=15)
        pygame.draw.rect(self.screen, (0, 0, 0), bubble_rect, 3, border_radius=15)
        
        if point_down:
            tail_points = [
                (x + width // 2 - 15, y + height),
                (x + width // 2, y + height + 20),
                (x + width // 2 + 15, y + height)
            ]
            pygame.draw.polygon(self.screen, (255, 255, 255), tail_points)
            pygame.draw.lines(self.screen, (0, 0, 0), False, 
                            [(tail_points[0][0], tail_points[0][1] - 1),
                             tail_points[1],
                             (tail_points[2][0], tail_points[2][1] - 1)], 3)
        
        for i, line in enumerate(lines):
            text_surface = self.pixel_fonts['small'].render(line, True, config.BLACK)
            text_rect = text_surface.get_rect(centerx=x + width // 2, 
                                             y=y + padding + i * line_height)
            self.screen.blit(text_surface, text_rect)

    def _draw_shield_icon(self, surface, size, enabled=True):
        """Draw a shield icon."""
        color = (200, 200, 200) if enabled else (80, 80, 80)
        center = size // 2
        
        points = [
            (center, 5),
            (size - 5, 10),
            (size - 5, size // 2),
            (center, size - 5),
            (5, size // 2),
            (5, 10)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (0, 0, 0), points, 2)

    def _draw_missile_icon(self, surface, size, enabled=True):
        """Draw a missile/airstrike icon."""
        color = (200, 50, 50) if enabled else (80, 80, 80)
        center = size // 2
        
        pygame.draw.rect(surface, color, (center - 3, 8, 6, 15))
        
        pygame.draw.polygon(surface, color, [
            (center - 3, 8),
            (center, 3),
            (center + 3, 8)
        ])
        
        pygame.draw.polygon(surface, color, [
            (center - 6, 20),
            (center - 3, 23),
            (center - 3, 18)
        ])
        pygame.draw.polygon(surface, color, [
            (center + 6, 20),
            (center + 3, 23),
            (center + 3, 18)
        ])

    def _draw_parachute_icon(self, surface, size, enabled=True):
        """Draw a parachute icon."""
        color = (100, 150, 200) if enabled else (80, 80, 80)
        center = size // 2
        
        pygame.draw.arc(surface, color, (5, 5, size - 10, size // 2), 0, 3.14, 3)
        
        for x in [8, center, size - 8]:
            pygame.draw.line(surface, color, (x, 5 + size // 4), 
                           (center, size - 8), 1)
        
        pygame.draw.circle(surface, color, (center, size - 8), 3)

    def _draw_helicopter_icon(self, card_rect, enabled=True):
        """Draw a helicopter icon directly on screen."""
        color = (100, 100, 150) if enabled else (80, 80, 80)
        
        heli_x = card_rect.centerx
        heli_y = card_rect.y + 20
        
        body_rect = pygame.Rect(heli_x - 15, heli_y, 30, 15)
        pygame.draw.ellipse(self.screen, color, body_rect)
        
        pygame.draw.rect(self.screen, color, (heli_x + 10, heli_y + 5, 20, 5))
        pygame.draw.polygon(self.screen, color, [
            (heli_x + 25, heli_y),
            (heli_x + 30, heli_y + 5),
            (heli_x + 30, heli_y + 10)
        ])
        
        pygame.draw.line(self.screen, color, (heli_x - 20, heli_y - 3), 
                        (heli_x + 20, heli_y - 3), 2)
        
        pygame.draw.circle(self.screen, color, (heli_x + 30, heli_y + 5), 4, 1)