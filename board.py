"""
Chess Board Logic and Piece Movement
Enhanced with Powerup System Integration
"""

import pygame

class ChessBoard:
    def __init__(self):
        self.scale = 1.0
        self.reset()
        
    def reset(self):
        """Reset board to starting position."""
        from config import INITIAL_BOARD, STARTING_PLAYER
        self.board = [row[:] for row in INITIAL_BOARD]
        self.current_turn = STARTING_PLAYER
        self.selected_piece = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        self.captured_pieces = {"white": [], "black": []}
        
        # Animation state
        self.animating = False
        self.animation_start = 0
        self.animation_from = None
        self.animation_to = None
        self.animation_piece = None
        
        # Drag state
        self.dragging = False
        self.drag_piece = None
        self.drag_start = None
        
        # Promotion
        self.promoting = False
        self.promotion_square = None
        self.promotion_color = None
        
        # Powerup system reference (will be set by game)
        self.powerup_system = None
        
    def set_powerup_system(self, powerup_system):
        """Set reference to powerup system."""
        self.powerup_system = powerup_system
        
    def update_scale(self, scale):
        """Update the scale factor for fullscreen mode."""
        self.scale = scale
        
    def get_piece(self, row, col):
        """Get piece at position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return ""
        
    def set_piece(self, row, col, piece):
        """Set piece at position."""
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece
            
    def get_square_pos(self, row, col):
        """Convert row/col to pixel position."""
        import config
        # Calculate the position within the board first (unscaled)
        x = config.BOARD_BORDER_LEFT + col * config.SQUARE_SIZE
        y = config.BOARD_BORDER_TOP + row * config.SQUARE_SIZE
        
        # Then scale and add the board offset
        x = config.BOARD_OFFSET_X + x * self.scale
        y = config.BOARD_OFFSET_Y + y * self.scale
        return x, y
        
    def get_square_from_pos(self, pos):
        """Convert pixel position to row/col."""
        import config
        x, y = pos
        # First remove the board offset, then scale, then remove border
        board_x = ((x - config.BOARD_OFFSET_X) / self.scale) - config.BOARD_BORDER_LEFT
        board_y = ((y - config.BOARD_OFFSET_Y) / self.scale) - config.BOARD_BORDER_TOP
        
        if 0 <= board_x < config.PLAYING_AREA_WIDTH and 0 <= board_y < config.PLAYING_AREA_HEIGHT:
            return int(board_y // config.SQUARE_SIZE), int(board_x // config.SQUARE_SIZE)
        return -1, -1
        
    def is_valid_selection(self, row, col):
        """Check if piece belongs to current player."""
        piece = self.get_piece(row, col)
        if not piece:
            return False
        piece_color = "white" if piece[0] == 'w' else "black"
        return piece_color == self.current_turn
        
    def find_king(self, color):
        """Find the king's position for given color."""
        king = "wK" if color == "white" else "bK"
        for row in range(8):
            for col in range(8):
                if self.get_piece(row, col) == king:
                    return (row, col)
        return None
        
    def is_in_check(self):
        """Check if current player's king is in check."""
        king_pos = self.find_king(self.current_turn)
        if not king_pos:
            return False
        
        opponent_color = "b" if self.current_turn == "white" else "w"
        
        # Check all opponent pieces
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece[0] == opponent_color:
                    # For check detection, ignore shields (you can put a king in check even if it's shielded)
                    moves = self.get_valid_moves(row, col, ignore_shields=True)
                    if king_pos in moves:
                        return True
        return False
        
    def get_valid_moves(self, row, col, ignore_shields=False):
        """Get all valid moves for piece at row/col."""
        piece = self.get_piece(row, col)
        if not piece:
            return []
            
        piece_type = piece[1]
        piece_color = piece[0]
        moves = []
        
        if piece_type == 'P':  # Pawn
            direction = -1 if piece_color == 'w' else 1
            start_row = 6 if piece_color == 'w' else 1
            
            # Forward one
            new_row = row + direction
            if 0 <= new_row < 8 and self.get_piece(new_row, col) == "":
                moves.append((new_row, col))
                
                # Forward two from start
                if row == start_row:
                    new_row2 = row + direction * 2
                    if self.get_piece(new_row2, col) == "":
                        moves.append((new_row2, col))
                        
            # Capture diagonally
            for dc in [-1, 1]:
                new_col = col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = self.get_piece(new_row, new_col)
                    if target and target[0] != piece_color:
                        # Check if target is shielded
                        if ignore_shields or (self.powerup_system and not self.powerup_system.is_piece_shielded(new_row, new_col)) or not self.powerup_system:
                            moves.append((new_row, new_col))
                        
        elif piece_type == 'R':  # Rook
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                for i in range(1, 8):
                    nr, nc = row + dr*i, col + dc*i
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    target = self.get_piece(nr, nc)
                    if target == "":
                        moves.append((nr, nc))
                    else:
                        if target[0] != piece_color:
                            # Check if target is shielded
                            if ignore_shields or (self.powerup_system and not self.powerup_system.is_piece_shielded(nr, nc)) or not self.powerup_system:
                                moves.append((nr, nc))
                        break
                        
        elif piece_type == 'N':  # Knight
            for dr, dc in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.get_piece(nr, nc)
                    if target == "":
                        moves.append((nr, nc))
                    elif target[0] != piece_color:
                        if ignore_shields or (self.powerup_system and not self.powerup_system.is_piece_shielded(nr, nc)) or not self.powerup_system:
                            moves.append((nr, nc))
                        
        elif piece_type == 'B':  # Bishop
            for dr, dc in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                for i in range(1, 8):
                    nr, nc = row + dr*i, col + dc*i
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    target = self.get_piece(nr, nc)
                    if target == "":
                        moves.append((nr, nc))
                    else:
                        if target[0] != piece_color:
                            # Check if target is shielded
                            if ignore_shields or (self.powerup_system and not self.powerup_system.is_piece_shielded(nr, nc)) or not self.powerup_system:
                                moves.append((nr, nc))
                        break
                        
        elif piece_type == 'Q':  # Queen
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                for i in range(1, 8):
                    nr, nc = row + dr*i, col + dc*i
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    target = self.get_piece(nr, nc)
                    if target == "":
                        moves.append((nr, nc))
                    else:
                        if target[0] != piece_color:
                            # Check if target is shielded
                            if ignore_shields or (self.powerup_system and not self.powerup_system.is_piece_shielded(nr, nc)) or not self.powerup_system:
                                moves.append((nr, nc))
                        break
                        
        elif piece_type == 'K':  # King
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.get_piece(nr, nc)
                    if target == "":
                        moves.append((nr, nc))
                    elif target[0] != piece_color:
                        if ignore_shields or (self.powerup_system and not self.powerup_system.is_piece_shielded(nr, nc)) or not self.powerup_system:
                            moves.append((nr, nc))
                        
        return moves
        
    def start_move(self, from_row, from_col, to_row, to_col):
        """Start animated move."""
        self.animating = True
        self.animation_start = pygame.time.get_ticks()
        self.animation_from = (from_row, from_col)
        self.animation_to = (to_row, to_col)
        self.animation_piece = self.get_piece(from_row, from_col)
        
    def complete_move(self):
        """Complete the animated move."""
        if not self.animating:
            return None
            
        from_row, from_col = self.animation_from
        to_row, to_col = self.animation_to
        piece = self.animation_piece
        
        # Move shield if piece is shielded
        if self.powerup_system:
            self.powerup_system.move_shield((from_row, from_col), (to_row, to_col))
        
        # Check for capture
        captured = self.get_piece(to_row, to_col)
        if captured:
            # Track captured piece
            capturing_color = "white" if piece[0] == 'w' else "black"
            self.captured_pieces[capturing_color].append(captured)
            
            # Award points for capture
            if self.powerup_system:
                points = self.powerup_system.add_points_for_capture(captured, capturing_color)
                print(f"{capturing_color} earned {points} points for capturing {captured}")
            
            # Check for game over
            if captured[1] == 'K':
                self.game_over = True
                self.winner = self.current_turn
                
        # Make the move
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, "")
        
        # Check for promotion
        if piece[1] == 'P':
            if (piece[0] == 'w' and to_row == 0) or (piece[0] == 'b' and to_row == 7):
                self.promoting = True
                self.promotion_square = (to_row, to_col)
                self.promotion_color = piece[0]
                self.animating = False
                return captured
                
        # Switch turns
        if not self.game_over:
            self.current_turn = "black" if self.current_turn == "white" else "white"
            # Update shield counters on turn change
            if self.powerup_system:
                self.powerup_system.update_shields()
            
        self.animating = False
        return captured
        
    def promote_pawn(self, piece_type):
        """Promote pawn to chosen piece."""
        if self.promoting and self.promotion_square:
            row, col = self.promotion_square
            self.set_piece(row, col, self.promotion_color + piece_type)
            self.promoting = False
            self.current_turn = "black" if self.current_turn == "white" else "white"
            # Update shield counters on turn change
            if self.powerup_system:
                self.powerup_system.update_shields()