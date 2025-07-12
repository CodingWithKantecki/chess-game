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
        self.intro_start_time = None  # Will be set when main menu is first shown
        self.intro_jet_triggered = False  # Don't start until we're on main menu
        self.intro_sound_played = False
        
        # Fire system - COMPLETELY REDESIGNED
        self.fire_zones = []  # List of fire zones that scroll with background
        self.fire_particles = []  # Active fire particles
        self.bomb_explosions = []  # Explosion animations
        self.last_parallax_offset = 0
        
        # Falling chess pieces system
        self.falling_chess_pieces = []  # Chess pieces falling from trees
        self.chess_pieces_enabled = False  # Enable after bombs drop
        
        # Add missing attributes
        self._fire_updated_this_frame = False
        self.current_screen = None
        self.falling_bombs = []
        
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
    
    def _draw_fire_at_depth(self, current_time, depth):
        """Draw fire particles at a specific depth layer."""
        if self._fire_updated_this_frame:
            return
            
        # Initialize smoke particles list if not exists
        if not hasattr(self, 'smoke_particles'):
            self.smoke_particles = []
            
        # Clean up old fire zones that have scrolled off screen
        zones_to_remove = []
        for zone in self.fire_zones:
            # Calculate zone's screen position
            zone_screen_x = zone['world_x'] - self.parallax_offset * zone['depth']
            # Remove if scrolled far off screen
            if zone_screen_x < -500:
                zones_to_remove.append(zone)
        
        for zone in zones_to_remove:
            if zone in self.fire_zones:
                self.fire_zones.remove(zone)
            
        # Update fire zones at this depth
        for zone in self.fire_zones:
            if zone['depth'] == depth:
                # Calculate zone age and intensity
                if 'creation_time' in zone:
                    zone_age = (current_time - zone['creation_time']) / 1000.0  # Age in seconds
                    
                    # Fire dies down after 10 seconds
                    if zone_age < 10:
                        # Intensity decreases after 5 seconds
                        if zone_age > 5:
                            zone['intensity'] = max(0, 1.0 - (zone_age - 5) / 5.0)
                        else:
                            zone['intensity'] = 1.0
                    else:
                        zone['intensity'] = 0
                        
                    # Spawn smoke after fire starts dying (after 3 seconds)
                    if zone_age > 3 and zone_age < 15 and zone['spawn_timer'] <= 0:  # Stop smoke after 15 seconds
                        # Spawn smoke particles (less frequently)
                        smoke_intensity = max(0, 1.0 - (zone_age - 10) / 5.0) if zone_age > 10 else 1.0
                        if random.random() < 0.3 * smoke_intensity:  # Only 30% chance to spawn smoke
                            smoke_particle = {
                                'x': zone['world_x'] - self.parallax_offset * depth + random.randint(-zone['width']//2, zone['width']//2),
                                'y': zone['y'] + random.randint(-20, 0),
                                'vx': random.uniform(-0.3, 0.3),
                                'vy': random.uniform(-0.8, -0.3),
                                'size': random.randint(15, 30),
                                'life': 1.0,
                                'depth': depth,
                                'opacity': random.uniform(0.2, 0.4) * smoke_intensity  # Less opaque smoke
                            }
                            self.smoke_particles.append(smoke_particle)
                
                # Spawn new fire particles if still burning
                if zone['spawn_timer'] <= 0 and zone['intensity'] > 0:
                    # Create fire particles (less as intensity decreases)
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
        
        # Draw particles with additive blending for realism
        fire_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        
        # Update and draw smoke particles first (behind fire)
        smoke_to_remove = []
        # Limit total smoke particles for performance
        if len(self.smoke_particles) > 50:  # Cap at 50 smoke particles
            # Remove oldest smoke particles
            self.smoke_particles = self.smoke_particles[-50:]
            
        for smoke in self.smoke_particles:
            if smoke['depth'] == depth:
                # Update smoke
                smoke['x'] += smoke['vx']
                smoke['y'] += smoke['vy']
                smoke['vy'] -= 0.02  # Gentle rise
                smoke['life'] -= 0.008  # Slower decay (was 0.01)
                smoke['size'] += 0.3  # Slower expansion (was 0.5)
                smoke['vx'] += random.uniform(-0.05, 0.05)  # Drift
                
                if smoke['life'] <= 0 or smoke['y'] < -100:  # Remove if too high
                    smoke_to_remove.append(smoke)
                else:
                    # Draw smoke
                    screen_x = int(smoke['x'] - self.parallax_offset * depth)
                    screen_y = int(smoke['y'])
                    
                    if 0 <= screen_x <= config.WIDTH:
                        # Smoke color (dark gray to light gray)
                        gray_value = int(50 + (1 - smoke['life']) * 100)
                        smoke_color = (gray_value, gray_value, gray_value)
                        alpha = int(smoke['life'] * smoke['opacity'] * 120)  # Reduced max alpha
                        size = int(smoke['size'] * self.scale)
                        
                        # Draw smoke cloud
                        smoke_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                        # Fewer overlapping circles for performance
                        for i in range(2):  # Reduced from 3
                            offset_x = random.randint(-3, 3)
                            offset_y = random.randint(-3, 3)
                            pygame.draw.circle(smoke_surf, (*smoke_color, alpha // 2), 
                                             (size + offset_x, size + offset_y), size)
                        fire_surface.blit(smoke_surf, (screen_x - size, screen_y - size))
        
        # Remove dead smoke
        for smoke in smoke_to_remove:
            if smoke in self.smoke_particles:
                self.smoke_particles.remove(smoke)
        
        # Update and draw fire particles
        particles_to_remove = []
        for particle in self.fire_particles:
            if particle['depth'] == depth:
                # Update particle
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vy'] -= 0.08
                particle['life'] -= 0.035
                particle['size'] = max(1, particle['size'] - 0.3)
                particle['flicker'] += 0.3
                
                # Add turbulence and flicker
                flicker_offset = math.sin(particle['flicker']) * 2
                particle['vx'] += random.uniform(-0.1, 0.1) + flicker_offset * 0.1
                
                if particle['life'] <= 0 or particle['y'] < zone['y'] - 60:
                    particles_to_remove.append(particle)
                else:
                    # Draw particle
                    screen_x = int(particle['x'] - self.parallax_offset * depth)
                    screen_y = int(particle['y'])
                    
                    # Fire colors
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
                    
                    # Draw spiky fire shape
                    if 0 <= screen_x <= config.WIDTH and particle['life'] > 0.3:
                        flame_height = int(size * particle['spike_height'])
                        
                        # Outer glow
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
                        
                        # Inner flame core
                        particle_surf = pygame.Surface((size * 2, flame_height * 2), pygame.SRCALPHA)
                        for i in range(3):
                            offset_y = i * flame_height // 4
                            radius = size - (i * size // 3)
                            if radius > 0:
                                # Ensure alpha is never negative
                                flame_alpha = max(0, alpha - (i * 30))
                                pygame.draw.circle(particle_surf, (*base_color, flame_alpha), 
                                                 (size, size + offset_y), radius)
                        
                        fire_surface.blit(particle_surf, (screen_x - size, screen_y - size), 
                                        special_flags=pygame.BLEND_ADD)
        
        # Blit fire surface with additive blending
        self.screen.blit(fire_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # Remove dead particles
        for particle in particles_to_remove:
            if particle in self.fire_particles:
                self.fire_particles.remove(particle)
    
    def _draw_chess_pieces_at_layer(self, depth):
        """Draw falling chess pieces at a specific depth layer."""
        # Draw chess pieces that match this depth
        for piece in self.falling_chess_pieces:
            if abs(piece['depth'] - depth) < 0.1:  # Close enough to this layer
                # Calculate screen position based on depth
                screen_x = int(piece['x'] - self.parallax_offset * piece['depth'])
                screen_y = int(piece['y'])
                
                # Only draw if on screen
                if -50 <= screen_x <= config.WIDTH + 50:
                    # Get the piece image
                    piece_key = piece['piece']
                    if piece_key in self.assets.pieces:
                        piece_img = self.assets.pieces[piece_key]
                        
                        # Scale based on depth
                        scale_factor = 0.3 + (piece['depth'] * 0.7)  # Smaller in back
                        piece_size = int(50 * self.scale * scale_factor)
                        scaled_piece = pygame.transform.scale(piece_img, (piece_size, piece_size))
                        
                        # Rotate the piece
                        rotated_piece = pygame.transform.rotate(scaled_piece, piece['rotation'])
                        
                        # Apply transparency based on depth
                        alpha = int(100 + piece['depth'] * 155)  # More opaque in front
                        rotated_piece.set_alpha(alpha)
                        
                        # Draw the piece
                        piece_rect = rotated_piece.get_rect(center=(screen_x, screen_y))
                        self.screen.blit(rotated_piece, piece_rect)
    
    def _update_chess_pieces(self):
        """Update physics for falling chess pieces."""
        pieces_to_remove = []
        current_time = pygame.time.get_ticks()
        
        # Spawn new pieces occasionally
        if not hasattr(self, 'next_piece_spawn'):
            self.next_piece_spawn = current_time + random.randint(500, 2000)
        
        if current_time >= self.next_piece_spawn and len(self.falling_chess_pieces) < 20:
            # Random piece types
            piece_types = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
            
            # Create new falling piece - spawn from middle of screen at tree level
            new_piece = {
                'x': random.randint(0, config.WIDTH) + self.parallax_offset * 0.7,
                'y': random.randint(config.HEIGHT // 3, config.HEIGHT // 2),  # Middle third of screen
                'vy': random.uniform(0.5, 1.5),  # Gentle initial fall
                'vx': random.uniform(-0.3, 0.3),  # Minimal horizontal drift
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-2, 2),  # Gentle rotation
                'piece': random.choice(piece_types),
                'depth': random.choice([0.3, 0.5, 0.7, 0.9])
            }
            self.falling_chess_pieces.append(new_piece)
            self.next_piece_spawn = current_time + random.randint(500, 2000)
        
        # Update existing pieces
        for piece in self.falling_chess_pieces:
            # Update position
            piece['x'] += piece['vx']
            piece['y'] += piece['vy']
            piece['rotation'] += piece['rotation_speed']
            
            # Very gentle gravity
            piece['vy'] += 0.03  # Very slow acceleration
            
            # Add slight air resistance
            piece['vy'] = min(piece['vy'], 4)  # Terminal velocity
            
            # Remove if off screen
            if piece['y'] > config.HEIGHT + 100:
                pieces_to_remove.append(piece)
        
        # Remove pieces that fell off screen
        for piece in pieces_to_remove:
            if piece in self.falling_chess_pieces:
                self.falling_chess_pieces.remove(piece)
    
    def _draw_intro_jet_with_bombs(self, time_elapsed):
        """Draw the intro jet sequence with bomb drops."""
        if not hasattr(self.assets, 'jet_frames') or not self.assets.jet_frames:
            return
            
        # Jet appears immediately and flies across
        jet_start_time = 0
        jet_duration = 4000  # 4 seconds to cross screen
        
        if time_elapsed < jet_start_time + jet_duration:
            # Calculate jet position
            progress = (time_elapsed - jet_start_time) / jet_duration
            jet_x = -200 + (config.WIDTH + 400) * progress
            jet_y = 100
            
            # Play jet sound once
            if not self.intro_sound_played and hasattr(self.assets, 'jet_sound') and self.assets.jet_sound:
                self.assets.jet_sound.play()
                self.intro_sound_played = True
            
            # Draw jet
            frame_index = int((time_elapsed / 100) % len(self.assets.jet_frames))
            jet_frame = self.assets.jet_frames[frame_index]
            
            # Scale jet - SMALLER
            jet_scale = 0.3 * self.scale  # Reduced from 0.5 to 0.3
            jet_width = int(jet_frame.get_width() * jet_scale)
            jet_height = int(jet_frame.get_height() * jet_scale)
            scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
            
            # Flip the jet to face the correct direction (right)
            flipped_jet = pygame.transform.flip(scaled_jet, True, False)
            
            self.screen.blit(flipped_jet, (int(jet_x), int(jet_y)))
            
            # Initialize falling bombs list if not exists
            if not hasattr(self, 'falling_bombs'):
                self.falling_bombs = []
            
            # Drop MORE bombs at closer intervals
            bomb_drop_times = [500, 800, 1100, 1400, 1700, 2000, 2300, 2600, 2900, 3200, 3500]  # More bombs!
            
            for drop_time in bomb_drop_times:
                if jet_start_time + drop_time <= time_elapsed < jet_start_time + drop_time + 50:
                    # Check if we already dropped a bomb at this time
                    already_dropped = any(b['drop_time'] == drop_time for b in self.falling_bombs)
                    
                    if not already_dropped:
                        # Calculate bomb drop position
                        bomb_progress = drop_time / jet_duration
                        bomb_x = -200 + (config.WIDTH + 400) * bomb_progress + jet_width // 2
                        
                        self.falling_bombs.append({
                            'x': bomb_x,
                            'y': jet_y + jet_height // 2,  # Changed from jet_y + jet_height to spawn from middle of jet
                            'vy': 2,
                            'world_x': bomb_x + self.parallax_offset,
                            'exploded': False,
                            'drop_time': drop_time
                        })
                        
                        # Play bomb sound
                        if hasattr(self.assets, 'bomb_sound') and self.assets.bomb_sound:
                            self.assets.bomb_sound.play()
        
        # Enable chess pieces after first bomb
        if time_elapsed > 1500 and not self.chess_pieces_enabled:
            self.chess_pieces_enabled = True
            
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
            # Initialize jet sequence timing when first showing main menu
            if self.intro_start_time is None:
                self.intro_start_time = pygame.time.get_ticks()
                self.intro_jet_triggered = True
                
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
                    'speed': random.uniform(5, 8),  # Increased speed from 2-4 to 5-8
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
                                    'depth': layer['depth'],
                                    'creation_time': pygame.time.get_ticks()  # Track when fire was created
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
                
                # Position it higher up to avoid overlap
                badge_x = rect.right - int(20 * config.SCALE)  # Closer to title
                badge_y = rect.top - int(70 * config.SCALE)  # Moved up from -60 to -70
                
                self.screen.blit(rotated_badge, (badge_x, badge_y))
            
            # Buttons
            self._draw_button(buttons['play'], "PLAY GAME", (70, 150, 70), (100, 200, 100), mouse_pos)
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
            
    def draw_bar_intro(self, dialogue_index, dialogues, mouse_pos):
        """Draw the bar intro scene with Tariq."""
        # Draw bar background
        if hasattr(self.assets, 'bar_background') and self.assets.bar_background:
            # Scale background to fill screen
            scaled_bg = pygame.transform.scale(self.assets.bar_background, (config.WIDTH, config.HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
        else:
            # Fallback: dark bar atmosphere
            self.screen.fill((20, 15, 10))
            
        # Semi-transparent overlay for better text visibility
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))
        
        # Draw Tariq on the left side
        if hasattr(self.assets, 'tariq_image') and self.assets.tariq_image:
            # Scale Tariq appropriately
            tariq_height = int(500 * config.SCALE)
            aspect_ratio = self.assets.tariq_image.get_width() / self.assets.tariq_image.get_height()
            tariq_width = int(tariq_height * aspect_ratio)
            scaled_tariq = pygame.transform.smoothscale(self.assets.tariq_image, (tariq_width, tariq_height))
            
            # Position on left side
            tariq_x = int(50 * config.SCALE)
            tariq_y = config.HEIGHT - tariq_height
            
            self.screen.blit(scaled_tariq, (tariq_x, tariq_y))
            
            # Draw speech bubble to the right of Tariq
            if 0 <= dialogue_index < len(dialogues):
                dialogue = dialogues[dialogue_index]
                bubble_width = int(500 * config.SCALE)  # Increased from 400 to 500
                bubble_x = tariq_x + tariq_width - int(100 * config.SCALE)  # Moved more to the left (from -50 to -100)
                bubble_y = config.HEIGHT // 2 - int(50 * config.SCALE)  # Moved down (from -150 to -50)
                self._draw_speech_bubble(bubble_x, bubble_y, dialogue, bubble_width)
        
        # Instructions
        instruction_text = "Click anywhere to continue..." if dialogue_index < len(dialogues) - 1 else "Click to begin!"
        instruction = self.pixel_fonts['small'].render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction.get_rect(center=(config.WIDTH // 2, config.HEIGHT - int(40 * config.SCALE)))
        self.screen.blit(instruction, instruction_rect)
        
        # Progress indicator
        progress_text = f"{dialogue_index + 1}/{len(dialogues)}"
        progress = self.pixel_fonts['small'].render(progress_text, True, (150, 150, 150))
        progress_rect = progress.get_rect(bottomright=(config.WIDTH - int(20 * config.SCALE), 
                                                       config.HEIGHT - int(20 * config.SCALE)))
        self.screen.blit(progress, progress_rect)
            
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
            if powerup_key == "gun" and hasattr(self, 'assets') and hasattr(self.assets, 'revolver_image') and self.assets.revolver_image:
                # Use the actual revolver image for gun powerup
                icon_size = 25
                scaled_revolver = pygame.transform.scale(self.assets.revolver_image, (icon_size, icon_size))
                
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
                
                icon_rect = scaled_revolver.get_rect(centerx=card_rect.centerx, y=card_rect.y + 12)
                self.screen.blit(scaled_revolver, icon_rect)
            elif powerup_key == "chopper":
                # Draw helicopter icon
                self._draw_helicopter_icon(card_rect, can_afford)
            else:
                # Draw custom icons for other powerups
                icon_size = 30
                icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                icon_surface.fill((0, 0, 0, 0))
                
                if powerup_key == "airstrike":
                    # Draw missile icon
                    self._draw_missile_icon(icon_surface, icon_size, can_afford)
                elif powerup_key == "shield":
                    # Draw shield icon
                    self._draw_shield_icon(icon_surface, icon_size, can_afford)
                elif powerup_key == "paratroopers":
                    # Draw parachute icon
                    self._draw_parachute_icon(icon_surface, icon_size, can_afford)
                else:
                    # Fallback to text icon
                    icon_color = config.WHITE if can_afford else (80, 80, 80)
                    icon_surface = self.pixel_fonts['large'].render(powerup["icon"], True, icon_color)
                
                icon_rect = icon_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 10)
                self.screen.blit(icon_surface, icon_rect)
            
            # Draw name
            name_color = (0, 255, 0) if can_afford else (80, 80, 80)
            name_surface = self.pixel_fonts['small'].render(powerup["name"], True, name_color)
            name_rect = name_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 35)
            self.screen.blit(name_surface, name_rect)
            
            # Draw cost
            cost_text = f"Cost: {powerup['cost']}"
            cost_color = (255, 204, 0) if can_afford else (80, 80, 80)
            cost_surface = self.pixel_fonts['tiny'].render(cost_text, True, cost_color)
            cost_rect = cost_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 55)
            self.screen.blit(cost_surface, cost_rect)
            
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

    def _draw_button(self, rect, text, base_color, hover_color, mouse_pos):
        """Helper method to draw a button."""
        is_hover = rect.collidepoint(mouse_pos)
        color = hover_color if is_hover else base_color
        
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, config.WHITE, rect, 3, border_radius=10)
        
        text_surface = self.pixel_fonts['medium'].render(text, True, config.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

    def _draw_speech_bubble(self, x, y, text, width, point_down=False):
        """Draw a speech bubble with text."""
        padding = int(20 * self.scale)
        line_height = int(20 * self.scale)
        
        # Word wrap the text
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
        
        # Calculate bubble height
        height = len(lines) * line_height + 2 * padding
        
        # Draw bubble background
        bubble_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (255, 255, 255), bubble_rect, border_radius=15)
        pygame.draw.rect(self.screen, (0, 0, 0), bubble_rect, 3, border_radius=15)
        
        # Draw pointer/tail
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
        
        # Draw text
        for i, line in enumerate(lines):
            text_surface = self.pixel_fonts['small'].render(line, True, config.BLACK)
            text_rect = text_surface.get_rect(centerx=x + width // 2, 
                                             y=y + padding + i * line_height)
            self.screen.blit(text_surface, text_rect)

    def _draw_shield_icon(self, surface, size, enabled=True):
        """Draw a shield icon."""
        color = (200, 200, 200) if enabled else (80, 80, 80)
        center = size // 2
        
        # Shield shape
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
        
        # Missile body
        pygame.draw.rect(surface, color, (center - 3, 8, 6, 15))
        
        # Nose cone
        pygame.draw.polygon(surface, color, [
            (center - 3, 8),
            (center, 3),
            (center + 3, 8)
        ])
        
        # Fins
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
        
        # Parachute canopy
        pygame.draw.arc(surface, color, (5, 5, size - 10, size // 2), 0, 3.14, 3)
        
        # Strings
        for x in [8, center, size - 8]:
            pygame.draw.line(surface, color, (x, 5 + size // 4), 
                           (center, size - 8), 1)
        
        # Person
        pygame.draw.circle(surface, color, (center, size - 8), 3)

    def _draw_helicopter_icon(self, card_rect, enabled=True):
        """Draw a helicopter icon directly on screen."""
        color = (100, 100, 150) if enabled else (80, 80, 80)
        
        # Position at top of card
        heli_x = card_rect.centerx
        heli_y = card_rect.y + 20
        
        # Main body
        body_rect = pygame.Rect(heli_x - 15, heli_y, 30, 15)
        pygame.draw.ellipse(self.screen, color, body_rect)
        
        # Tail
        pygame.draw.rect(self.screen, color, (heli_x + 10, heli_y + 5, 20, 5))
        pygame.draw.polygon(self.screen, color, [
            (heli_x + 25, heli_y),
            (heli_x + 30, heli_y + 5),
            (heli_x + 30, heli_y + 10)
        ])
        
        # Main rotor
        pygame.draw.line(self.screen, color, (heli_x - 20, heli_y - 3), 
                        (heli_x + 20, heli_y - 3), 2)
        
        # Tail rotor
        pygame.draw.circle(self.screen, color, (heli_x + 30, heli_y + 5), 4, 1)
        
        # Landing skids
        pygame.draw.line(self.screen, color, (heli_x - 10, heli_y + 15), 
                        (heli_x + 10, heli_y + 15), 2)