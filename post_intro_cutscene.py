"""
Post-Intro Cutscene Implementation
Shows jet flying through rainy jungle with parallax background
"""

import pygame
import random
import math
import config

class PostIntroCutscene:
    def __init__(self, screen, assets, renderer):
        self.screen = screen
        self.assets = assets
        self.renderer = renderer
        self.active = False
        self.complete = False
        
        # Timing
        self.start_time = 0
        # No duration - wait for user input
        
        # Jet properties - we'll remove the main jet movement but keep animation for background jets
        self.jet_x = config.WIDTH + 200  # Set jet as already off screen
        self.jet_y = config.HEIGHT // 2 - 50
        self.jet_speed = 0  # No movement
        self.jet_frame = 0
        self.jet_animation_timer = 0
        self.jet_animation_speed = 140  # Milliseconds per frame for animation
        self.jet_reached_end = True  # Already at end
        self.jet_final_x = config.WIDTH + 200
        
        # Use animated jet frames from assets
        self.jet_frames = []
        if hasattr(assets, 'jet_frames') and assets.jet_frames:
            self.jet_frames = assets.jet_frames
            # Scale and flip jet frames horizontally
            jet_width = 150  # Larger for more impact
            scaled_frames = []
            for frame in self.jet_frames:
                aspect_ratio = frame.get_height() / frame.get_width()
                jet_height = int(jet_width * aspect_ratio)
                scaled_frame = pygame.transform.scale(frame, (jet_width, jet_height))
                # Flip horizontally so jet faces right
                flipped_frame = pygame.transform.flip(scaled_frame, True, False)
                scaled_frames.append(flipped_frame)
            self.jet_frames = scaled_frames
        
        # Trail effect properties
        self.trail_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        self.logo_revealed = False
        self.logo_font = None
        if hasattr(renderer, 'pixel_fonts'):
            self.logo_font = renderer.pixel_fonts['huge']
        else:
            self.logo_font = pygame.font.Font(None, 72)
                    
        # Camera properties
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.camera_shake_x = 0
        self.camera_shake_y = 0
        self.turbulence_timer = 0
        
        # Parallax scrolling
        self.parallax_offset = 0
        
        # Rain properties
        self.rain_drops = []
        self.initialize_rain()
        
        # Lightning properties
        self.lightning_timer = 0
        self.lightning_active = False
        self.lightning_duration = 100  # Milliseconds
        self.next_lightning = random.randint(2000, 4000)  # Time until next lightning
        
        # Fade in/out
        self.fade_alpha = 255  # Start with black
        self.fade_in_duration = 1000
        self.fade_out_duration = 1000
        self.fade_out_started = False
        
        # Text blink timer
        self.text_blink_timer = 0
        self.text_visible = True
        
        # Falling chess pieces
        self.falling_pieces = []
        self.piece_types = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
        self.initialize_falling_pieces()
        
        # Background jets
        self.background_jets = []
        self.initialize_background_jets()
        
        # Lightning in cleared area
        self.cleared_lightning_timer = 0
        self.cleared_lightning_active = False
        self.next_cleared_lightning = random.randint(1000, 3000)
        
        # Logo fade-in appearance
        self.logo_text1 = "CHECKMATE"
        self.logo_text2 = "PROTOCOL"
        self.logo_fade_alpha = 0
        self.logo_fade_start = None
        self.logo_fade_duration = 2000  # 2 seconds fade-in
        self.logo_complete = False
        
        # Binary code streams
        self.binary_streams = []
        self.initialize_binary_streams()
        
        # Military data/coordinates
        self.military_data = []
        self.initialize_military_data()
        
        # Film grain
        self.grain_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        self.generate_film_grain()
        
    def initialize_rain(self):
        """Create initial rain drops."""
        for _ in range(200):
            self.rain_drops.append({
                'x': random.randint(0, config.WIDTH),
                'y': random.randint(-config.HEIGHT, config.HEIGHT),
                'speed': random.randint(8, 15),
                'length': random.randint(10, 20),
                'opacity': random.randint(100, 200)
            })
            
    def initialize_falling_pieces(self):
        """Initialize falling chess pieces."""
        for _ in range(300):  # Double to 300 pieces!
            self.falling_pieces.append({
                'type': random.choice(self.piece_types),
                'x': random.randint(0, config.WIDTH),
                'y': random.randint(-config.HEIGHT * 3, config.HEIGHT),  # Some already on screen
                'speed': random.uniform(0.2, 1.5),  # Even slower for more atmosphere
                'rotation': random.randint(0, 360),
                'rotation_speed': random.uniform(-3, 3),
                'scale': random.uniform(0.1, 0.5),  # Even smaller
                'opacity': random.randint(15, 100)  # More subtle
            })
            
    def initialize_background_jets(self):
        """Initialize background jets flying in formation."""
        for i in range(5):  # 5 background jets
            self.background_jets.append({
                'x': random.randint(-500, -200),
                'y': random.randint(50, config.HEIGHT - 150),
                'speed': random.uniform(2.0, 4.0),
                'scale': random.uniform(0.3, 0.6),
                'opacity': random.randint(30, 80),
                'frame': random.randint(0, len(self.jet_frames) - 1) if self.jet_frames else 0,
                'animation_timer': random.randint(0, 100)
            })
            
    def initialize_military_data(self):
        """Initialize military-style scrolling data."""
        data_types = [
            "LAT: {:.4f}°N",
            "LON: {:.4f}°W", 
            "ALT: {}m",
            "SPD: {}kts",
            "HDG: {}°",
            "TACTICAL: ENGAGED",
            "MISSION: CHECKMATE",
            "STATUS: ACTIVE",
            "TARGET: ACQUIRED",
            "ETA: {}s"
        ]
        
        for i in range(20):
            self.military_data.append({
                'text': random.choice(data_types).format(
                    random.uniform(0, 90),  # For coordinates
                    random.uniform(0, 180),  # For coordinates
                    random.randint(1000, 10000),  # For altitude
                    random.randint(200, 600),  # For speed
                    random.randint(0, 359),  # For heading
                    random.randint(10, 99)  # For ETA
                ),
                'x': random.randint(0, config.WIDTH),
                'y': random.randint(0, config.HEIGHT),
                'speed': random.uniform(0.2, 0.5),
                'opacity': random.randint(20, 50),
                'font_size': random.choice(['tiny', 'tiny', 'small'])
            })
            
    def initialize_binary_streams(self):
        """Initialize binary code streams."""
        for i in range(30):  # 30 binary streams
            # Generate random binary string
            binary_string = ''.join(random.choice('01') for _ in range(random.randint(8, 16)))
            self.binary_streams.append({
                'text': binary_string,
                'x': random.randint(0, config.WIDTH),
                'y': random.randint(-config.HEIGHT, config.HEIGHT * 2),
                'speed': random.uniform(0.3, 0.8),
                'opacity': random.randint(15, 35),
                'direction': random.choice([-1, 1])  # -1 for up, 1 for down
            })
            
    def generate_film_grain(self):
        """Generate film grain overlay."""
        self.grain_surface.fill((0, 0, 0, 0))
        for _ in range(2000):
            x = random.randint(0, config.WIDTH - 1)
            y = random.randint(0, config.HEIGHT - 1)
            brightness = random.randint(0, 50)
            alpha = random.randint(10, 30)
            pygame.draw.circle(self.grain_surface, (brightness, brightness, brightness, alpha), (x, y), 1)
            
    def start(self):
        """Start the cutscene."""
        self.active = True
        self.complete = False
        self.start_time = pygame.time.get_ticks()
        self.jet_x = config.WIDTH + 200  # Already off screen
        self.fade_alpha = 255
        self.fade_out_started = False
        
    def update(self):
        """Update cutscene state."""
        if not self.active:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # Don't auto-complete - wait for user input
        # The skip() method will handle completion
                
        # Update fade
        if elapsed < self.fade_in_duration:
            self.fade_alpha = int(255 * (1 - elapsed / self.fade_in_duration))
        elif self.fade_out_started:
            fade_elapsed = current_time - self.fade_out_start_time
            self.fade_alpha = int(255 * (fade_elapsed / self.fade_out_duration))
            # Mark complete when fade out finishes
            if fade_elapsed >= self.fade_out_duration:
                self.complete = True
                self.active = False
        else:
            self.fade_alpha = 0
            
        # No jet movement - it's already off screen
        # Keep camera steady
        self.camera_offset_x = 0
        
        # Update turbulence
        self.turbulence_timer += 16  # Assume 60 FPS
        self.camera_shake_x = math.sin(self.turbulence_timer * 0.002) * 2
        self.camera_shake_y = math.cos(self.turbulence_timer * 0.003) * 3
        
        # Update parallax
        self.parallax_offset += 1
        
        # Update rain
        for drop in self.rain_drops:
            drop['y'] += drop['speed']
            drop['x'] -= 2  # Slight wind effect
            
            # Reset drops that go off screen
            if drop['y'] > config.HEIGHT:
                drop['y'] = random.randint(-50, -10)
                drop['x'] = random.randint(0, config.WIDTH + 100)
                
        # Update lightning
        self.lightning_timer += 16
        if self.lightning_timer >= self.next_lightning and not self.lightning_active:
            self.lightning_active = True
            self.lightning_start = current_time
            self.next_lightning = random.randint(2000, 4000)
            self.lightning_timer = 0
            
        if self.lightning_active:
            if current_time - self.lightning_start >= self.lightning_duration:
                self.lightning_active = False
                
        # Update text blink
        self.text_blink_timer += 16
        if self.text_blink_timer >= 500:  # Blink every 500ms
            self.text_visible = not self.text_visible
            self.text_blink_timer = 0
            
        # Update falling chess pieces immediately
        if True:
            for piece in self.falling_pieces:
                piece['y'] += piece['speed']
                piece['rotation'] += piece['rotation_speed']
                
                # Reset pieces that fall off screen
                if piece['y'] > config.HEIGHT:
                    piece['y'] = random.randint(-200, -50)
                    piece['x'] = random.randint(0, config.WIDTH)  # Spawn anywhere
                    piece['speed'] = random.uniform(0.2, 1.5)
                    piece['type'] = random.choice(self.piece_types)
                    
        # Update background jets
        for jet in self.background_jets:
            jet['x'] += jet['speed']
            jet['animation_timer'] += 16
            if jet['animation_timer'] >= self.jet_animation_speed:
                jet['animation_timer'] = 0
                jet['frame'] = (jet['frame'] + 1) % len(self.jet_frames) if self.jet_frames else 0
            
            # Reset jets that go off screen
            if jet['x'] > config.WIDTH + 200:
                jet['x'] = random.randint(-500, -300)
                jet['y'] = random.randint(50, config.HEIGHT - 150)
                jet['speed'] = random.uniform(2.0, 4.0)
                
        # Update cleared area lightning
        if True:  # Always show
            self.cleared_lightning_timer += 16
            if self.cleared_lightning_timer >= self.next_cleared_lightning and not self.cleared_lightning_active:
                self.cleared_lightning_active = True
                self.cleared_lightning_start = current_time
                self.next_cleared_lightning = random.randint(2000, 4000)
                self.cleared_lightning_timer = 0
                
            if self.cleared_lightning_active:
                if current_time - self.cleared_lightning_start >= 150:  # Slightly longer than normal lightning
                    self.cleared_lightning_active = False
                    
        # Update logo fade-in
        if not self.logo_complete:
            # Start fade when intro is done (immediately)
            if self.logo_fade_start is None:
                self.logo_fade_start = pygame.time.get_ticks()
            
            # Calculate fade progress
            elapsed = pygame.time.get_ticks() - self.logo_fade_start
            if elapsed < self.logo_fade_duration:
                self.logo_fade_alpha = int(255 * (elapsed / self.logo_fade_duration))
            else:
                self.logo_fade_alpha = 255
                self.logo_complete = True
                    
        # Update military data immediately
        if True:  # Always show
            for data in self.military_data:
                data['y'] -= data['speed']
                if data['y'] < -20:
                    data['y'] = config.HEIGHT + 20
                    data['x'] = random.randint(0, config.WIDTH)
                # Regenerate text
                data_types = [
                    "LAT: {:.4f}°N",
                    "LON: {:.4f}°W", 
                    "ALT: {}m",
                    "SPD: {}kts",
                    "HDG: {}°",
                    "TACTICAL: ENGAGED",
                    "MISSION: CHECKMATE",
                    "STATUS: ACTIVE",
                    "TARGET: ACQUIRED",
                    "ETA: {}s"
                ]
                data['text'] = random.choice(data_types).format(
                    random.uniform(0, 90),
                    random.uniform(0, 180),
                    random.randint(1000, 10000),
                    random.randint(200, 600),
                    random.randint(0, 359),
                    random.randint(10, 99)
                )
                
            # Update binary streams
            for stream in self.binary_streams:
                stream['y'] += stream['speed'] * stream['direction']
                # Wrap around
                if stream['direction'] == 1 and stream['y'] > config.HEIGHT + 20:
                    stream['y'] = -20
                    stream['x'] = random.randint(0, config.WIDTH)
                    # Regenerate binary string
                    stream['text'] = ''.join(random.choice('01') for _ in range(random.randint(8, 16)))
                elif stream['direction'] == -1 and stream['y'] < -20:
                    stream['y'] = config.HEIGHT + 20
                    stream['x'] = random.randint(0, config.WIDTH)
                    # Regenerate binary string
                    stream['text'] = ''.join(random.choice('01') for _ in range(random.randint(8, 16)))
                
        # Regenerate film grain occasionally for animated effect
        if random.randint(0, 3) == 0:
            self.generate_film_grain()
            
    def draw(self):
        """Draw the cutscene."""
        if not self.active:
            return
            
        # Draw parallax background with camera offset
        if hasattr(self.assets, 'parallax_layers') and self.assets.parallax_layers:
            for i, layer in enumerate(self.assets.parallax_layers):
                # Calculate layer offset based on depth
                layer_offset = self.camera_offset_x * layer['speed'] + self.camera_shake_x
                
                # Draw layer twice for seamless scrolling
                x_pos = -(self.parallax_offset * layer['speed']) % layer['width'] + layer_offset
                self.screen.blit(layer['image'], (x_pos, self.camera_shake_y))
                self.screen.blit(layer['image'], (x_pos - layer['width'], self.camera_shake_y))
        else:
            # Fallback - dark jungle colors
            self.screen.fill((10, 25, 10))
            
        # Apply darkening for storm atmosphere
        dark_overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(60)
        self.screen.blit(dark_overlay, (0, 0))
        
        # Draw lightning flash - DISABLED
        # if self.lightning_active:
        #     flash_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
        #     flash_surface.fill((255, 255, 255))
        #     flash_alpha = 100 if (pygame.time.get_ticks() // 50) % 2 == 0 else 50
        #     flash_surface.set_alpha(flash_alpha)
        #     self.screen.blit(flash_surface, (0, 0))
            
        # Draw rain
        rain_surface = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        for drop in self.rain_drops:
            # Draw rain drop as a line
            start_y = drop['y']
            end_y = drop['y'] + drop['length']
            color = (200, 200, 255, drop['opacity'])
            pygame.draw.line(rain_surface, color, 
                           (drop['x'], start_y), 
                           (drop['x'], end_y), 1)
        self.screen.blit(rain_surface, (0, 0))
        
        # Show the entire cleared area (no jet clearing effect)
        clear_width = config.WIDTH  # Full screen is "cleared"
        
        if True:  # Always show
            # Create a vertical clearing effect that covers the full screen height
            clear_rect = pygame.Rect(0, 0, clear_width, config.HEIGHT)
            
            # Draw black background for cleared area
            pygame.draw.rect(self.screen, (0, 0, 0), clear_rect)
            
            # Draw falling chess pieces
            if True:  # Always show
                # Create a clipping rect for the cleared area
                clip_rect = self.screen.get_clip()
                self.screen.set_clip(clear_rect)
                
                # Draw falling pieces
                for piece in self.falling_pieces:
                    if piece['x'] < clear_rect.width:  # Only draw in cleared area
                        if hasattr(self.assets, 'pieces') and piece['type'] in self.assets.pieces:
                            piece_img = self.assets.pieces[piece['type']].copy()
                            
                            # Scale the piece
                            piece_size = int(80 * piece['scale'])
                            piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                            
                            # Rotate the piece
                            rotated_piece = pygame.transform.rotate(piece_img, piece['rotation'])
                            
                            # Set opacity
                            rotated_piece.set_alpha(piece['opacity'])
                            
                            # Get rect for positioning
                            piece_rect = rotated_piece.get_rect(center=(int(piece['x']), int(piece['y'])))
                            
                            # Draw the piece
                            self.screen.blit(rotated_piece, piece_rect)
                
                # Restore clip
                self.screen.set_clip(clip_rect)
                
                # Draw background jets in cleared area
                for jet in self.background_jets:
                    if jet['x'] < clear_rect.width and jet['x'] > -150:  # Only draw in cleared area
                        if self.jet_frames and len(self.jet_frames) > 0:
                            jet_frame = self.jet_frames[jet['frame']]
                            # Scale the jet
                            jet_width = int(150 * jet['scale'])
                            jet_height = int(jet_width * jet_frame.get_height() / jet_frame.get_width())
                            scaled_jet = pygame.transform.scale(jet_frame, (jet_width, jet_height))
                            scaled_jet.set_alpha(jet['opacity'])
                            
                            self.screen.blit(scaled_jet, (int(jet['x']), int(jet['y'])))
                
                # Draw military data and binary streams immediately
                if True:
                    # Draw binary streams
                    for stream in self.binary_streams:
                        if stream['x'] < clear_rect.width:
                            font = self.renderer.pixel_fonts.get('tiny')
                            text = font.render(stream['text'], True, (0, 255, 0))  # Green binary
                            text.set_alpha(stream['opacity'])
                            self.screen.blit(text, (int(stream['x']), int(stream['y'])))
                    
                    # Draw military data
                    for data in self.military_data:
                        if data['x'] < clear_rect.width:  # Only in cleared area
                            font = self.renderer.pixel_fonts.get(data['font_size'], self.renderer.pixel_fonts['tiny'])
                            text = font.render(data['text'], True, (0, 255, 0))  # Green military text
                            text.set_alpha(data['opacity'])
                            self.screen.blit(text, (int(data['x']), int(data['y'])))
                
                # Draw the logo with fade-in effect
                if self.logo_font and self.logo_fade_alpha > 0:
                    # Draw "CHECKMATE PROTOCOL" as one line with fade
                    full_title = "CHECKMATE PROTOCOL"
                    logo_surface = self.logo_font.render(full_title, True, config.WHITE)
                    logo_surface.set_alpha(self.logo_fade_alpha)
                    logo_rect = logo_surface.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
                    self.screen.blit(logo_surface, logo_rect)
                    
                # Draw cleared area lightning - DISABLED
                # if self.cleared_lightning_active and clear_rect.width > 0:
                #     # Create vertical lightning bolts in cleared area
                #     for i in range(3):  # Multiple bolts
                #         bolt_x = random.randint(50, min(clear_rect.width - 50, config.WIDTH - 50))
                #         bolt_segments = []
                #         current_x = bolt_x
                #         current_y = 0
                #         
                #         while current_y < config.HEIGHT:
                #             next_x = current_x + random.randint(-20, 20)
                #             next_y = current_y + random.randint(30, 60)
                #             bolt_segments.append(((current_x, current_y), (next_x, next_y)))
                #             current_x = next_x
                #             current_y = next_y
                #             
                #         # Draw the lightning bolt
                #         for segment in bolt_segments:
                #             pygame.draw.line(self.screen, (200, 200, 255), segment[0], segment[1], 2)
                #             # Glow effect
                #             pygame.draw.line(self.screen, (150, 150, 255, 100), segment[0], segment[1], 4)
                
            # No edge effect needed since there's no jet clearing
        
        # Don't draw the main jet - we removed it
            
        # Draw "PRESS ANYWHERE TO CONTINUE" text
        if self.text_visible and self.fade_alpha < 200:  # Don't show during fade
            if hasattr(self.renderer, 'pixel_fonts'):
                text = self.renderer.pixel_fonts['medium'].render("PRESS ANYWHERE TO CONTINUE", True, config.WHITE)
            else:
                font = pygame.font.Font(None, 36)
                text = font.render("PRESS ANYWHERE TO CONTINUE", True, config.WHITE)
            text_rect = text.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 80))
            
            # Add glow effect
            glow_surf = pygame.Surface((text_rect.width + 20, text_rect.height + 20), pygame.SRCALPHA)
            glow_color = (255, 255, 255, 50)
            for i in range(3):
                offset = (10 - i * 3, 10 - i * 3)
                text_glow = text.copy()
                text_glow.set_alpha(50 - i * 15)
                glow_surf.blit(text_glow, offset)
            
            self.screen.blit(glow_surf, (text_rect.x - 10, text_rect.y - 10))
            self.screen.blit(text, text_rect)
            
        # Draw film grain overlay
        self.screen.blit(self.grain_surface, (0, 0))
        
        # Draw fade overlay
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface((config.WIDTH, config.HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            
    def skip(self):
        """Skip the cutscene."""
        if not self.fade_out_started:
            # Play click sound if available
            if hasattr(self.assets, 'sounds') and 'click' in self.assets.sounds:
                try:
                    self.assets.sounds['click'].play()
                except:
                    pass  # Ignore if sound fails to play
            
            self.fade_out_started = True
            self.fade_out_start_time = pygame.time.get_ticks()