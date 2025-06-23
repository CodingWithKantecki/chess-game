"""
Chopper Gunner Mode
First-person helicopter minigun gameplay
"""

import pygame
import math
import random
from config import *

class ChopperGunnerMode:
    def __init__(self, screen, assets, board):
        self.screen = screen
        self.assets = assets
        self.board = board
        self.active = False
        self.phase = "takeoff"  # takeoff, descent, active, complete
        self.phase_timer = 0
        
        # Camera properties
        self.altitude = 1000  # Start high
        self.target_altitude = 300  # Combat altitude
        self.camera_shake = {"x": 0, "y": 0, "intensity": 0}
        
        # Camera rotation for circling
        self.camera_angle = 0  # Angle for circling around board
        self.camera_tilt = 30  # Lowered by 10 more degrees for gentler angle
        self.camera_distance = 400  # Moved back from 300 to 400
        self.camera_bank = 0  # Banking angle (leaning into turns)
        self.prev_camera_angle = 0  # To calculate angular velocity
        
        # Helicopter movement dynamics - smoother values
        self.hover_offset_y = 0  # Vertical bobbing
        self.sway_offset_x = 0   # Horizontal swaying
        self.turbulence_x = 0    # Current turbulence
        self.turbulence_y = 0
        self.target_turbulence_x = 0  # Target turbulence to smoothly move to
        self.target_turbulence_y = 0
        self.hover_time = 0      # For sine wave calculations
        
        # Crosshair position
        self.crosshair_x = WIDTH // 2
        self.crosshair_y = HEIGHT // 2
        
        # Minigun properties
        self.ammo = 150
        self.firing = False
        self.fire_rate = 100  # ms between shots
        self.last_shot_time = 0
        self.muzzle_flash_timer = 0
        
        # Visual effects
        self.explosions = []
        self.bullet_tracers = []
        self.destroyed_pieces = []
        self.piece_hit_counts = {}  # Track hits on each piece
        self.piece_shake = {}  # Track shake effect for hit pieces
        
        # Board view properties
        self.board_center_x = WIDTH // 2
        self.board_center_y = HEIGHT // 2
        self.board_scale = 1.0
        
        # Cockpit overlay
        self.cockpit_overlay = None
        if hasattr(assets, 'cockpit_view') and assets.cockpit_view:
            # Scale cockpit to screen size
            self.cockpit_overlay = pygame.transform.scale(
                assets.cockpit_view, (WIDTH, HEIGHT))
                
        # Sounds
        self.helicopter_sound = None
        self.helicopter_blade_sound = None
        self.minigun_sound = None
        self.minigun_revup_sound = None
        self.minigun_fire_sound = None
        self.minigun_spindown_sound = None
        if hasattr(assets, 'sounds'):
            if 'helicopter' in assets.sounds:
                self.helicopter_sound = assets.sounds['helicopter']
            if 'helicopter_blade' in assets.sounds:
                self.helicopter_blade_sound = assets.sounds['helicopter_blade']
            if 'minigun' in assets.sounds:
                self.minigun_sound = assets.sounds['minigun']
            if 'minigun_revup' in assets.sounds:
                self.minigun_revup_sound = assets.sounds['minigun_revup']
            if 'minigun_fire' in assets.sounds:
                self.minigun_fire_sound = assets.sounds['minigun_fire']
            if 'minigun_spindown' in assets.sounds:
                self.minigun_spindown_sound = assets.sounds['minigun_spindown']
                
        # Minigun sound state
        self.minigun_state = "idle"  # idle, revving, firing, spindown
        self.minigun_fire_channel = None  # To loop the firing sound
                
    def start(self):
        """Start the chopper gunner sequence."""
        self.active = True
        self.phase = "sequence"  # Start with sequence instead of takeoff
        self.phase_timer = pygame.time.get_ticks()
        self.sequence_state = 0  # Track which image we're showing
        
        # Debug prints
        print("Starting chopper gunner mode...")
        print(f"Helicopter sound available: {self.helicopter_sound is not None}")
        print(f"Helicopter blade sound available: {self.helicopter_blade_sound is not None}")
        
        # Start helicopter sounds
        if self.helicopter_sound:
            self.helicopter_sound.play(-1)  # Loop
            print("Playing helicopter sound")
        # Play blade sound if available
        if self.helicopter_blade_sound:
            self.helicopter_blade_sound.play(-1)  # Loop the blade sound
            print("Playing helicopter blade sound")
        else:
            print("No helicopter blade sound loaded!")
            
    def stop(self):
        """End chopper gunner mode."""
        self.active = False
        
        # Stop sounds
        if self.helicopter_sound:
            self.helicopter_sound.stop()
        if self.helicopter_blade_sound:
            self.helicopter_blade_sound.stop()
            
        # Stop any minigun sounds
        if self.minigun_fire_channel:
            self.minigun_fire_channel.stop()
        self.minigun_state = "idle"
            
    def handle_mouse(self, pos):
        """Update crosshair position."""
        self.crosshair_x, self.crosshair_y = pos
        
    def handle_click(self, pos):
        """Handle firing."""
        if self.phase == "active" and self.ammo > 0:
            self.firing = True
            
            # Start minigun rev up if not already firing
            if self.minigun_state == "idle":
                self.minigun_state = "revving"
                if self.minigun_revup_sound:
                    self.minigun_revup_sound.play()
                    # Schedule firing sound to start after rev up
                    self.rev_start_time = pygame.time.get_ticks()
            
    def handle_release(self):
        """Stop firing."""
        self.firing = False
        
        # Start spin down if was firing
        if self.minigun_state == "firing":
            self.minigun_state = "spindown"
            if self.minigun_fire_channel:
                self.minigun_fire_channel.stop()
            if self.minigun_spindown_sound:
                self.minigun_spindown_sound.play()
                self.spindown_start_time = pygame.time.get_ticks()
        elif self.minigun_state == "revving":
            # If released during rev up, just go back to idle
            self.minigun_state = "idle"
        
    def update(self):
        """Update chopper gunner state."""
        current_time = pygame.time.get_ticks()
        
        # Update phase
        if self.phase == "sequence":
            elapsed = current_time - self.phase_timer
            
            if elapsed < 2000:
                # First image (0-2 seconds)
                self.sequence_state = 0
            elif elapsed < 4000:
                # Second image (2-4 seconds)
                self.sequence_state = 1
            else:
                # Move to takeoff phase
                self.phase = "takeoff"
                self.phase_timer = current_time
                
        # Only update movement calculations after sequence
        if self.phase != "sequence":
            # Update hover time for movement calculations
            self.hover_time = current_time / 1000.0  # Convert to seconds
            self.vibration_time = current_time / 100.0  # Faster for vibration
            
            # Update camera rotation for circling effect
            self.prev_camera_angle = self.camera_angle
            self.camera_angle += 0.5  # Slowly rotate around the board
            if self.camera_angle >= 360:
                self.camera_angle -= 360
                
            # Calculate banking based on turn rate
            # Helicopter banks into the turn (tilts inward when circling)
            turn_rate = 0.5  # degrees per frame
            max_bank = 15  # Maximum banking angle in degrees
            
            # Since we're always turning at constant rate, calculate bank based on direction
            # For clockwise rotation, bank to the right (positive)
            target_bank = max_bank * (turn_rate / 2.0)  # Scale banking with turn rate
            
            # Add dynamic banking based on current movement
            # Check which quadrant we're in for more realistic banking
            angle_rad = math.radians(self.camera_angle)
            
            # Add sinusoidal variation to make banking more dynamic
            # This simulates the helicopter adjusting its bank through the turn
            bank_variation = math.sin(angle_rad * 2) * 5  # Varies by ±5 degrees
            target_bank += bank_variation
            
            # Smoothly interpolate to target bank angle
            bank_smoothing = 0.1
            self.camera_bank += (target_bank - self.camera_bank) * bank_smoothing
                
            # Add realistic helicopter movement - much smoother
            # Vertical bobbing (gentle up and down)
            self.hover_offset_y = math.sin(self.hover_time * 0.8) * 8  # Reduced from 15 to 8
            
            # Horizontal swaying (subtle side-to-side)
            self.sway_offset_x = math.sin(self.hover_time * 0.6) * 5  # Reduced from 10 to 5
            
            # Constant engine vibration
            vibration_x = math.sin(self.vibration_time * 15) * 1.5  # Rapid small vibration
            vibration_y = math.cos(self.vibration_time * 17) * 1.5  # Different frequency for Y
            
            # Smooth turbulence system - no sudden jumps
            if random.random() < 0.005:  # 0.5% chance to change turbulence target
                # Set new target, but don't jump to it
                self.target_turbulence_x = random.uniform(-3, 3)
                self.target_turbulence_y = random.uniform(-3, 3)
            else:
                # Gradually move target back to zero
                self.target_turbulence_x *= 0.99
                self.target_turbulence_y *= 0.99
                
            # Smoothly interpolate current turbulence toward target
            turbulence_smoothing = 0.05  # How fast to move toward target (lower = smoother)
            self.turbulence_x += (self.target_turbulence_x - self.turbulence_x) * turbulence_smoothing
            self.turbulence_y += (self.target_turbulence_y - self.turbulence_y) * turbulence_smoothing
            
            # Add vibration to turbulence
            self.turbulence_x += vibration_x
            self.turbulence_y += vibration_y
                
            # Update altitude with very slight variations
            if self.phase == "active":
                # Add small altitude variations during combat
                altitude_variation = math.sin(self.hover_time * 0.5) * 10  # Reduced from 20 to 10
                self.altitude = self.target_altitude + altitude_variation
                
        # Handle phase transitions
        if self.phase == "takeoff":
            if current_time - self.phase_timer > 3000:  # 3 second takeoff
                self.phase = "descent"
                self.phase_timer = current_time
                
        elif self.phase == "descent":
            # Descend to combat altitude - SLOWER DESCENT
            # Calculate descent speed based on altitude difference
            altitude_diff = self.altitude - self.target_altitude
            
            # Start fast, slow down as we approach target (easing)
            if altitude_diff > 500:
                descent_speed = 15  # Fast at first
            elif altitude_diff > 200:
                descent_speed = 8   # Medium speed
            elif altitude_diff > 50:
                descent_speed = 4   # Slow down
            else:
                descent_speed = 2   # Very slow at the end
                
            self.altitude = max(self.target_altitude, self.altitude - descent_speed)
            
            if self.altitude <= self.target_altitude:
                self.phase = "active"
                self.phase_timer = current_time
                
        elif self.phase == "active":
            # Update minigun sound state
            current_time = pygame.time.get_ticks()
            
            if self.minigun_state == "revving":
                # Check if rev up is complete (0.5 second rev up)
                if hasattr(self, 'rev_start_time') and current_time - self.rev_start_time > 500:
                    self.minigun_state = "firing"
                    # Start looping fire sound
                    if self.minigun_fire_sound:
                        self.minigun_fire_channel = self.minigun_fire_sound.play(-1)
                        
            elif self.minigun_state == "spindown":
                # Check if spin down is complete (assuming 1.5 second spin down)
                if hasattr(self, 'spindown_start_time') and current_time - self.spindown_start_time > 1500:
                    self.minigun_state = "idle"
            
            # Handle firing
            if self.firing and self.ammo > 0 and self.minigun_state == "firing":
                if current_time - self.last_shot_time > self.fire_rate:
                    self.fire_minigun()
                    self.last_shot_time = current_time
                    
            # Update muzzle flash
            if self.muzzle_flash_timer > 0:
                self.muzzle_flash_timer -= 1
                
            # Check if all enemy pieces destroyed
            if self.all_pieces_destroyed():
                # Player wins!
                self.board.game_over = True
                self.board.winner = "white"
                self.phase = "complete"
                self.phase_timer = current_time
            elif self.ammo <= 0:
                # Out of ammo, exit chopper mode
                self.phase = "complete"
                self.phase_timer = current_time
                
        elif self.phase == "complete":
            if current_time - self.phase_timer > 2000:  # 2 second exit
                self.stop()
                
        # Update visual effects
        self.update_explosions()
        self.update_bullet_tracers()
        self.update_camera_shake()
        self.update_piece_shake()
        
    def fire_minigun(self):
        """Fire the minigun."""
        self.ammo -= 1
        self.muzzle_flash_timer = 5
        
        # Camera shake - moderate when firing
        self.camera_shake["intensity"] = 6  # Reduced from 8
        
        # Add very slight recoil movement to target (not instant)
        self.target_turbulence_x += random.uniform(-1.5, 1.5)
        self.target_turbulence_y += random.uniform(-1, 0.5)  # Slight upward tendency
        
        # Keep targets reasonable
        self.target_turbulence_x = max(-5, min(5, self.target_turbulence_x))
        self.target_turbulence_y = max(-5, min(5, self.target_turbulence_y))
        
        # Note: Fire sound is already playing in loop from handle_click
            
        # Get gun position from draw method
        gun_pos = getattr(self, '_gun_position', (WIDTH - 150, HEIGHT // 2))
            
        # Add bullet tracer from gun to crosshair
        self.bullet_tracers.append({
            "start_x": gun_pos[0],
            "start_y": gun_pos[1],
            "end_x": self.crosshair_x,
            "end_y": self.crosshair_y,
            "timer": 10
        })
        
        # Create bullet impact effects at crosshair location
        self.create_bullet_impact(self.crosshair_x, self.crosshair_y)
        
        # Check for hit
        hit_piece = self.check_hit(self.crosshair_x, self.crosshair_y)
        if hit_piece:
            self.hit_piece(hit_piece)
            
    def create_bullet_impact(self, x, y):
        """Create small impact effects where bullets land."""
        # Create 3-5 small sparks/fragments
        num_sparks = random.randint(3, 5)
        
        for _ in range(num_sparks):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            
            self.explosions.append({
                "x": x,
                "y": y,
                "timer": 15,  # Short lifetime
                "particles": [{
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - 1,  # Slight upward bias
                    "life": 15,
                    "size": random.randint(1, 3),
                    "color": random.choice([
                        (200, 200, 200),  # Light grey
                        (255, 255, 200),  # Yellowish (spark)
                        (150, 150, 150),  # Medium grey
                        (255, 200, 100)   # Orange (hot metal)
                    ])
                }]
            })
            
    def check_hit(self, x, y):
        """Check if crosshair is over an enemy piece."""
        # Convert screen coordinates to board coordinates
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                # Only target enemy (black) pieces
                if piece and piece[0] == 'b' and (row, col) not in self.destroyed_pieces:
                    piece_x, piece_y = self.get_piece_screen_pos(row, col)
                    
                    # Get piece size based on perspective
                    piece_size = self.get_piece_size(row, col)
                    
                    # Check if crosshair is within piece bounds
                    if (abs(x - piece_x) < piece_size // 2 and 
                        abs(y - piece_y) < piece_size // 2):
                        return (row, col)
        return None
        
    def hit_piece(self, pos):
        """Hit a piece at given position."""
        row, col = pos
        
        # Initialize hit count if not tracked
        if pos not in self.piece_hit_counts:
            self.piece_hit_counts[pos] = 0
            
        # Increment hit count
        self.piece_hit_counts[pos] += 1
        
        # Add shake effect
        self.piece_shake[pos] = {
            "timer": 15,  # Shake for 15 frames
            "intensity": 5  # Shake intensity
        }
        
        # Create impact fragments at hit location
        piece_x, piece_y = self.get_piece_screen_pos(row, col)
        self.create_impact_fragments(piece_x, piece_y)
        
        # Check if piece should be destroyed (3 hits)
        if self.piece_hit_counts[pos] >= 3:
            self.destroy_piece(pos)
            
    def create_impact_fragments(self, x, y):
        """Create small grey fragments at impact location."""
        # Create 5-8 small fragments
        num_fragments = random.randint(5, 8)
        
        for _ in range(num_fragments):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            size = random.randint(2, 4)
            
            self.explosions.append({
                "x": x,
                "y": y,
                "timer": 20,  # Shorter lifetime than explosion
                "particles": [{
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - 2,  # Initial upward velocity
                    "life": 20,
                    "size": size,
                    "color": random.choice([
                        (128, 128, 128),  # Grey
                        (105, 105, 105),  # Dim grey
                        (160, 160, 160),  # Light grey
                        (80, 80, 80)      # Dark grey
                    ])
                }]
            })
            
    def destroy_piece(self, pos):
        """Destroy a piece at given position."""
        row, col = pos
        self.destroyed_pieces.append(pos)
        
        # Add explosion effect
        piece_x, piece_y = self.get_piece_screen_pos(row, col)
        self.explosions.append({
            "x": piece_x,
            "y": piece_y,
            "timer": 30,
            "particles": self.create_explosion_particles(piece_x, piece_y)
        })
        
        # Remove piece from board
        self.board.set_piece(row, col, "")
        
        # Play capture sound
        if hasattr(self.assets, 'sounds') and 'capture' in self.assets.sounds:
            self.assets.sounds['capture'].play()
            
        # Clean up tracking
        if pos in self.piece_hit_counts:
            del self.piece_hit_counts[pos]
        if pos in self.piece_shake:
            del self.piece_shake[pos]
        
    def update_piece_shake(self):
        """Update shake effects for hit pieces."""
        to_remove = []
        for pos, shake in self.piece_shake.items():
            shake["timer"] -= 1
            if shake["timer"] <= 0:
                to_remove.append(pos)
                
        for pos in to_remove:
            del self.piece_shake[pos]
            
    def get_piece_screen_pos(self, row, col):
        """Get screen position of a piece with perspective and rotation."""
        # Flip the board so white is at bottom (row 7 becomes row 0)
        flipped_row = 7 - row
        
        # Calculate board position relative to center
        board_x = col - 3.5  # Center around board center
        board_y = flipped_row - 3.5  # Use flipped row
        
        # Apply camera position offset (helicopter circling)
        angle_rad = math.radians(self.camera_angle)
        
        # Apply rotation based on camera angle
        rotated_x = board_x * math.cos(angle_rad) - board_y * math.sin(angle_rad)
        rotated_y = board_x * math.sin(angle_rad) + board_y * math.cos(angle_rad)
        
        # Apply banking (roll) - this tilts the view
        bank_rad = math.radians(self.camera_bank)
        
        # Banking affects the x-coordinate based on y-position
        # This creates the effect of the world tilting
        banked_x = rotated_x * math.cos(bank_rad) - rotated_y * 0.2 * math.sin(bank_rad)
        
        # Apply tilt - looking down at the board
        tilt_rad = math.radians(self.camera_tilt)
        
        # For a proper 3D perspective looking down:
        # Y coordinate should be compressed based on tilt angle
        # Items farther away (negative rotated_y) should be higher on screen
        projected_x = banked_x
        projected_y = rotated_y * math.sin(tilt_rad)  # Compress Y based on tilt
        projected_z = rotated_y * math.cos(tilt_rad)  # Depth component
        
        # Apply perspective based on depth
        # Objects farther away (larger projected_z) should be smaller
        # Include altitude variations in perspective calculation
        altitude_scale = 1.0 - (self.altitude - self.target_altitude) / 1500.0
        altitude_scale = max(0.4, min(1.0, altitude_scale))
        perspective_scale = (600 / (600 + projected_z * 50 + (self.altitude - self.target_altitude) * 0.5)) * altitude_scale
        
        # Scale positions
        screen_x = self.board_center_x + projected_x * 100 * perspective_scale
        screen_y = self.board_center_y - projected_y * 100 * perspective_scale  # Negative because Y increases downward
        
        # Apply helicopter movement offsets
        screen_x += self.sway_offset_x + self.turbulence_x
        screen_y += self.hover_offset_y + self.turbulence_y
        
        # Apply camera shake (from firing)
        screen_x += self.camera_shake["x"]
        screen_y += self.camera_shake["y"]
        
        # Apply piece shake if this piece is being hit
        if (row, col) in self.piece_shake:
            shake = self.piece_shake[(row, col)]
            shake_x = random.randint(-shake["intensity"], shake["intensity"])
            shake_y = random.randint(-shake["intensity"], shake["intensity"])
            screen_x += shake_x
            screen_y += shake_y
        
        return int(screen_x), int(screen_y)
        
    def get_piece_size(self, row, col):
        """Get visual size of piece based on perspective."""
        # Get the screen position to calculate perspective
        _, screen_y = self.get_piece_screen_pos(row, col)
        
        # Size should be smaller for pieces farther away (higher on screen)
        # Normalize Y position (0 at top, 1 at bottom)
        y_normalized = screen_y / HEIGHT if HEIGHT > 0 else 0.5
        
        # Base size with perspective scaling - INCREASED from 60 to 80
        base_size = 80
        
        # Apply altitude scaling - pieces should be smaller when helicopter is higher
        altitude_factor = 1.0 - (self.altitude - self.target_altitude) / 1000.0
        altitude_factor = max(0.3, min(1.0, altitude_factor))  # Clamp between 30% and 100%
        
        # Combine perspective factors
        size_factor = 0.6 + y_normalized * 0.4  # Size varies from 60% to 100%
        
        return int(base_size * size_factor * altitude_factor)
        
    def create_explosion_particles(self, x, y):
        """Create explosion particle effects."""
        particles = []
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 30,
                "color": random.choice([
                    (255, 200, 0),
                    (255, 150, 0),
                    (255, 100, 0),
                    (200, 50, 0)
                ])
            })
        return particles
        
    def update_explosions(self):
        """Update explosion effects."""
        remaining = []
        for explosion in self.explosions:
            explosion["timer"] -= 1
            
            # Update particles
            remaining_particles = []
            for particle in explosion["particles"]:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["vy"] += 0.5  # Gravity
                particle["life"] -= 1
                
                # Add some air resistance to fragments
                if "size" in particle:
                    particle["vx"] *= 0.95
                    particle["vy"] *= 0.98
                
                if particle["life"] > 0:
                    remaining_particles.append(particle)
                    
            explosion["particles"] = remaining_particles
            
            if explosion["timer"] > 0:
                remaining.append(explosion)
                
        self.explosions = remaining
        
    def update_bullet_tracers(self):
        """Update bullet tracer effects."""
        remaining = []
        for tracer in self.bullet_tracers:
            tracer["timer"] -= 1
            if tracer["timer"] > 0:
                remaining.append(tracer)
        self.bullet_tracers = remaining
        
    def update_camera_shake(self):
        """Update camera shake effect."""
        if self.camera_shake["intensity"] > 0:
            # Convert intensity to int for randint
            intensity = int(self.camera_shake["intensity"])
            if intensity > 0:
                self.camera_shake["x"] = random.randint(-intensity, intensity)
                self.camera_shake["y"] = random.randint(-intensity, intensity)
            else:
                self.camera_shake["x"] = 0
                self.camera_shake["y"] = 0
            self.camera_shake["intensity"] *= 0.9
        else:
            self.camera_shake["x"] = 0
            self.camera_shake["y"] = 0
            
    def all_pieces_destroyed(self):
        """Check if all enemy pieces except kings are destroyed."""
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                # Only check black (enemy) pieces
                if piece and piece[0] == 'b' and piece[1] != 'K' and (row, col) not in self.destroyed_pieces:
                    return False
        return True
        
    def draw(self):
        """Draw the chopper gunner view."""
        # Handle sequence phase separately
        if self.phase == "sequence":
            self.draw_sequence()
            return
            
        # Draw parallax background with rotation
        self.draw_rotating_parallax_background()
        
        # Draw board and pieces from aerial view
        self.draw_aerial_board()
        
        # Draw effects
        self.draw_explosions()
        self.draw_bullet_tracers()
        
        # Draw cockpit overlay
        if self.cockpit_overlay:
            self.screen.blit(self.cockpit_overlay, (0, 0))
            
        # Draw minigun
        self.draw_minigun()
        
        # Draw crosshair
        self.draw_crosshair()
        
        # Draw HUD
        self.draw_hud()
        
    def draw_rotating_parallax_background(self):
        """Draw parallax background that rotates with the helicopter."""
        # Clear screen with base color
        self.screen.fill((30, 30, 40))
        
        # Check if parallax layers exist
        if not hasattr(self.assets, 'parallax_layers') or not self.assets.parallax_layers:
            # Fallback to gradient if no parallax
            self.draw_sky_gradient()
            return
            
        # SIMPLIFIED APPROACH: Just draw the bottom 2-3 layers without rotation
        # This gives the effect of distant scenery without the performance hit
        
        # Only use the farthest background layers (usually sky and distant mountains)
        layers_to_draw = min(3, len(self.assets.parallax_layers))
        
        for i in range(layers_to_draw):
            layer = self.assets.parallax_layers[i]
            if not layer.get("image"):
                continue
                
            # Simple horizontal scrolling based on camera angle
            scroll_offset = int(self.camera_angle * layer["speed"] * 2)
            
            # Get image dimensions
            img = layer["image"]
            img_width = img.get_width()
            
            # Calculate position (no rotation, just scrolling)
            x = -(scroll_offset % img_width)
            
            # Draw the layer twice for seamless scrolling
            while x < WIDTH:
                # Simple vertical offset for banking
                y_offset = int(self.camera_bank * layer["speed"] * 5)
                self.screen.blit(img, (x, y_offset))
                x += img_width
                
        # Add a gradient overlay to blend with the sky
        gradient_surface = pygame.Surface((WIDTH, HEIGHT // 3), pygame.SRCALPHA)
        for y in range(HEIGHT // 3):
            alpha = int(255 * (1 - y / (HEIGHT // 3)))
            color = (30, 30, 40, alpha)
            pygame.draw.rect(gradient_surface, color, (0, y, WIDTH, 1))
        self.screen.blit(gradient_surface, (0, 0))
            
    def draw_sky_gradient(self):
        """Draw the sky gradient with banking effect."""
        # Calculate horizon tilt based on banking
        bank_offset = int(self.camera_bank * 10)  # Pixels to shift horizon
        
        for y in range(0, HEIGHT, 5):
            progress = y / HEIGHT
            color = (
                int(50 - progress * 30),  # R: 50 to 20
                int(50 - progress * 30),  # G: 50 to 20  
                int(70 - progress * 40)   # B: 70 to 30
            )
            
            # Create a polygon that's tilted based on banking
            left_y = y - bank_offset
            right_y = y + bank_offset
            
            points = [
                (0, left_y),
                (WIDTH, right_y),
                (WIDTH, right_y + 5),
                (0, left_y + 5)
            ]
            
            pygame.draw.polygon(self.screen, color, points)
        
    def draw_sequence(self):
        """Draw the helicopter takeoff sequence."""
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.phase_timer
        
        # Check if we have the sequence images
        if hasattr(self.assets, 'airstrike_sequence') and len(self.assets.airstrike_sequence) >= 2:
            if self.sequence_state == 0 and elapsed < 2000:
                # First image (0-2 seconds)
                alpha = 255
                if elapsed < 500:  # Fade in
                    alpha = int((elapsed / 500) * 255)
                elif elapsed > 1500:  # Fade out
                    alpha = int(((2000 - elapsed) / 500) * 255)
                
                # Scale image to screen
                img = self.assets.airstrike_sequence[0]
                scaled_img = pygame.transform.scale(img, (WIDTH, HEIGHT))
                
                # Create a copy to set alpha
                fade_img = scaled_img.copy()
                fade_img.set_alpha(alpha)
                self.screen.blit(fade_img, (0, 0))
                
            elif self.sequence_state == 1 and elapsed >= 2000 and elapsed < 4000:
                # Second image (2-4 seconds)
                alpha = 255
                if elapsed < 2500:  # Fade in
                    alpha = int(((elapsed - 2000) / 500) * 255)
                elif elapsed > 3500:  # Fade out
                    alpha = int(((4000 - elapsed) / 500) * 255)
                
                # Scale image to screen
                img = self.assets.airstrike_sequence[1]
                scaled_img = pygame.transform.scale(img, (WIDTH, HEIGHT))
                
                # Create a copy to set alpha
                fade_img = scaled_img.copy()
                fade_img.set_alpha(alpha)
                self.screen.blit(fade_img, (0, 0))
        else:
            # Fallback if images not loaded - just show black screen
            self.screen.fill((0, 0, 0))
        
    def draw_aerial_board(self):
        """Draw the chess board from aerial perspective with rotation."""
        # Draw board squares with rotation and perspective
        for row in range(8):
            for col in range(8):
                # Get screen position with rotation
                x, y = self.get_piece_screen_pos(row, col)
                size = self.get_piece_size(row, col)
                
                # Skip squares that are behind the camera
                if y < -100:
                    continue
                
                # Alternate square colors
                if (row + col) % 2 == 0:
                    color = (200, 180, 140)
                else:
                    color = (120, 100, 70)
                    
                # Calculate the four corners of the square with perspective
                corners = []
                for dr, dc in [(0, 0), (1, 0), (1, 1), (0, 1)]:
                    corner_x, corner_y = self.get_piece_screen_pos(row + dr - 0.5, col + dc - 0.5)
                    corners.append((corner_x, corner_y))
                
                # Draw the square as a polygon for proper perspective
                if len(corners) == 4:
                    pygame.draw.polygon(self.screen, color, corners)
                    pygame.draw.polygon(self.screen, (80, 80, 80), corners, 1)
        
        # Draw pieces with perspective scaling
        piece_draw_order = []  # Store pieces with their y position for depth sorting
        
        for row in range(8):
            for col in range(8):
                if (row, col) not in self.destroyed_pieces:
                    piece = self.board.get_piece(row, col)
                    if piece:
                        x, y = self.get_piece_screen_pos(row, col)
                        if y > -100:  # Only draw if in front of camera
                            piece_draw_order.append((y, row, col, piece))
        
        # Sort pieces by y position (draw farther pieces first)
        piece_draw_order.sort(key=lambda p: p[0])
        
        # Draw pieces in depth order
        for _, row, col, piece in piece_draw_order:
            self.draw_piece_aerial(row, col, piece)
                        
    def draw_piece_aerial(self, row, col, piece):
        """Draw a single piece from aerial view using actual piece images."""
        x, y = self.get_piece_screen_pos(row, col)
        size = self.get_piece_size(row, col)
        
        # Use actual piece images if available
        if hasattr(self.assets, 'pieces') and piece in self.assets.pieces:
            piece_image = self.assets.pieces[piece]
            # Scale the piece image based on perspective
            scaled_piece = pygame.transform.scale(piece_image, (size, size))
            
            # Don't rotate the piece - just center it at the position
            rect = scaled_piece.get_rect(center=(x, y))
            self.screen.blit(scaled_piece, rect)
        else:
            # Fallback: Draw piece as a circle with letter if no image
            color = (200, 200, 200) if piece[0] == 'w' else (50, 50, 50)
            pygame.draw.circle(self.screen, color, (x, y), size // 2)
            pygame.draw.circle(self.screen, (100, 100, 100), (x, y), size // 2, 2)
            
            # Draw piece type letter
            if hasattr(self, 'font'):
                font = self.font
            else:
                self.font = pygame.font.Font(None, size // 2)
                font = self.font
                
            text = font.render(piece[1], True, 
                              (50, 50, 50) if piece[0] == 'w' else (200, 200, 200))
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)
        
    def draw_minigun(self):
        """Draw the minigun at side of screen (mounted on helicopter)."""
        # Position minigun on the right side, angled towards center
        gun_x = WIDTH - 150
        gun_y = HEIGHT // 2
        
        # Gun mount/base
        mount_width = 60
        mount_height = 80
        pygame.draw.rect(self.screen, (40, 40, 40), 
                        (gun_x, gun_y - mount_height // 2, mount_width, mount_height))
        pygame.draw.rect(self.screen, (60, 60, 60), 
                        (gun_x + 5, gun_y - mount_height // 2 + 5, mount_width - 10, mount_height - 10))
        
        # Gun body angled towards center
        angle_to_center = math.atan2(self.crosshair_y - gun_y, self.crosshair_x - gun_x)
        
        # Draw rotating barrels
        barrel_length = 80
        barrel_end_x = gun_x + math.cos(angle_to_center) * barrel_length
        barrel_end_y = gun_y + math.sin(angle_to_center) * barrel_length
        
        # Main barrel housing
        pygame.draw.line(self.screen, (80, 80, 80), (gun_x, gun_y), 
                        (barrel_end_x, barrel_end_y), 25)
        
        # Rotating barrels effect
        barrel_rotation = (pygame.time.get_ticks() // 30) % 360
        for i in range(6):
            angle = barrel_rotation + i * 60
            # Small offset for each barrel
            offset_x = math.cos(math.radians(angle)) * 8
            offset_y = math.sin(math.radians(angle)) * 8
            
            start_x = gun_x + offset_x
            start_y = gun_y + offset_y
            end_x = barrel_end_x + offset_x
            end_y = barrel_end_y + offset_y
            
            pygame.draw.line(self.screen, (50, 50, 50), 
                           (start_x, start_y), (end_x, end_y), 3)
            
        # Muzzle flash at barrel end
        if self.muzzle_flash_timer > 0:
            flash_size = 50 + random.randint(-10, 10)
            flash_surface = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
            
            # Multiple flash layers for better effect
            for i in range(3):
                size = flash_size - i * 15
                alpha = 200 - i * 50
                color = (255, 255 - i * 30, 200 - i * 60, alpha)
                pygame.draw.circle(flash_surface, color, 
                                 (flash_size, flash_size), size)
            
            self.screen.blit(flash_surface, 
                           (barrel_end_x - flash_size, barrel_end_y - flash_size))
            
        # Update tracer start position
        self._gun_position = (barrel_end_x, barrel_end_y)
            
    def draw_explosions(self):
        """Draw explosion effects."""
        for explosion in self.explosions:
            # Only draw expanding circle for actual explosions (not fragments)
            if explosion["timer"] > 20:  # Full explosions have timer of 30
                radius = (30 - explosion["timer"]) * 3
                if radius > 0:
                    pygame.draw.circle(self.screen, (255, 200, 0), 
                                     (explosion["x"], explosion["y"]), radius, 3)
                
            # Draw particles
            for particle in explosion["particles"]:
                # Check if it's a fragment (has size attribute) or explosion particle
                if "size" in particle:
                    # Draw fragment
                    size = particle["size"]
                    if size > 0 and particle["life"] > 0:
                        # Fade out based on life
                        alpha = int(255 * (particle["life"] / 20))
                        color = particle["color"]
                        
                        # Draw as small rectangle fragments
                        fragment_rect = pygame.Rect(
                            int(particle["x"]) - size // 2,
                            int(particle["y"]) - size // 2,
                            size, size
                        )
                        pygame.draw.rect(self.screen, color, fragment_rect)
                else:
                    # Original explosion particle drawing
                    size = particle["life"] // 5
                    if size > 0:
                        pygame.draw.circle(self.screen, particle["color"], 
                                         (int(particle["x"]), int(particle["y"])), size)
                                     
    def draw_bullet_tracers(self):
        """Draw bullet tracer effects."""
        for tracer in self.bullet_tracers:
            alpha = tracer["timer"] * 25
            
            # Draw multiple lines for a thicker, more visible tracer
            # Main tracer line (bright yellow/orange)
            pygame.draw.line(self.screen, (255, 200, 100), 
                           (tracer["start_x"], tracer["start_y"]),
                           (tracer["end_x"], tracer["end_y"]), 3)
            
            # Outer glow (slightly transparent)
            if tracer["timer"] > 5:
                pygame.draw.line(self.screen, (255, 150, 50), 
                               (tracer["start_x"], tracer["start_y"]),
                               (tracer["end_x"], tracer["end_y"]), 5)
                               
            # Inner hot core
            pygame.draw.line(self.screen, (255, 255, 200), 
                           (tracer["start_x"], tracer["start_y"]),
                           (tracer["end_x"], tracer["end_y"]), 1)
                           
    def draw_crosshair(self):
        """Draw targeting crosshair."""
        # Crosshair lines
        size = 30
        gap = 10
        
        # Horizontal lines
        pygame.draw.line(self.screen, (0, 255, 0), 
                        (self.crosshair_x - size, self.crosshair_y),
                        (self.crosshair_x - gap, self.crosshair_y), 2)
        pygame.draw.line(self.screen, (0, 255, 0), 
                        (self.crosshair_x + gap, self.crosshair_y),
                        (self.crosshair_x + size, self.crosshair_y), 2)
                        
        # Vertical lines
        pygame.draw.line(self.screen, (0, 255, 0), 
                        (self.crosshair_x, self.crosshair_y - size),
                        (self.crosshair_x, self.crosshair_y - gap), 2)
        pygame.draw.line(self.screen, (0, 255, 0), 
                        (self.crosshair_x, self.crosshair_y + gap),
                        (self.crosshair_x, self.crosshair_y + size), 2)
                        
        # Center dot
        pygame.draw.circle(self.screen, (0, 255, 0), 
                         (self.crosshair_x, self.crosshair_y), 2)
                         
    def draw_hud(self):
        """Draw heads-up display."""
        # Draw ammo counter
        font = pygame.font.Font(None, 36)
        ammo_text = font.render(f"AMMO: {self.ammo}", True, (0, 255, 0))
        self.screen.blit(ammo_text, (WIDTH - 200, HEIGHT - 50))
        
        # Draw altitude
        if self.phase in ["descent", "active"]:
            alt_text = font.render(f"ALT: {int(self.altitude)}ft", True, (0, 255, 0))
            self.screen.blit(alt_text, (WIDTH - 200, HEIGHT - 90))
            
        # Draw phase indicator
        phase_text = ""
        if self.phase == "takeoff":
            phase_text = "TAKING OFF..."
        elif self.phase == "descent":
            phase_text = "DESCENDING..."
        elif self.phase == "complete":
            phase_text = "MISSION COMPLETE"
            
        if phase_text:
            text = font.render(phase_text, True, (255, 255, 0))
            rect = text.get_rect(center=(WIDTH // 2, 50))
            self.screen.blit(text, rect)