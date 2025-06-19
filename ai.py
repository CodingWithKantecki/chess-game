"""
Chess AI Bot System
Different difficulty levels from Easy to Very Hard
"""

import random
import pygame
import time
from config import *

class ChessAI:
    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty
        self.thinking_time = {
            "easy": 500,      # 0.5 seconds
            "medium": 1000,   # 1 second
            "hard": 1500,     # 1.5 seconds
            "very_hard": 2000 # 2 seconds
        }
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
        
    def start_turn(self):
        """Start the AI's thinking timer."""
        self.start_thinking = pygame.time.get_ticks()
        
    def is_thinking(self):
        """Check if AI is still thinking."""
        if self.start_thinking is None:
            return False
        elapsed = pygame.time.get_ticks() - self.start_thinking
        return elapsed < self.thinking_time[self.difficulty]
        
    def get_move(self, board):
        """Get the AI's move based on difficulty."""
        if self.difficulty == "easy":
            return self._get_easy_move(board)
        elif self.difficulty == "medium":
            return self._get_medium_move(board)
        elif self.difficulty == "hard":
            return self._get_hard_move(board)
        else:  # very_hard
            return self._get_very_hard_move(board)
            
    def _get_easy_move(self, board):
        """Easy AI - Makes random legal moves, sometimes blunders."""
        moves = self._get_all_legal_moves(board)
        if not moves:
            return None
            
        # 30% chance to make a bad move (if possible)
        if random.random() < 0.3:
            bad_moves = self._filter_bad_moves(board, moves)
            if bad_moves:
                return random.choice(bad_moves)
                
        return random.choice(moves)
        
    def _get_medium_move(self, board):
        """Medium AI - Captures when possible, avoids obvious blunders."""
        moves = self._get_all_legal_moves(board)
        if not moves:
            return None
            
        # Check for checkmate moves first
        for move in moves:
            if self._move_gives_checkmate(board, move):
                return move
                
        # Prioritize captures
        capture_moves = self._get_capture_moves(board, moves)
        if capture_moves:
            # Choose the best capture (highest value piece)
            return self._choose_best_capture(board, capture_moves)
            
        # Check for moves that put opponent in check
        check_moves = []
        for move in moves:
            if self._move_gives_check(board, move):
                check_moves.append(move)
                
        if check_moves:
            return random.choice(check_moves)
            
        # Avoid moves that lose pieces
        safe_moves = self._filter_safe_moves(board, moves)
        if safe_moves:
            # Prefer center control
            center_moves = []
            for move in safe_moves:
                to_row, to_col = move[1]
                if 2 <= to_row <= 5 and 2 <= to_col <= 5:
                    center_moves.append(move)
            
            if center_moves:
                return random.choice(center_moves)
            return random.choice(safe_moves)
            
        return random.choice(moves)
        
    def _get_hard_move(self, board):
        """Hard AI - Good tactics, protects pieces, controls center."""
        moves = self._get_all_legal_moves(board)
        if not moves:
            return None
            
        # Always check for immediate checkmate
        for move in moves:
            if self._move_gives_checkmate(board, move):
                return move
                
        # Use minimax with depth 2
        best_move = None
        best_score = -999999
        
        for move in moves:
            score = self._minimax(board, 2, -999999, 999999, False, move)
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
        
    def _get_very_hard_move(self, board):
        """Very Hard AI - Strong tactics and strategy."""
        moves = self._get_all_legal_moves(board)
        if not moves:
            return None
            
        # Always check for immediate checkmate
        for move in moves:
            if self._move_gives_checkmate(board, move):
                return move
                
        # Order moves for better search
        moves = self._order_moves(board, moves)
        
        # Use minimax with depth 3
        best_move = None
        best_score = -999999
        
        for move in moves:
            score = self._minimax(board, 3, -999999, 999999, False, move)
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
        """Evaluate board position."""
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
                        
                # Position bonus based on piece type
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
        
    def _get_capture_moves(self, board, moves):
        """Filter moves that capture opponent pieces."""
        captures = []
        for move in moves:
            to_row, to_col = move[1]
            target = board.get_piece(to_row, to_col)
            if target and target[0] == 'w':
                captures.append(move)
        return captures
        
    def _choose_best_capture(self, board, capture_moves):
        """Choose capture of highest value piece."""
        best_move = None
        best_value = -1
        
        for move in capture_moves:
            from_row, from_col = move[0]
            to_row, to_col = move[1]
            
            attacker = board.get_piece(from_row, from_col)
            target = board.get_piece(to_row, to_col)
            
            if target:
                # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
                target_value = self.piece_values[target[1]]
                attacker_value = self.piece_values[attacker[1]]
                
                # Prefer capturing with less valuable pieces
                capture_score = target_value * 10 - attacker_value
                
                if capture_score > best_value:
                    best_value = capture_score
                    best_move = move
                    
        return best_move or capture_moves[0]
        
    def _filter_safe_moves(self, board, moves):
        """Filter out moves that would lose pieces."""
        safe = []
        for move in moves:
            if not self._move_loses_piece(board, move):
                safe.append(move)
        return safe if safe else moves
        
    def _filter_bad_moves(self, board, moves):
        """Find moves that lose pieces (for easy AI to blunder)."""
        bad = []
        for move in moves:
            if self._move_loses_piece(board, move):
                bad.append(move)
        return bad
        
    def _move_loses_piece(self, board, move):
        """Check if a move would result in losing the piece."""
        from_row, from_col = move[0]
        to_row, to_col = move[1]
        
        piece = board.get_piece(from_row, from_col)
        original_target = board.get_piece(to_row, to_col)
        
        # Make move
        board.set_piece(to_row, to_col, piece)
        board.set_piece(from_row, from_col, "")
        
        # Check if piece can be captured
        is_attacked = self._square_is_attacked(board, to_row, to_col, 'w')
        
        # Undo move
        board.set_piece(from_row, from_col, piece)
        board.set_piece(to_row, to_col, original_target)
        
        # If we're capturing something valuable, it might be worth it
        if original_target and is_attacked:
            our_value = self.piece_values[piece[1]]
            their_value = self.piece_values[original_target[1]]
            if their_value >= our_value:
                return False  # Good trade
                
        return is_attacked
        
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