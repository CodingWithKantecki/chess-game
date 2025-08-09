"""
Graphics and Rendering Functions - Enhanced with Mode Selection and Story UI
"""

import pygame
import pygame.gfxdraw
import math
import random
import config
from animated_dialogue import AnimatedDialogueBox

class Renderer:
    def __init__(self, screen, assets):
        self.screen = screen
        self.assets = assets
        self.parallax_offset = 0
        self.scale = 1.0
        self.allow_typewriter_additions = True  # Flag to control typewriter text additions
        
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
        
        # Typewriter effect system
        self.typewriter_texts = []
        self.typewriter_speed = 30  # Characters per second
        self.typewriter_added_texts = set()  # Track which texts have been added
        
        # Animated dialogue box for story mode
        self.animated_dialogue_box = AnimatedDialogueBox(self)
        
        # Performance optimization: Cache frequently used surfaces
        self._cached_overlays = {}
        self._cached_text_surfaces = {}
        self._text_cache_max_size = 100
        
        # Particle surface pool for performance
        self._particle_surface_pool = []
        self._max_pool_size = 50
        
    def update_scale(self, scale):
        """Update scale factor for fullscreen mode."""
        self.scale = scale
        self.pixel_fonts = self.load_pixel_fonts()
        # Clear caches when scale changes
        self._cached_overlays.clear()
        self._cached_text_surfaces.clear()
        
    def _get_cached_overlay(self, width, height, color, alpha):
        """Get a cached overlay surface to avoid recreating it every frame."""
        cache_key = (width, height, color, alpha)
        if cache_key not in self._cached_overlays:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((*color, alpha))
            self._cached_overlays[cache_key] = overlay
        return self._cached_overlays[cache_key]
        
    def _get_cached_text(self, text, font_key, color):
        """Get a cached text surface to avoid re-rendering every frame."""
        cache_key = (text, font_key, color)
        if cache_key not in self._cached_text_surfaces:
            if len(self._cached_text_surfaces) > self._text_cache_max_size:
                # Remove oldest cached text to prevent memory issues
                self._cached_text_surfaces.pop(next(iter(self._cached_text_surfaces)))
            font = self.pixel_fonts.get(font_key, self.pixel_fonts['medium'])
            self._cached_text_surfaces[cache_key] = font.render(text, True, color)
        return self._cached_text_surfaces[cache_key]
        
    def _get_particle_surface(self, size):
        """Get a particle surface from the pool or create a new one."""
        # Try to find a surface of the right size in the pool
        for i, (surf_size, surf) in enumerate(self._particle_surface_pool):
            if surf_size == size:
                # Remove from pool and return it
                return self._particle_surface_pool.pop(i)[1]
        
        # Create new surface if none available
        return pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    
    def _return_particle_surface(self, size, surface):
        """Return a particle surface to the pool for reuse."""
        if len(self._particle_surface_pool) < self._max_pool_size:
            surface.fill((0, 0, 0, 0))  # Clear the surface
            self._particle_surface_pool.append((size, surface))
        
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
                    pass  # Loaded pixel font
                    return fonts
            except:
                continue
                
        pass  # Using default monospace font
        for key, size in sizes.items():
            fonts[key] = pygame.font.Font(pygame.font.get_default_font(), size)
        
        return fonts
        
    def add_typewriter_text(self, text, position, font_key='medium', color=config.WHITE, center=False, callback=None, speed=None):
        """Add a text to be displayed with typewriter effect."""
        self.typewriter_texts.append({
            'full_text': text,
            'current_text': '',
            'position': position,
            'font_key': font_key,
            'color': color,
            'center': center,
            'start_time': pygame.time.get_ticks(),
            'char_index': 0,
            'callback': callback,
            'completed': False,
            'speed': speed if speed is not None else self.typewriter_speed
        })
        
    def update_typewriter_texts(self):
        """Update all active typewriter texts."""
        current_time = pygame.time.get_ticks()
        
        for text_data in self.typewriter_texts[:]:
            if text_data['completed']:
                continue
                
            # Calculate how many characters should be shown
            elapsed_time = (current_time - text_data['start_time']) / 1000.0
            speed = text_data.get('speed', self.typewriter_speed)
            chars_to_show = int(elapsed_time * speed)
            
            if chars_to_show > text_data['char_index']:
                text_data['char_index'] = min(chars_to_show, len(text_data['full_text']))
                text_data['current_text'] = text_data['full_text'][:text_data['char_index']]
                
                if text_data['char_index'] >= len(text_data['full_text']):
                    text_data['completed'] = True
                    if text_data['callback']:
                        text_data['callback']()
                        
    def draw_typewriter_texts(self):
        """Draw all active typewriter texts."""
        for text_data in self.typewriter_texts:
            if text_data['current_text']:
                text_surface = self._get_cached_text(text_data['current_text'], text_data['font_key'], text_data['color'])
                
                if text_data['center']:
                    text_rect = text_surface.get_rect(center=text_data['position'])
                    self.screen.blit(text_surface, text_rect)
                else:
                    self.screen.blit(text_surface, text_data['position'])
                    
    def clear_typewriter_texts(self, preserve_ids=None):
        """Clear all typewriter texts.
        
        Args:
            preserve_ids: Optional set of text IDs to preserve (won't be cleared)
        """
        if preserve_ids:
            # Keep only the texts with IDs in preserve_ids
            self.typewriter_texts = [text for text in self.typewriter_texts 
                                   if any(text.get('text', '').find(pid) != -1 or 
                                         str(text.get('position', '')).find(pid) != -1 
                                         for pid in preserve_ids)]
            # Remove preserved IDs from added set so they can be re-added if needed
            self.typewriter_added_texts = self.typewriter_added_texts.difference(preserve_ids)
        else:
            self.typewriter_texts = []
            self.typewriter_added_texts.clear()
            
        # Reset badge fade timer
        if hasattr(self, 'badge_fade_start'):
            delattr(self, 'badge_fade_start')
        # Reset buttons fade timer
        if hasattr(self, 'buttons_fade_start'):
            delattr(self, 'buttons_fade_start')
            
    def reset_dialogue_state(self):
        """Reset the animated dialogue box state."""
        self.animated_dialogue_box.reset()
        # Clear story dialogue typewriter texts
        self.typewriter_added_texts = {key for key in self.typewriter_added_texts if not key.startswith("story_dialogue_")}
        
    def draw_text_typewriter(self, text, position, font_key='medium', color=config.WHITE, center=False, instant=False, text_id=None, speed=None):
        """Draw text with typewriter effect (immediate version for single frame)."""
        if instant:
            font = self.pixel_fonts[font_key]
            text_surface = font.render(text, True, color)
            if center:
                text_rect = text_surface.get_rect(center=position)
                self.screen.blit(text_surface, text_rect)
            else:
                self.screen.blit(text_surface, position)
        else:
            # Only add typewriter texts if allowed (not during fade transitions)
            if not self.allow_typewriter_additions:
                return
                
            # Use text_id or create one from text and position
            if text_id is None:
                text_id = f"{text}_{position}"
            
            # Only add if not already added
            if text_id not in self.typewriter_added_texts:
                self.add_typewriter_text(text, position, font_key, color, center, speed=speed)
                self.typewriter_added_texts.add(text_id)
        
    def draw_mode_select(self, mode_buttons, back_button, mouse_pos):
        """Draw game mode selection screen with dramatic futuristic design."""
        self.draw_parallax_background(1.0)
        
        # Dark overlay for contrast
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 140)
        self.screen.blit(overlay, (0, 0))
        
        current_time = pygame.time.get_ticks()
        
        # Removed binary rain for cleaner look
        
        # Flying jets in background using actual jet assets - reduced spawn
        if not hasattr(self, '_jets'):
            self._jets = []
            # Start with just 1 jet, spawn the other later
            self._jets.append({
                'x': -200,
                'y': random.randint(150, 250),
                'speed': random.uniform(6, 8),
                'shooting': False,
                'shoot_timer': 0,
                'team': 0,
                'frame': 0,
                'frame_timer': 0,
                'tilt': 0,
                'target_y': random.randint(150, 250),
                'vy': 0,
                'evasion_timer': 0,
                'pursuit_mode': False,
                'spawn_timer': 120  # Wait before spawning opponent
            })
            self._projectiles = []
            self._explosions = []  # Store explosion effects
            self._jet_spawn_timer = 600  # Very long delay (10 seconds) before spawning second jet
        
        # Spawn second jet after delay
        if hasattr(self, '_jet_spawn_timer') and self._jet_spawn_timer > 0:
            self._jet_spawn_timer -= 1
            if self._jet_spawn_timer == 0 and len(self._jets) < 2:
                # Spawn opponent jet
                self._jets.append({
                    'x': config.WIDTH + 200,
                    'y': random.randint(150, 250),
                    'speed': random.uniform(-8, -6),
                    'shooting': False,
                    'shoot_timer': 0,
                    'team': 1,
                    'frame': 0,
                    'frame_timer': 0,
                    'tilt': 0,
                    'target_y': random.randint(150, 250),
                    'vy': 0,
                    'evasion_timer': 0,
                    'pursuit_mode': False,
                    'spawn_timer': 0
                })
        
        # Update jets with AI dogfighting
        for i, jet in enumerate(self._jets):
            # Handle respawn delay
            if 'respawn_delay' in jet and jet['respawn_delay'] > 0:
                jet['respawn_delay'] -= 1
                if jet['respawn_delay'] == 0:
                    # Move jet back to normal spawn position
                    if jet['speed'] > 0:
                        jet['x'] = -200
                    else:
                        jet['x'] = config.WIDTH + 200
                continue  # Skip updating this jet until respawn
            
            jet['x'] += jet['speed']
            jet['shoot_timer'] += 1
            jet['frame_timer'] += 1
            jet['evasion_timer'] -= 1
            
            # Find enemy jet
            enemy_jet = None
            for other_jet in self._jets:
                if other_jet['team'] != jet['team']:
                    enemy_jet = other_jet
                    break
            
            # AI dogfighting behavior
            if enemy_jet:
                # Calculate distance to enemy
                dx = enemy_jet['x'] - jet['x']
                dy = enemy_jet['y'] - jet['y']
                distance = math.sqrt(dx*dx + dy*dy)
                
                # If enemy is in front and close, pursue
                if (jet['speed'] > 0 and dx > 0) or (jet['speed'] < 0 and dx < 0):
                    if distance < 400:
                        jet['pursuit_mode'] = True
                        # Track enemy altitude
                        jet['target_y'] = enemy_jet['y'] + random.uniform(-20, 20)
                        
                        # Shoot if aligned (reduced frequency)
                        if abs(dy) < 40 and jet['shoot_timer'] > 60 and random.random() < 0.7:  # 70% chance even when aligned
                            # Fire burst at enemy
                            for _ in range(2):  # Reduced from 3 to 2 bullets
                                self._projectiles.append({
                                    'x': jet['x'],
                                    'y': jet['y'],
                                    'vx': jet['speed'] * 3,
                                    'vy': dy * 0.1 + random.uniform(-1, 1),
                                    'team': jet['team']
                                })
                            jet['shoot_timer'] = 0
                else:
                    jet['pursuit_mode'] = False
                
                # Evasive maneuvers if being pursued
                if jet['evasion_timer'] <= 0 and random.random() < 0.02:
                    jet['target_y'] = random.randint(100, 300)
                    jet['evasion_timer'] = 60
            
            # Default movement if not pursuing
            if not jet['pursuit_mode'] and random.random() < 0.01:
                jet['target_y'] = random.randint(100, 300)
            
            # Calculate vertical velocity towards target with smoother acceleration
            y_diff = jet['target_y'] - jet['y']
            target_vy = y_diff * 0.02  # Slower, smoother approach
            jet['vy'] += (target_vy - jet['vy']) * 0.1  # Smooth acceleration
            jet['y'] += jet['vy']
            
            # Calculate tilt based on vertical movement
            # When jet goes UP (vy negative), nose should point UP (positive rotation = CCW)
            # When jet goes DOWN (vy positive), nose should point DOWN (negative rotation = CW)
            # In pygame: positive angle = counterclockwise, negative angle = clockwise
            # So: vy positive -> need negative rotation, vy negative -> need positive rotation
            target_tilt = min(25, max(-25, -jet['vy'] * 10))  # NEGATIVE multiplier
            jet['tilt'] += (target_tilt - jet['tilt']) * 0.15  # Smoother tilt transition
            
            # Animate jet frames
            if jet['frame_timer'] > 5:  # Change frame every 5 ticks
                jet['frame'] = (jet['frame'] + 1) % 4  # Cycle through 4 frames
                jet['frame_timer'] = 0
            
            # Wrap around screen
            if jet['speed'] > 0 and jet['x'] > config.WIDTH + 200:
                jet['x'] = -200
                jet['y'] = random.randint(150, 250)
                jet['target_y'] = jet['y']
            elif jet['speed'] < 0 and jet['x'] < -200:
                jet['x'] = config.WIDTH + 200
                jet['y'] = random.randint(150, 250)
                jet['target_y'] = jet['y']
            
            # Randomly shoot
            if jet['shoot_timer'] > 40 and random.random() < 0.03:
                # Create multiple bullets for machine gun effect
                for _ in range(2):
                    self._projectiles.append({
                        'x': jet['x'],
                        'y': jet['y'],
                        'vx': jet['speed'] * 3 + random.uniform(-1, 1),
                        'vy': random.uniform(-0.5, 0.5),
                        'team': jet['team']
                    })
                jet['shoot_timer'] = 0
            
            # Draw jet using actual jet frames if available
            if hasattr(self, 'assets') and hasattr(self.assets, 'jet_frames') and self.assets.jet_frames:
                # Use actual jet image
                frame_index = min(jet['frame'], len(self.assets.jet_frames) - 1)
                jet_image = self.assets.jet_frames[frame_index]
                
                # Scale jet to be much smaller
                jet_scale = 0.15  # Much smaller jets
                scaled_width = int(jet_image.get_width() * jet_scale)
                scaled_height = int(jet_image.get_height() * jet_scale)
                scaled_jet = pygame.transform.scale(jet_image, (scaled_width, scaled_height))
                
                # Flip image based on direction (jets face LEFT by default in the image)
                if jet['speed'] > 0:
                    # Going right - need to flip
                    scaled_jet = pygame.transform.flip(scaled_jet, True, False)
                    # Apply rotation for right-facing jets
                    scaled_jet = pygame.transform.rotate(scaled_jet, jet['tilt'])
                else:
                    # Going left - no flip needed
                    # Apply rotation for left-facing jets
                    scaled_jet = pygame.transform.rotate(scaled_jet, jet['tilt'])
                
                # Don't apply color tint - just use original jet colors
                # Set slight transparency
                scaled_jet.set_alpha(200)
                
                # Draw the jet
                jet_rect = scaled_jet.get_rect(center=(int(jet['x']), int(jet['y'])))
                self.screen.blit(scaled_jet, jet_rect)
                
                # Engine trail effect
                direction = 1 if jet['speed'] > 0 else -1
                for i in range(5):
                    trail_x = jet['x'] - direction * (30 + i * 15)
                    trail_alpha = 100 - i * 20
                    trail_size = 5 - i
                    # Orange/yellow engine glow
                    glow_surf = pygame.Surface((trail_size*4, trail_size*4), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (255, 200, 0, trail_alpha), 
                                     (trail_size*2, trail_size*2), trail_size)
                    self.screen.blit(glow_surf, (trail_x - trail_size*2, jet['y'] - trail_size*2))
            else:
                # Fallback to simple triangle if no assets
                jet_color = (100, 150, 200, 180) if jet['team'] == 0 else (200, 100, 100, 180)
                direction = 1 if jet['speed'] > 0 else -1
                points = [
                    (jet['x'] + direction * 20, jet['y']),
                    (jet['x'] - direction * 15, jet['y'] - 8),
                    (jet['x'] - direction * 15, jet['y'] + 8)
                ]
                pygame.draw.polygon(self.screen, jet_color, points)
        
        # Check for bullet-jet collisions
        jets_to_remove = []
        projectiles_to_remove = []
        
        for proj_idx, proj in enumerate(self._projectiles):
            for jet_idx, jet in enumerate(self._jets):
                # Check if bullet hits enemy jet
                if proj['team'] != jet['team']:
                    # Simple collision detection
                    if abs(proj['x'] - jet['x']) < 30 and abs(proj['y'] - jet['y']) < 20:
                        # Create realistic explosion with particles
                        self._explosions.append({
                            'x': jet['x'],
                            'y': jet['y'],
                            'frame': 0,
                            'particles': []  # Individual debris particles
                        })
                        
                        # Create debris particles
                        for _ in range(15):
                            self._explosions[-1]['particles'].append({
                                'x': jet['x'],
                                'y': jet['y'],
                                'vx': random.uniform(-8, 8),
                                'vy': random.uniform(-8, 8),
                                'size': random.uniform(2, 5),
                                'life': random.randint(20, 40),
                                'color_index': random.randint(0, 2)  # Different colors for variety
                            })
                        # Mark jet for respawn
                        if jet_idx not in jets_to_remove:
                            jets_to_remove.append(jet_idx)
                        if proj_idx not in projectiles_to_remove:
                            projectiles_to_remove.append(proj_idx)
        
        # Respawn destroyed jets with delay
        for jet_idx in sorted(jets_to_remove, reverse=True):
            jet = self._jets[jet_idx]
            # Move jet far off screen and add respawn delay
            if jet['speed'] > 0:
                jet['x'] = -800  # Far off screen
            else:
                jet['x'] = config.WIDTH + 800  # Far off screen
            jet['y'] = random.randint(150, 250)
            jet['target_y'] = jet['y']
            jet['respawn_delay'] = 480  # 8 second respawn delay after destruction
        
        # Remove hit projectiles
        for idx in sorted(projectiles_to_remove, reverse=True):
            if idx < len(self._projectiles):
                del self._projectiles[idx]
        
        # Update and draw realistic explosions
        explosions_to_remove = []
        for i, explosion in enumerate(self._explosions):
            explosion['frame'] += 1
            
            # Draw explosion with particle system
            if explosion['frame'] < 45:
                # Update and draw particles
                particles_to_remove = []
                for p_idx, particle in enumerate(explosion['particles']):
                    # Update particle physics
                    particle['x'] += particle['vx']
                    particle['y'] += particle['vy']
                    particle['vy'] += 0.3  # Gravity
                    particle['vx'] *= 0.98  # Air resistance
                    particle['life'] -= 1
                    
                    if particle['life'] > 0:
                        # Particle colors: yellow -> orange -> red -> dark red -> smoke
                        color_progression = [
                            (255, 255, 200),  # White-yellow (hot)
                            (255, 220, 0),    # Yellow
                            (255, 150, 0),    # Orange
                            (255, 50, 0),     # Red
                            (100, 30, 30)     # Dark red/smoke
                        ]
                        
                        # Calculate color based on life
                        life_ratio = particle['life'] / 40
                        color_idx = min(4, int((1 - life_ratio) * 5))
                        color = color_progression[color_idx]
                        
                        # Calculate alpha fade
                        alpha = int(255 * life_ratio)
                        
                        # Draw particle with glow
                        particle_size = particle['size'] * (0.5 + life_ratio * 0.5)
                        
                        # Glow effect
                        glow_size = particle_size * 2
                        glow_surf = pygame.Surface((int(glow_size * 4), int(glow_size * 4)), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*color, min(alpha // 3, 50)), 
                                         (int(glow_size * 2), int(glow_size * 2)), int(glow_size))
                        self.screen.blit(glow_surf, (particle['x'] - glow_size * 2, particle['y'] - glow_size * 2))
                        
                        # Main particle
                        pygame.draw.circle(self.screen, (*color, alpha), 
                                         (int(particle['x']), int(particle['y'])), int(particle_size))
                    else:
                        particles_to_remove.append(p_idx)
                
                # Remove dead particles
                for idx in sorted(particles_to_remove, reverse=True):
                    del explosion['particles'][idx]
                
                # Central flash for first few frames
                if explosion['frame'] < 5:
                    flash_size = 30 - explosion['frame'] * 5
                    flash_alpha = 255 - explosion['frame'] * 50
                    flash_surf = pygame.Surface((flash_size * 4, flash_size * 4), pygame.SRCALPHA)
                    pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha), 
                                     (flash_size * 2, flash_size * 2), flash_size)
                    self.screen.blit(flash_surf, (explosion['x'] - flash_size * 2, explosion['y'] - flash_size * 2))
                
                # Smoke trail effect for later frames
                if explosion['frame'] > 10:
                    smoke_alpha = max(0, 100 - (explosion['frame'] - 10) * 3)
                    smoke_size = 20 + (explosion['frame'] - 10)
                    smoke_surf = pygame.Surface((smoke_size * 2, smoke_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(smoke_surf, (80, 80, 80, smoke_alpha), 
                                     (smoke_size, smoke_size), smoke_size)
                    self.screen.blit(smoke_surf, (explosion['x'] - smoke_size, explosion['y'] - smoke_size))
            else:
                explosions_to_remove.append(i)
        
        # Remove finished explosions
        for idx in sorted(explosions_to_remove, reverse=True):
            del self._explosions[idx]
        
        # Update and draw remaining projectiles
        self._projectiles = [p for p in self._projectiles 
                            if -50 < p['x'] < config.WIDTH + 50 and -50 < p['y'] < config.HEIGHT + 50]
        
        for proj in self._projectiles:
            proj['x'] += proj['vx']
            proj['y'] += proj['vy']
            
            # Draw tracer bullets (yellow/orange like real gunfire)
            tracer_color = (255, 220, 100)  # Yellow tracer color
            tracer_glow = (255, 150, 0)  # Orange glow
            
            # Draw tracer trail
            pygame.draw.line(self.screen, tracer_color, 
                           (proj['x'], proj['y']), 
                           (proj['x'] - proj['vx'], proj['y'] - proj['vy']), 1)
            
            # Draw bullet point with glow
            pygame.draw.circle(self.screen, tracer_glow, (int(proj['x']), int(proj['y'])), 2)
            pygame.draw.circle(self.screen, tracer_color, (int(proj['x']), int(proj['y'])), 1)
        
        # Clean title
        title_text = "SELECT GAME MODE"
        title_y = 80
        
        # Background glow for title
        for i in range(4, 0, -1):
            glow_alpha = 20 - i * 4
            glow_color = (100, 150, 255)
            glow_surf = pygame.Surface((800, 100), pygame.SRCALPHA)
            glow_text = self.pixel_fonts['huge'].render(title_text, True, (*glow_color, glow_alpha))
            glow_rect = glow_text.get_rect(center=(400, 50))
            glow_surf.blit(glow_text, glow_rect.move(0, i))
            title_surf_rect = glow_surf.get_rect(center=(config.WIDTH // 2, title_y))
            self.screen.blit(glow_surf, title_surf_rect)
        
        # Main title with gradient effect
        title_surface = self.pixel_fonts['huge'].render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(config.WIDTH // 2, title_y))
        self.screen.blit(title_surface, title_rect)
        
        # Futuristic mode cards with unique designs
        modes = [
            {
                "key": "classic",
                "name": "CLASSIC",
                "subtitle": "MASTER THE FUNDAMENTALS",
                "desc": ["• Strategic warfare", "• Earn powerups", "• Traditional rules"],
                "icon": "♔",
                "color": (0, 255, 136),
                "bg_gradient": [(0, 40, 30), (0, 80, 50)],
                "glow_color": (0, 255, 100)
            },
            {
                "key": "story",
                "name": "CAMPAIGN",
                "subtitle": "EPIC STORYLINE",
                "desc": ["• 25+ unique battles", "• Boss encounters", "• Unlock rewards"],
                "icon": "⚔",
                "color": (255, 140, 0),
                "bg_gradient": [(60, 30, 0), (120, 60, 0)],
                "glow_color": (255, 180, 0),
                "recommended": True
            },
            {
                "key": "freeplay",
                "name": "SANDBOX",
                "subtitle": "UNLIMITED CHAOS",
                "desc": ["• Infinite resources", "• Test strategies", "• No restrictions"],
                "icon": "∞",
                "color": (147, 0, 255),
                "bg_gradient": [(30, 0, 60), (60, 0, 120)],
                "glow_color": (200, 100, 255)
            }
        ]
        
        # Larger, more dramatic cards
        card_width = 280
        card_height = 380
        cards_per_row = 3
        spacing = 50
        
        start_x = (config.WIDTH - (cards_per_row * card_width + (cards_per_row - 1) * spacing)) // 2
        start_y = 160
        
        mode_buttons.clear()
        
        for i, mode in enumerate(modes):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = start_x + col * (card_width + spacing)
            y = start_y + row * (card_height + spacing)
            
            rect = pygame.Rect(x, y, card_width, card_height)
            mode_buttons[mode["key"]] = rect
            
            # Check hover with animation
            is_hover = rect.collidepoint(mouse_pos)
            hover_offset = -15 if is_hover else 0
            animated_rect = rect.move(0, hover_offset)
            
            # Create dramatic card surface
            card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            
            # Gradient background
            gradient_colors = mode['bg_gradient']
            for y_offset in range(card_height):
                factor = y_offset / card_height
                r = int(gradient_colors[0][0] + (gradient_colors[1][0] - gradient_colors[0][0]) * factor)
                g = int(gradient_colors[0][1] + (gradient_colors[1][1] - gradient_colors[0][1]) * factor)
                b = int(gradient_colors[0][2] + (gradient_colors[1][2] - gradient_colors[0][2]) * factor)
                alpha = 230 if is_hover else 200
                pygame.draw.line(card_surface, (r, g, b, alpha), (0, y_offset), (card_width, y_offset))
            
            # Neon border effect
            if is_hover:
                # Animated outer glow
                pulse = abs(math.sin(current_time * 0.003 + i)) * 0.5 + 0.5
                for glow_size in range(4, 0, -1):
                    glow_alpha = int((30 - glow_size * 6) * pulse)
                    glow_surf = pygame.Surface((card_width + glow_size*4, card_height + glow_size*4), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (*mode['glow_color'], glow_alpha), 
                                   glow_surf.get_rect(), 3, border_radius=30)
                    glow_rect = glow_surf.get_rect(center=(card_width//2, card_height//2))
                    card_surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
            
            # Smoother rounded corners with larger radius
            border_color = mode['glow_color'] if is_hover else mode['color']
            pygame.draw.rect(card_surface, (*border_color, 255), 
                           card_surface.get_rect(), 3, border_radius=25)
            
            # Inner accent line with smooth corners
            inner_rect = card_surface.get_rect().inflate(-8, -8)
            pygame.draw.rect(card_surface, (*border_color, 80), inner_rect, 1, border_radius=25)
            
            self.screen.blit(card_surface, animated_rect)
            
            # Large dramatic icon with glow
            icon_y = animated_rect.y + 70
            icon_font_size = 72 if is_hover else 64
            try:
                icon_font = pygame.font.Font(None, icon_font_size)
            except:
                icon_font = self.pixel_fonts['huge']
            
            # Icon glow layers
            if is_hover:
                for layer in range(3, 0, -1):
                    glow_alpha = 40 - layer * 10
                    icon_glow = icon_font.render(mode['icon'], True, mode['glow_color'])
                    icon_glow.set_alpha(glow_alpha)
                    for dx, dy in [(0, layer), (0, -layer), (layer, 0), (-layer, 0)]:
                        glow_rect = icon_glow.get_rect(center=(animated_rect.centerx + dx, icon_y + dy))
                        self.screen.blit(icon_glow, glow_rect)
            
            # Main icon
            icon_text = icon_font.render(mode['icon'], True, (255, 255, 255))
            icon_rect = icon_text.get_rect(center=(animated_rect.centerx, icon_y))
            self.screen.blit(icon_text, icon_rect)
            
            # Mode name with glow
            name_y = animated_rect.y + 140
            name_color = mode['glow_color'] if is_hover else (255, 255, 255)
            name_text = self.pixel_fonts['large'].render(mode['name'], True, name_color)
            name_rect = name_text.get_rect(center=(animated_rect.centerx, name_y))
            self.screen.blit(name_text, name_rect)
            
            # Subtitle
            subtitle_y = name_y + 30
            subtitle_text = self.pixel_fonts['small'].render(mode['subtitle'], True, (180, 180, 180))
            subtitle_rect = subtitle_text.get_rect(center=(animated_rect.centerx, subtitle_y))
            self.screen.blit(subtitle_text, subtitle_rect)
            
            # Glowing divider line
            divider_y = subtitle_y + 25
            divider_color = (*mode['color'], 120)
            pygame.draw.line(self.screen, divider_color,
                           (animated_rect.x + 50, divider_y),
                           (animated_rect.x + card_width - 50, divider_y), 2)
            
            # Feature list
            feature_y = divider_y + 35
            for feature in mode['desc']:
                feature_color = (220, 220, 220) if is_hover else (200, 200, 200)
                feature_text = self.pixel_fonts['small'].render(feature, True, feature_color)
                feature_rect = feature_text.get_rect(center=(animated_rect.centerx, feature_y))
                self.screen.blit(feature_text, feature_rect)
                feature_y += 30
                
            # Special animated badge for recommended mode
            if mode.get("recommended"):
                badge_y = animated_rect.y + card_height + 20
                pulse = abs(math.sin(current_time * 0.004)) * 0.6 + 0.4
                
                # Glowing badge
                badge_width = 160
                badge_height = 35
                
                # Multiple glow layers
                for i in range(3, 0, -1):
                    glow_surf = pygame.Surface((badge_width + i*12, badge_height + i*12), pygame.SRCALPHA)
                    glow_alpha = int((25 - i*7) * pulse)
                    pygame.draw.rect(glow_surf, (255, 200, 0, glow_alpha), 
                                   glow_surf.get_rect(), border_radius=20)
                    glow_rect = glow_surf.get_rect(center=(animated_rect.centerx, badge_y))
                    self.screen.blit(glow_surf, glow_rect)
                
                # Main badge background
                badge_surf = pygame.Surface((badge_width, badge_height), pygame.SRCALPHA)
                pygame.draw.rect(badge_surf, (255, 200, 0, 220), badge_surf.get_rect(), 
                               border_radius=17)
                pygame.draw.rect(badge_surf, (255, 255, 200, 255), badge_surf.get_rect(), 
                               2, border_radius=17)
                badge_rect = badge_surf.get_rect(center=(animated_rect.centerx, badge_y))
                self.screen.blit(badge_surf, badge_rect)
                
                # Badge text with stars
                badge_text = "★ RECOMMENDED ★"
                text_surf = self.pixel_fonts['small'].render(badge_text, True, (50, 50, 50))
                text_rect = text_surf.get_rect(center=(animated_rect.centerx, badge_y))
                self.screen.blit(text_surf, text_rect)
                
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_story_chapters(self, story_mode, chapter_buttons, back_button, mouse_pos):
        """Draw story mode chapter selection."""
        self.draw_parallax_background(0.8)
        
        # Overlay
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 100)
        self.screen.blit(overlay, (0, 0))
        
        # Draw walking capybaras
        self._draw_walking_capybaras()
        
        # Title
        title = self.pixel_fonts['huge'].render("STORY MODE", True, config.WHITE)
        title_rect = title.get_rect(center=(config.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Overall progress
        total_progress = story_mode.get_total_progress()
        progress_text = f"Campaign Progress: {total_progress}%"
        progress_surface = self.pixel_fonts['medium'].render(progress_text, True, (220, 190, 130))
        progress_rect = progress_surface.get_rect(center=(config.WIDTH // 2, 100))
        self.screen.blit(progress_surface, progress_rect)
        
        # Display player money - use in-memory value
        money_text = f"Money: ${config.get_money()}"
        money_surface = self.pixel_fonts['medium'].render(money_text, True, (180, 220, 180))
        money_rect = money_surface.get_rect(center=(config.WIDTH // 2, 130))
        self.screen.blit(money_surface, money_rect)
        
        # Chapter list
        chapter_buttons.clear()
        y_offset = 170
        
        # Debug output only once per second to reduce spam
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_debug_time') or current_time - self._last_debug_time > 1000:
            self._last_debug_time = current_time
            pass  # Story chapters display
        
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
                border_color = (200, 180, 120)
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
                lock_surface = self.pixel_fonts['medium'].render(lock_text, True, (200, 50, 50))
                # Position on the right side, below the chapter title to avoid overlap
                lock_rect = lock_surface.get_rect(center=(bar_x - 80, button_rect.centery + 15))
                self.screen.blit(lock_surface, lock_rect)
                
            y_offset += button_height + 20
            
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_story_battles(self, chapter, story_mode, battle_buttons, back_button, mouse_pos):
        """Draw battle selection within a chapter."""
        self.draw_parallax_background(0.8)
        
        # Overlay
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 100)
        self.screen.blit(overlay, (0, 0))
        
        # Draw walking capybaras
        self._draw_walking_capybaras()
        
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
            
            # Check if completed and unlocked
            is_completed = story_mode.is_battle_completed(battle["id"])
            # Get chapter index to check unlock status
            chapter_index = next((idx for idx, ch in enumerate(story_mode.chapters) if ch["id"] == chapter["id"]), 0)
            is_unlocked = story_mode.is_battle_unlocked(chapter_index, i)
            is_hover = card_rect.collidepoint(mouse_pos) and is_unlocked
            
            # Card color
            if not is_unlocked:
                card_color = (30, 30, 30)  # Dark gray for locked
                border_color = (80, 80, 80)
            elif is_completed:
                card_color = (40, 60, 40)  # Green tint
                border_color = (100, 200, 100)
            else:
                card_color = (50, 50, 70) if not is_hover else (70, 70, 90)
                border_color = (200, 200, 200)
                
            pygame.draw.rect(self.screen, card_color, card_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, card_rect, 3, border_radius=10)
            
            # Portrait with special handling for BOT
            portrait_text = battle.get("portrait", "X")
            
            if portrait_text == "BOT":
                # Use bot.png image if available, otherwise draw mini robot icon
                if self.assets.bot_image:
                    # Scale bot image to fit card portrait area
                    mini_bot_size = 80
                    bot_scaled = pygame.transform.smoothscale(self.assets.bot_image, 
                                                            (mini_bot_size, mini_bot_size))
                    bot_rect = bot_scaled.get_rect(center=(card_x + 60, card_rect.centery))
                    self.screen.blit(bot_scaled, bot_rect)
                else:
                    # Fallback to drawn mini robot
                    robot_x = card_x + 60
                    robot_y = card_rect.centery
                    robot_color = (100, 200, 255)
                    
                    # Mini robot head
                    head_rect = pygame.Rect(robot_x - 20, robot_y - 25, 40, 30)
                    pygame.draw.rect(self.screen, robot_color, head_rect, border_radius=5)
                    pygame.draw.rect(self.screen, (150, 230, 255), head_rect, 2, border_radius=5)
                    
                    # Eyes
                    pygame.draw.circle(self.screen, (255, 100, 100), (robot_x - 10, robot_y - 15), 6)
                    pygame.draw.circle(self.screen, (255, 100, 100), (robot_x + 10, robot_y - 15), 6)
                    pygame.draw.circle(self.screen, (0, 0, 0), (robot_x - 10, robot_y - 15), 2)
                    pygame.draw.circle(self.screen, (0, 0, 0), (robot_x + 10, robot_y - 15), 2)
                    
                    # Mouth
                    pygame.draw.rect(self.screen, (50, 50, 50), (robot_x - 12, robot_y - 5, 24, 5))
                    
                    # Antenna
                    pygame.draw.line(self.screen, robot_color, (robot_x, robot_y - 25), (robot_x, robot_y - 35), 2)
                    pygame.draw.circle(self.screen, (255, 255, 100), (robot_x, robot_y - 35), 3)
                    
                    # Body
                    body_rect = pygame.Rect(robot_x - 18, robot_y + 5, 36, 25)
                    pygame.draw.rect(self.screen, robot_color, body_rect, border_radius=3)
                    pygame.draw.rect(self.screen, (150, 230, 255), body_rect, 2, border_radius=3)
                    
                    # Lights
                    pygame.draw.circle(self.screen, (0, 255, 0), (robot_x - 8, robot_y + 15), 3)
                    pygame.draw.circle(self.screen, (255, 0, 0), (robot_x + 8, robot_y + 15), 3)
            elif portrait_text == "SGT":
                # Use mills.png image if available
                if self.assets.mills_image:
                    # Scale mills image to fit card portrait area
                    mini_mills_size = 80
                    mills_scaled = pygame.transform.smoothscale(self.assets.mills_image, 
                                                              (mini_mills_size, mini_mills_size))
                    mills_rect = mills_scaled.get_rect(center=(card_x + 60, card_rect.centery))
                    self.screen.blit(mills_scaled, mills_rect)
                else:
                    # Fallback to text if image not loaded
                    portrait_surface = self.pixel_fonts['huge'].render(portrait_text, True, config.WHITE)
                    portrait_rect = portrait_surface.get_rect(center=(card_x + 60, card_rect.centery))
                    self.screen.blit(portrait_surface, portrait_rect)
            else:
                # Regular portrait
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
            reward_surface = self.pixel_fonts['small'].render(reward_text, True, (220, 190, 130))
            reward_rect = reward_surface.get_rect(midleft=(card_x + 100, card_rect.centery + 30))
            self.screen.blit(reward_surface, reward_rect)
            
            # Completion/Lock status
            if not is_unlocked:
                # Draw lock icon
                lock_text = "🔒 LOCKED"
                lock_surface = self.pixel_fonts['medium'].render(lock_text, True, (150, 150, 150))
                lock_rect = lock_surface.get_rect(midright=(card_x + card_width - 20, card_rect.centery))
                self.screen.blit(lock_surface, lock_rect)
                
                # Draw unlock requirement
                if i == 0 and chapter_index > 0:
                    req_text = "Complete previous chapter"
                else:
                    req_text = "Complete previous battle"
                req_surface = self.pixel_fonts['tiny'].render(req_text, True, (100, 100, 100))
                req_rect = req_surface.get_rect(midright=(card_x + card_width - 20, card_rect.centery + 20))
                self.screen.blit(req_surface, req_rect)
            elif is_completed:
                complete_text = "✓ COMPLETE"
                complete_surface = self.pixel_fonts['medium'].render(complete_text, True, (100, 255, 100))
                complete_rect = complete_surface.get_rect(midright=(card_x + card_width - 20, card_rect.centery))
                self.screen.blit(complete_surface, complete_rect)
                
            y_offset += card_height + 20
            
        # Back button
        self._draw_button(back_button, "BACK", (150, 70, 70), (200, 100, 100), mouse_pos)
        
    def draw_story_dialogue(self, battle_data, dialogue_index, dialogue_complete, is_fade_active=False):
        """Draw pre-battle dialogue screen."""
        self.draw_parallax_background(0.6)
        
        # Dark overlay
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 180)
        self.screen.blit(overlay, (0, 0))
        
        # Draw tech grid background
        self._draw_tech_grid()
        
        # Get current time for animations
        current_time = pygame.time.get_ticks()
        
        # Draw digital rain effect (behind everything else)
        self._draw_digital_rain(current_time)
        
        # Character portrait
        portrait_size = 200
        portrait_x = config.WIDTH // 2 - portrait_size // 2
        portrait_y = 100
        
        # Draw scanner effect around portrait
        self._draw_scanner_effect(portrait_x - 20, portrait_y - 20, portrait_size + 40, portrait_size + 40, current_time)
        
        # Portrait background with tech style
        # Outer glow
        for i in range(3):
            glow_alpha = 100 - i * 30
            glow_surf = pygame.Surface((portrait_size + 40 + i*10, portrait_size + 40 + i*10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 255, 255, glow_alpha), 
                           (0, 0, portrait_size + 40 + i*10, portrait_size + 40 + i*10), 
                           3, border_radius=15)
            self.screen.blit(glow_surf, (portrait_x - 20 - i*5, portrait_y - 20 - i*5))
        
        # Main portrait background
        pygame.draw.rect(self.screen, (20, 30, 40), 
                       (portrait_x - 10, portrait_y - 10, portrait_size + 20, portrait_size + 20), 
                       border_radius=10)
        pygame.draw.rect(self.screen, (0, 200, 255), 
                       (portrait_x - 10, portrait_y - 10, portrait_size + 20, portrait_size + 20), 
                       3, border_radius=10)
        
        # Portrait emoji/text with special handling for BOT
        portrait_text = battle_data.get("portrait", "X")
        
        if portrait_text == "BOT":
            # Use bot.png image if available, otherwise fall back to drawn robot
            if self.assets.bot_image:
                # Scale bot image to fit portrait area
                bot_scaled = pygame.transform.smoothscale(self.assets.bot_image, 
                                                         (portrait_size - 20, portrait_size - 20))
                bot_rect = bot_scaled.get_rect(center=(portrait_x + portrait_size // 2, 
                                                      portrait_y + portrait_size // 2))
                self.screen.blit(bot_scaled, bot_rect)
            else:
                # Fallback to drawn robot if image not loaded
                robot_color = (100, 200, 255)
                robot_center_x = portrait_x + portrait_size // 2
                robot_center_y = portrait_y + portrait_size // 2
                
                # Robot head
                head_rect = pygame.Rect(robot_center_x - 40, robot_center_y - 50, 80, 60)
                pygame.draw.rect(self.screen, robot_color, head_rect, border_radius=10)
                pygame.draw.rect(self.screen, (150, 230, 255), head_rect, 3, border_radius=10)
                
                # Robot eyes
                eye_size = 15
                eye_y = robot_center_y - 35
                # Left eye
                pygame.draw.circle(self.screen, (255, 100, 100), (robot_center_x - 20, eye_y), eye_size)
                pygame.draw.circle(self.screen, (255, 255, 255), (robot_center_x - 20, eye_y), eye_size - 5)
                pygame.draw.circle(self.screen, (0, 0, 0), (robot_center_x - 20, eye_y), 5)
                # Right eye
                pygame.draw.circle(self.screen, (255, 100, 100), (robot_center_x + 20, eye_y), eye_size)
                pygame.draw.circle(self.screen, (255, 255, 255), (robot_center_x + 20, eye_y), eye_size - 5)
                pygame.draw.circle(self.screen, (0, 0, 0), (robot_center_x + 20, eye_y), 5)
                
                # Robot mouth
                mouth_rect = pygame.Rect(robot_center_x - 25, robot_center_y - 15, 50, 10)
                pygame.draw.rect(self.screen, (50, 50, 50), mouth_rect)
                for i in range(5):
                    pygame.draw.line(self.screen, (150, 230, 255), 
                                   (robot_center_x - 25 + i * 12, robot_center_y - 15),
                                   (robot_center_x - 25 + i * 12, robot_center_y - 5), 2)
                
                # Robot antenna
                pygame.draw.line(self.screen, robot_color, 
                               (robot_center_x, robot_center_y - 50),
                               (robot_center_x, robot_center_y - 70), 3)
                pygame.draw.circle(self.screen, (255, 255, 100), 
                                 (robot_center_x, robot_center_y - 70), 6)
                
                # Robot body
                body_rect = pygame.Rect(robot_center_x - 35, robot_center_y + 10, 70, 50)
                pygame.draw.rect(self.screen, robot_color, body_rect, border_radius=5)
                pygame.draw.rect(self.screen, (150, 230, 255), body_rect, 3, border_radius=5)
                
                # Body details
                for i in range(3):
                    for j in range(2):
                        light_x = robot_center_x - 20 + i * 20
                        light_y = robot_center_y + 25 + j * 15
                        light_color = (0, 255, 0) if (i + j) % 2 == 0 else (255, 0, 0)
                        pygame.draw.circle(self.screen, light_color, (light_x, light_y), 4)
        elif portrait_text == "SGT":
            # Use mills.png image if available
            if self.assets.mills_image:
                # Scale mills image to fit portrait area
                mills_scaled = pygame.transform.smoothscale(self.assets.mills_image, 
                                                           (portrait_size - 20, portrait_size - 20))
                mills_rect = mills_scaled.get_rect(center=(portrait_x + portrait_size // 2, 
                                                         portrait_y + portrait_size // 2))
                self.screen.blit(mills_scaled, mills_rect)
            else:
                # Fallback to text if image not loaded
                portrait_surface = pygame.font.Font(None, 120).render(portrait_text, True, config.WHITE)
                portrait_rect = portrait_surface.get_rect(center=(portrait_x + portrait_size // 2, portrait_y + portrait_size // 2))
                self.screen.blit(portrait_surface, portrait_rect)
        else:
            # Regular emoji/text portrait
            portrait_surface = pygame.font.Font(None, 120).render(portrait_text, True, config.WHITE)
            portrait_rect = portrait_surface.get_rect(center=(portrait_x + portrait_size // 2, portrait_y + portrait_size // 2))
            self.screen.blit(portrait_surface, portrait_rect)
        
        # Character name with tech styling
        name_text = battle_data["opponent"]
        name_y = portrait_y + portrait_size + 40
        
        # Name background panel
        name_width = len(name_text) * 20 + 60
        name_height = 40
        name_x = config.WIDTH // 2 - name_width // 2
        
        # Draw tech panel for name
        pygame.draw.rect(self.screen, (10, 20, 30), 
                       (name_x, name_y - 20, name_width, name_height), 
                       border_radius=5)
        pygame.draw.rect(self.screen, (0, 255, 200), 
                       (name_x, name_y - 20, name_width, name_height), 
                       2, border_radius=5)
        
        # Draw corner brackets
        bracket_size = 15
        bracket_color = (0, 255, 255)
        # Top left
        pygame.draw.lines(self.screen, bracket_color, False, 
                         [(name_x, name_y - 20 + bracket_size), (name_x, name_y - 20), (name_x + bracket_size, name_y - 20)], 2)
        # Top right
        pygame.draw.lines(self.screen, bracket_color, False, 
                         [(name_x + name_width - bracket_size, name_y - 20), (name_x + name_width, name_y - 20), (name_x + name_width, name_y - 20 + bracket_size)], 2)
        # Bottom left
        pygame.draw.lines(self.screen, bracket_color, False, 
                         [(name_x, name_y + 20 - bracket_size), (name_x, name_y + 20), (name_x + bracket_size, name_y + 20)], 2)
        # Bottom right
        pygame.draw.lines(self.screen, bracket_color, False, 
                         [(name_x + name_width - bracket_size, name_y + 20), (name_x + name_width, name_y + 20), (name_x + name_width, name_y + 20 - bracket_size)], 2)
        
        # Character name with glow
        name_surface = self.pixel_fonts['large'].render(name_text, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(config.WIDTH // 2, name_y))
        
        # Draw glow behind text
        glow_surf = self.pixel_fonts['large'].render(name_text, True, (0, 255, 255))
        for offset in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            glow_rect = glow_surf.get_rect(center=(config.WIDTH // 2 + offset[0], name_y + offset[1]))
            glow_surf.set_alpha(100)
            self.screen.blit(glow_surf, glow_rect)
        
        self.screen.blit(name_surface, name_rect)
        
        # Character Information Sheet
        self._draw_character_info_sheet(battle_data, portrait_x - 50, name_y + 50)
        
        # Animated dialogue box
        dialogue_lines = battle_data.get("pre_battle", [])
        if 0 <= dialogue_index < len(dialogue_lines):
            current_line = dialogue_lines[dialogue_index]
            
            # Don't start dialogue animations during fade transitions
            if not is_fade_active:
                # Check if we need to start a new dialogue animation
                # Only start if this is truly a new dialogue index
                if self.animated_dialogue_box.current_dialogue_index != dialogue_index:
                    self.animated_dialogue_box.current_dialogue_index = dialogue_index
                    self.animated_dialogue_box.start_dialogue(current_line)
                elif self.animated_dialogue_box.animation_state == "idle":
                    # If somehow we're idle but at the right index, restart
                    self.animated_dialogue_box.start_dialogue(current_line)
            
            # Always update and draw if we have an active animation
            if self.animated_dialogue_box.animation_state != "idle":
                self.animated_dialogue_box.update()
                self.animated_dialogue_box.draw(self.screen)
        else:
            # Reset dialogue box if no dialogue to show or all dialogues complete
            if self.animated_dialogue_box.animation_state != "idle":
                self.animated_dialogue_box.reset()
                
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
        battle_surface = self._get_cached_text(battle_text, 'medium', (220, 190, 130))
        self.screen.blit(battle_surface, (20, 20))
        
        # Special rules indicator
        if battle_data.get("special_rules"):
            rules_text = "SPECIAL RULES ACTIVE"
            rules_surface = self._get_cached_text(rules_text, 'small', (255, 100, 100))
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
        """Helper method to draw a modern minimal button."""
        is_hover = rect.collidepoint(mouse_pos)
        
        # Create button surface with alpha
        button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        if is_hover:
            # Hover state - filled with subtle glow
            pygame.draw.rect(button_surface, (*hover_color, 220), button_surface.get_rect(), 
                           border_radius=25)
            # Subtle outer glow
            for i in range(1, 3):
                glow_alpha = 30 - i * 10
                glow_rect = button_surface.get_rect().inflate(i*4, i*4)
                pygame.draw.rect(button_surface, (*hover_color, glow_alpha), glow_rect, 
                               2, border_radius=25)
        else:
            # Normal state - transparent with border
            pygame.draw.rect(button_surface, (*base_color, 40), button_surface.get_rect(), 
                           border_radius=25)
            pygame.draw.rect(button_surface, (*base_color, 180), button_surface.get_rect(), 
                           2, border_radius=25)
        
        # Blit button to screen
        self.screen.blit(button_surface, rect)
        
        # Text with better contrast
        text_color = (255, 255, 255) if is_hover else (230, 230, 230)
        text_surface = self.pixel_fonts['medium'].render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
        
    def _draw_button_with_alpha(self, rect, text, base_color, hover_color, mouse_pos, alpha):
        """Helper method to draw a button with alpha transparency."""
        if alpha <= 0:
            return
            
        # Create a surface for the button
        button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        is_hover = rect.collidepoint(mouse_pos)
        color = hover_color if is_hover else base_color
        
        # Apply alpha to colors
        color_with_alpha = (*color, alpha)
        border_color_with_alpha = (*config.WHITE, alpha)
        
        # Draw button on the surface
        pygame.draw.rect(button_surface, color_with_alpha, (0, 0, rect.width, rect.height), border_radius=10)
        pygame.draw.rect(button_surface, border_color_with_alpha, (0, 0, rect.width, rect.height), 3, border_radius=10)
        
        # Draw text
        text_surface = self.pixel_fonts['medium'].render(text, True, config.WHITE)
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect(center=(rect.width // 2, rect.height // 2))
        button_surface.blit(text_surface, text_rect)
        
        # Blit the button surface to screen
        self.screen.blit(button_surface, rect)
        
    def draw_parallax_background(self, brightness=1.0, surface=None):
        """Draw scrolling background."""
        target = surface if surface else self.screen
        target.fill((20, 20, 30))
        
        if not hasattr(self.assets, 'parallax_layers') or not self.assets.parallax_layers:
            for y in range(0, config.HEIGHT, 10):
                color_val = int(30 + (y / config.HEIGHT) * 20)
                pygame.draw.rect(target, (color_val, color_val, color_val + 10), 
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
                target.blit(scaled_img, (x, 0))
                x += layer_width
                
        if brightness < 1.0:
            overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
            overlay.fill(config.BLACK)
            overlay.set_alpha(int((1.0 - brightness) * 255))
            target.blit(overlay, (0, 0))
        elif brightness > 1.0:
            overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
            overlay.fill(config.WHITE)
            overlay.set_alpha(int((brightness - 1.0) * 128))
            target.blit(overlay, (0, 0))
            
    def draw_parallax_background_with_fire(self, brightness=1.0):
        """Draw scrolling background with fire integrated at appropriate depth."""
        self._fire_updated_this_frame = False
        self.screen.fill((20, 20, 30))
        
        if not hasattr(self.assets, 'parallax_layers') or not self.assets.parallax_layers:
            pass  # No parallax layers warning
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
                pass  # Layer has no image warning
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
                        
                        smoke_surf = self._get_particle_surface(size)
                        for i in range(2):
                            offset_x = random.randint(-3, 3)
                            offset_y = random.randint(-3, 3)
                            pygame.draw.circle(smoke_surf, (*smoke_color, alpha // 2), 
                                             (size + offset_x, size + offset_y), size)
                        fire_surface.blit(smoke_surf, (screen_x - size, screen_y - size))
                        self._return_particle_surface(size, smoke_surf)
        
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
        
    def reset_game_over_fade(self):
        """Reset the victory screen fade timer."""
        if hasattr(self, 'victory_fade_start'):
            delattr(self, 'victory_fade_start')
    
    def draw_game_over(self, board):
        """Draw game over screen styled exactly like story dialogue screen."""
        if not board.game_over:
            # Reset fade if game is not over
            if hasattr(self, 'victory_fade_start'):
                delattr(self, 'victory_fade_start')
            return None, None
            
        current_time = pygame.time.get_ticks()
        
        # Initialize fade-in on first call
        if not hasattr(self, 'victory_fade_start'):
            self.victory_fade_start = current_time
        
        # Two-phase fade: first 0.8s fade to black, then 1.5s fade in victory screen
        fade_to_black_duration = 800
        fade_in_duration = 1500
        total_duration = fade_to_black_duration + fade_in_duration
        
        time_elapsed = current_time - self.victory_fade_start
        
        if time_elapsed < fade_to_black_duration:
            # Phase 1: Fade to black (keep showing the game board)
            black_alpha = int((time_elapsed / fade_to_black_duration) * 255)
            black_overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
            black_overlay.fill((0, 0, 0))
            black_overlay.set_alpha(black_alpha)
            # Don't clear screen - let game board show through
            self.screen.blit(black_overlay, (0, 0))
            return None, None  # Don't show buttons yet
        
        # Phase 2: Victory screen
        fade_progress = min(1.0, (time_elapsed - fade_to_black_duration) / fade_in_duration)
        # Smooth easing for the fade in
        fade_eased = fade_progress * fade_progress * (3.0 - 2.0 * fade_progress)
        
        # Now fill with black and draw victory screen
        self.screen.fill((0, 0, 0))
        
        # Draw background with fade brightness
        self.draw_parallax_background(0.6 * fade_eased)
    
        # Dark overlay
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 180)
        self.screen.blit(overlay, (0, 0))
        
        # Draw effects only after partial fade
        if fade_eased > 0.3:
            # Draw tech grid background
            self._draw_tech_grid()
            
            # Draw digital rain effect for victory screen
            if fade_eased > 0.5:
                self._draw_digital_rain(current_time, victory_screen=True)
        
        # Fade in content after background
        content_fade = max(0, (fade_eased - 0.3) / 0.7)  # Start fading in content at 30%
        
        if board.winner == "white" and content_fade > 0:
            # Get battle data
            battle_data = None
            if hasattr(board, 'is_story_mode') and board.is_story_mode and hasattr(board, 'story_battle'):
                battle_data = board.story_battle
            else:
                # For tutorial/classic mode, use Training Bot data
                battle_data = {
                    "opponent": "TRAINING BOT ALPHA",
                    "portrait": "BOT",
                    "affiliation": "HELIX ACADEMY",
                    "rank": "TRAINING UNIT",
                    "threat_level": "MINIMAL",
                    "classification": "TUTORIAL",
                    "victory": [
                        "TRAINING BOT: ADEQUATE PERFORMANCE.",
                        "TRAINING BOT: YOU MAY PROCEED TO ADVANCED TRAINING."
                    ]
                }
            
            # Create a surface for all victory content with proper alpha
            victory_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
            
            # Character portrait (EXACTLY like story dialogue screen)
            portrait_size = 200
            portrait_x = config.WIDTH // 2 - portrait_size // 2
            portrait_y = 100  # No slide effect, just fade
            
            # Draw scanner effect around portrait with fade
            scanner_alpha = int(255 * content_fade)
            scanner_surface = pygame.Surface((portrait_size + 40, portrait_size + 40), pygame.SRCALPHA)
            # Draw scanner on temp surface then blit with alpha
            self._draw_scanner_effect_on_surface(scanner_surface, 0, 0, portrait_size + 40, portrait_size + 40, current_time, scanner_alpha)
            victory_surface.blit(scanner_surface, (portrait_x - 20, portrait_y - 20))
            
            # Portrait background with tech style - simplified for performance
            # Draw glow with fade alpha
            for i in range(2, -1, -1):  # Draw from back to front
                glow_alpha = int((150 - i*40) * content_fade)
                glow_color = (0, int((150 - i*40) * content_fade), int((150 - i*40) * content_fade))
                pygame.draw.rect(victory_surface, (*glow_color, glow_alpha), 
                               (portrait_x - 20 - i*5, portrait_y - 20 - i*5, 
                                portrait_size + 40 + i*10, portrait_size + 40 + i*10), 
                               3, border_radius=15)
            
            # Main portrait background with fade
            bg_alpha = int(255 * content_fade)
            pygame.draw.rect(victory_surface, (20, 30, 40, bg_alpha), 
                           (portrait_x - 10, portrait_y - 10, portrait_size + 20, portrait_size + 20), 
                           border_radius=10)
            pygame.draw.rect(victory_surface, (0, 200, 255, bg_alpha), 
                           (portrait_x - 10, portrait_y - 10, portrait_size + 20, portrait_size + 20), 
                           3, border_radius=10)
            
            # Portrait - Use bot.png if available
            if battle_data.get("portrait") == "BOT":
                if self.assets.bot_image:
                    bot_scaled = pygame.transform.smoothscale(self.assets.bot_image, 
                                                             (portrait_size - 20, portrait_size - 20))
                    bot_scaled.set_alpha(int(255 * content_fade))
                    bot_rect = bot_scaled.get_rect(center=(portrait_x + portrait_size // 2, 
                                                          portrait_y + portrait_size // 2))
                    victory_surface.blit(bot_scaled, bot_rect)
            
            # VICTORY text - clean and simple like the character intro screen
            victory_text_str = "VICTORY"
            victory_y = portrait_y - 50
            
            # Just draw the text once, cleanly with fade
            text_color = (int(220 * content_fade), int(190 * content_fade), int(130 * content_fade))
            victory_text_surface = self.pixel_fonts['huge'].render(victory_text_str, True, text_color)
            victory_text_rect = victory_text_surface.get_rect(center=(config.WIDTH // 2, victory_y))
            victory_surface.blit(victory_text_surface, victory_text_rect)
            
            # Character name with tech styling (like story dialogue)
            name_text = battle_data["opponent"]
            name_y = portrait_y + portrait_size + 40
            
            # Name background panel
            name_width = len(name_text) * 20 + 60
            name_height = 40
            name_x = config.WIDTH // 2 - name_width // 2
            
            # Draw tech panel for name with fade
            panel_alpha = int(255 * content_fade)
            pygame.draw.rect(victory_surface, (10, 20, 30, panel_alpha), 
                           (name_x, name_y - 20, name_width, name_height), 
                           border_radius=5)
            pygame.draw.rect(victory_surface, (0, 255, 200, panel_alpha), 
                           (name_x, name_y - 20, name_width, name_height), 
                           2, border_radius=5)
            
            # Draw corner brackets with fade
            bracket_size = 15
            bracket_color = (int(0 * content_fade), int(255 * content_fade), int(255 * content_fade))
            # Top left
            pygame.draw.lines(victory_surface, bracket_color, False, 
                             [(name_x, name_y - 20 + bracket_size), (name_x, name_y - 20), (name_x + bracket_size, name_y - 20)], 2)
            # Top right
            pygame.draw.lines(victory_surface, bracket_color, False, 
                             [(name_x + name_width - bracket_size, name_y - 20), (name_x + name_width, name_y - 20), (name_x + name_width, name_y - 20 + bracket_size)], 2)
            # Bottom left
            pygame.draw.lines(victory_surface, bracket_color, False, 
                             [(name_x, name_y + 20 - bracket_size), (name_x, name_y + 20), (name_x + bracket_size, name_y + 20)], 2)
            # Bottom right
            pygame.draw.lines(victory_surface, bracket_color, False, 
                             [(name_x + name_width - bracket_size, name_y + 20), (name_x + name_width, name_y + 20), (name_x + name_width, name_y + 20 - bracket_size)], 2)
            
            # Name text with glow and fade
            name_glow_color = (int(0 * content_fade), int(255 * content_fade), int(255 * content_fade))
            name_glow = self.pixel_fonts['huge'].render(name_text, True, name_glow_color)
            name_glow.set_alpha(int(50 * content_fade))
            name_glow_rect = name_glow.get_rect(center=(config.WIDTH // 2, name_y))
            victory_surface.blit(name_glow, name_glow_rect)
            
            name_surface_text = self.pixel_fonts['huge'].render(name_text, True, name_glow_color)
            name_rect = name_surface_text.get_rect(center=(config.WIDTH // 2, name_y))
            victory_surface.blit(name_surface_text, name_rect)
            
            # Status text with fade
            status_text = "STATUS: DEFEATED"
            status_color = (int(255 * content_fade), int(100 * content_fade), int(100 * content_fade))
            status_surface = self.pixel_fonts['medium'].render(status_text, True, status_color)
            status_rect = status_surface.get_rect(center=(config.WIDTH // 2, name_y + 50))
            victory_surface.blit(status_surface, status_rect)
            
            # Info section with tech styling
            info_y = name_y + 100
            
            # Reward display with fade
            if hasattr(board, 'victory_reward') and board.victory_reward > 0:
                reward_text = f"REWARD: + ${board.victory_reward}"
                reward_color = (int(220 * content_fade), int(190 * content_fade), int(130 * content_fade))
                reward_surface = self.pixel_fonts['large'].render(reward_text, True, reward_color)
                reward_rect = reward_surface.get_rect(center=(config.WIDTH // 2, info_y))
                victory_surface.blit(reward_surface, reward_rect)
                info_y += 40
            
            # Skip battle stats for cleaner look
            
            # Victory dialogue with fade
            if battle_data.get("victory"):
                for i, line in enumerate(battle_data["victory"][:2]):
                    dialogue_color = (int(0 * content_fade), int(200 * content_fade), int(255 * content_fade))
                    line_surface = self.pixel_fonts['small'].render(line, True, dialogue_color)
                    line_rect = line_surface.get_rect(center=(config.WIDTH // 2, info_y))
                    victory_surface.blit(line_surface, line_rect)
                    info_y += 25
            
            # Blit the entire victory surface with content fade
            self.screen.blit(victory_surface, (0, 0))
                
        elif content_fade > 0:
            # DEFEAT screen with similar design
            defeat_text = "DEFEAT"
            
            # Create defeat surface for fading
            defeat_content = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
            
            # Create glowing defeat text with fade
            if 'huge' in self.pixel_fonts:
                # Glow layers with fade
                for i in range(3):
                    glow_alpha = int((100 - i * 30) * content_fade)
                    glow_color = (int(200 * content_fade), int(50 * content_fade), int(50 * content_fade))
                    glow_surface = self.pixel_fonts['huge'].render(defeat_text, True, glow_color)
                    glow_surface.set_alpha(glow_alpha)
                    glow_rect = glow_surface.get_rect(center=(config.WIDTH // 2, 
                                                             config.HEIGHT // 2 - 200 * self.scale))
                    glow_rect.inflate_ip(i * 4, i * 4)
                    defeat_content.blit(glow_surface, glow_rect)
                
                # Main text with fade
                defeat_color = (int(200 * content_fade), int(50 * content_fade), int(50 * content_fade))
                defeat_surface = self.pixel_fonts['huge'].render(defeat_text, True, defeat_color)
            else:
                defeat_font = pygame.font.Font(None, int(72 * self.scale))
                defeat_color = (int(200 * content_fade), int(50 * content_fade), int(50 * content_fade))
                defeat_surface = defeat_font.render(defeat_text, True, defeat_color)
            
            rect = defeat_surface.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 200 * self.scale))
            defeat_content.blit(defeat_surface, rect)
            
            if hasattr(board, 'is_story_mode') and board.is_story_mode and hasattr(board, 'story_battle'):
                battle = board.story_battle
                if "defeat" in battle:
                    defeat_dialogue_y = config.HEIGHT // 2 - 20 * self.scale
                    for line in battle["defeat"]:
                        if line:
                            line_color = (int(200 * content_fade), int(200 * content_fade), int(200 * content_fade))
                            line_surface = self.pixel_fonts['small'].render(line, True, line_color)
                            line_rect = line_surface.get_rect(center=(config.WIDTH // 2, defeat_dialogue_y))
                            defeat_content.blit(line_surface, line_rect)
                            defeat_dialogue_y += 25
                else:
                    encourage_text = "Better luck next time!"
                    text_color = (int(150 * content_fade), int(150 * content_fade), int(150 * content_fade))
                    text = self.pixel_fonts['medium'].render(encourage_text, True, text_color)
                    rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 20 * self.scale))
                    defeat_content.blit(text, rect)
            
            # Blit defeat content to screen
            self.screen.blit(defeat_content, (0, 0))
        
        # Clean button design positioned lower
        button_y = config.HEIGHT // 2 + 180 * self.scale
        button_width = 180 * self.scale
        button_height = 50 * self.scale
        button_spacing = 40 * self.scale
        
        # Restart button
        restart_x = config.WIDTH // 2 - button_width - button_spacing // 2
        restart_rect = pygame.Rect(restart_x, button_y, button_width, button_height)
        
        # Modern button style with hover effect
        mouse_pos = pygame.mouse.get_pos()
        restart_hover = restart_rect.collidepoint(mouse_pos)
        
        # Button background with fade
        button_alpha = int(255 * content_fade) if content_fade > 0 else 255
        restart_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        if restart_hover:
            bg_alpha = min(220, int(220 * content_fade)) if content_fade > 0 else 220
            border_alpha = min(255, int(255 * content_fade)) if content_fade > 0 else 255
            pygame.draw.rect(restart_surface, (60, 120, 60, bg_alpha), restart_surface.get_rect(), border_radius=22)
            pygame.draw.rect(restart_surface, (100, 200, 100, border_alpha), restart_surface.get_rect(), 2, border_radius=22)
        else:
            bg_alpha = min(200, int(200 * content_fade)) if content_fade > 0 else 200
            border_alpha = min(200, int(200 * content_fade)) if content_fade > 0 else 200
            pygame.draw.rect(restart_surface, (40, 80, 40, bg_alpha), restart_surface.get_rect(), border_radius=22)
            pygame.draw.rect(restart_surface, (80, 160, 80, border_alpha), restart_surface.get_rect(), 2, border_radius=22)
        self.screen.blit(restart_surface, restart_rect)
        
        # Button text - "NEXT ENEMY" for story mode with more battles, otherwise "PLAY AGAIN"
        button_label = "PLAY AGAIN"
        if hasattr(board, 'is_story_mode') and board.is_story_mode:
            # Check if there are more battles in the chapter
            if hasattr(board, 'has_next_battle') and board.has_next_battle:
                button_label = "NEXT ENEMY"
        
        # Button text with fade
        text_alpha = int(255 * content_fade) if content_fade > 0 else 255
        text_color = (text_alpha, text_alpha, text_alpha)
        restart_text = self.pixel_fonts['medium'].render(button_label, True, text_color)
        restart_text_rect = restart_text.get_rect(center=restart_rect.center)
        self.screen.blit(restart_text, restart_text_rect)
        
        # Menu button
        menu_x = config.WIDTH // 2 + button_spacing // 2
        menu_rect = pygame.Rect(menu_x, button_y, button_width, button_height)
        menu_hover = menu_rect.collidepoint(mouse_pos)
        
        # Button background with fade
        menu_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        if menu_hover:
            bg_alpha = min(220, int(220 * content_fade)) if content_fade > 0 else 220
            border_alpha = min(255, int(255 * content_fade)) if content_fade > 0 else 255
            pygame.draw.rect(menu_surface, (80, 80, 80, bg_alpha), menu_surface.get_rect(), border_radius=22)
            pygame.draw.rect(menu_surface, (160, 160, 160, border_alpha), menu_surface.get_rect(), 2, border_radius=22)
        else:
            bg_alpha = min(200, int(200 * content_fade)) if content_fade > 0 else 200
            border_alpha = min(200, int(200 * content_fade)) if content_fade > 0 else 200
            pygame.draw.rect(menu_surface, (50, 50, 50, bg_alpha), menu_surface.get_rect(), border_radius=22)
            pygame.draw.rect(menu_surface, (120, 120, 120, border_alpha), menu_surface.get_rect(), 2, border_radius=22)
        self.screen.blit(menu_surface, menu_rect)
        
        # Menu text with fade
        menu_text = self.pixel_fonts['medium'].render("MAIN MENU", True, text_color)
        menu_text_rect = menu_text.get_rect(center=menu_rect.center)
        self.screen.blit(menu_text, menu_text_rect)
        
        # Keyboard shortcuts hint with fade
        hint_y = button_y + button_height + 20 * self.scale
        hint_alpha = int(150 * content_fade) if content_fade > 0 else 150
        hint_color = (hint_alpha, hint_alpha, hint_alpha)
        hint_text = self.pixel_fonts['tiny'].render("Press R to restart • ESC for menu", True, hint_color)
        hint_rect = hint_text.get_rect(center=(config.WIDTH // 2, hint_y))
        self.screen.blit(hint_text, hint_rect)
        
        # Return button rectangles for click handling
        return restart_rect, menu_rect
        
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
        
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 100)
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
            self.draw_parallax_background_with_fire(1.0)
        else:
            self.draw_parallax_background(1.0)
        
        overlay_alpha = 80 if screen_type == config.SCREEN_START else 120
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), overlay_alpha)
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
                
            # Title with typewriter effect - slower speed for dramatic effect
            title_pos = (game_center_x, game_center_y - 150 * config.SCALE)
            self.draw_text_typewriter("CHECKMATE PROTOCOL", title_pos, 'huge', config.WHITE, center=True, text_id="main_title", speed=15)
            
            # Check if main title typewriter effect is complete
            main_title_complete = False
            for text_data in self.typewriter_texts:
                if text_data.get('full_text') == "CHECKMATE PROTOCOL" and text_data.get('completed', False):
                    main_title_complete = True
                    break
            
            if hasattr(self.assets, 'beta_badge') and self.assets.beta_badge and main_title_complete:
                badge_height = int(80 * config.SCALE)
                aspect_ratio = self.assets.beta_badge.get_width() / self.assets.beta_badge.get_height()
                badge_width = int(badge_height * aspect_ratio)
                
                scaled_badge = pygame.transform.scale(self.assets.beta_badge, (badge_width, badge_height))
                rotated_badge = pygame.transform.rotate(scaled_badge, -15)
                
                # Calculate badge position based on title
                title_width = self.pixel_fonts['huge'].size("CHECKMATE PROTOCOL")[0]
                badge_x = game_center_x + title_width // 2 - int(5 * config.SCALE)
                badge_y = game_center_y - 150 * config.SCALE - int(70 * config.SCALE)
                
                # Calculate fade-in alpha based on time since title completion
                if not hasattr(self, 'badge_fade_start'):
                    self.badge_fade_start = pygame.time.get_ticks()
                
                fade_duration = 500  # 0.5 seconds fade-in
                elapsed = pygame.time.get_ticks() - self.badge_fade_start
                alpha = min(255, int(255 * (elapsed / fade_duration)))
                
                rotated_badge.set_alpha(alpha)
                self.screen.blit(rotated_badge, (badge_x, badge_y))
                
                # Calculate button fade-in based on badge fade completion
                badge_fade_complete = elapsed >= fade_duration
                if badge_fade_complete:
                    if not hasattr(self, 'buttons_fade_start'):
                        self.buttons_fade_start = pygame.time.get_ticks()
                    
                    buttons_fade_duration = 800  # 0.8 seconds fade-in
                    buttons_elapsed = pygame.time.get_ticks() - self.buttons_fade_start
                    buttons_alpha = min(255, int(255 * (buttons_elapsed / buttons_fade_duration)))
                    
                    # Draw buttons with fade effect
                    self._draw_button_with_alpha(buttons['play'], "PLAY GAME", (70, 150, 70), (100, 200, 100), mouse_pos, buttons_alpha)
                    self._draw_button_with_alpha(buttons['tutorial'], "TUTORIAL", (70, 100, 150), (100, 130, 200), mouse_pos, buttons_alpha)
                    self._draw_button_with_alpha(buttons['beta'], "BETA TEST INFO", (150, 150, 70), (200, 200, 100), mouse_pos, buttons_alpha)
                    self._draw_button_with_alpha(buttons['credits'], "CREDITS", (70, 70, 150), (100, 100, 200), mouse_pos, buttons_alpha)
            else:
                # If no badge or title not complete, don't show buttons yet
                pass
            
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
            # Animated background particles
            current_time = pygame.time.get_ticks()
            
            # Draw floating particles in background
            if not hasattr(self, '_mode_particles'):
                self._mode_particles = []
                for _ in range(30):
                    self._mode_particles.append({
                        'x': random.randint(0, config.WIDTH),
                        'y': random.randint(0, config.HEIGHT),
                        'size': random.randint(2, 5),
                        'speed': random.uniform(0.5, 2),
                        'opacity': random.randint(30, 100)
                    })
            
            # Update and draw particles
            for particle in self._mode_particles:
                particle['y'] -= particle['speed']
                if particle['y'] < -10:
                    particle['y'] = config.HEIGHT + 10
                    particle['x'] = random.randint(0, config.WIDTH)
                
                # Glow effect
                glow_surf = pygame.Surface((particle['size']*4, particle['size']*4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (100, 200, 255, particle['opacity']//3), 
                                 (particle['size']*2, particle['size']*2), particle['size']*2)
                self.screen.blit(glow_surf, (particle['x'] - particle['size']*2, particle['y'] - particle['size']*2))
                pygame.draw.circle(self.screen, (200, 230, 255, particle['opacity']), 
                                 (int(particle['x']), int(particle['y'])), particle['size'])
            
            # Animated title with glow effect
            title_text = "CHOOSE YOUR PATH"
            title_y = config.GAME_OFFSET_Y + 80 * config.SCALE
            
            # Create glowing title effect
            for i in range(3, 0, -1):
                glow_alpha = 40 - i * 10
                glow_color = (100 + i*20, 150 + i*20, 255)
                glow_text = self.pixel_fonts['huge'].render(title_text, True, glow_color)
                glow_text.set_alpha(glow_alpha)
                glow_rect = glow_text.get_rect(center=(game_center_x, title_y))
                self.screen.blit(glow_text, glow_rect.move(0, i))
            
            # Main title
            text = self.pixel_fonts['huge'].render(title_text, True, (255, 255, 255))
            rect = text.get_rect(center=(game_center_x, title_y))
            self.screen.blit(text, rect)
            
            # Futuristic card layout with icons
            modes = [
                {
                    "key": "classic",
                    "name": "CLASSIC",
                    "subtitle": "TRADITIONAL WARFARE",
                    "desc": ["Strategic chess battles", "Earn powerup points", "Master the basics"],
                    "icon": "♔",  # Chess king
                    "color": (0, 255, 136),  # Neon green
                    "hover_color": (50, 255, 156),
                    "bg_gradient": [(0, 80, 50), (0, 120, 70)]
                },
                {
                    "key": "story",
                    "name": "CAMPAIGN",
                    "subtitle": "EPIC STORYLINE",
                    "desc": ["25+ unique battles", "Boss encounters", "Unlock rewards"],
                    "icon": "⚔",  # Crossed swords
                    "color": (255, 140, 0),  # Neon orange
                    "hover_color": (255, 170, 30),
                    "bg_gradient": [(120, 60, 0), (180, 90, 0)],
                    "recommended": True
                },
                {
                    "key": "freeplay",
                    "name": "SANDBOX",
                    "subtitle": "UNLIMITED POWER",
                    "desc": ["Infinite resources", "Test strategies", "Pure chaos"],
                    "icon": "∞",  # Infinity
                    "color": (147, 0, 255),  # Neon purple
                    "hover_color": (177, 50, 255),
                    "bg_gradient": [(60, 0, 100), (90, 0, 150)]
                }
            ]
            
            # Larger, more dramatic cards
            card_width = int(280 * config.SCALE)
            card_height = int(380 * config.SCALE)
            card_spacing = int(50 * config.SCALE)
            total_width = len(modes) * card_width + (len(modes) - 1) * card_spacing
            start_x = game_center_x - total_width // 2
            card_y = config.GAME_OFFSET_Y + 180 * config.SCALE
            
            for i, mode in enumerate(modes):
                card_x = start_x + i * (card_width + card_spacing)
                card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                
                # Check hover with animation
                is_hover = card_rect.collidepoint(mouse_pos)
                hover_offset = -10 if is_hover else 0
                animated_rect = card_rect.move(0, hover_offset)
                
                # Create dramatic card with depth
                card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                
                # Dark gradient background
                gradient_colors = mode['bg_gradient']
                for y_offset in range(card_height):
                    factor = y_offset / card_height
                    r = int(gradient_colors[0][0] + (gradient_colors[1][0] - gradient_colors[0][0]) * factor)
                    g = int(gradient_colors[0][1] + (gradient_colors[1][1] - gradient_colors[0][1]) * factor)
                    b = int(gradient_colors[0][2] + (gradient_colors[1][2] - gradient_colors[0][2]) * factor)
                    alpha = 220 if is_hover else 180
                    pygame.draw.line(card_surface, (r, g, b, alpha), (0, y_offset), (card_width, y_offset))
                
                # Neon border effect
                if is_hover:
                    # Outer glow
                    for glow_size in range(5, 0, -1):
                        glow_alpha = 30 - glow_size * 5
                        glow_rect = card_surface.get_rect().inflate(glow_size*2, glow_size*2)
                        pygame.draw.rect(card_surface, (*mode['hover_color'], glow_alpha), 
                                       glow_rect, 3, border_radius=20)
                
                # Main border
                border_color = mode['hover_color'] if is_hover else mode['color']
                pygame.draw.rect(card_surface, (*border_color, 255), 
                               card_surface.get_rect(), 3, border_radius=15)
                
                # Inner glow line
                inner_rect = card_surface.get_rect().inflate(-6, -6)
                pygame.draw.rect(card_surface, (*border_color, 100), inner_rect, 1, border_radius=15)
                
                self.screen.blit(card_surface, animated_rect)
                
                # Large dramatic icon
                icon_y = animated_rect.y + int(60 * config.SCALE)
                
                # Icon with glow effect
                icon_color = mode['hover_color'] if is_hover else mode['color']
                
                # Create icon glow
                if 'huge' in self.pixel_fonts:
                    icon_font = self.pixel_fonts['huge']
                else:
                    icon_font = pygame.font.Font(None, int(80 * config.SCALE))
                
                # Multiple layers for glow effect
                for glow_layer in range(3, 0, -1):
                    glow_alpha = 60 - glow_layer * 15
                    glow_size = glow_layer * 2
                    icon_glow = icon_font.render(mode['icon'], True, icon_color)
                    icon_glow.set_alpha(glow_alpha)
                    for dx in range(-glow_size, glow_size+1):
                        for dy in range(-glow_size, glow_size+1):
                            if abs(dx) == glow_size or abs(dy) == glow_size:
                                glow_rect = icon_glow.get_rect(center=(card_x + card_width // 2 + dx, icon_y + dy))
                                self.screen.blit(icon_glow, glow_rect)
                
                # Main icon
                icon_text = icon_font.render(mode['icon'], True, (255, 255, 255))
                icon_rect = icon_text.get_rect(center=(card_x + card_width // 2, icon_y))
                self.screen.blit(icon_text, icon_rect)
                
                # Mode name with futuristic style
                name_y = animated_rect.y + int(140 * config.SCALE)
                name_color = mode['hover_color'] if is_hover else mode['color']
                name_text = self.pixel_fonts['large'].render(mode['name'], True, name_color)
                name_rect = name_text.get_rect(center=(card_x + card_width // 2, name_y))
                self.screen.blit(name_text, name_rect)
                
                # Subtitle
                subtitle_y = name_y + int(30 * config.SCALE)
                subtitle_text = self.pixel_fonts['small'].render(mode['subtitle'], True, (180, 180, 180))
                subtitle_rect = subtitle_text.get_rect(center=(card_x + card_width // 2, subtitle_y))
                self.screen.blit(subtitle_text, subtitle_rect)
                
                # Divider line
                divider_y = subtitle_y + int(25 * config.SCALE)
                divider_color = (*mode['color'], 100)
                pygame.draw.line(self.screen, divider_color,
                               (card_x + card_width // 4, divider_y),
                               (card_x + 3 * card_width // 4, divider_y), 2)
                
                # Feature list with bullets
                feature_y = divider_y + int(30 * config.SCALE)
                for feature in mode['desc']:
                    # Bullet point
                    bullet_color = mode['color'] if is_hover else (150, 150, 150)
                    pygame.draw.circle(self.screen, bullet_color,
                                     (card_x + int(40 * config.SCALE), feature_y),
                                     int(3 * config.SCALE))
                    
                    # Feature text
                    feature_text = self.pixel_fonts['small'].render(feature, True, (220, 220, 220))
                    feature_rect = feature_text.get_rect(left=card_x + int(55 * config.SCALE), 
                                                        centery=feature_y)
                    self.screen.blit(feature_text, feature_rect)
                    feature_y += int(35 * config.SCALE)
                
                # Special badges and effects
                if mode.get('recommended'):
                    # Animated recommended badge
                    badge_y = animated_rect.y + card_height - int(45 * config.SCALE)
                    pulse = abs(math.sin(current_time * 0.003)) * 0.5 + 0.5
                    
                    # Glowing badge background
                    badge_width = int(140 * config.SCALE)
                    badge_height = int(35 * config.SCALE)
                    
                    # Outer glow
                    for i in range(3, 0, -1):
                        glow_surf = pygame.Surface((badge_width + i*10, badge_height + i*10), pygame.SRCALPHA)
                        glow_alpha = int((20 - i*5) * pulse)
                        pygame.draw.rect(glow_surf, (255, 200, 0, glow_alpha), 
                                       glow_surf.get_rect(), border_radius=20)
                        glow_rect = glow_surf.get_rect(center=(card_x + card_width // 2, badge_y))
                        self.screen.blit(glow_surf, glow_rect)
                    
                    # Main badge
                    badge_surf = pygame.Surface((badge_width, badge_height), pygame.SRCALPHA)
                    pygame.draw.rect(badge_surf, (255, 200, 0, 200), badge_surf.get_rect(), 
                                   border_radius=17)
                    pygame.draw.rect(badge_surf, (255, 255, 200, 255), badge_surf.get_rect(), 
                                   2, border_radius=17)
                    badge_rect = badge_surf.get_rect(center=(card_x + card_width // 2, badge_y))
                    self.screen.blit(badge_surf, badge_rect)
                    
                    # Badge text with star icons
                    star = "★"
                    badge_text = f"{star} RECOMMENDED {star}"
                    text_surf = self.pixel_fonts['tiny'].render(badge_text, True, (50, 50, 50))
                    text_rect = text_surf.get_rect(center=(card_x + card_width // 2, badge_y))
                    self.screen.blit(text_surf, text_rect)
            
            # Instruction text at bottom
            instruction_y = config.HEIGHT - int(80 * config.SCALE)
            instruction_text = "CLICK TO SELECT YOUR DESTINY"
            inst_alpha = int(abs(math.sin(current_time * 0.002)) * 150 + 105)
            inst_color = (150, 200, 255, inst_alpha)
            
            # Create instruction surface for alpha
            inst_surf = pygame.Surface((config.WIDTH, 30), pygame.SRCALPHA)
            inst_text_render = self.pixel_fonts['medium'].render(instruction_text, True, (150, 200, 255))
            inst_text_render.set_alpha(inst_alpha)
            inst_rect = inst_text_render.get_rect(center=(config.WIDTH // 2, 15))
            inst_surf.blit(inst_text_render, inst_rect)
            self.screen.blit(inst_surf, (0, instruction_y))
            
            # Clean back button
            self._draw_button(buttons['back'], "BACK", (80, 80, 80), (120, 120, 120), mouse_pos)
            
    def draw_tutorial(self, tutorial_page_data, tutorial_buttons, mouse_pos):
        """Draw tutorial screen with navigation."""
        self.draw_parallax_background(1.0)
        
        tutorial_page = tutorial_page_data['page']
        current_index = tutorial_page_data['current_index']
        total_pages = tutorial_page_data['total_pages']
        
        overlay = self._get_cached_overlay(config.WIDTH, config.HEIGHT, (0, 0, 0), 120)
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
            title_surface = self.pixel_fonts['large'].render(tutorial_page["title"], True, (220, 190, 130))
            title_rect = title_surface.get_rect(center=(game_center_x, y))
            self.screen.blit(title_surface, title_rect)
            y += 50 * config.SCALE
        
        if "content" in tutorial_page:
            for line in tutorial_page["content"]:
                if line:
                    if line.startswith("•"):
                        color = (200, 200, 200)
                    elif "=" in line:
                        color = (220, 190, 130)
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
        
    def draw_tutorial_hints(self, story_tutorial):
        """Draw tutorial hints and highlights."""
        # Draw highlighted squares as circles
        for square in story_tutorial.get_highlight_squares():
            col, row = square  # Tutorial stores as (col, row)
            # Use the same positioning calculation as board.get_square_pos() but with scaling
            border_left_scaled = int(config.BOARD_BORDER_LEFT * self.scale)
            border_top_scaled = int(config.BOARD_BORDER_TOP * self.scale)
            square_size_scaled = int(config.SQUARE_SIZE * self.scale)
            
            x = config.BOARD_OFFSET_X + border_left_scaled + col * square_size_scaled
            y = config.BOARD_OFFSET_Y + border_top_scaled + row * square_size_scaled
            
            # Center of the square
            center_x = x + square_size_scaled // 2
            center_y = y + square_size_scaled // 2
            
            # Create pulsing highlight with cleaner pixel-art style
            pulse = (pygame.time.get_ticks() // 150) % 20  # Smoother pulsing
            pulse_factor = abs(10 - pulse) / 10.0  # Creates smooth in-out pulse
            
            # Draw a cleaner double-ring highlight
            outer_radius = int(square_size_scaled * 0.42)
            inner_radius = int(square_size_scaled * 0.35)
            
            # Outer ring with subtle glow (just one clean layer)
            glow_alpha = int(80 + pulse_factor * 40)
            glow_surf = pygame.Surface((square_size_scaled * 2, square_size_scaled * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (200, 180, 100, glow_alpha), 
                             (square_size_scaled, square_size_scaled), outer_radius, 2)
            self.screen.blit(glow_surf, (center_x - square_size_scaled, center_y - square_size_scaled))
            
            # Main highlight ring (solid, clean edges)
            ring_alpha = int(180 + pulse_factor * 75)
            pygame.draw.circle(self.screen, (220, 190, 130, ring_alpha), (center_x, center_y), inner_radius, 3)
            
            # Inner dot for emphasis
            dot_radius = int(3 * self.scale)
            pygame.draw.circle(self.screen, (230, 210, 160), (center_x, center_y), dot_radius)
        
        # Draw highlight for powerup buttons
        highlighted_powerup = story_tutorial.get_highlight_powerup()
        if highlighted_powerup:
            # Calculate powerup menu position (matching powerup_renderer exactly)
            extra_spacing = 20  # Normal gap in windowed mode
            menu_x = config.BOARD_OFFSET_X + config.BOARD_SIZE + extra_spacing
            menu_y = config.BOARD_OFFSET_Y + 36  # Move down by the board border size
            menu_width = config.POWERUP_MENU_WIDTH  # Use actual config value (250)
            
            # Define powerup order (same as in powerup_renderer)
            powerup_keys = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
            
            # Find the index of the highlighted powerup
            if highlighted_powerup in powerup_keys:
                index = powerup_keys.index(highlighted_powerup)
                # Match the actual button positioning from powerup_renderer.py
                button_y = menu_y + 120  # Buttons start at menu_y + 120
                button_height = 70
                button_spacing = 15
                button_margin = 20
                
                # Calculate the actual button position
                card_y = button_y + index * (button_height + button_spacing)
                card_height = button_height
                
                # Draw pulsing highlight around the powerup card
                pulse = (pygame.time.get_ticks() // 200) % 10
                thickness = 4 + (pulse // 3)
                
                # Calculate actual button dimensions (matching powerup_renderer)
                button_width = menu_width - 2 * button_margin
                button_x = menu_x + button_margin
                
                # Create glowing effect
                for i in range(3):
                    alpha = 150 - (i * 50)
                    glow_surf = pygame.Surface((button_width + i*8, card_height + i*8), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 215, 0, alpha), 
                                   (0, 0, button_width + i*8, card_height + i*8), 
                                   thickness + i*2, border_radius=10)
                    self.screen.blit(glow_surf, (button_x - i*4, card_y - i*4))
                
                # Draw main highlight border
                pygame.draw.rect(self.screen, (255, 215, 0), 
                               (button_x, card_y, button_width, card_height), 
                               thickness, border_radius=10)
        
        # Draw instruction panel
        instruction = story_tutorial.get_current_instruction()
        if instruction:
            panel_width = 700
            panel_height = 60
            panel_x = (config.WIDTH - panel_width) // 2
            panel_y = config.HEIGHT - panel_height - 10
            
            # Panel background
            panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel_surf.fill((0, 0, 0, 220))
            pygame.draw.rect(panel_surf, (200, 180, 120), panel_surf.get_rect(), 3)
            self.screen.blit(panel_surf, (panel_x, panel_y))
            
            # Tutorial text
            lines = self._wrap_text(instruction, self.pixel_fonts['medium'], panel_width - 20)
            y_offset = 15
            for line in lines:
                text_surf = self.pixel_fonts['medium'].render(line, True, (255, 255, 255))
                text_rect = text_surf.get_rect(centerx=config.WIDTH // 2, y=panel_y + y_offset)
                self.screen.blit(text_surf, text_rect)
                y_offset += 25
                
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within a given width."""
        words = text.split()
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
        
    def draw_arms_dealer(self, powerup_system, shop_buttons, back_button, mouse_pos, dialogue_index=0, dialogues=None, story_tutorial=None, fade_progress=1.0):
        """Draw the arms dealer shop with simple design."""
        current_time = pygame.time.get_ticks()
        
        # Simple background
        if hasattr(self.assets, 'arms_background') and self.assets.arms_background:
            scaled_bg = pygame.transform.scale(self.assets.arms_background, (config.WIDTH, config.HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
        else:
            # Simple dark background
            self.screen.fill((30, 30, 40))
        
        if config.SCALE != 1.0:
            game_center_x = config.GAME_OFFSET_X + (config.BASE_WIDTH * config.SCALE) // 2
            game_center_y = config.GAME_OFFSET_Y + (config.BASE_HEIGHT * config.SCALE) // 2
        else:
            game_center_x = config.WIDTH // 2
            game_center_y = config.HEIGHT // 2
        
        # Simple Tariq character with fade-in effect
        if hasattr(self.assets, 'tariq_image') and self.assets.tariq_image:
            tariq_height = int(400 * config.SCALE)
            aspect_ratio = self.assets.tariq_image.get_width() / self.assets.tariq_image.get_height()
            tariq_width = int(tariq_height * aspect_ratio)
            
            scaled_tariq = pygame.transform.smoothscale(self.assets.tariq_image, (tariq_width, tariq_height))
            
            # Apply fade effect to Tariq
            if fade_progress < 1.0:
                # Create a copy with alpha
                tariq_copy = scaled_tariq.copy()
                tariq_copy.set_alpha(int(255 * fade_progress))
                scaled_tariq = tariq_copy
            
            # Slide in from left during fade
            base_x = int(50 * config.SCALE)
            slide_offset = int((1 - fade_progress) * -100 * config.SCALE)
            tariq_x = base_x + slide_offset
            tariq_y = config.HEIGHT - tariq_height
            
            self.screen.blit(scaled_tariq, (tariq_x, tariq_y))
            
            self.tariq_rect = pygame.Rect(tariq_x, tariq_y, tariq_width, tariq_height)
            
            # Simple speech bubble with fade and delay
            if dialogues and 0 <= dialogue_index < len(dialogues) and fade_progress > 0.3:
                dialogue = dialogues[dialogue_index]
                bubble_width = int(320 * config.SCALE)
                tariq_center_x = tariq_x + tariq_width // 2
                bubble_x = tariq_center_x - bubble_width // 2 - 3
                bubble_y = tariq_y - int(100 * config.SCALE)
                
                # Calculate bubble fade (starts after Tariq is 30% visible)
                bubble_fade = min(1.0, (fade_progress - 0.3) / 0.7)
                
                # Draw bubble with fade by adjusting colors
                original_alpha = int(255 * bubble_fade)
                self._draw_speech_bubble(bubble_x, bubble_y, 
                                       dialogue, bubble_width, point_down=True, 
                                       use_typewriter=True, text_id=f"tariq_dialogue_{dialogue_index}")
        
        # Simple title
        title_text = "TARIQ'S ARMORY"
        title_y = game_center_y - 280 * config.SCALE
        
        title_surface = self.pixel_fonts['huge'].render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(game_center_x, title_y))
        self.screen.blit(title_surface, title_rect)
        
        # Simple money display - use in-memory value
        money = config.get_money()
        
        money_text = f"Money: ${money:,}"
        money_surface = self.pixel_fonts['large'].render(money_text, True, (220, 190, 130))
        money_rect = money_surface.get_rect(center=(game_center_x, title_y + 60))
        self.screen.blit(money_surface, money_rect)
        
        # Check if in tutorial mode and use tutorial unlocked powerups
        if story_tutorial and story_tutorial.active:
            # In tutorial, use whatever is currently unlocked (initially nothing, then shield after visit)
            unlocked = config.tutorial_unlocked_powerups
        else:
            unlocked = config.get_unlocked_powerups()
        
        # Simple powerup display
        
        # Simple rectangular card layout
        powerup_keys = ["shield", "gun", "airstrike", "paratroopers", "chopper"]
        
        # Calculate positions for simple row arrangement - smaller cards
        card_width = 100 * self.scale
        card_height = 140 * self.scale
        card_spacing = 15 * self.scale
        total_width = len(powerup_keys) * card_width + (len(powerup_keys) - 1) * card_spacing
        start_x = game_center_x - total_width / 2 + 100 * self.scale  # Shift right
        card_y = game_center_y - 80 * self.scale
        
        shop_buttons.clear()
        
        for i, powerup_key in enumerate(powerup_keys):
            powerup = powerup_system.powerups[powerup_key]
            price = powerup_system.powerup_prices[powerup_key]
            is_unlocked = powerup_key in unlocked
            can_afford = money >= price and not is_unlocked
            
            # Calculate card position
            card_x = start_x + i * (card_width + card_spacing)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            shop_buttons[powerup_key] = card_rect
            
            # Check hover
            is_hover = card_rect.collidepoint(mouse_pos) and not is_unlocked
            
            # Modern card design with gradients and better colors
            if is_unlocked:
                # Owned - clean green gradient effect
                card_base_color = (40, 90, 50)
                card_highlight_color = (60, 140, 80)
                border_color = (100, 255, 150)
                glow_color = (0, 255, 100, 30)
            elif can_afford:
                # Affordable - warm gold gradient
                card_base_color = (80, 60, 30)
                card_highlight_color = (120, 90, 40)
                border_color = (200, 180, 120)
                glow_color = (255, 200, 0, 20)
            else:
                # Too expensive - clean gray
                card_base_color = (50, 50, 55)
                card_highlight_color = (70, 70, 75)
                border_color = (120, 120, 130)
                glow_color = None
            
            # Draw card with gradient effect
            # Shadow first
            shadow_surf = pygame.Surface((card_rect.width + 10, card_rect.height + 10), pygame.SRCALPHA)
            shadow_color = (0, 0, 0, 80)
            pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(), border_radius=10)
            self.screen.blit(shadow_surf, (card_rect.x - 3, card_rect.y + 3))
            
            # Base layer
            pygame.draw.rect(self.screen, card_base_color, card_rect, border_radius=8)
            
            # Highlight gradient (top half lighter)
            highlight_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, card_rect.height // 2)
            highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
            highlight_surf.fill((*card_highlight_color, 100))
            self.screen.blit(highlight_surf, highlight_rect)
            
            # Clean border
            pygame.draw.rect(self.screen, border_color, card_rect, 2, border_radius=8)
            
            # Modern hover effect with glow
            if is_hover:
                # Outer glow
                for i in range(3):
                    glow_rect = card_rect.inflate(4 + i*4, 4 + i*4)
                    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    glow_alpha = 40 - i*12
                    pygame.draw.rect(glow_surf, (*border_color, glow_alpha), glow_surf.get_rect(), border_radius=10)
                    self.screen.blit(glow_surf, glow_rect)
                
                # Inner bright border
                pygame.draw.rect(self.screen, border_color, card_rect, 3, border_radius=8)
            
            # Tutorial highlighting for shield
            if story_tutorial and story_tutorial.active and powerup_key == "shield" and not is_unlocked:
                # Draw pulsing golden highlight
                pulse = (pygame.time.get_ticks() // 200) % 10
                thickness = 4 + (pulse // 3)
                
                # Create glowing effect
                for i in range(3):
                    alpha = 150 - (i * 50)
                    glow_surf = pygame.Surface((card_width + i*8, card_height + i*8), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 215, 0, alpha), 
                                   (0, 0, card_width + i*8, card_height + i*8), 
                                   thickness + i*2, border_radius=5)
                    self.screen.blit(glow_surf, (card_x - i*4, card_y - i*4))
                
                # Draw main highlight border
                pygame.draw.rect(self.screen, (255, 215, 0), card_rect, thickness, border_radius=5)
                
                # Add "CLICK ME!" text
                click_text = self.pixel_fonts['small'].render("CLICK TO UNLOCK!", True, (220, 190, 130))
                click_rect = click_text.get_rect(center=(card_rect.centerx, card_rect.top - 20))
                self.screen.blit(click_text, click_rect)
            
            # Simple powerup icons
            icon_y = card_rect.centery - 20
            
            if powerup_key == "gun" and hasattr(self, 'assets') and hasattr(self.assets, 'revolver_image') and self.assets.revolver_image:
                icon_size = 40
                scaled_revolver = pygame.transform.scale(self.assets.revolver_image, (icon_size, icon_size))
                icon_rect = scaled_revolver.get_rect(center=(card_rect.centerx, icon_y))
                self.screen.blit(scaled_revolver, icon_rect)
            elif powerup_key == "shield":
                self._draw_shield_icon(self.screen, card_rect, icon_y, can_afford or is_unlocked)
            elif powerup_key == "airstrike":
                self._draw_missile_icon(self.screen, card_rect, icon_y, can_afford or is_unlocked)
            elif powerup_key == "paratroopers":
                self._draw_parachute_icon(self.screen, card_rect, icon_y, can_afford or is_unlocked)
            elif powerup_key == "chopper":
                self._draw_helicopter_icon(self.screen, card_rect, icon_y, can_afford or is_unlocked)
            
            # Simple powerup name - use smaller font for longer names
            powerup_name = powerup["name"]
            
            # Special handling for very long names
            if powerup_key == "chopper":
                # Split "CHOPPER GUNNER" into two lines with less spacing
                line1_surface = self.pixel_fonts['small'].render("CHOPPER", True, (255, 255, 255))
                line2_surface = self.pixel_fonts['small'].render("GUNNER", True, (255, 255, 255))
                line1_rect = line1_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 12))
                line2_rect = line2_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 28))
                self.screen.blit(line1_surface, line1_rect)
                self.screen.blit(line2_surface, line2_rect)
            elif powerup_key == "paratroopers":
                # Use extra small font for PARATROOPERS
                # Try using tiny font if available, otherwise use small
                if 'tiny' in self.pixel_fonts:
                    name_surface = self.pixel_fonts['tiny'].render(powerup_name, True, (255, 255, 255))
                else:
                    name_surface = self.pixel_fonts['small'].render(powerup_name, True, (255, 255, 255))
                name_rect = name_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 20))
                self.screen.blit(name_surface, name_rect)
            else:
                # Check if name fits in card width
                test_surface = self.pixel_fonts['medium'].render(powerup_name, True, (255, 255, 255))
                if test_surface.get_width() > card_width - 20:
                    # Use small font for long names with more padding
                    name_surface = self.pixel_fonts['small'].render(powerup_name, True, (255, 255, 255))
                else:
                    # Use medium font for short names
                    name_surface = self.pixel_fonts['medium'].render(powerup_name, True, (255, 255, 255))
                name_rect = name_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 20))
                self.screen.blit(name_surface, name_rect)
            
            # Simple price/status display
            if is_unlocked:
                owned_text = self.pixel_fonts['small'].render("OWNED", True, (100, 255, 100))
                owned_rect = owned_text.get_rect(center=(card_rect.centerx, card_rect.bottom - 30))
                self.screen.blit(owned_text, owned_rect)
            else:
                price_text = f"${price}"
                price_color = (255, 255, 255) if can_afford else (150, 150, 150)
                price_surface = self.pixel_fonts['medium'].render(price_text, True, price_color)
                price_rect = price_surface.get_rect(center=(card_rect.centerx, card_rect.bottom - 30))
                self.screen.blit(price_surface, price_rect)
        
        # Tutorial instruction text at the bottom
        if story_tutorial and story_tutorial.active:
            # Show tutorial instruction in a panel at the bottom
            instruction = story_tutorial.get_current_instruction()
            if instruction:
                panel_width = 700
                panel_height = 60
                panel_x = (config.WIDTH - panel_width) // 2
                panel_y = config.HEIGHT - panel_height - 90  # More room for back button to avoid overlap
                
                # Panel background
                panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
                panel_surf.fill((0, 0, 0, 220))
                pygame.draw.rect(panel_surf, (200, 180, 120), panel_surf.get_rect(), 3)
                self.screen.blit(panel_surf, (panel_x, panel_y))
                
                # Tutorial text
                lines = self._wrap_text(instruction, self.pixel_fonts['medium'], panel_width - 20)
                y_offset = 15
                for line in lines:
                    text_surf = self.pixel_fonts['medium'].render(line, True, (255, 255, 255))
                    text_rect = text_surf.get_rect(centerx=config.WIDTH // 2, y=panel_y + y_offset)
                    self.screen.blit(text_surf, text_rect)
                    y_offset += 25
        else:
            # Normal instruction text when not in tutorial
            inst_text = "Click on items to purchase. Click Tariq for more info!"
            inst_surface = self.pixel_fonts['small'].render(inst_text, True, (255, 255, 255))
            inst_rect = inst_surface.get_rect(center=(game_center_x, game_center_y + 180 * self.scale))
            self.screen.blit(inst_surface, inst_rect)
        
        # Simple back button
        self._draw_button(back_button, "BACK TO GAME", (150, 70, 70), (200, 100, 100), mouse_pos)

    def _draw_speech_bubble(self, x, y, text, width, point_down=False, use_typewriter=False, text_id=None):
        """Draw a speech bubble with text.
        
        Args:
            x, y: Position of the bubble
            text: Text to display
            width: Width of the bubble
            point_down: Whether to draw a tail pointing down
            use_typewriter: Whether to use typewriter effect for the text
            text_id: ID for typewriter effect tracking
        """
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
        
        if use_typewriter:
            # Use typewriter effect for dialogue
            full_text = '\n'.join(lines)
            if text_id is None:
                text_id = f"dialogue_{x}_{y}_{text[:20]}"
            
            # Draw the text with typewriter effect
            for i, line in enumerate(lines):
                line_y = y + padding + i * line_height
                self.draw_text_typewriter(line, (x + width // 2, line_y), 'small', config.BLACK, 
                                        center=True, text_id=f"{text_id}_line_{i}")
        else:
            # Draw text normally
            for i, line in enumerate(lines):
                text_surface = self.pixel_fonts['small'].render(line, True, config.BLACK)
                text_rect = text_surface.get_rect(centerx=x + width // 2, 
                                                 y=y + padding + i * line_height)
                self.screen.blit(text_surface, text_rect)

    def _draw_shield_icon(self, screen, card_rect, icon_y, enabled=True):
        """Draw a modern shield icon."""
        # Use blue/cyan for enabled, gray for disabled
        if enabled:
            fill_color = (100, 200, 255)
            border_color = (255, 255, 255)
            accent_color = (150, 220, 255)
        else:
            fill_color = (80, 80, 80)
            border_color = (120, 120, 120)
            accent_color = (100, 100, 100)
        
        size = 36
        cx = card_rect.centerx
        cy = icon_y
        
        # Shield shape with smoother curves
        shield_surf = pygame.Surface((size + 10, size + 10), pygame.SRCALPHA)
        
        # Main shield body
        points = [
            (size // 2, 2),
            (size - 2, 8),
            (size - 2, size // 2 + 4),
            (size // 2, size - 2),
            (2, size // 2 + 4),
            (2, 8)
        ]
        
        # Draw gradient-like effect
        for i in range(3):
            offset_points = [(p[0] + 5 - i*2, p[1] + 5 - i*2) for p in points]
            alpha = 255 - i * 60
            temp_color = (*fill_color, alpha)
            pygame.draw.polygon(shield_surf, temp_color, offset_points)
        
        # Draw main shield
        offset_points = [(p[0] + 5, p[1] + 5) for p in points]
        pygame.draw.polygon(shield_surf, fill_color, offset_points)
        
        # Add highlight
        highlight_points = [
            (size // 2 + 5, 7),
            (size - 5, 12),
            (size - 5, size // 4 + 8),
            (size // 2 + 5, size // 3 + 5)
        ]
        pygame.draw.polygon(shield_surf, accent_color, highlight_points)
        
        # Clean border
        pygame.draw.polygon(shield_surf, border_color, offset_points, 2)
        
        # Center the shield
        shield_rect = shield_surf.get_rect(center=(cx, cy))
        screen.blit(shield_surf, shield_rect)

    def _draw_missile_icon(self, screen, card_rect, icon_y, enabled=True):
        """Draw a modern missile/airstrike icon."""
        if enabled:
            fill_color = (255, 100, 100)
            accent_color = (255, 150, 150)
            flame_color = (255, 200, 100)
        else:
            fill_color = (80, 80, 80)
            accent_color = (100, 100, 100)
            flame_color = (90, 90, 90)
        
        cx = card_rect.centerx
        cy = icon_y
        
        # Create surface for smooth rendering
        icon_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        center = (25, 25)
        
        # Missile body (sleeker design)
        body_rect = pygame.Rect(center[0] - 4, center[1] - 15, 8, 20)
        pygame.draw.rect(icon_surf, fill_color, body_rect, border_radius=4)
        
        # Nose cone (smoother)
        nose_points = [
            (center[0], center[1] - 20),
            (center[0] - 4, center[1] - 15),
            (center[0] + 4, center[1] - 15)
        ]
        pygame.draw.polygon(icon_surf, fill_color, nose_points)
        
        # Fins (more modern)
        # Left fin
        left_fin = [
            (center[0] - 4, center[1] + 2),
            (center[0] - 10, center[1] + 5),
            (center[0] - 8, center[1] + 8),
            (center[0] - 4, center[1] + 5)
        ]
        pygame.draw.polygon(icon_surf, accent_color, left_fin)
        
        # Right fin
        right_fin = [
            (center[0] + 4, center[1] + 2),
            (center[0] + 10, center[1] + 5),
            (center[0] + 8, center[1] + 8),
            (center[0] + 4, center[1] + 5)
        ]
        pygame.draw.polygon(icon_surf, accent_color, right_fin)
        
        # Exhaust flame
        flame_points = [
            (center[0] - 3, center[1] + 5),
            (center[0], center[1] + 12),
            (center[0] + 3, center[1] + 5)
        ]
        pygame.draw.polygon(icon_surf, flame_color, flame_points)
        
        # Highlight on body
        pygame.draw.rect(icon_surf, accent_color, (center[0] - 2, center[1] - 13, 2, 10))
        
        # Draw to screen
        icon_rect = icon_surf.get_rect(center=(cx, cy))
        screen.blit(icon_surf, icon_rect)

    def _draw_parachute_icon(self, screen, card_rect, icon_y, enabled=True):
        """Draw a modern parachute icon."""
        if enabled:
            chute_color = (100, 200, 150)
            line_color = (150, 220, 180)
            soldier_color = (80, 80, 100)
        else:
            chute_color = (80, 80, 80)
            line_color = (100, 100, 100)
            soldier_color = (60, 60, 60)
        
        cx = card_rect.centerx
        cy = icon_y
        
        # Create surface for smooth rendering
        icon_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        center = (25, 25)
        
        # Draw parachute canopy (filled semicircle)
        chute_rect = pygame.Rect(center[0] - 18, center[1] - 18, 36, 20)
        pygame.draw.ellipse(icon_surf, chute_color, chute_rect)
        # Cut off bottom half
        pygame.draw.rect(icon_surf, (0, 0, 0, 0), (center[0] - 20, center[1] - 5, 40, 20))
        
        # Add highlight to canopy
        highlight_rect = pygame.Rect(center[0] - 12, center[1] - 15, 15, 8)
        pygame.draw.ellipse(icon_surf, line_color, highlight_rect)
        
        # Draw suspension lines (cleaner)
        line_start_y = center[1] - 5
        line_end = (center[0], center[1] + 8)
        
        for offset in [-12, -6, 0, 6, 12]:
            start_point = (center[0] + offset, line_start_y)
            pygame.draw.line(icon_surf, line_color, start_point, line_end, 2 if offset == 0 else 1)
        
        # Draw soldier (simplified figure)
        # Head
        pygame.draw.circle(icon_surf, soldier_color, (center[0], center[1] + 10), 4)
        # Body
        pygame.draw.rect(icon_surf, soldier_color, (center[0] - 3, center[1] + 12, 6, 8), border_radius=2)
        
        # Draw to screen
        icon_rect = icon_surf.get_rect(center=(cx, cy))
        screen.blit(icon_surf, icon_rect)

    def _draw_helicopter_icon(self, screen, card_rect, icon_y, enabled=True):
        """Draw a modern nighttime helicopter icon with glowing cockpit."""
        if enabled:
            # Dark military colors for nighttime
            body_color = (30, 35, 40)  # Dark gray/black
            rotor_color = (50, 55, 60)  # Slightly lighter for visibility
            window_color = (20, 20, 25)  # Very dark for contrast
            red_glow = (255, 50, 50)  # Bright red for cockpit light
            highlight_color = (40, 45, 50)  # Subtle highlights
        else:
            body_color = (40, 40, 40)
            rotor_color = (60, 60, 60)
            window_color = (30, 30, 30)
            red_glow = (100, 30, 30)
            highlight_color = (50, 50, 50)
        
        cx = card_rect.centerx
        cy = icon_y
        
        # Create surface for smooth rendering
        icon_surf = pygame.Surface((60, 50), pygame.SRCALPHA)
        center = (30, 25)
        
        # Main rotor (darker, more menacing)
        # Rotor hub
        pygame.draw.circle(icon_surf, rotor_color, (center[0], center[1] - 8), 3)
        # Rotor blades with motion blur
        for angle in [0, 120, 240]:
            end_x = center[0] + int(20 * math.cos(math.radians(angle)))
            end_y = center[1] - 8 + int(3 * math.sin(math.radians(angle)))
            # Multiple lines for blur effect
            for i in range(3):
                blade_color = (*rotor_color, 150 - i * 40)
                offset_angle = angle + i * 5
                blur_end_x = center[0] + int(20 * math.cos(math.radians(offset_angle)))
                blur_end_y = center[1] - 8 + int(3 * math.sin(math.radians(offset_angle)))
                pygame.draw.line(icon_surf, blade_color, (center[0], center[1] - 8), (blur_end_x, blur_end_y), 2 - i)
        
        # Body (military style)
        # Main fuselage
        body_points = [
            (center[0] - 12, center[1] - 2),
            (center[0] - 12, center[1] + 8),
            (center[0] + 8, center[1] + 8),
            (center[0] + 12, center[1] + 3),
            (center[0] + 12, center[1] - 2)
        ]
        pygame.draw.polygon(icon_surf, body_color, body_points)
        
        # Add subtle edge highlight
        edge_points = [
            (center[0] - 12, center[1] - 2),
            (center[0] + 12, center[1] - 2),
            (center[0] + 12, center[1] + 1)
        ]
        pygame.draw.lines(icon_surf, highlight_color, False, edge_points, 1)
        
        # Cockpit window (dark)
        window_points = [
            (center[0] - 11, center[1] - 1),
            (center[0] - 11, center[1] + 4),
            (center[0] - 2, center[1] + 4),
            (center[0] + 2, center[1] - 1)
        ]
        pygame.draw.polygon(icon_surf, window_color, window_points)
        
        # RED GLOWING COCKPIT LIGHT
        # Create glow effect
        for i in range(4):
            glow_radius = 6 - i
            glow_alpha = 80 - i * 20
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*red_glow, glow_alpha), (glow_radius, glow_radius), glow_radius)
            glow_pos = (center[0] - 7 - glow_radius, center[1] + 1 - glow_radius)
            icon_surf.blit(glow_surf, glow_pos)
        
        # Bright red center dot
        pygame.draw.circle(icon_surf, red_glow, (center[0] - 7, center[1] + 1), 2)
        
        # Tail boom (darker)
        tail_rect = pygame.Rect(center[0] + 8, center[1] + 2, 18, 4)
        pygame.draw.rect(icon_surf, body_color, tail_rect, border_radius=2)
        
        # Small red position light on tail
        pygame.draw.circle(icon_surf, red_glow, (center[0] + 24, center[1] + 2), 1)
        
        # Tail rotor
        pygame.draw.circle(icon_surf, rotor_color, (center[0] + 24, center[1] + 4), 4, 2)
        
        # Landing skids (darker)
        pygame.draw.rect(icon_surf, rotor_color, (center[0] - 10, center[1] + 8, 20, 2), border_radius=1)
        
        # Optional: Add subtle downward light cone effect
        light_cone = pygame.Surface((30, 20), pygame.SRCALPHA)
        for i in range(10):
            cone_alpha = 30 - i * 3
            cone_width = 10 + i * 2
            pygame.draw.line(light_cone, (255, 255, 200, cone_alpha), 
                           (15, 0), (15 - cone_width//2 + i, 20), 1)
            pygame.draw.line(light_cone, (255, 255, 200, cone_alpha), 
                           (15, 0), (15 + cone_width//2 - i, 20), 1)
        icon_surf.blit(light_cone, (center[0] - 15, center[1] + 8))
        
        # Draw to screen
        icon_rect = icon_surf.get_rect(center=(cx, cy))
        screen.blit(icon_surf, icon_rect)
    
    def _draw_tech_grid(self):
        """Draw animated tech grid background."""
        grid_color = (0, 50, 80, 30)
        line_spacing = 50
        time_offset = pygame.time.get_ticks() * 0.02
        
        # Vertical lines
        for x in range(0, config.WIDTH, line_spacing):
            offset = int(math.sin(time_offset + x * 0.01) * 5)
            line_surf = pygame.Surface((2, config.HEIGHT), pygame.SRCALPHA)
            line_surf.fill(grid_color)
            self.screen.blit(line_surf, (x + offset, 0))
        
        # Horizontal lines
        for y in range(0, config.HEIGHT, line_spacing):
            offset = int(math.cos(time_offset + y * 0.01) * 5)
            line_surf = pygame.Surface((config.WIDTH, 2), pygame.SRCALPHA)
            line_surf.fill(grid_color)
            self.screen.blit(line_surf, (0, y + offset))
    
    def _draw_scanner_effect_on_surface(self, surface, x, y, width, height, current_time, alpha=255):
        """Draw scanner effect on a given surface with alpha."""
        scanner_color = (0, 255, 255, alpha)
        
        # Rotating scanner line
        angle = (current_time * 0.1) % 360
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Calculate scanner line endpoints
        radius = max(width, height) // 2
        end_x = center_x + int(math.cos(math.radians(angle)) * radius)
        end_y = center_y + int(math.sin(math.radians(angle)) * radius)
        
        # Draw scanner line with alpha
        for i in range(2, -1, -1):  # Draw from thick to thin
            line_alpha = int(alpha * (1.0 - i*0.2))  # Fade alpha
            line_color = (0, 255 - i*50, 255 - i*50, line_alpha)
            pygame.draw.line(surface, line_color, 
                           (center_x, center_y), (end_x, end_y), 3 - i)
        
        # Corner brackets that pulse
        pulse = abs(math.sin(current_time * 0.003)) * 0.5 + 0.5
        bracket_size = int(30 * pulse + 20)
        bracket_alpha = int(alpha * pulse)
        bracket_color = (0, 255, 255, bracket_alpha)
        thickness = 3
        
        # Top-left
        pygame.draw.lines(surface, bracket_color, False,
                         [(x, y + bracket_size), (x, y), (x + bracket_size, y)], thickness)
        # Top-right
        pygame.draw.lines(surface, bracket_color, False,
                         [(x + width - bracket_size, y), (x + width, y), (x + width, y + bracket_size)], thickness)
        # Bottom-left
        pygame.draw.lines(surface, bracket_color, False,
                         [(x, y + height - bracket_size), (x, y + height), (x + bracket_size, y + height)], thickness)
        # Bottom-right
        pygame.draw.lines(surface, bracket_color, False,
                         [(x + width - bracket_size, y + height), (x + width, y + height), (x + width, y + height - bracket_size)], thickness)
    
    def _draw_scanner_effect(self, x, y, width, height, current_time):
        """Draw scanner effect around an area."""
        scanner_color = (0, 255, 255)
        
        # Rotating scanner line
        angle = (current_time * 0.1) % 360
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Calculate scanner line endpoints
        radius = max(width, height) // 2
        end_x = center_x + int(math.cos(math.radians(angle)) * radius)
        end_y = center_y + int(math.sin(math.radians(angle)) * radius)
        
        # Draw scanner line directly (no surfaces for performance)
        for i in range(2, -1, -1):  # Draw from thick to thin
            line_color = (0, 255 - i*50, 255 - i*50)  # Fade color instead of alpha
            pygame.draw.line(self.screen, line_color, 
                           (center_x, center_y), (end_x, end_y), 3 - i)
        
        # Corner brackets that pulse
        pulse = abs(math.sin(current_time * 0.003)) * 0.5 + 0.5
        bracket_size = int(30 * pulse + 20)
        bracket_color = (0, int(255 * pulse), int(255 * pulse))
        thickness = 3
        
        # Top-left
        pygame.draw.lines(self.screen, bracket_color, False,
                         [(x, y + bracket_size), (x, y), (x + bracket_size, y)], thickness)
        # Top-right
        pygame.draw.lines(self.screen, bracket_color, False,
                         [(x + width - bracket_size, y), (x + width, y), (x + width, y + bracket_size)], thickness)
        # Bottom-left
        pygame.draw.lines(self.screen, bracket_color, False,
                         [(x, y + height - bracket_size), (x, y + height), (x + bracket_size, y + height)], thickness)
        # Bottom-right
        pygame.draw.lines(self.screen, bracket_color, False,
                         [(x + width - bracket_size, y + height), (x + width, y + height), (x + width, y + height - bracket_size)], thickness)
    
    def _draw_digital_rain(self, current_time, victory_screen=False):
        """Draw Matrix-style digital rain effect."""
        # Use different rain columns for victory screen to avoid conflicts
        column_attr = 'victory_rain_columns' if victory_screen else 'rain_columns'
        
        # Initialize rain columns if not exists
        if not hasattr(self, column_attr):
            columns = []
            # Fewer columns for victory screen
            spacing = 40 if victory_screen else 20
            for x in range(0, config.WIDTH, spacing):
                columns.append({
                    'x': x,
                    'y': random.randint(-config.HEIGHT, 0),
                    'speed': random.uniform(2, 6),
                    'chars': [chr(random.randint(33, 126)) for _ in range(20)],
                    'length': random.randint(10, 20)
                })
            setattr(self, column_attr, columns)
        
        columns = getattr(self, column_attr)
        
        # Cache rain surface for victory screen to avoid recreating
        if victory_screen and not hasattr(self, 'victory_rain_surf'):
            self.victory_rain_surf = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        
        rain_surf = self.victory_rain_surf if victory_screen else pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        rain_surf.fill((0, 0, 0, 0))  # Clear it
        
        # Update and draw rain columns
        for col in columns:
            # Update position
            col['y'] += col['speed']
            
            # Reset column when it goes off screen
            if col['y'] > config.HEIGHT + 200:
                col['y'] = random.randint(-400, -100)
                col['speed'] = random.uniform(2, 6)
                col['chars'] = [chr(random.randint(33, 126)) for _ in range(20)]
                col['length'] = random.randint(10, 20)
            
            # Draw characters in column
            for i in range(col['length']):
                char_y = col['y'] - i * 20
                if 0 <= char_y <= config.HEIGHT:
                    # Fade based on position in trail
                    if i == 0:
                        color = (150, 255, 150)  # Bright green for head
                        alpha = 255
                    else:
                        fade = 1 - (i / col['length'])
                        color = (0, int(180 * fade), 0)
                        alpha = int(200 * fade)
                    
                    # Change character occasionally
                    if random.random() < 0.1:
                        col['chars'][i % len(col['chars'])] = chr(random.randint(33, 126))
                    
                    # Draw character
                    if 'tiny' in self.pixel_fonts:
                        char_surf = self.pixel_fonts['tiny'].render(col['chars'][i % len(col['chars'])], True, (*color, alpha))
                        rain_surf.blit(char_surf, (col['x'], char_y))
        
        self.screen.blit(rain_surf, (0, 0))
    
    def _draw_character_info_sheet(self, battle_data, x, y):
        """Draw character information sheet with badges and stats."""
        sheet_width = 300
        sheet_height = 180
        
        # Info sheet background
        sheet_surf = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
        pygame.draw.rect(sheet_surf, (10, 20, 30, 200), (0, 0, sheet_width, sheet_height), border_radius=10)
        pygame.draw.rect(sheet_surf, (0, 150, 200), (0, 0, sheet_width, sheet_height), 2, border_radius=10)
        
        # Draw grid pattern on sheet
        for i in range(0, sheet_width, 30):
            pygame.draw.line(sheet_surf, (0, 100, 150, 50), (i, 0), (i, sheet_height), 1)
        for i in range(0, sheet_height, 30):
            pygame.draw.line(sheet_surf, (0, 100, 150, 50), (0, i), (sheet_width, i), 1)
        
        # Affiliation Badge
        affiliation = battle_data.get("affiliation", "UNKNOWN")
        badge_y = 15
        
        # Draw badge background
        badge_color = self._get_affiliation_color(affiliation)
        pygame.draw.polygon(sheet_surf, badge_color,
                          [(20, badge_y), (50, badge_y - 10), (80, badge_y), 
                           (80, badge_y + 20), (50, badge_y + 30), (20, badge_y + 20)])
        pygame.draw.polygon(sheet_surf, (255, 255, 255),
                          [(20, badge_y), (50, badge_y - 10), (80, badge_y), 
                           (80, badge_y + 20), (50, badge_y + 30), (20, badge_y + 20)], 2)
        
        # Affiliation text
        aff_text = affiliation
        aff_surf = self.pixel_fonts['tiny'].render(aff_text, True, (255, 255, 255))
        sheet_surf.blit(aff_surf, (90, badge_y + 5))
        
        # Information fields
        info_y = 60
        info_spacing = 25
        
        # Rank
        rank = battle_data.get("rank", "UNKNOWN")
        self._draw_info_field(sheet_surf, "RANK:", rank, 20, info_y, badge_color)
        
        # Threat Level
        threat = battle_data.get("threat_level", "UNKNOWN")
        threat_color = self._get_threat_color(threat)
        self._draw_info_field(sheet_surf, "THREAT:", threat, 20, info_y + info_spacing, threat_color)
        
        # Classification
        classification = battle_data.get("classification", "UNKNOWN")
        self._draw_info_field(sheet_surf, "CLASS:", classification, 20, info_y + info_spacing * 2, (100, 200, 255))
        
        # Specialization
        spec = battle_data.get("specialization", "Unknown")
        self._draw_info_field(sheet_surf, "SPEC:", spec, 20, info_y + info_spacing * 3, (150, 150, 200))
        
        # Difficulty indicator
        diff = battle_data.get("difficulty", "unknown")
        diff_text = f"DIFFICULTY: {diff.upper()}"
        diff_color = {"easy": (100, 255, 100), "medium": (255, 255, 100), "hard": (255, 100, 100)}.get(diff, (200, 200, 200))
        diff_surf = self.pixel_fonts['small'].render(diff_text, True, diff_color)
        sheet_surf.blit(diff_surf, (20, sheet_height - 30))
        
        # Blit the sheet to screen
        self.screen.blit(sheet_surf, (x, y))
    
    def _draw_info_field(self, surface, label, value, x, y, color):
        """Draw an information field with label and value."""
        label_surf = self.pixel_fonts['tiny'].render(label, True, (150, 150, 150))
        surface.blit(label_surf, (x, y))
        
        value_surf = self.pixel_fonts['small'].render(value, True, color)
        surface.blit(value_surf, (x + 60, y - 2))
    
    def _get_affiliation_color(self, affiliation):
        """Get color based on affiliation."""
        colors = {
            "HELIX ACADEMY": (0, 150, 255),
            "HELIX DEFENSE FORCE": (0, 200, 100),
            "NEXUS CORP": (255, 100, 0),
            "SHADOW COLLECTIVE": (150, 0, 200),
            "ROGUE": (255, 50, 50)
        }
        return colors.get(affiliation, (150, 150, 150))
    
    def _get_threat_color(self, threat_level):
        """Get color based on threat level."""
        colors = {
            "MINIMAL": (100, 255, 100),
            "LOW": (150, 255, 100),
            "MODERATE": (255, 255, 100),
            "HIGH": (255, 150, 100),
            "EXTREME": (255, 50, 50),
            "CRITICAL": (255, 0, 255)
        }
        return colors.get(threat_level, (200, 200, 200))
    
    def _draw_walking_capybaras(self):
        """Draw sitting capybaras that move with parallax background."""
        if not self.assets.capy_image:
            return
            
        # Initialize capybara list and auto-scroll if not exists
        if not hasattr(self, 'sitting_capybaras'):
            self.sitting_capybaras = []
            self.last_capybara_spawn = 0
            self.story_mode_scroll_offset = 0
            # Don't start with capybaras on screen
        
        current_time = pygame.time.get_ticks()
        
        # Auto-scroll for story mode screens (since there's no mouse parallax)
        self.story_mode_scroll_offset += 2.0  # Constant rightward scroll speed
        
        # Spawn new capybara occasionally (every 8-15 seconds)
        spawn_interval = random.randint(8000, 15000) if self.last_capybara_spawn == 0 else 8000
        if current_time - self.last_capybara_spawn > spawn_interval:
            # Spawn capybara just off-screen to the left
            self.sitting_capybaras.append({
                'world_x': -150 + self.story_mode_scroll_offset,  # World position (off-screen left)
                'size': random.randint(45, 65),
                'flip': random.choice([True, False])
            })
            self.last_capybara_spawn = current_time
        
        # Draw capybaras
        capybaras_to_remove = []
        for i, capy in enumerate(self.sitting_capybaras):
            # Calculate screen position
            # Capybaras stay at their world position while the "camera" moves right
            screen_x = capy['world_x'] - self.story_mode_scroll_offset
            capy_y = config.HEIGHT - capy['size'] - 100  # Position to sit on grass
            
            # Remove if moved too far off screen
            if screen_x < -200 or screen_x > config.WIDTH + 200:
                capybaras_to_remove.append(i)
                continue
            
            # Draw sitting capybara
            capy_scaled = pygame.transform.smoothscale(self.assets.capy_image, 
                                                      (capy['size'], capy['size']))
            if capy['flip']:
                capy_scaled = pygame.transform.flip(capy_scaled, True, False)
            
            self.screen.blit(capy_scaled, (int(screen_x), int(capy_y)))
        
        # Remove capybaras that have left the screen
        for i in reversed(capybaras_to_remove):
            self.sitting_capybaras.pop(i)