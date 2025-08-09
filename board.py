"""
Chess Board Logic and Piece Movement FINAL
Enhanced with Powerup System Integration
"""

import pygame

class ChessBoard:
    def __init__(self):
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
        
        # Castling rights
        self.castling_rights = {
            "white": {"kingside": True, "queenside": True},
            "black": {"kingside": True, "queenside": True}
        }
        
        # En passant
        self.en_passant_target = None  # (row, col) of square where en passant capture can occur
        
        # Game state
        self.is_check = False
        self.is_checkmate = False
        self.is_stalemate = False
        
    def set_powerup_system(self, powerup_system):
        """Set reference to powerup system."""
        self.powerup_system = powerup_system
        
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
        # Calculate the position within the board
        x = config.BOARD_BORDER_LEFT + col * config.SQUARE_SIZE
        y = config.BOARD_BORDER_TOP + row * config.SQUARE_SIZE
        
        # Add the board offset
        x = config.BOARD_OFFSET_X + x
        y = config.BOARD_OFFSET_Y + y
        return x, y
        
    def get_square_from_pos(self, pos):
        """Convert pixel position to row/col."""
        import config
        x, y = pos
        # First remove the board offset, then remove border
        board_x = (x - config.BOARD_OFFSET_X) - config.BOARD_BORDER_LEFT
        board_y = (y - config.BOARD_OFFSET_Y) - config.BOARD_BORDER_TOP
        
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
                        if self.powerup_system and self.powerup_system.is_piece_shielded(new_row, new_col) and not ignore_shields:
                            pass  # Skip shielded pieces
                        else:
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
                            if self.powerup_system and self.powerup_system.is_piece_shielded(nr, nc) and not ignore_shields:
                                pass  # Skip shielded pieces
                            else:
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
                            if self.powerup_system and self.powerup_system.is_piece_shielded(nr, nc) and not ignore_shields:
                                pass  # Skip shielded pieces
                            else:
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
                            if self.powerup_system and self.powerup_system.is_piece_shielded(nr, nc) and not ignore_shields:
                                pass  # Skip shielded pieces
                            else:
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
        
        # Add castling moves for king (only check when not called from is_square_attacked)
        if piece_type == 'K' and not ignore_shields:
            # Check castling rights
            color_name = "white" if piece_color == 'w' else "black"
            
            # Kingside castling
            if self.castling_rights[color_name]["kingside"]:
                # Check if squares between king and rook are empty
                if (self.get_piece(row, 5) == "" and 
                    self.get_piece(row, 6) == "" and
                    not self.is_square_attacked(row, 5, piece_color) and
                    not self.is_square_attacked(row, 6, piece_color)):
                    # Check if rook is in place
                    rook = self.get_piece(row, 7)
                    if rook == piece_color + 'R':
                        moves.append((row, 6))  # King moves to g-file
            
            # Queenside castling  
            if self.castling_rights[color_name]["queenside"]:
                # Check if squares between king and rook are empty
                if (self.get_piece(row, 1) == "" and 
                    self.get_piece(row, 2) == "" and
                    self.get_piece(row, 3) == "" and
                    not self.is_square_attacked(row, 2, piece_color) and
                    not self.is_square_attacked(row, 3, piece_color)):
                    # Check if rook is in place
                    rook = self.get_piece(row, 0)
                    if rook == piece_color + 'R':
                        moves.append((row, 2))  # King moves to c-file
        
        # Add en passant for pawns
        if piece_type == 'P' and self.en_passant_target:
            ep_row, ep_col = self.en_passant_target
            # Check if pawn is in position to capture en passant
            if row == (3 if piece_color == 'w' else 4):  # Correct rank for en passant
                if abs(col - ep_col) == 1 and ep_row == row + (-1 if piece_color == 'w' else 1):
                    moves.append((ep_row, ep_col))
                        
        return moves
    
    def is_square_attacked(self, row, col, by_color):
        """Check if a square is attacked by the given color."""
        opponent_color = 'b' if by_color == 'w' else 'w'
        
        # Check all opponent pieces
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece and piece[0] == opponent_color:
                    # Get moves for this piece (ignoring shields for attack detection)
                    moves = self.get_valid_moves(r, c, ignore_shields=True)
                    if (row, col) in moves:
                        return True
        return False
    
    def would_be_in_check(self, from_row, from_col, to_row, to_col, color):
        """Check if a move would leave the king in check."""
        # Make the move temporarily
        piece = self.get_piece(from_row, from_col)
        captured = self.get_piece(to_row, to_col)
        
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, "")
        
        # Handle en passant capture
        if piece and piece[1] == 'P' and self.en_passant_target == (to_row, to_col):
            # Remove the captured pawn
            capture_row = to_row + (1 if piece[0] == 'w' else -1)
            en_passant_captured = self.get_piece(capture_row, to_col)
            self.set_piece(capture_row, to_col, "")
        else:
            en_passant_captured = None
        
        # Find king position
        king_pos = self.find_king(color)
        in_check = False
        
        if king_pos:
            in_check = self.is_square_attacked(king_pos[0], king_pos[1], color[0])
        
        # Undo the move
        self.set_piece(from_row, from_col, piece)
        self.set_piece(to_row, to_col, captured)
        
        # Restore en passant captured pawn if needed
        if en_passant_captured:
            capture_row = to_row + (1 if piece[0] == 'w' else -1)
            self.set_piece(capture_row, to_col, en_passant_captured)
        
        return in_check
    
    def get_legal_moves(self, row, col):
        """Get all legal moves for a piece (moves that don't leave king in check)."""
        piece = self.get_piece(row, col)
        if not piece:
            return []
        
        color = "white" if piece[0] == 'w' else "black"
        all_moves = self.get_valid_moves(row, col)
        legal_moves = []
        
        for move_row, move_col in all_moves:
            if not self.would_be_in_check(row, col, move_row, move_col, color):
                legal_moves.append((move_row, move_col))
        
        return legal_moves
    
    def has_legal_moves(self, color):
        """Check if a color has any legal moves."""
        piece_color = 'w' if color == "white" else 'b'
        
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece[0] == piece_color:
                    if len(self.get_legal_moves(row, col)) > 0:
                        return True
        return False
    
    def check_game_state(self):
        """Check for check, checkmate, or stalemate."""
        # Check if current player is in check
        king_pos = self.find_king(self.current_turn)
        if king_pos:
            self.is_check = self.is_square_attacked(king_pos[0], king_pos[1], self.current_turn[0])
        else:
            self.is_check = False
        
        # Check if current player has any legal moves
        if not self.has_legal_moves(self.current_turn):
            if self.is_check:
                # Checkmate
                self.is_checkmate = True
                self.game_over = True
                self.winner = "black" if self.current_turn == "white" else "white"
            else:
                # Stalemate
                self.is_stalemate = True
                self.game_over = True
                self.winner = None  # Draw
        else:
            self.is_checkmate = False
            self.is_stalemate = False
        
    def start_move(self, from_row, from_col, to_row, to_col):
        """Start animated move."""
        # SAFETY CHECK: Validate move is legal before starting animation
        piece = self.get_piece(from_row, from_col)
        target = self.get_piece(to_row, to_col)
        
        if piece:
            legal_moves = self.get_legal_moves(from_row, from_col)
            if (to_row, to_col) not in legal_moves:
                print(f"ILLEGAL MOVE BLOCKED: {piece} from ({from_row},{from_col}) to ({to_row},{to_col})")
                if target:
                    print(f"  Attempted to capture: {target}")
                print(f"  Legal moves for {piece}: {legal_moves}")
                
                # Special check for knight moves
                if piece[1] == 'N':
                    row_diff = abs(to_row - from_row)
                    col_diff = abs(to_col - from_col)
                    print(f"  Knight move check: row_diff={row_diff}, col_diff={col_diff}")
                    print(f"  Valid knight move pattern: {(row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)}")
                
                # Don't execute illegal moves
                return
        
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
        
        if not piece:
            self.animating = False
            return None
        
        piece_color = "white" if piece[0] == 'w' else "black"
        
        # Check for castling
        if piece[1] == 'K' and abs(to_col - from_col) == 2:
            # This is a castling move
            if to_col > from_col:  # Kingside
                # Move rook from h-file to f-file
                rook = self.get_piece(from_row, 7)
                self.set_piece(from_row, 5, rook)
                self.set_piece(from_row, 7, "")
            else:  # Queenside
                # Move rook from a-file to d-file
                rook = self.get_piece(from_row, 0)
                self.set_piece(from_row, 3, rook)
                self.set_piece(from_row, 0, "")
        
        # Check for en passant capture
        en_passant_capture = False
        if piece[1] == 'P' and self.en_passant_target == (to_row, to_col):
            # This is an en passant capture
            en_passant_capture = True
            capture_row = to_row + (1 if piece[0] == 'w' else -1)
            captured = self.get_piece(capture_row, to_col)
            self.set_piece(capture_row, to_col, "")
        else:
            # Normal capture
            captured = self.get_piece(to_row, to_col)
        
        # Handle powerup shields
        if self.powerup_system:
            if captured and self.powerup_system.is_piece_shielded(to_row, to_col):
                print(f"ERROR: Attempting to capture shielded piece at ({to_row}, {to_col})!")
                self.animating = False
                return None
            
            # Move or remove shield
            if not captured:
                self.powerup_system.move_shield((from_row, from_col), (to_row, to_col))
            else:
                if self.powerup_system.is_piece_shielded(from_row, from_col):
                    self.powerup_system.remove_shield_at(from_row, from_col)
                if not en_passant_capture:
                    self.powerup_system.remove_shield_at(to_row, to_col)
                else:
                    capture_row = to_row + (1 if piece[0] == 'w' else -1)
                    self.powerup_system.remove_shield_at(capture_row, to_col)
        
        # Track captured piece
        if captured:
            capturing_color = "white" if piece[0] == 'w' else "black"
            self.captured_pieces[capturing_color].append(captured)
            
            # Award points for capture
            if self.powerup_system:
                points = self.powerup_system.add_points_for_capture(captured, capturing_color)
                print(f"{capturing_color} earned {points} points for capturing {captured}")
            
            # Fallback: If king is captured (shouldn't happen with legal moves), end game
            if captured[1] == 'K':
                print(f"WARNING: King captured! This shouldn't happen with proper move validation.")
                self.game_over = True
                self.winner = capturing_color
        
        # Make the move
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, "")
        
        # Update castling rights
        if piece[1] == 'K':
            # King moved, lose all castling rights
            self.castling_rights[piece_color] = {"kingside": False, "queenside": False}
        elif piece[1] == 'R':
            # Rook moved, lose castling on that side
            if from_col == 0:  # Queenside rook
                self.castling_rights[piece_color]["queenside"] = False
            elif from_col == 7:  # Kingside rook
                self.castling_rights[piece_color]["kingside"] = False
        
        # Update en passant target
        self.en_passant_target = None
        if piece[1] == 'P' and abs(to_row - from_row) == 2:
            # Pawn moved two squares, set en passant target
            self.en_passant_target = ((from_row + to_row) // 2, to_col)
        
        # Check for promotion
        if piece[1] == 'P':
            if (piece[0] == 'w' and to_row == 0) or (piece[0] == 'b' and to_row == 7):
                self.promoting = True
                self.promotion_square = (to_row, to_col)
                self.promotion_color = piece[0]
                self.animating = False
                return captured
        
        # Switch turns and check game state
        if not self.game_over:
            self.current_turn = "black" if self.current_turn == "white" else "white"
            
            # Check for checkmate/stalemate
            self.check_game_state()
            
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
            
            # Check for checkmate/stalemate after promotion
            self.check_game_state()
            
            # Update shield counters on turn change
            if self.powerup_system:
                self.powerup_system.update_shields()
