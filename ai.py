"""
Chess AI Bot System - Enhanced with Powerup Usage and ELO Ratings
Different difficulty levels from Easy to Very Hard with ELO-based play strength
"""

import random
import pygame
import time
import math
from config import *

class ChessAI:
    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty
        
        # ELO ratings for each difficulty level
        self.elo_ratings = {
            "easy": 800,      # Beginner
            "medium": 1200,   # Casual player
            "hard": 1600,     # Club player
            "very_hard": 2000 # Expert
        }
        
        # Get the ELO rating for this difficulty
        self.elo = self.elo_ratings[difficulty]
        
        # Thinking time based on ELO (higher rated players think longer)
        self.thinking_time = {
            "easy": 500,      # 0.5 seconds
            "medium": 800,    # 0.8 seconds
            "hard": 1200,     # 1.2 seconds
            "very_hard": 1500 # 1.5 seconds (reduced from 2000)
        }
        
        # Powerup usage probability based on ELO
        # Higher rated players use powerups more strategically
        self.powerup_usage_chance = {
            "easy": 0.05,      # 5% chance per turn (rarely uses)
            "medium": 0.15,    # 15% chance per turn
            "hard": 0.25,      # 25% chance per turn
            "very_hard": 0.35  # 35% chance per turn (strategic use)
        }
        
        # Strategic weights for powerup selection based on ELO
        self.powerup_weights = self._calculate_powerup_weights()
        
        self.start_thinking = None
        
        # Piece values for evaluation
        self.piece_values = {
            'P': 100,
            'N': 320,
            'B': 330,
            'R': 500,
            'Q': 900,
            'K': 20000
        }
        
        # Position tables for better evaluation (from white's perspective)
        self.pawn_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ]
        
        self.knight_table = [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ]
        
        self.bishop_table = [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ]
        
        self.rook_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ]
        
        self.queen_table = [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ]
        
        self.king_table = [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ]
        
        # Endgame king table (more active)
        self.king_endgame_table = [
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ]
        
    def _calculate_powerup_weights(self):
        """Calculate strategic weights for powerup selection based on ELO."""
        if self.elo < 1000:  # Easy
            # Random powerup usage, no strategy
            return {
                "shield": 1.0,
                "gun": 1.0,
                "airstrike": 1.0,
                "paratroopers": 1.0,
                "chopper": 1.0
            }
        elif self.elo < 1400:  # Medium
            # Prefer defensive and simple offensive powerups
            return {
                "shield": 2.0,
                "gun": 1.5,
                "airstrike": 1.0,
                "paratroopers": 0.5,
                "chopper": 0.3
            }
        elif self.elo < 1800:  # Hard
            # Strategic use based on game state
            return {
                "shield": 1.5,
                "gun": 2.0,
                "airstrike": 1.5,
                "paratroopers": 1.0,
                "chopper": 0.5
            }
        else:  # Very Hard
            # Highly strategic, saves powerful powerups
            return {
                "shield": 1.0,
                "gun": 2.5,
                "airstrike": 2.0,
                "paratroopers": 1.5,
                "chopper": 1.0  # Will use when advantageous
            }
            
    def start_turn(self):
        """Start the AI's thinking timer."""
        self.start_thinking = pygame.time.get_ticks()
        
    def is_thinking(self):
        """Check if AI is still thinking."""
        if self.start_thinking is None:
            return False
        elapsed = pygame.time.get_ticks() - self.start_thinking
        return elapsed < self.thinking_time[self.difficulty]
        
    def should_use_powerup(self, board, powerup_system):
        """Decide if AI should use a powerup this turn."""
        # Check if it's AI's turn
        if board.current_turn != "black":
            return None
            
        # Random chance based on difficulty
        if random.random() > self.powerup_usage_chance[self.difficulty]:
            return None
            
        # Get available powerups
        available_powerups = []
        for powerup_key in powerup_system.powerups:
            if powerup_system.can_afford_powerup("black", powerup_key):
                available_powerups.append(powerup_key)
                
        if not available_powerups:
            return None
            
        # Select powerup based on strategic weights and game state
        selected_powerup = self._select_best_powerup(board, powerup_system, available_powerups)
        
        return selected_powerup
        
    def _select_best_powerup(self, board, powerup_system, available_powerups):
        """Select the best powerup based on game state and AI strategy."""
        # Evaluate game state
        material_balance = self._evaluate_material_balance(board)
        is_losing = material_balance < -200  # AI is down significant material
        is_winning = material_balance > 200   # AI is up significant material
        
        # Adjust weights based on game state
        adjusted_weights = {}
        for powerup in available_powerups:
            weight = self.powerup_weights.get(powerup, 1.0)
            
            # Strategic adjustments based on ELO
            if self.elo >= 1600:  # Hard and Very Hard
                if powerup == "shield" and is_losing:
                    weight *= 2.0  # Protect valuable pieces when losing
                elif powerup == "gun" and self._has_good_gun_target(board, powerup_system):
                    weight *= 3.0  # High priority if can eliminate valuable piece
                elif powerup == "airstrike" and self._has_good_airstrike_target(board):
                    weight *= 2.5  # Good for clearing clustered pieces
                elif powerup == "paratroopers" and is_winning:
                    weight *= 2.0  # Press advantage with more pieces
                elif powerup == "chopper" and is_losing and powerup_system.points["black"] >= 25:
                    weight *= 5.0  # Desperation move when losing badly
                    
            adjusted_weights[powerup] = weight
            
        # Weighted random selection
        total_weight = sum(adjusted_weights.values())
        if total_weight == 0:
            return random.choice(available_powerups)
            
        r = random.uniform(0, total_weight)
        cumulative = 0
        for powerup, weight in adjusted_weights.items():
            cumulative += weight
            if r <= cumulative:
                return powerup
                
        return available_powerups[-1]  # Fallback
        
    def _evaluate_material_balance(self, board):
        """Evaluate material balance from AI's perspective (positive = AI advantage)."""
        white_material = 0
        black_material = 0
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    value = self.piece_values.get(piece[1], 0)
                    if piece[0] == 'w':
                        white_material += value
                    else:
                        black_material += value
                        
        return black_material - white_material
        
    def _has_good_gun_target(self, board, powerup_system):
        """Check if there's a valuable enemy piece that can be shot."""
        # Find all black pieces that could shoot
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == 'b':
                    # Check potential gun targets from this position
                    targets = self._get_gun_targets_for_ai(row, col, board)
                    for target_row, target_col in targets:
                        target_piece = board.get_piece(target_row, target_col)
                        if target_piece and target_piece[1] in ['Q', 'R']:
                            return True  # Can shoot queen or rook
        return False
        
    def _get_gun_targets_for_ai(self, row, col, board):
        """Get valid gun targets for AI (same as player logic)."""
        targets = []
        
        # Check all 8 directions for line of sight
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal
        ]
        
        for dr, dc in directions:
            for distance in range(1, 8):
                check_row = row + dr * distance
                check_col = col + dc * distance
                
                if not (0 <= check_row < 8 and 0 <= check_col < 8):
                    break
                    
                target = board.get_piece(check_row, check_col)
                if target:
                    if target[0] == 'w' and target[1] != 'K':
                        targets.append((check_row, check_col))
                    break  # Can't shoot through pieces
                    
        return targets
        
    def _has_good_airstrike_target(self, board):
        """Check if there's a good 3x3 area to airstrike."""
        best_value = 0
        
        for center_row in range(8):
            for center_col in range(8):
                value = 0
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        r, c = center_row + dr, center_col + dc
                        if 0 <= r < 8 and 0 <= c < 8:
                            piece = board.get_piece(r, c)
                            if piece and piece[0] == 'w' and piece[1] != 'K':
                                value += self.piece_values.get(piece[1], 0)
                                
                if value > best_value:
                    best_value = value
                    
        return best_value >= 500  # Worth it if can destroy 500+ points of material
        
    def execute_powerup(self, board, powerup_system, powerup_key):
        """Execute the selected powerup for AI."""
        if powerup_key == "shield":
            return self._execute_shield(board, powerup_system)
        elif powerup_key == "gun":
            return self._execute_gun(board, powerup_system)
        elif powerup_key == "airstrike":
            return self._execute_airstrike(board, powerup_system)
        elif powerup_key == "paratroopers":
            return self._execute_paratroopers(board, powerup_system)
        elif powerup_key == "chopper":
            return self._execute_chopper(board, powerup_system)
            
        return None
        
    def _execute_shield(self, board, powerup_system):
        """AI uses shield powerup."""
        # Find most valuable unshielded piece
        best_piece = None
        best_value = 0
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == 'b' and not powerup_system.is_piece_shielded(row, col):
                    value = self.piece_values.get(piece[1], 0)
                    
                    # Prioritize pieces under attack if ELO >= 1400
                    if self.elo >= 1400 and self._square_is_attacked(board, row, col, 'w'):
                        value *= 2
                        
                    if value > best_value:
                        best_value = value
                        best_piece = (row, col)
                        
        if best_piece:
            return {
                "type": "shield",
                "target": best_piece
            }
            
        return None
        
    def _execute_gun(self, board, powerup_system):
        """AI uses gun powerup."""
        best_shot = None
        best_value = 0
        
        # Check all black pieces for shooting opportunities
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == 'b':
                    targets = self._get_gun_targets_for_ai(row, col, board)
                    for target_row, target_col in targets:
                        target_piece = board.get_piece(target_row, target_col)
                        if target_piece:
                            value = self.piece_values.get(target_piece[1], 0)
                            if value > best_value:
                                best_value = value
                                best_shot = {
                                    "shooter": (row, col),
                                    "target": (target_row, target_col)
                                }
                                
        if best_shot:
            return {
                "type": "gun",
                "shooter": best_shot["shooter"],
                "target": best_shot["target"]
            }
            
        return None
        
    def _execute_airstrike(self, board, powerup_system):
        """AI uses airstrike powerup."""
        best_target = None
        best_value = 0
        
        for center_row in range(8):
            for center_col in range(8):
                value = 0
                hits = []
                
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        r, c = center_row + dr, center_col + dc
                        if 0 <= r < 8 and 0 <= c < 8:
                            piece = board.get_piece(r, c)
                            if piece:
                                if piece[0] == 'w' and piece[1] != 'K':
                                    value += self.piece_values.get(piece[1], 0)
                                    hits.append((r, c))
                                elif piece[0] == 'b':
                                    value -= self.piece_values.get(piece[1], 0) * 0.5  # Penalty for friendly fire
                                    
                if value > best_value:
                    best_value = value
                    best_target = (center_row, center_col)
                    
        if best_target and best_value > 0:
            return {
                "type": "airstrike",
                "target": best_target
            }
            
        return None
        
    def _execute_paratroopers(self, board, powerup_system):
        """AI uses paratroopers powerup."""
        # Find 3 strategic empty squares
        empty_squares = []
        for row in range(8):
            for col in range(8):
                if board.get_piece(row, col) == "":
                    empty_squares.append((row, col))
                    
        if len(empty_squares) < 3:
            return None
            
        # Prioritize squares based on strategy
        scored_squares = []
        for row, col in empty_squares:
            score = 0
            
            # Prefer advanced positions
            if row <= 3:  # Closer to white's side
                score += 10
                
            # Prefer central squares
            if 2 <= col <= 5:
                score += 5
                
            # Check if can immediately threaten pieces
            # Pawn attacks diagonally
            for dc in [-1, 1]:
                attack_row = row + 1  # Black pawns move down
                attack_col = col + dc
                if 0 <= attack_row < 8 and 0 <= attack_col < 8:
                    target = board.get_piece(attack_row, attack_col)
                    if target and target[0] == 'w':
                        score += self.piece_values.get(target[1], 0) / 100
                        
            scored_squares.append((score, row, col))
            
        # Sort by score and pick top 3
        scored_squares.sort(reverse=True)
        targets = [(row, col) for _, row, col in scored_squares[:3]]
        
        return {
            "type": "paratroopers",
            "targets": targets
        }
        
    def _execute_chopper(self, board, powerup_system):
        """AI uses chopper gunner powerup."""
        # Only use if it's advantageous
        material_balance = self._evaluate_material_balance(board)
        
        # Count enemy pieces (excluding king)
        enemy_pieces = 0
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == 'w' and piece[1] != 'K':
                    enemy_pieces += 1
                    
        # Use chopper if losing badly or if can eliminate many pieces
        if material_balance < -500 or enemy_pieces >= 8:
            return {
                "type": "chopper",
                "confirm": True
            }
            
        return None
        
    def get_move(self, board):
        """Get the AI's move based on difficulty and ELO rating."""
        # Use ELO to determine search depth and move quality
        if self.elo < 1000:
            return self._get_elo_based_move(board, random_error_rate=0.3)
        elif self.elo < 1400:
            return self._get_elo_based_move(board, random_error_rate=0.15)
        elif self.elo < 1800:
            return self._get_elo_based_move(board, random_error_rate=0.05)
        else:
            return self._get_elo_based_move(board, random_error_rate=0.01)
            
    def _get_elo_based_move(self, board, random_error_rate):
        """Get move with ELO-based strength and random errors."""
        moves = self._get_all_legal_moves(board)
        if not moves:
            return None
            
        # Random error (blunder) based on ELO
        if random.random() < random_error_rate:
            # Make a random move (blunder)
            return random.choice(moves)
            
        # Calculate search depth based on ELO
        if self.elo < 1000:
            depth = 1
        elif self.elo < 1400:
            depth = 2
        elif self.elo < 1800:
            depth = 3
        else:
            depth = 3  # Limit to 3 for Very Hard to prevent lag
            
        # Always check for immediate checkmate
        for move in moves:
            if self._move_gives_checkmate(board, move):
                return move
                
        # Use minimax with ELO-based depth
        best_move = None
        best_score = -999999
        
        # Add some randomness to move ordering for lower ELO
        if self.elo < 1400:
            random.shuffle(moves)
        else:
            moves = self._order_moves(board, moves)
        
        for move in moves:
            score = self._minimax(board, depth, -999999, 999999, False, move)
            
            # Add small random factor for move variety
            score += random.uniform(-10, 10) * (2000 - self.elo) / 1000
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
        
    def _minimax(self, board, depth, alpha, beta, is_maximizing, initial_move):
        """Minimax with alpha-beta pruning."""
        # Terminal node
        if depth == 0:
            return self._evaluate_board(board)
            
        # Make the initial move
        from_row, from_col = initial_move[0]
        to_row, to_col = initial_move[1]
        
        moving_piece = board.get_piece(from_row, from_col)
        captured_piece = board.get_piece(to_row, to_col)
        
        # Make move
        board.set_piece(to_row, to_col, moving_piece)
        board.set_piece(from_row, from_col, "")
        
        # Check for immediate win (king capture)
        if captured_piece and captured_piece[1] == 'K':
            # Undo move
            board.set_piece(from_row, from_col, moving_piece)
            board.set_piece(to_row, to_col, captured_piece)
            return 999999 - (5 - depth) * 1000  # Prefer faster checkmates
            
        # Recursive minimax
        if is_maximizing:
            max_eval = -999999
            moves = self._get_all_moves_for_color(board, 'b')
            
            # Order moves for better pruning
            if depth > 2:
                moves = self._order_moves_simple(board, moves)
                
            for move in moves:
                eval_score = self._minimax_recursive(board, depth - 1, alpha, beta, False, move)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
                    
            score = max_eval
        else:
            min_eval = 999999
            moves = self._get_all_moves_for_color(board, 'w')
            
            # Order moves for better pruning
            if depth > 2:
                moves = self._order_moves_simple(board, moves)
                
            for move in moves:
                eval_score = self._minimax_recursive(board, depth - 1, alpha, beta, True, move)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
                    
            score = min_eval
            
        # Undo move
        board.set_piece(from_row, from_col, moving_piece)
        board.set_piece(to_row, to_col, captured_piece)
        
        return score
        
    def _minimax_recursive(self, board, depth, alpha, beta, is_maximizing, move):
        """Recursive part of minimax."""
        if depth == 0:
            return self._evaluate_board(board)
            
        from_row, from_col = move[0]
        to_row, to_col = move[1]
        
        moving_piece = board.get_piece(from_row, from_col)
        captured_piece = board.get_piece(to_row, to_col)
        
        # Make move
        board.set_piece(to_row, to_col, moving_piece)
        board.set_piece(from_row, from_col, "")
        
        # Check for king capture
        if captured_piece and captured_piece[1] == 'K':
            # Undo move
            board.set_piece(from_row, from_col, moving_piece)
            board.set_piece(to_row, to_col, captured_piece)
            if is_maximizing:
                return -999999 + (5 - depth) * 1000
            else:
                return 999999 - (5 - depth) * 1000
                
        # Continue minimax
        if is_maximizing:
            max_eval = -999999
            moves = self._get_all_moves_for_color(board, 'b')
            for next_move in moves:
                eval_score = self._minimax_recursive(board, depth - 1, alpha, beta, False, next_move)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            score = max_eval
        else:
            min_eval = 999999
            moves = self._get_all_moves_for_color(board, 'w')
            for next_move in moves:
                eval_score = self._minimax_recursive(board, depth - 1, alpha, beta, True, next_move)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            score = min_eval
            
        # Undo move
        board.set_piece(from_row, from_col, moving_piece)
        board.set_piece(to_row, to_col, captured_piece)
        
        return score
        
    def _evaluate_board(self, board):
        """Evaluate board position with ELO-based accuracy."""
        white_score = 0
        black_score = 0
        white_pieces = 0
        black_pieces = 0
        
        # Count material and positions
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if not piece:
                    continue
                    
                piece_type = piece[1]
                piece_color = piece[0]
                
                # Base piece value
                value = self.piece_values[piece_type]
                
                # Count pieces for endgame detection
                if piece_type != 'K' and piece_type != 'P':
                    if piece_color == 'w':
                        white_pieces += 1
                    else:
                        black_pieces += 1
                        
                # Position bonus based on piece type (only for higher ELO)
                if self.elo >= 1200:
                    if piece_type == 'P':
                        if piece_color == 'w':
                            value += self.pawn_table[row][col]
                        else:
                            value += self.pawn_table[7-row][col]
                    elif piece_type == 'N':
                        value += self.knight_table[row][col]
                    elif piece_type == 'B':
                        value += self.bishop_table[row][col]
                    elif piece_type == 'R':
                        value += self.rook_table[row][col]
                    elif piece_type == 'Q':
                        value += self.queen_table[row][col]
                    elif piece_type == 'K':
                        # Use endgame table if few pieces left
                        total_pieces = white_pieces + black_pieces
                        if total_pieces <= 6:  # Endgame
                            if piece_color == 'w':
                                value += self.king_endgame_table[row][col]
                            else:
                                value += self.king_endgame_table[7-row][col]
                        else:  # Middle/Opening
                            if piece_color == 'w':
                                value += self.king_table[row][col]
                            else:
                                value += self.king_table[7-row][col]
                                
                # Add to appropriate score
                if piece_color == 'w':
                    white_score += value
                else:
                    black_score += value
                    
        # Return from black's perspective (AI plays black)
        return black_score - white_score
        
    def _get_all_legal_moves(self, board):
        """Get all legal moves for black (AI)."""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == 'b':
                    piece_moves = board.get_valid_moves(row, col)
                    for to_row, to_col in piece_moves:
                        moves.append(((row, col), (to_row, to_col)))
        return moves
        
    def _get_all_moves_for_color(self, board, color):
        """Get all legal moves for a specific color."""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece[0] == color:
                    piece_moves = board.get_valid_moves(row, col)
                    for to_row, to_col in piece_moves:
                        moves.append(((row, col), (to_row, to_col)))
        return moves
        
    def _order_moves(self, board, moves):
        """Order moves for better alpha-beta pruning."""
        scored_moves = []
        
        for move in moves:
            score = 0
            from_row, from_col = move[0]
            to_row, to_col = move[1]
            
            moving_piece = board.get_piece(from_row, from_col)
            target_piece = board.get_piece(to_row, to_col)
            
            # Captures - MVV/LVA (Most Valuable Victim / Least Valuable Attacker)
            if target_piece:
                victim_value = self.piece_values[target_piece[1]]
                attacker_value = self.piece_values[moving_piece[1]]
                score += victim_value * 10 - attacker_value
                
            # Check moves
            if self._move_gives_check(board, move):
                score += 50
                
            # Center control
            if 2 <= to_row <= 5 and 2 <= to_col <= 5:
                score += 10
                
            # Pawn promotion
            if moving_piece[1] == 'P' and to_row == 7:
                score += 800
                
            scored_moves.append((move, score))
            
        # Sort by score descending
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, score in scored_moves]
        
    def _order_moves_simple(self, board, moves):
        """Simple move ordering for recursive calls."""
        capture_moves = []
        other_moves = []
        
        for move in moves:
            to_row, to_col = move[1]
            if board.get_piece(to_row, to_col):
                capture_moves.append(move)
            else:
                other_moves.append(move)
                
        return capture_moves + other_moves
        
    def _square_is_attacked(self, board, row, col, by_color):
        """Check if a square is attacked by given color."""
        # Check all pieces of the attacking color
        for r in range(8):
            for c in range(8):
                piece = board.get_piece(r, c)
                if piece and piece[0] == by_color:
                    # Get all possible moves for this piece
                    moves = board.get_valid_moves(r, c)
                    if (row, col) in moves:
                        return True
        return False
        
    def _move_gives_check(self, board, move):
        """Check if a move puts opponent in check."""
        from_row, from_col = move[0]
        to_row, to_col = move[1]
        
        # Make move
        piece = board.get_piece(from_row, from_col)
        original_target = board.get_piece(to_row, to_col)
        
        board.set_piece(to_row, to_col, piece)
        board.set_piece(from_row, from_col, "")
        
        # Find white king
        king_pos = board.find_king("white")
        in_check = False
        
        if king_pos:
            in_check = self._square_is_attacked(board, king_pos[0], king_pos[1], 'b')
            
        # Undo move
        board.set_piece(from_row, from_col, piece)
        board.set_piece(to_row, to_col, original_target)
        
        return in_check
        
    def _move_gives_checkmate(self, board, move):
        """Check if a move delivers checkmate."""
        # First check if it gives check
        if not self._move_gives_check(board, move):
            return False
            
        from_row, from_col = move[0]
        to_row, to_col = move[1]
        
        # Make move
        piece = board.get_piece(from_row, from_col)
        original_target = board.get_piece(to_row, to_col)
        
        board.set_piece(to_row, to_col, piece)
        board.set_piece(from_row, from_col, "")
        
        # Check if white has any legal moves that escape check
        can_escape = False
        
        for row in range(8):
            for col in range(8):
                p = board.get_piece(row, col)
                if p and p[0] == 'w':
                    piece_moves = board.get_valid_moves(row, col)
                    for move_row, move_col in piece_moves:
                        # Test this move
                        test_piece = board.get_piece(row, col)
                        test_target = board.get_piece(move_row, move_col)
                        
                        board.set_piece(move_row, move_col, test_piece)
                        board.set_piece(row, col, "")
                        
                        # Check if king is still in check
                        king_pos = board.find_king("white")
                        if king_pos:
                            still_in_check = self._square_is_attacked(board, king_pos[0], king_pos[1], 'b')
                            if not still_in_check:
                                can_escape = True
                                
                        # Undo test move
                        board.set_piece(row, col, test_piece)
                        board.set_piece(move_row, move_col, test_target)
                        
                        if can_escape:
                            break
                            
                    if can_escape:
                        break
                        
            if can_escape:
                break
                
        # Undo original move
        board.set_piece(from_row, from_col, piece)
        board.set_piece(to_row, to_col, original_target)
        
        return not can_escape