"""
Chopper Gunner Mode FINAL
First-person helicopter minigun gameplay
"""

import pygame
import math
import random
from config import *

class ChopperGunnerMode:
    def __init__(self, screen, assets, board, game=None):
        self.screen = screen
        self.assets = assets
        self.board = board
        self.game = game  # Reference to game for volume control
        self.active = False
        self.phase = "approach"  # approach, descent, active, complete
        self.phase_timer = 0
        
        # Camera properties
        self.altitude = 300  # Start at combat altitude
        self.target_altitude = 300  # Combat altitude
        self.camera_shake = {"x": 0, "y": 0, "intensity": 0}
        
        # Camera rotation for circling
        self.camera_angle = 0  # Angle for side-to-side movement
        self.camera_tilt = 55  # Slightly less steep to see your pieces
        self.camera_distance = 650  # Increased to see some of your pieces
        self.camera_bank = 0  # Banking angle (leaning into turns)
        self.prev_camera_angle = 0  # To calculate angular velocity
        self.sine_offset = 0  # Initialize sine offset for smooth transition
        
        # Simple zoom in effect
        self.zoom_scale = 0.3  # Start zoomed out
        self.target_zoom = 1.0  # Target zoom level
        
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
        self.board_center_y = HEIGHT // 2 + 120  # Adjusted to show some of your pieces at bottom
        self.board_scale = 1.0
        
        # Weather effects
        self.rain_particles = []
        self.lightning_flash = 0
        self.next_lightning = pygame.time.get_ticks() + random.randint(5000, 15000)
        self.thunder_delay = 0
        self.clouds = []
        
        # Fighter jets
        self.fighter_jets = []
        self.next_jet_spawn = pygame.time.get_ticks() + random.randint(5000, 10000)  # First jet in 5-10 seconds
        self.jet_image = None
        
        # Try multiple ways to load the jet image
        if hasattr(assets, 'jet55'):
            self.jet_image = assets.jet55
            pass
        elif hasattr(assets, 'images') and 'jet55' in assets.images:
            self.jet_image = assets.images['jet55']
            pass
        elif hasattr(assets, 'jet_image'):
            self.jet_image = assets.jet_image
            pass
        else:
            # Try to load it directly if not in assets
            try:
                import os
                jet_path = os.path.join('assets', 'jet55.png')
                if os.path.exists(jet_path):
                    self.jet_image = pygame.image.load(jet_path).convert_alpha()
                    pass
                else:
                    pass
            except Exception as e:
                pass
                
        if self.jet_image is None:
            pass
        
        # Initialize rain (reasonable amount)
        # Initialize rain particles
        for _ in range(150):  # Reduced from 500 to 150
            particle = {
                "x": random.randint(-50, WIDTH + 50),
                "y": random.randint(-200, HEIGHT),  # Start distributed across screen
                "speed": random.randint(20, 30),  # Moderate speed
                "length": random.randint(20, 35),  # Shorter streaks
                "wind": random.uniform(-2, -4)  # Less wind
            }
            self.rain_particles.append(particle)
        pass
        
        # Rain particles initialized
            
        # Initialize clouds
        for _ in range(5):
            self.clouds.append({
                "x": random.randint(-200, WIDTH + 200),
                "y": random.randint(50, 200),
                "width": random.randint(300, 600),
                "height": random.randint(100, 200),
                "speed": random.uniform(0.5, 1.5),
                "darkness": random.uniform(0.3, 0.6)
            })
        
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
        self.phase = "approach"  # Start with approach
        self.phase_timer = pygame.time.get_ticks()
        
        # Start zoomed out
        self.zoom_scale = 0.3
        self.target_zoom = 1.0
        
        # Starting chopper gunner mode
        
        # Apply SFX volume to sounds before playing
        if self.game and hasattr(self.game, 'sfx_volume'):
            sfx_vol = self.game.sfx_volume
            if self.helicopter_sound:
                self.helicopter_sound.set_volume(sfx_vol * 0.4)
            if self.helicopter_blade_sound:
                self.helicopter_blade_sound.set_volume(sfx_vol * 0.5)
            if self.minigun_revup_sound:
                self.minigun_revup_sound.set_volume(sfx_vol * 0.4)
            if self.minigun_fire_sound:
                self.minigun_fire_sound.set_volume(sfx_vol * 0.3)
            if self.minigun_spindown_sound:
                self.minigun_spindown_sound.set_volume(sfx_vol * 0.4)
        
        # Start helicopter sounds
        if self.helicopter_sound:
            self.helicopter_sound.play(-1)  # Loop
            pass
        # Play blade sound if available
        if self.helicopter_blade_sound:
            self.helicopter_blade_sound.play(-1)  # Loop the blade sound
            pass
        else:
            pass
            
    def stop(self):
        """End chopper gunner mode."""
        self.active = False
        
        # Fade out sounds gradually if they exist
        if self.helicopter_sound:
            self.helicopter_sound.fadeout(500)  # 0.5 second fadeout
        if self.helicopter_blade_sound:
            self.helicopter_blade_sound.fadeout(500)
            
        # Stop any minigun sounds
        if self.minigun_fire_channel:
            self.minigun_fire_channel.stop()
        self.minigun_state = "idle"
            
    def handle_mouse(self, pos):
        """Update crosshair position."""
        self.crosshair_x, self.crosshair_y = pos
        
    def handle_click(self, pos):
        """Handle firing."""
        if self.phase == "active":  # Unlimited ammo
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
        
        # Update weather effects
        self.update_weather(current_time)
        
        # Update fighter jets
        self.update_fighter_jets(current_time)
        
        # Update hover time for movement calculations
        self.hover_time = current_time / 1000.0  # Convert to seconds
        self.vibration_time = current_time / 100.0  # Faster for vibration
        
        # Update phase
        if self.phase == "approach":
            elapsed = current_time - self.phase_timer
            approach_duration = 4000  # 4 seconds to zoom in (doubled from 2)
            
            if elapsed < approach_duration:
                # Simple zoom in effect
                progress = elapsed / approach_duration
                # Smooth easing - even smoother curve
                eased_progress = 1 - math.pow(1 - progress, 4)  # Changed to quartic for smoother effect
                self.zoom_scale = 0.3 + (0.7 * eased_progress)
                
                # Gradually start rotating in the last 25% of approach
                if progress > 0.75:
                    rotation_progress = (progress - 0.75) / 0.25  # 0 to 1 in last quarter
                    
                    # Use a sine-based rotation that will match the active phase pattern
                    # This ensures continuity when switching phases
                    transition_time = self.hover_time * 0.3
                    
                    # Start with small amplitude that grows
                    amplitude = 30 * rotation_progress * rotation_progress
                    self.camera_angle = math.sin(transition_time) * amplitude
                    
                    # Store the sine offset that makes this work
                    self.sine_offset = 0  # We're already using hover_time directly
                    
                    # Start introducing banking based on actual movement
                    if hasattr(self, 'prev_camera_angle'):
                        angle_change = self.camera_angle - self.prev_camera_angle
                        target_bank = angle_change * 5 * rotation_progress
                        self.camera_bank += (target_bank - self.camera_bank) * 0.1
                    self.prev_camera_angle = self.camera_angle
            else:
                # Move to active phase
                self.phase = "active"
                self.phase_timer = current_time
                self.zoom_scale = 1.0
                # No need to recalculate - we're already in sync
                
        elif self.phase == "active":
            # Update camera rotation for side-to-side movement
            self.prev_camera_angle = self.camera_angle
            
            # Side-to-side movement - continue the exact same sine wave pattern
            # No offset needed since we're already using hover_time directly
            self.camera_angle = math.sin(self.hover_time * 0.3) * 30  # ±30 degrees side to side
            
            # Calculate banking based on movement direction
            # Bank into the turn
            angle_change = self.camera_angle - self.prev_camera_angle
            target_bank = angle_change * 5  # Scale banking with turn rate
            
            # Smoothly interpolate to target bank angle
            bank_smoothing = 0.1
            self.camera_bank += (target_bank - self.camera_bank) * bank_smoothing
            
            # Update minigun sound state
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
            if self.firing and self.minigun_state == "firing":  # Unlimited ammo
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
            # Keep hovering and rotating during the complete phase
            # Continue the orbital rotation during victory
            self.prev_camera_angle = self.camera_angle
            self.camera_angle = math.sin(self.hover_time * 0.3) * 30  # Keep rotating
            
            # Calculate banking based on movement direction
            angle_change = self.camera_angle - self.prev_camera_angle
            target_bank = angle_change * 5
            bank_smoothing = 0.1
            self.camera_bank += (target_bank - self.camera_bank) * bank_smoothing
            
            # Let it run longer if game is won
            exit_delay = 5000 if self.board.game_over and self.board.winner == "white" else 2000
            if current_time - self.phase_timer > exit_delay:
                # Don't stop here - let the game.py handle it after fade is complete
                pass  # Will be stopped by game.py
                
        # Update movement calculations - always apply some movement
        # Add realistic helicopter movement - MODERATE SHAKE
        # Vertical bobbing (moderate)
        self.hover_offset_y = math.sin(self.hover_time * 0.8) * 10  # Reduced from 15
        
        # Horizontal swaying (moderate)
        self.sway_offset_x = math.sin(self.hover_time * 0.6) * 7  # Reduced from 10
        
        # Constant engine vibration - MODERATE
        vibration_x = math.sin(self.vibration_time * 25) * 2  # Reduced from 3
        vibration_y = math.cos(self.vibration_time * 28) * 2  # Reduced from 3
        
        # Add secondary high-frequency vibration for that helicopter feel
        vibration_x += math.sin(self.vibration_time * 45) * 1
        vibration_y += math.cos(self.vibration_time * 48) * 1
        
        # Random turbulence system - moderate
        if random.random() < 0.015:  # 1.5% chance (slightly less frequent)
            # Set new target with moderate variation
            self.target_turbulence_x = random.uniform(-5, 5)  # Reduced from -8,8
            self.target_turbulence_y = random.uniform(-5, 5)
        else:
            # Gradually move target back to zero
            self.target_turbulence_x *= 0.98
            self.target_turbulence_y *= 0.98
            
        # Smoothly interpolate current turbulence toward target
        turbulence_smoothing = 0.06  # Slightly slower for smoother movement
        self.turbulence_x += (self.target_turbulence_x - self.turbulence_x) * turbulence_smoothing
        self.turbulence_y += (self.target_turbulence_y - self.turbulence_y) * turbulence_smoothing
        
        # Add vibration to turbulence
        self.turbulence_x += vibration_x
        self.turbulence_y += vibration_y
        
        # Add occasional "bumps" from air pockets (less frequent)
        if random.random() < 0.007:  # 0.7% chance per frame
            bump_x = random.uniform(-3, 3)
            bump_y = random.uniform(-3, 3)
            self.turbulence_x += bump_x
            self.turbulence_y += bump_y
                
        # Update visual effects
        self.update_explosions()
        self.update_bullet_tracers()
        self.update_camera_shake()
        self.update_piece_shake()
        
    def fire_minigun(self):
        """Fire the minigun."""
        # Unlimited ammo - no decrement
        self.muzzle_flash_timer = 5
        
        # Camera shake - moderate when firing
        self.camera_shake["intensity"] = 6  # Reduced from 8
        
        # Add moderate recoil movement
        self.target_turbulence_x += random.uniform(-2, 2)
        self.target_turbulence_y += random.uniform(-1.5, 0.5)  # Moderate upward kick
        
        # Keep targets reasonable
        self.target_turbulence_x = max(-7, min(7, self.target_turbulence_x))
        self.target_turbulence_y = max(-7, min(7, self.target_turbulence_y))
        
        # Get helicopter bottom center position (where bullets come from)
        heli_x = WIDTH // 2
        heli_y = HEIGHT - 100  # Bottom of screen, helicopter position
            
        # Add bullet tracer from helicopter to crosshair
        self.bullet_tracers.append({
            "start_x": heli_x,
            "start_y": heli_y,
            "end_x": self.crosshair_x,
            "end_y": self.crosshair_y,
            "timer": 10,
            "ricochet": random.random() < 0.15  # 15% chance of ricochet
        })
        
        # Create bullet impact effects at crosshair location
        self.create_bullet_impact(self.crosshair_x, self.crosshair_y)
        
        # Check for hit
        hit_piece = self.check_hit(self.crosshair_x, self.crosshair_y)
        if hit_piece:
            self.hit_piece(hit_piece)
            
        # Check for hitting jets
        self.check_jet_hit(self.crosshair_x, self.crosshair_y)
            
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
        
    def check_jet_hit(self, x, y):
        """Check if crosshair is over a jet."""
        for jet in self.fighter_jets[:]:  # Copy list to allow removal during iteration
            # Calculate jet bounds (simple rectangle check)
            jet_width = 150 * (1.0 - (jet["altitude"] / 300.0))  # Size based on altitude
            jet_height = 150 * (1.0 - (jet["altitude"] / 300.0))
            
            # Check if crosshair is within jet bounds
            if (abs(x - jet["x"]) < jet_width // 2 and 
                abs(y - jet["y"]) < jet_height // 2):
                # Hit! Create explosion
                self.create_jet_explosion(jet["x"], jet["y"])
                # Remove the jet
                self.fighter_jets.remove(jet)
                # Award bonus ammo
                self.ammo += 10
                # Play explosion sound if available
                if 'bomb' in self.assets.sounds:
                    self.assets.sounds['bomb'].play()
                return True
        return False
        
    def create_jet_explosion(self, x, y):
        """Create explosion effect for destroyed jet."""
        # Create large explosion
        self.explosions.append({
            "x": x,
            "y": y,
            "timer": 40,  # Longer duration
            "particles": self.create_jet_explosion_particles(x, y)
        })
        
        # Add camera shake
        self.camera_shake["intensity"] = 12
        
    def create_jet_explosion_particles(self, x, y):
        """Create explosion particles for jet destruction."""
        particles = []
        # More particles for bigger explosion
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 12)
            particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 40,
                "color": random.choice([
                    (255, 200, 0),
                    (255, 150, 0),
                    (255, 100, 0),
                    (255, 50, 0),
                    (200, 50, 0),
                    (150, 30, 0)
                ])
            })
        # Add some debris particles
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 15)
            particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 3,  # Upward bias
                "life": 50,
                "size": random.randint(3, 8),
                "color": random.choice([
                    (80, 80, 80),   # Grey metal
                    (60, 60, 60),   # Dark metal
                    (100, 100, 100) # Light metal
                ])
            })
        return particles
        
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
        # Fixed calculation to prevent stretching during descent
        altitude_factor = self.altitude / 1000.0  # Normalize altitude (0 to 1)
        altitude_factor = max(0.3, min(1.0, altitude_factor))  # Clamp
        
        # Use fixed perspective that doesn't change dramatically with altitude
        base_distance = 400
        depth_factor = max(0.1, base_distance / (base_distance + projected_z * 30))
        perspective_scale = depth_factor * 0.85  # Fixed scale
        
        # Apply zoom scale
        perspective_scale *= self.zoom_scale
        
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
        
        # Apply zoom scale
        size_factor = 0.6 + y_normalized * 0.4  # Size varies from 60% to 100%
        
        return int(base_size * size_factor * self.zoom_scale)
        
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
        
    def update_weather(self, current_time):
        """Update weather effects."""
        # Update rain particles
        for particle in self.rain_particles:
            particle["y"] += particle["speed"]
            particle["x"] += particle["wind"]
            
            # Reset rain that goes off screen
            if particle["y"] > HEIGHT:
                particle["y"] = random.randint(-100, -50)
                particle["x"] = random.randint(-50, WIDTH + 50)
            if particle["x"] < -50:
                particle["x"] = WIDTH + 50
            elif particle["x"] > WIDTH + 50:
                particle["x"] = -50
                
        # Handle lightning
        if current_time >= self.next_lightning:
            self.lightning_flash = 15  # Flash duration in frames
            self.thunder_delay = random.randint(500, 2000)  # Delay before thunder
            self.next_lightning = current_time + random.randint(8000, 20000)
            
            # Add moderate turbulence during lightning
            self.target_turbulence_x += random.uniform(-10, 10)
            self.target_turbulence_y += random.uniform(-10, 10)
            
        # Decay lightning flash
        if self.lightning_flash > 0:
            self.lightning_flash -= 1
            
    def update_fighter_jets(self, current_time):
        """Update fighter jet spawning and movement."""
        # Spawn new jets
        if current_time >= self.next_jet_spawn and self.phase == "active":
            # Decide on jet path
            if random.random() < 0.5:
                # Left to right
                start_x = -200
                end_x = WIDTH + 200
                direction = 1
            else:
                # Right to left
                start_x = WIDTH + 200
                end_x = -200
                direction = -1
            
            # Random altitude (appears below helicopter)
            altitude = random.randint(50, 150)  # How far below helicopter
            
            # Random path across screen
            start_y = random.randint(HEIGHT // 3, HEIGHT - 200)
            
            # Create jet
            jet = {
                "x": start_x,
                "y": start_y,
                "start_x": start_x,
                "end_x": end_x,
                "direction": direction,
                "speed": random.uniform(8, 12),  # Fast!
                "altitude": altitude,
                "angle": 0 if direction > 0 else 180,  # Face direction of travel
                "trail": [],  # Vapor trail positions
                "wobble": random.uniform(0, math.pi * 2)  # Starting phase for sine wobble
            }
            
            self.fighter_jets.append(jet)
            
            # Schedule next jet
            self.next_jet_spawn = current_time + random.randint(8000, 15000)
            
            # Play jet sound if available
            if hasattr(self.assets, 'sounds') and 'jet_flyby' in self.assets.sounds:
                self.assets.sounds['jet_flyby'].play()
        
        # Update existing jets
        jets_to_remove = []
        for jet in self.fighter_jets:
            # Move jet
            jet["x"] += jet["speed"] * jet["direction"]
            
            # Add slight sine wave movement for realism
            jet["wobble"] += 0.1
            jet["y"] += math.sin(jet["wobble"]) * 0.5
            
            # Update vapor trail
            jet["trail"].append({"x": jet["x"], "y": jet["y"], "life": 30})
            
            # Keep only recent trail positions
            jet["trail"] = [t for t in jet["trail"] if t["life"] > 0]
            for trail_point in jet["trail"]:
                trail_point["life"] -= 1
            
            # Remove if off screen
            if jet["direction"] > 0 and jet["x"] > jet["end_x"]:
                jets_to_remove.append(jet)
            elif jet["direction"] < 0 and jet["x"] < jet["end_x"]:
                jets_to_remove.append(jet)
        
        # Remove jets that have flown off screen
        for jet in jets_to_remove:
            self.fighter_jets.remove(jet)
            
    def draw_fighter_jets(self):
        """Draw fighter jets flying below the helicopter."""
        for jet in self.fighter_jets:
            # Draw vapor trail first (behind jet)
            for i, trail_point in enumerate(jet["trail"]):
                if trail_point["life"] > 0:
                    # Fade out trail over time
                    alpha = trail_point["life"] / 30.0
                    size = int(3 * alpha)
                    if size > 0:
                        color = (
                            int(200 + 55 * alpha),  # R
                            int(200 + 55 * alpha),  # G 
                            int(200 + 55 * alpha)   # B
                        )
                        pygame.draw.circle(self.screen, color, 
                                         (int(trail_point["x"]), int(trail_point["y"])), size)
            
            # Calculate size based on altitude (perspective)
            # Jets at higher altitude (smaller number) appear larger
            size_factor = 1.0 - (jet["altitude"] / 300.0)
            size_factor = max(0.3, min(1.0, size_factor))
            
            # Draw jet
            if self.jet_image:
                # Scale jet based on altitude - INCREASED SIZE
                jet_width = int(150 * size_factor)  # Increased from 80 to 150
                jet_height = int(150 * size_factor)  # Increased from 80 to 150
                
                scaled_jet = pygame.transform.scale(self.jet_image, (jet_width, jet_height))
                
                # The jet image is oriented vertically (facing up), so rotate it to face horizontally
                if jet["direction"] > 0:
                    # Moving right - rotate 90 degrees clockwise
                    scaled_jet = pygame.transform.rotate(scaled_jet, -90)
                else:
                    # Moving left - rotate 90 degrees counter-clockwise
                    scaled_jet = pygame.transform.rotate(scaled_jet, 90)
                
                # Add slight tilt based on movement
                tilt_angle = math.sin(jet["wobble"]) * 5  # Slight banking
                if abs(tilt_angle) > 0.1:
                    scaled_jet = pygame.transform.rotate(scaled_jet, tilt_angle)
                
                # Draw with slight transparency for distance
                scaled_jet.set_alpha(int(255 * (0.7 + 0.3 * size_factor)))
                
                jet_rect = scaled_jet.get_rect(center=(int(jet["x"]), int(jet["y"])))
                self.screen.blit(scaled_jet, jet_rect)
            else:
                # Fallback: draw as triangle if no image - ALSO INCREASED
                jet_size = int(40 * size_factor)  # Increased from 20 to 40
                points = []
                if jet["direction"] > 0:
                    # Pointing right
                    points = [
                        (jet["x"] - jet_size, jet["y"]),
                        (jet["x"] + jet_size, jet["y"]),
                        (jet["x"], jet["y"] - jet_size // 2),
                        (jet["x"], jet["y"] + jet_size // 2)
                    ]
                else:
                    # Pointing left
                    points = [
                        (jet["x"] + jet_size, jet["y"]),
                        (jet["x"] - jet_size, jet["y"]),
                        (jet["x"], jet["y"] - jet_size // 2),
                        (jet["x"], jet["y"] + jet_size // 2)
                    ]
                
                pygame.draw.polygon(self.screen, (100, 100, 120), points)
                
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
        # Draw parallax background with rotation
        self.draw_rotating_parallax_background()
        
        # Draw board and pieces from aerial view
        self.draw_aerial_board()
        
        # Draw fighter jets (below helicopter, above ground)
        self.draw_fighter_jets()
        
        # Draw effects (before rain so explosions appear under rain)
        self.draw_explosions()
        self.draw_bullet_tracers()
        
        # Draw rain BEFORE cockpit so it appears outside
        self.draw_rain()
        
        # Draw lightning flash
        if self.lightning_flash > 0:
            flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = int(50 * (self.lightning_flash / 15))
            flash_surface.fill((255, 255, 255, alpha))
            self.screen.blit(flash_surface, (0, 0))
        
        # Draw cockpit overlay AFTER rain so cockpit blocks rain
        if self.cockpit_overlay:
            # Add subtle shake effect (increased slightly)
            current_time = pygame.time.get_ticks()
            shake_x = math.sin(current_time * 0.003) * 3 + math.sin(current_time * 0.007) * 2
            shake_y = math.cos(current_time * 0.004) * 3 + math.cos(current_time * 0.006) * 2
            
            # Increase shake when firing
            if self.firing:  # Unlimited ammo
                shake_x += random.randint(-3, 3)
                shake_y += random.randint(-3, 3)
            
            # Create a copy of the cockpit overlay to apply lighting effects
            lit_cockpit = self.cockpit_overlay.copy()
            
            # Apply red cockpit lighting to the cockpit image
            self.apply_cockpit_lighting(lit_cockpit, current_time)
            
            # Fill only the exposed edges with black when shaking
            if shake_x > 0:
                pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, int(shake_x), HEIGHT))
            if shake_x < 0:
                pygame.draw.rect(self.screen, (0, 0, 0), (WIDTH + int(shake_x), 0, -int(shake_x), HEIGHT))
            if shake_y > 0:
                pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, WIDTH, int(shake_y)))
            if shake_y < 0:
                pygame.draw.rect(self.screen, (0, 0, 0), (0, HEIGHT + int(shake_y), WIDTH, -int(shake_y)))
            
            self.screen.blit(lit_cockpit, (int(shake_x), int(shake_y)))
        
        # Draw crosshair
        self.draw_crosshair()
        
        # Draw HUD
        self.draw_hud()
        
        # Add fade to black when in complete phase
        if self.phase == "complete":
            current_time = pygame.time.get_ticks()
            time_in_phase = current_time - self.phase_timer
            
            # Start fade later if victory (2.5 seconds of victory airtime before fade)
            fade_start_delay = 2500 if (self.board.game_over and self.board.winner == "white") else 500
            fade_duration = 2000  # 2 seconds fade for smoother transition
            
            if time_in_phase > fade_start_delay:
                fade_time = time_in_phase - fade_start_delay
                
                if fade_time < fade_duration:
                    # Fade to black
                    fade_alpha = int((fade_time / fade_duration) * 255)
                    fade_surface = pygame.Surface((WIDTH, HEIGHT))
                    fade_surface.fill((0, 0, 0))
                    fade_surface.set_alpha(fade_alpha)
                    self.screen.blit(fade_surface, (0, 0))
                else:
                    # Full black
                    self.screen.fill((0, 0, 0))
        
    def draw_rotating_parallax_background(self):
        """Draw parallax background that rotates with the helicopter."""
        # Dark stormy sky
        self.screen.fill((15, 15, 25))  # Very dark blue-grey
        
        # Draw storm clouds
        for cloud in self.clouds:
            # Multiple layers for cloud depth
            for i in range(3):
                cloud_surface = pygame.Surface((cloud["width"], cloud["height"]), pygame.SRCALPHA)
                alpha = int(100 * cloud["darkness"] * (1 - i * 0.3))
                gray = 30 + i * 10
                cloud_surface.fill((gray, gray, gray + 5, alpha))
                
                # Draw cloud shape with circles
                for _ in range(10):
                    circle_x = random.randint(0, cloud["width"])
                    circle_y = random.randint(0, cloud["height"])
                    circle_r = random.randint(cloud["height"] // 4, cloud["height"] // 2)
                    pygame.draw.circle(cloud_surface, (gray, gray, gray + 5, alpha), 
                                     (circle_x, circle_y), circle_r)
                
                self.screen.blit(cloud_surface, (int(cloud["x"]), int(cloud["y"]) - i * 10))
        
        # Update cloud positions
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"]
            if cloud["x"] > WIDTH + 200:
                cloud["x"] = -cloud["width"]
                cloud["y"] = random.randint(50, 200)
                
    def draw_aerial_board(self):
        """Draw the chess board from aerial perspective with rotation."""
        # Draw ground/terrain first (before the board)
        self.draw_ground_terrain()
        
        # Calculate board bounds for proper 3D positioning
        board_y_min = float('inf')
        board_y_max = float('-inf')
        
        # First pass: determine the vertical bounds of the board
        for row in range(8):
            for col in range(8):
                _, y = self.get_piece_screen_pos(row, col)
                board_y_min = min(board_y_min, y)
                board_y_max = max(board_y_max, y)
        
        # Draw board squares with rotation and perspective
        for row in range(8):
            for col in range(8):
                # Get screen position with rotation
                x, y = self.get_piece_screen_pos(row, col)
                size = self.get_piece_size(row, col)
                
                # Skip squares that are behind the camera
                if y < -100:
                    continue
                
                # Alternate square colors - darker for stormy atmosphere
                if (row + col) % 2 == 0:
                    color = (120, 100, 80)  # Darker light squares
                else:
                    color = (60, 50, 40)    # Much darker dark squares
                    
                # Calculate the four corners of the square with perspective
                corners = []
                for dr, dc in [(0, 0), (1, 0), (1, 1), (0, 1)]:
                    corner_x, corner_y = self.get_piece_screen_pos(row + dr - 0.5, col + dc - 0.5)
                    corners.append((corner_x, corner_y))
                
                # Draw the square as a polygon for proper perspective
                if len(corners) == 4:
                    pygame.draw.polygon(self.screen, color, corners)
                    pygame.draw.polygon(self.screen, (40, 40, 40), corners, 1)  # Darker border
        
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
            
    def draw_ground_terrain(self):
        """Draw ground terrain with trees and other objects."""
        # Horizon position based on altitude - moves up as we descend
        # At altitude 300 (combat), horizon should be off screen
        # At altitude 800+ (approach), horizon should be visible
        altitude_factor = (self.altitude - 300) / 500  # 0 at combat altitude, 1 at high altitude
        altitude_factor = max(0, min(1, altitude_factor))  # Clamp between 0 and 1
        
        # Horizon starts at 25% when high, moves to -10% (off screen) when low
        horizon_y = int(HEIGHT * (0.25 - 0.35 * (1 - altitude_factor)))
        
        # Draw dark ground gradient
        for y in range(max(0, horizon_y), HEIGHT):
            progress = (y - horizon_y) / (HEIGHT - horizon_y) if HEIGHT > horizon_y else 0
            progress = max(0, min(1, progress))  # Clamp progress
            # Much darker ground for nighttime
            color = (
                int(10 + progress * 10),   # R: 10 to 20
                int(12 + progress * 10),   # G: 12 to 22
                int(8 + progress * 8)      # B: 8 to 16
            )
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        
        # Draw trees around the battlefield
        tree_positions = [
            # Trees arranged in a circle around the board
            (-5, -5), (-3, -5), (0, -5), (3, -5), (5, -5),
            (-5, -3), (5, -3),
            (-5, 0), (5, 0),
            (-5, 3), (5, 3),
            (-5, 5), (-3, 5), (0, 5), (3, 5), (5, 5),
            # Additional trees further out
            (-7, -7), (7, -7), (-7, 7), (7, 7),
            (-8, 0), (8, 0), (0, -8), (0, 8)
        ]
        
        # Sort trees by distance from camera for proper depth ordering
        angle_rad = math.radians(self.camera_angle)
        trees_with_depth = []
        
        for tree_x, tree_z in tree_positions:
            # Apply rotation based on camera angle
            rotated_x = tree_x * math.cos(angle_rad) - tree_z * math.sin(angle_rad)
            rotated_z = tree_x * math.sin(angle_rad) + tree_z * math.cos(angle_rad)
            
            # Trees are at ground level (y = 0 in 3D space)
            trees_with_depth.append((rotated_z, tree_x, tree_z, rotated_x, rotated_z))
        
        # Sort by depth (farther trees first)
        trees_with_depth.sort(key=lambda t: -t[0])
        
        # Draw trees
        for _, orig_x, orig_z, rotated_x, rotated_z in trees_with_depth:
            self.draw_tree(orig_x, orig_z, rotated_x, rotated_z)
            
    def draw_tree(self, grid_x, grid_z, rotated_x, rotated_z):
        """Draw a single tree with proper 3D perspective."""
        # Trees are positioned at same level as board base
        tree_y = 0  # Same level as board
        
        # Apply camera tilt and perspective
        tilt_rad = math.radians(self.camera_tilt)
        
        # Project 3D position to 2D screen - using similar math to original perspective
        projected_x = rotated_x
        projected_y = tree_y + rotated_z * math.sin(tilt_rad)
        projected_z = rotated_z * math.cos(tilt_rad)
        
        # Apply perspective based on depth
        altitude_scale = 1.0 - (self.altitude - self.target_altitude) / 1500.0
        altitude_scale = max(0.4, min(1.0, altitude_scale))
        
        # Perspective calculation with camera distance
        perspective_scale = (self.camera_distance / (self.camera_distance + projected_z * 50)) * 0.85
        
        # Apply zoom scale
        perspective_scale *= self.zoom_scale
        
        # Screen position
        screen_x = self.board_center_x + projected_x * 100 * perspective_scale
        screen_y = self.board_center_y - projected_y * 100 * perspective_scale
        
        # Apply helicopter movement
        screen_x += self.sway_offset_x + self.turbulence_x
        screen_y += self.hover_offset_y + self.turbulence_y
        
        # Apply camera shake
        screen_x += self.camera_shake["x"]
        screen_y += self.camera_shake["y"]
        
        # Skip if tree is behind camera or too far below screen
        # Allow trees to be drawn above the top of the screen
        if screen_y > HEIGHT + 100:
            return
        
        # Tree size based on perspective - scale with altitude for consistency
        tree_height = int(100 * perspective_scale)
        trunk_width = int(12 * perspective_scale)
        foliage_width = int(50 * perspective_scale)
        
        # Draw trunk (brown rectangle)
        trunk_height = int(tree_height * 0.4)
        trunk_x = int(screen_x - trunk_width // 2)
        trunk_y = int(screen_y - trunk_height)
        
        # Only draw trunk if it's visible on screen
        if trunk_height > 0 and trunk_width > 0:
            # Darker trunk colors for stormy weather
            pygame.draw.rect(self.screen, (40, 30, 20), 
                            (trunk_x, trunk_y, trunk_width, trunk_height))
            pygame.draw.rect(self.screen, (30, 20, 15), 
                            (trunk_x, trunk_y, trunk_width, trunk_height), 1)
        
        # Draw foliage (green circles/triangles)
        foliage_y = trunk_y
        foliage_height = int(tree_height * 0.6)
        
        # Draw three overlapping circles for foliage
        if foliage_width > 10:  # Only draw if big enough
            for i in range(3):
                circle_y = foliage_y - i * (foliage_height // 3)
                circle_radius = foliage_width // 2 - i * 5
                
                # Draw circles even if they're above the horizon
                if circle_radius > 0:
                    # Darker green for stormy atmosphere
                    green_variation = (15 + i * 5, 25 + i * 5, 15)
                    pygame.draw.circle(self.screen, green_variation, 
                                     (int(screen_x), int(circle_y)), circle_radius)
                    
        # Add a simple shadow on the ground
        shadow_width = int(foliage_width * 0.8)
        shadow_height = int(shadow_width * 0.3)
        if shadow_width > 5 and shadow_height > 2 and screen_y < HEIGHT:
            shadow_surface = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, 50), 
                               (0, 0, shadow_width, shadow_height))
            self.screen.blit(shadow_surface, 
                            (int(screen_x - shadow_width // 2), int(screen_y)))
                        
    def draw_piece_aerial(self, row, col, piece):
        """Draw a single piece from aerial view using actual piece images."""
        x, y = self.get_piece_screen_pos(row, col)
        size = self.get_piece_size(row, col)
        
        # Use actual piece images if available
        if hasattr(self.assets, 'pieces') and piece in self.assets.pieces:
            piece_image = self.assets.pieces[piece]
            # Scale the piece image based on perspective
            scaled_piece = pygame.transform.scale(piece_image, (size, size))
            
            # Create a darker version by adjusting the piece itself
            darkened_piece = scaled_piece.copy()
            darkened_piece.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_MULT)
            
            # Don't rotate the piece - just center it at the position
            rect = darkened_piece.get_rect(center=(x, y))
            self.screen.blit(darkened_piece, rect)
        else:
            # Fallback: Draw piece as a circle with letter if no image
            # Darker colors for stormy weather
            color = (100, 100, 100) if piece[0] == 'w' else (30, 30, 30)
            pygame.draw.circle(self.screen, color, (x, y), size // 2)
            pygame.draw.circle(self.screen, (50, 50, 50), (x, y), size // 2, 2)
            
            # Draw piece type letter
            if hasattr(self, 'font'):
                font = self.font
            else:
                self.font = pygame.font.Font(None, size // 2)
                font = self.font
                
            text = font.render(piece[1], True, 
                              (30, 30, 30) if piece[0] == 'w' else (100, 100, 100))
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)
            
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
            
            # Check if this is a ricochet
            if tracer.get("ricochet", False):
                # Calculate ricochet from the impact point
                if tracer["timer"] < 8:  # Start ricochet effect
                    progress = 1 - (tracer["timer"] / 10)
                    
                    # Ricochet starts from the end point (impact)
                    start_x = tracer["end_x"]
                    start_y = tracer["end_y"]
                    
                    # Ricochet upward and to the side
                    ricochet_angle = tracer.get("ricochet_angle", random.uniform(-45, 45))
                    tracer["ricochet_angle"] = ricochet_angle  # Store angle for consistency
                    
                    ricochet_distance = progress * 150
                    end_x = start_x + math.cos(math.radians(ricochet_angle)) * ricochet_distance
                    end_y = start_y - ricochet_distance  # Goes up
                    
                    # Draw the ricochet part
                    pygame.draw.line(self.screen, (255, 150, 50), 
                                   (start_x, start_y), (end_x, end_y), 2)
                    
                    # Spark effect at impact point
                    if tracer["timer"] > 6:
                        pygame.draw.circle(self.screen, (255, 255, 150), 
                                         (tracer["end_x"], tracer["end_y"]), 5)
                
                # Draw the main tracer dimmer
                pygame.draw.line(self.screen, (150, 100, 50), 
                               (tracer["start_x"], tracer["start_y"]),
                               (tracer["end_x"], tracer["end_y"]), 2)
            else:
                # Normal tracer
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
        
        # Crosshair color - red tinted for night vision
        crosshair_color = (255, 100, 100)
        
        # Horizontal lines
        pygame.draw.line(self.screen, crosshair_color, 
                        (self.crosshair_x - size, self.crosshair_y),
                        (self.crosshair_x - gap, self.crosshair_y), 2)
        pygame.draw.line(self.screen, crosshair_color, 
                        (self.crosshair_x + gap, self.crosshair_y),
                        (self.crosshair_x + size, self.crosshair_y), 2)
                        
        # Vertical lines
        pygame.draw.line(self.screen, crosshair_color, 
                        (self.crosshair_x, self.crosshair_y - size),
                        (self.crosshair_x, self.crosshair_y - gap), 2)
        pygame.draw.line(self.screen, crosshair_color, 
                        (self.crosshair_x, self.crosshair_y + gap),
                        (self.crosshair_x, self.crosshair_y + size), 2)
                        
        # Center dot with slight glow
        pygame.draw.circle(self.screen, (255, 150, 150), 
                         (self.crosshair_x, self.crosshair_y), 3)
        pygame.draw.circle(self.screen, crosshair_color, 
                         (self.crosshair_x, self.crosshair_y), 2)
                         
    def draw_rain(self):
        """Draw rain effect."""
        # Draw rain particles with more subtle appearance
        for particle in self.rain_particles:
            # Rain color - slightly brighter for visibility at night
            rain_color = (120, 120, 150)
            
            # Draw rain streak
            start_x = int(particle["x"])
            start_y = int(particle["y"])
            end_x = int(particle["x"] + particle["wind"] * 2)
            end_y = int(particle["y"] + particle["length"])
            
            # Only draw if at least part of the line is on screen
            if end_y > 0 and start_y < HEIGHT and start_x > -50 and start_x < WIDTH + 50:
                # Draw thicker rain for more intensity
                pygame.draw.line(self.screen, rain_color, 
                                 (start_x, start_y), (end_x, end_y), 2)
                # Add slight glow to rain
                if random.random() < 0.1:  # 10% of rain drops have a slight shimmer
                    pygame.draw.line(self.screen, (150, 150, 180), 
                                     (start_x, start_y), (end_x, end_y), 1)
                               
    def draw_hud(self):
        """Draw heads-up display."""
        # Removed ammo and altitude display - unlimited ammo mode
            
        # Removed phase indicator display
            
    def apply_cockpit_lighting(self, cockpit_surface, current_time):
        """Apply realistic red lighting effects to the cockpit overlay."""
        # Create a lighting overlay
        lighting_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Smooth pulsing effect - more noticeable
        pulse = (math.sin(current_time * 0.002) + 1.0) * 0.5  # Varies smoothly between 0 and 1
        
        # Create a smooth vertical gradient using pygame's built-in gradient capabilities
        # Bottom section - bright console area
        bottom_section = pygame.Surface((WIDTH, HEIGHT // 2), pygame.SRCALPHA)
        
        # Removed all ambient glow - cockpit stays dark
        
        # Blit bottom section to main overlay
        lighting_overlay.blit(bottom_section, (0, HEIGHT // 2))
        
        # Removed console glow dot - only ambient lighting remains
        
        # Apply the lighting to the cockpit using additive blending
        cockpit_surface.blit(lighting_overlay, (0, 0), special_flags=pygame.BLEND_ADD)
