"""
Powerup System for Chess Game
Handles powerup logic, effects, and visual feedback
"""

import pygame
import random
import math
from config import *

class PowerupSystem:
    def __init__(self):
        # Player points (white is human player, black is AI)
        self.points = {"white": 0, "black": 0}
        
        # Powerup definitions - Easy to add more!
        self.powerups = {
            "shield": {
                "name": "SHIELD",
                "cost": 5,
                "description": "Protect piece for 3 turns",
                "color": (100, 200, 255),
                "icon": "🛡️"
            },
            "gun": {
                "name": "GUN",
                "cost": 7,
                "description": "Shoot enemy in range",
                "color": (255, 200, 100),
                "icon": "🔫"
            },
            "airstrike": {
                "name": "AIRSTRIKE",
                "cost": 10,
                "description": "Bombard 3x3 area",
                "color": (255, 100, 100),
                "icon": "💥"
            },
            "paratroopers": {
                "name": "PARATROOPERS",
                "cost": 10,
                "description": "Drop 3 pawns",
                "color": (100, 150, 100),
                "icon": "🪂"
            },
            "nuke": {
                "name": "NUKE",
                "cost": 25,
                "description": "Destroy everything!",
                "color": (255, 50, 50),
                "icon": "☢️"
            }
        }
        
        # Add powerup prices (for the arms dealer)
        self.powerup_prices = {
            "shield": 0,      # Free starter powerup
            "gun": 500,       # Mid-tier
            "airstrike": 1000,  # Expensive
            "paratroopers": 1500,  # Very expensive
            "nuke": 3000      # Ultimate powerup
        }
        
        # Piece point values
        self.piece_values = {
            'P': 1,  # Pawn
            'N': 3,  # Knight
            'B': 3,  # Bishop
            'R': 5,  # Rook
            'Q': 9,  # Queen
            'K': 0   # King (can't be captured normally)
        }
        
        # Active powerup state
        self.active_powerup = None
        self.powerup_state = None
        
        # Shield tracking
        self.shielded_pieces = {}  # {(row, col): turns_remaining}
        
        # Visual effects
        self.effects = []
        self.animations = []
        
        # Screen shake
        self.screen_shake = {
            "active": False,
            "intensity": 0,
            "duration": 0,
            "start_time": 0
        }
        
        # UI positioning (will be set by renderer)
        self.menu_x = 0
        self.menu_y = 0
        self.menu_width = 0
        self.menu_height = 0
        self.button_rects = {}
        
        # Assets reference (will be set by game)
        self.assets = None
        
    def add_points_for_capture(self, captured_piece, capturing_player):
        """Award points when a piece is captured."""
        if captured_piece and captured_piece[1] in self.piece_values:
            points = self.piece_values[captured_piece[1]]
            self.points[capturing_player] += points
            return points
        return 0
        
    def can_afford_powerup(self, player, powerup_key):
        """Check if player has enough points for a powerup."""
        if powerup_key in self.powerups:
            return self.points[player] >= self.powerups[powerup_key]["cost"]
        return False
        
    def can_use_powerup(self, powerup_key):
        """Check if a powerup is unlocked."""
        progress = load_progress()
        unlocked = progress.get("unlocked_powerups", ["shield"])
        return powerup_key in unlocked
        
    def activate_powerup(self, player, powerup_key):
        """Start the activation process for a powerup."""
        # Check if unlocked first
        if not self.can_use_powerup(powerup_key):
            return False
            
        if not self.can_afford_powerup(player, powerup_key):
            return False
            
        self.active_powerup = powerup_key
        self.powerup_state = {
            "player": player,
            "phase": "selecting",
            "data": {}
        }
        
        return True
        
    def cancel_powerup(self):
        """Cancel the current powerup activation."""
        self.active_powerup = None
        self.powerup_state = None
        
    def handle_click(self, pos, board):
        """Handle click during powerup activation."""
        if not self.active_powerup or not self.powerup_state:
            return False
            
        row, col = board.get_square_from_pos(pos)
        if row < 0 or col < 0:
            return False
            
        if self.active_powerup == "airstrike":
            return self._handle_airstrike_click(row, col, board)
        elif self.active_powerup == "shield":
            return self._handle_shield_click(row, col, board)
        elif self.active_powerup == "gun":
            return self._handle_gun_click(row, col, board)
        elif self.active_powerup == "nuke":
            return self._handle_nuke_click(row, col, board)
        elif self.active_powerup == "paratroopers":
            return self._handle_paratroopers_click(row, col, board)
            
        return False
        
    def _handle_airstrike_click(self, row, col, board):
        """Handle airstrike targeting."""
        # Spend points
        player = self.powerup_state["player"]
        self.points[player] -= self.powerups["airstrike"]["cost"]
        
        # Create airstrike effect
        self._create_airstrike_effect(row, col, board)
        
        # Schedule piece destruction for when bomb hits (900ms delay)
        current_time = pygame.time.get_ticks()
        self.animations.append({
            "type": "delayed_destruction",
            "row": row,
            "col": col,
            "start_time": current_time + 900,  # Same timing as explosion
            "duration": 1,  # Instant once it triggers
            "board": board
        })
        
        # Clear powerup state
        self.active_powerup = None
        self.powerup_state = None
        
        return True
        
    def _handle_shield_click(self, row, col, board):
        """Handle shield placement."""
        player = self.powerup_state["player"]
        piece = board.get_piece(row, col)
        
        # Check if it's player's piece
        piece_color = "white" if piece and piece[0] == 'w' else "black"
        if piece and piece_color == player:
            # Spend points
            self.points[player] -= self.powerups["shield"]["cost"]
            
            # Apply shield
            self.shielded_pieces[(row, col)] = 3
            
            # Create shield effect
            self._create_shield_effect(row, col, board)
            
            # Clear powerup state
            self.active_powerup = None
            self.powerup_state = None
            
            return True
            
        return False
        
    def _handle_gun_click(self, row, col, board):
        """Handle gun powerup."""
        player = self.powerup_state["player"]
        
        if self.powerup_state["phase"] == "selecting":
            # First click - select shooter
            piece = board.get_piece(row, col)
            piece_color = "white" if piece and piece[0] == 'w' else "black"
            
            if piece and piece_color == player:
                self.powerup_state["phase"] = "targeting"
                self.powerup_state["data"]["shooter"] = (row, col)
                self.powerup_state["data"]["valid_targets"] = self._get_gun_targets(row, col, board)
                return False
                
        elif self.powerup_state["phase"] == "targeting":
            # Second click - select target
            if (row, col) in self.powerup_state["data"]["valid_targets"]:
                # Spend points
                self.points[player] -= self.powerups["gun"]["cost"]
                
                # Create gun effect
                shooter_pos = self.powerup_state["data"]["shooter"]
                self._create_gun_effect(shooter_pos, (row, col), board)
                
                # Destroy target (if not king or shielded)
                target = board.get_piece(row, col)
                if target and target[1] != 'K' and (row, col) not in self.shielded_pieces:
                    board.set_piece(row, col, "")
                    
                # Clear powerup state
                self.active_powerup = None
                self.powerup_state = None
                
                return True
                
        return False
        
    def _get_gun_targets(self, row, col, board):
        """Get valid targets for gun based on piece movement."""
        piece = board.get_piece(row, col)
        if not piece:
            return []
            
        # Get all squares the piece can move to
        valid_moves = board.get_valid_moves(row, col)
        
        # Filter for enemy pieces
        targets = []
        enemy_color = 'b' if piece[0] == 'w' else 'w'
        
        for move_row, move_col in valid_moves:
            target = board.get_piece(move_row, move_col)
            if target and target[0] == enemy_color:
                targets.append((move_row, move_col))
                
        return targets
        
    def update_shields(self):
        """Decrement shield counters each turn."""
        to_remove = []
        for pos, turns in self.shielded_pieces.items():
            self.shielded_pieces[pos] = turns - 1
            if self.shielded_pieces[pos] <= 0:
                to_remove.append(pos)
                
        for pos in to_remove:
            del self.shielded_pieces[pos]
            
    def move_shield(self, from_pos, to_pos):
        """Move shield when a shielded piece moves."""
        if from_pos in self.shielded_pieces:
            turns_remaining = self.shielded_pieces[from_pos]
            del self.shielded_pieces[from_pos]
            self.shielded_pieces[to_pos] = turns_remaining
            
    def is_piece_shielded(self, row, col):
        """Check if a piece is protected by shield."""
        return (row, col) in self.shielded_pieces
        
    def update_effects(self, current_time):
        """Update visual effects."""
        # Update animations
        remaining_animations = []
        for anim in self.animations:
            if current_time - anim["start_time"] < anim["duration"]:
                remaining_animations.append(anim)
            elif anim["type"] == "delayed_destruction" and current_time >= anim["start_time"]:
                # Handle delayed destruction when time is reached
                self._execute_delayed_destruction(anim)
            elif anim["type"] == "delayed_pawn_placement" and current_time >= anim["start_time"]:
                # Handle delayed pawn placement when parachute lands
                self._execute_delayed_pawn_placement(anim)
                
        self.animations = remaining_animations
        
        # Update particle effects
        self.effects = [effect for effect in self.effects 
                       if current_time - effect["start_time"] < effect["duration"]]
                       
    def _execute_delayed_destruction(self, anim):
        """Execute the delayed destruction of pieces from airstrike."""
        row = anim["row"]
        col = anim["col"]
        board = anim["board"]
        
        # Play bomb sound when explosion happens
        if self.assets and 'bomb' in self.assets.sounds:
            try:
                self.assets.sounds['bomb'].play()
            except Exception as e:
                print(f"Error playing bomb sound: {e}")
        
        # Trigger screen shake
        self.start_screen_shake(15, 500)  # 15 pixel intensity, 500ms duration
        
        # Destroy pieces in 3x3 area
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                target_row = row + dr
                target_col = col + dc
                if 0 <= target_row < 8 and 0 <= target_col < 8:
                    piece = board.get_piece(target_row, target_col)
                    if piece:
                        # Can't destroy kings or shielded pieces
                        if piece[1] != 'K' and (target_row, target_col) not in self.shielded_pieces:
                            board.set_piece(target_row, target_col, "")
                            
    def _execute_delayed_pawn_placement(self, anim):
        """Execute the delayed placement of a pawn from paratroopers."""
        row = anim["row"]
        col = anim["col"]
        board = anim["board"]
        pawn = anim["pawn"]
        
        # Place the pawn on the board
        board.set_piece(row, col, pawn)
        
    def _create_airstrike_effect(self, row, col, board):
        """Create visual effect for airstrike."""
        current_time = pygame.time.get_ticks()
        x, y = board.get_square_pos(row, col)
        
        # Add jet flyby animation FIRST
        self.animations.append({
            "type": "jet_flyby",
            "target_x": x,
            "target_y": y,
            "start_time": current_time,
            "duration": 1500,  # 1.5 seconds for jet to fly across
            "row": row,
            "col": col
        })
        
        # Add explosion animation AFTER bomb hits
        # The bomb drops from 0.4 to 0.6 progress (0.6-0.9 seconds into animation)
        # So explosion should start at 0.9 seconds after jet starts
        self.animations.append({
            "type": "airstrike",
            "x": x,
            "y": y,
            "start_time": current_time + 900,  # Delay explosion to match bomb impact
            "duration": 700,  # 100ms per frame x 7 frames
            "row": row,
            "col": col
        })
        
        # REMOVED: Particle effects - we don't need them since we have explosion sprites
            
    def _create_shield_effect(self, row, col, board):
        """Create visual effect for shield."""
        current_time = pygame.time.get_ticks()
        x, y = board.get_square_pos(row, col)
        
        self.animations.append({
            "type": "shield",
            "x": x,
            "y": y,
            "start_time": current_time,
            "duration": 1000,
            "row": row,
            "col": col
        })
        
    def _create_gun_effect(self, shooter_pos, target_pos, board):
        """Create visual effect for gun shot."""
        current_time = pygame.time.get_ticks()
        
        # Get pixel positions
        shooter_x, shooter_y = board.get_square_pos(*shooter_pos)
        target_x, target_y = board.get_square_pos(*target_pos)
        
        # Center positions
        shooter_x += SQUARE_SIZE // 2
        shooter_y += SQUARE_SIZE // 2
        target_x += SQUARE_SIZE // 2
        target_y += SQUARE_SIZE // 2
        
        self.animations.append({
            "type": "gunshot",
            "start_x": shooter_x,
            "start_y": shooter_y,
            "end_x": target_x,
            "end_y": target_y,
            "start_time": current_time,
            "duration": 500
        })
        
        # Add muzzle flash
        self.effects.append({
            "type": "muzzle_flash",
            "x": shooter_x,
            "y": shooter_y,
            "start_time": current_time,
            "duration": 200
        })
        
        # Add impact effect
        self.effects.append({
            "type": "impact",
            "x": target_x,
            "y": target_y,
            "start_time": current_time + 200,
            "duration": 300
        })
        
    def _handle_nuke_click(self, row, col, board):
        """Handle nuclear strike - destroys everything except kings."""
        # Spend points
        player = self.powerup_state["player"]
        self.points[player] -= self.powerups["nuke"]["cost"]
        
        # Create massive explosion effect
        self._create_nuke_effect(board)
        
        # Trigger intense screen shake for nuke
        self.start_screen_shake(25, 1000)  # 25 pixel intensity, 1 second duration
        
        # Destroy all pieces except kings
        destroyed_count = 0
        for r in range(8):
            for c in range(8):
                piece = board.get_piece(r, c)
                if piece and piece[1] != 'K':  # Don't destroy kings
                    board.set_piece(r, c, "")
                    destroyed_count += 1
                    
        print(f"NUCLEAR STRIKE! Destroyed {destroyed_count} pieces!")
        
        # Clear powerup state
        self.active_powerup = None
        self.powerup_state = None
        
        return True
        
    def _handle_paratroopers_click(self, row, col, board):
        """Handle paratroopers - place pawns on empty squares."""
        player = self.powerup_state["player"]
        
        # Check if square is empty
        if board.get_piece(row, col) != "":
            return False
            
        # Initialize data if first click
        if "placed" not in self.powerup_state["data"]:
            self.powerup_state["data"]["placed"] = []
            
        # Record where pawn will be placed
        self.powerup_state["data"]["placed"].append((row, col))
        
        # Create paratrooper drop effect
        self._create_paratrooper_effect(row, col, board)
        
        # Schedule pawn placement for when parachute lands (1500ms delay)
        current_time = pygame.time.get_ticks()
        pawn_color = 'w' if player == "white" else 'b'
        self.animations.append({
            "type": "delayed_pawn_placement",
            "row": row,
            "col": col,
            "pawn": pawn_color + 'P',
            "start_time": current_time + 1500,  # Same as paratrooper animation duration
            "duration": 1,  # Instant once it triggers
            "board": board
        })
        
        # Check if we've placed all 3 pawns
        if len(self.powerup_state["data"]["placed"]) >= 3:
            # Spend points
            self.points[player] -= self.powerups["paratroopers"]["cost"]
            
            # Clear powerup state
            self.active_powerup = None
            self.powerup_state = None
            
            return True
            
        return False
        
    def _create_nuke_effect(self, board):
        """Create nuclear explosion effect."""
        current_time = pygame.time.get_ticks()
        
        # Get center of board
        center_x = BOARD_OFFSET_X + (BOARD_SIZE // 2)
        center_y = BOARD_OFFSET_Y + (BOARD_SIZE // 2)
        
        # Add massive explosion animation
        self.animations.append({
            "type": "nuke",
            "x": center_x,
            "y": center_y,
            "start_time": current_time,
            "duration": 3000,  # 3 seconds
        })
        
        # Add radiation particles
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 500)
            self.effects.append({
                "type": "radiation_particle",
                "x": center_x,
                "y": center_y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": random.choice([(255, 255, 0), (255, 150, 0), (100, 255, 0)]),
                "size": random.randint(5, 15),
                "start_time": current_time,
                "duration": 2000
            })
            
    def start_screen_shake(self, intensity, duration):
        """Start a screen shake effect."""
        current_time = pygame.time.get_ticks()
        self.screen_shake = {
            "active": True,
            "intensity": intensity,
            "duration": duration,
            "start_time": current_time
        }
        
    def get_screen_shake_offset(self):
        """Get the current screen shake offset."""
        if not self.screen_shake["active"]:
            return 0, 0
            
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.screen_shake["start_time"]
        
        if elapsed >= self.screen_shake["duration"]:
            self.screen_shake["active"] = False
            return 0, 0
            
        # Calculate shake intensity with decay
        progress = elapsed / self.screen_shake["duration"]
        current_intensity = self.screen_shake["intensity"] * (1 - progress)
        
        # Random shake offset
        offset_x = random.randint(-int(current_intensity), int(current_intensity))
        offset_y = random.randint(-int(current_intensity), int(current_intensity))
        
        return offset_x, offset_y
        
    def _create_paratrooper_effect(self, row, col, board):
        """Create paratrooper drop effect."""
        current_time = pygame.time.get_ticks()
        x, y = board.get_square_pos(row, col)
        
        # Add parachute animation
        self.animations.append({
            "type": "paratrooper",
            "x": x,
            "y": y,
            "start_time": current_time,
            "duration": 1500,
            "row": row,
            "col": col
        })