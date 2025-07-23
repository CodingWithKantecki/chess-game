"""
Hint system for new players after tutorial completion.
Provides gentle guidance for chess moves and powerup usage.
"""

import pygame
import random

class HintSystem:
    def __init__(self):
        self.active = True  # Can be toggled by player
        self.current_hints = []
        self.powerup_hints = []
        self.move_hints = []
        self.games_played_after_tutorial = 0
        self.last_hint_time = 0
        self.hint_cooldown = 3000  # 3 seconds between hints
        
    def toggle_hints(self):
        """Toggle hint system on/off."""
        self.active = not self.active
        return self.active
        
    def update(self, board, current_player, powerup_system, game_state):
        """Update hints based on game state."""
        if not self.active:
            self.current_hints = []
            return
            
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hint_time < self.hint_cooldown:
            return
            
        self.current_hints = []
        
        # Only show hints for white player in first few games
        if current_player != 'w' or self.games_played_after_tutorial > 5:
            return
            
        # Movement hints for opening
        if board.move_count < 10:
            self._generate_opening_hints(board)
        
        # Powerup usage hints
        if powerup_system and powerup_system.points.get("white", 0) >= 3:
            self._generate_powerup_hints(powerup_system, board, game_state)
            
        self.last_hint_time = current_time
        
    def _generate_opening_hints(self, board):
        """Generate hints for opening moves."""
        hints = []
        
        # Check if center pawns haven't moved
        if board.get_piece(4, 6) == 'wP':  # e2 pawn
            hints.append({
                "type": "move",
                "highlight": [(4, 6), (4, 4)],
                "text": "Control the center! Move your e-pawn to e4"
            })
        elif board.get_piece(3, 6) == 'wP':  # d2 pawn
            hints.append({
                "type": "move", 
                "highlight": [(3, 6), (3, 4)],
                "text": "Control the center! Move your d-pawn to d4"
            })
            
        # Knight development hints
        if board.move_count >= 2:
            if board.get_piece(1, 7) == 'wN':  # b1 knight
                hints.append({
                    "type": "move",
                    "highlight": [(1, 7), (2, 5)],
                    "text": "Develop your knight to c3"
                })
            if board.get_piece(6, 7) == 'wN':  # g1 knight
                hints.append({
                    "type": "move",
                    "highlight": [(6, 7), (5, 5)],
                    "text": "Develop your knight to f3"
                })
                
        if hints:
            self.current_hints = [random.choice(hints)]
            
    def _generate_powerup_hints(self, powerup_system, board, game_state):
        """Generate hints for powerup usage."""
        hints = []
        points = powerup_system.points.get("white", 0)
        
        # Check if any pieces are under attack
        under_attack = self._find_pieces_under_attack(board, 'w')
        
        if under_attack and points >= powerup_system.powerups["shield"]["cost"]:
            valuable_pieces = [pos for pos in under_attack 
                              if board.get_piece(pos[0], pos[1])[1] in ['Q', 'R', 'N', 'B']]
            if valuable_pieces:
                hints.append({
                    "type": "powerup",
                    "powerup": "shield",
                    "highlight": valuable_pieces[0],
                    "text": "Your piece is under attack! Use SHIELD to protect it"
                })
                
        # Suggest offensive powerups if ahead
        if game_state.get("material_advantage", 0) > 3 and points >= 5:
            hints.append({
                "type": "powerup",
                "powerup": "gun",
                "text": "You're ahead! Use GUN to eliminate a key enemy piece"
            })
            
        if hints:
            self.current_hints = [random.choice(hints)]
            
    def _find_pieces_under_attack(self, board, color):
        """Find player's pieces that are under attack."""
        under_attack = []
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(col, row)
                if piece and piece[0] == color:
                    # Check if this piece is attacked by any enemy piece
                    for er in range(8):
                        for ec in range(8):
                            enemy = board.get_piece(ec, er)
                            if enemy and enemy[0] != color:
                                enemy_moves = board.get_valid_moves(er, ec, ignore_shields=True)
                                if (col, row) in enemy_moves:
                                    under_attack.append((col, row))
                                    break
                                    
        return under_attack
        
    def get_highlights(self):
        """Get squares to highlight for current hints."""
        highlights = []
        
        for hint in self.current_hints:
            if hint["type"] == "move" and "highlight" in hint:
                highlights.extend(hint["highlight"])
            elif hint["type"] == "powerup" and "highlight" in hint:
                highlights.append(hint["highlight"])
                
        return highlights
        
    def get_powerup_highlights(self):
        """Get powerups to highlight."""
        for hint in self.current_hints:
            if hint["type"] == "powerup" and "powerup" in hint:
                return hint["powerup"]
        return None
        
    def get_hint_text(self):
        """Get current hint text."""
        if self.current_hints:
            return self.current_hints[0]["text"]
        return None
        
    def increment_games_played(self):
        """Increment games played counter."""
        self.games_played_after_tutorial += 1
        
        # Disable hints after 5 games
        if self.games_played_after_tutorial > 5:
            self.active = False