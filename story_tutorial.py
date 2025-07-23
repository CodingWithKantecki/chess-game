"""
Story Mode Tutorial Integration - BULLETPROOF VERSION 3.0
Perfect tutorial with strategic powerup integration and movement restrictions
"""

import pygame
import config

class StoryTutorial:
    def __init__(self, game, board, powerup_system):
        self.game = game
        self.board = board
        self.powerup_system = powerup_system
        
        # Tutorial state
        self.active = False
        self.current_step = 0
        self.tutorial_complete = False
        
        # Visual hints
        self.highlight_squares = []
        self.instruction_text = ""
        self.waiting_for_action = False
        
        # Movement restrictions
        self.allowed_pieces = []  # Only these pieces can be moved
        self.forbidden_squares = []  # These squares cannot be clicked
        
        # STRATEGIC TUTORIAL WITH POWERUP INTEGRATION
        self.tutorial_steps = [
            # PHASE 1: Opening Development
            {
                "instruction": "Welcome to Chess Protocol! Control the center with your e2 pawn.",
                "highlight": [(4, 6)],
                "wait_for": "piece_select",
                "target_piece": (4, 6),
                "allowed_pieces": [(4, 6)],  # Only e2 pawn can move
                "completion_text": "Good! Center control is key in chess."
            },
            {
                "instruction": "Move your pawn to e4 - this controls key central squares!",
                "highlight": [(4, 4)],
                "wait_for": "move",
                "from_square": (4, 6),
                "to_square": (4, 4),
                "completion_text": "Perfect! You control d5 and f5."
            },
            {
                "instruction": "Enemy responds with e5...",
                "wait_for": "ai_move",
                "completion_text": "A classic opening!"
            },
            
            # PHASE 2: Simple Knight Development
            {
                "instruction": "Develop your knight! Click the knight on g1.",
                "highlight": [(6, 7)],
                "wait_for": "piece_select",
                "target_piece": (6, 7),
                "allowed_pieces": [(6, 7)],  # Only g1 knight
                "completion_text": "Good choice!"
            },
            {
                "instruction": "Move to f3 - knights control the center best from here!",
                "highlight": [(5, 5)],
                "wait_for": "move",
                "from_square": (6, 7),
                "to_square": (5, 5),
                "completion_text": "Perfect knight development!"
            },
            
            # PHASE 3: Wait for black to play something capturable
            {
                "instruction": "Enemy pushes another pawn forward...",
                "wait_for": "ai_move",
                "completion_text": "Now we can capture!"
            },
            
            # PHASE 4: Simple Capture Demo with Knight
            {
                "instruction": "CAPTURE OPPORTUNITY! Click your knight on f3!",
                "highlight": [(5, 5)],
                "wait_for": "piece_select", 
                "target_piece": (5, 5),
                "allowed_pieces": [(5, 5)],
                "completion_text": "Ready to capture!"
            },
            {
                "instruction": "Capture the black pawn on e5! Knights can jump!",
                "highlight": [(4, 3)],
                "wait_for": "move",
                "from_square": (5, 5),
                "to_square": (4, 3),
                "completion_text": "CAPTURE! +1 point! Points buy powerups!"
            },
            
            # PHASE 4: Strategic Arms Acquisition
            {
                "instruction": "Now you have 1 point from capturing! Let's get WEAPONS! Click 'VISIT ARMS DEALER'!",
                "wait_for": "arms_dealer_visit",
                "completion_text": "Time to meet Tariq!"
            },
            {
                "instruction": "🎁 TUTORIAL GIFT: Full arsenal unlocked! All weapons free for learning!",
                "wait_for": "tutorial_gift_complete",
                "completion_text": "Arsenal loaded! Ready for tactical warfare!"
            },
            {
                "instruction": "Return to dominate the battlefield! Click 'BACK TO GAME'!",
                "wait_for": "return_to_game",
                "completion_text": "Back to tactical chess!"
            },
            
            # PHASE 5: Defensive Tactics - Shield Usage
            {
                "instruction": "Your pawn on e5 is advanced and vulnerable. Click the SHIELD button (blue shield icon) for protection!",
                "wait_for": "powerup_select",
                "target_powerup": "shield",
                "highlight_powerup": "shield",
                "completion_text": "Shield ready! Choose your protected piece."
            },
            {
                "instruction": "Shield your brave pawn on e5! Click on it!",
                "highlight": [(4, 3)],
                "wait_for": "powerup_use",
                "powerup_type": "shield",
                "target_square": (4, 3),
                "completion_text": "Pawn protected! 3 turns of invulnerability."
            },
            {
                "instruction": "Enemy tries to attack your pawn but fails...",
                "wait_for": "ai_move",
                "completion_text": "Shield deflected their attack! Defensive success."
            },
            
            # PHASE 6: Aggressive Tactics - Gun Usage
            {
                "instruction": "Time for aggressive tactics! Click the GUN button (revolver icon) for precision elimination!",
                "wait_for": "powerup_select", 
                "target_powerup": "gun",
                "highlight_powerup": "gun",
                "completion_text": "Gun loaded! Select your target."
            },
            {
                "instruction": "ELIMINATE their most valuable piece - the BLACK QUEEN on a5! Click on her!",
                "highlight": [(0, 3)],
                "wait_for": "powerup_use",
                "powerup_type": "gun",
                "target_square": (0, 3),
                "completion_text": "QUEEN ELIMINATED! Devastating tactical blow!"
            },
            {
                "instruction": "Enemy is in shock, plays desperately...",
                "wait_for": "ai_move",
                "completion_text": "Without their queen, they're helpless!"
            },
            
            # PHASE 7: Area Control - Airstrike
            {
                "instruction": "Control the battlefield! Click the AIRSTRIKE button (bomb icon) to clear their pieces!",
                "wait_for": "powerup_select",
                "target_powerup": "airstrike", 
                "highlight_powerup": "airstrike",
                "completion_text": "Airstrike ready! Choose target zone."
            },
            {
                "instruction": "Bomb their rook on b8 to destroy multiple pieces!",
                "highlight": [(1, 0)],
                "wait_for": "powerup_use",
                "powerup_type": "airstrike",
                "target_square": (1, 0),
                "completion_text": "AIRSTRIKE SUCCESSFUL! Area denial complete!"
            },
            {
                "instruction": "Enemy's position collapses...",
                "wait_for": "ai_move",
                "completion_text": "Their army is decimated!"
            },
            
            # PHASE 8: Reinforcement - Paratroopers
            {
                "instruction": "Secure your advantage! Click the PARATROOPERS button (soldier icon) for battlefield control!",
                "wait_for": "powerup_select",
                "target_powerup": "paratroopers",
                "highlight_powerup": "paratroopers",
                "completion_text": "Paratroopers ready! Choose drop zones."
            },
            {
                "instruction": "Drop troops on e6 for central control! (1/3)",
                "highlight": [(4, 2)],
                "wait_for": "powerup_use",
                "powerup_type": "paratroopers",
                "target_square": (4, 2),
                "completion_text": "First wave deployed!"
            },
            {
                "instruction": "Second drop at f6! (2/3)",
                "highlight": [(5, 2)],
                "wait_for": "powerup_use", 
                "powerup_type": "paratroopers",
                "target_square": (5, 2),
                "completion_text": "Second wave landed!"
            },
            {
                "instruction": "Final drop at d6! (3/3)",
                "highlight": [(3, 2)],
                "wait_for": "powerup_use",
                "powerup_type": "paratroopers",
                "target_square": (3, 2),
                "completion_text": "BATTLEFIELD SECURED! Total control achieved!"
            },
            
            # PHASE 9: Ultimate Power - Chopper Usage
            {
                "instruction": "Final weapon demonstration! Click the CHOPPER button (helicopter icon) for TOTAL DOMINATION!",
                "wait_for": "powerup_select",
                "target_powerup": "chopper",
                "highlight_powerup": "chopper",
                "completion_text": "Chopper inbound! Click ANY square to activate!"
            },
            {
                "instruction": "Activate the chopper anywhere on the board! Click any square!",
                "highlight": [(4, 4)],  # Highlight center as suggestion
                "wait_for": "powerup_use",
                "powerup_type": "chopper",
                "completion_text": "CHOPPER DEVASTATION! Minigun + bombs = total destruction!"
            },
            {
                "instruction": "Enemy surrenders in the face of overwhelming firepower...",
                "wait_for": "ai_move",
                "completion_text": "Complete tactical superiority achieved!"
            },
            
            # PHASE 10: Victory
            {
                "instruction": "🎯 PERFECT! You've mastered chess tactics + modern warfare! You win through superior strategy!",
                "wait_for": "none",
                "completion_text": "🏆 TACTICAL MASTERY ACHIEVED!"
            }
        ]
        
        # STRATEGIC AI SEQUENCE - Simple tutorial moves
        self.ai_move_sequence = [
            [(4, 1), (4, 3)],      # 1. e7-e5 (black plays e5 in response to e4)
            [(3, 1), (3, 2)],      # 2. d7-d6 (black develops, e5 pawn stays there)
            [(0, 2), (1, 3)],      # 4. Bc8-d7 (developing bishop)
            [(3, 0), (0, 3)],      # 5. Qd8-a5 (queen comes out, gets shot by gun)
            [(1, 0), (2, 0)],      # 6. a7-a6 (desperate pawn push)
            [(6, 0), (5, 2)],      # 7. Ng8-f6 (other knight develops)
            [(0, 0), (1, 0)],      # 8. Ra8-b8 (rook moves to be bombed)
            [(1, 6), (2, 6)],      # 9. g7-g6 (preparing fianchetto)
            [(0, 4), (0, 3)],      # 10. Ke8-d8 (king moves away from danger)
        ]
        self.current_ai_move = 0
        
    def start_tutorial(self):
        """Start the bulletproof tutorial."""
        self.active = True
        self.current_step = 0
        self.tutorial_complete = False
        self.current_ai_move = 0
        
        # Reset board to standard position
        self.board.reset()
        
        # Reset powerups to just shield at tutorial start
        import config
        config.reset_tutorial_powerups()
        
        # Initialize restrictions
        self._update_restrictions()
        self._show_current_step()
        
    def _update_restrictions(self):
        """Update movement restrictions based on current step."""
        if self.current_step < len(self.tutorial_steps):
            step = self.tutorial_steps[self.current_step]
            self.allowed_pieces = step.get("allowed_pieces", [])
            self.forbidden_squares = step.get("forbidden_squares", [])
        else:
            self.allowed_pieces = []
            self.forbidden_squares = []
    
    def can_select_piece(self, row, col):
        """Check if a piece can be selected."""
        if not self.active:
            return True
            
        # If no restrictions, allow all
        if not self.allowed_pieces:
            return True
            
        # Check if this piece is allowed
        return (col, row) in self.allowed_pieces
    
    def get_next_ai_move(self):
        """Get next AI move."""
        if self.current_ai_move < len(self.ai_move_sequence):
            move = self.ai_move_sequence[self.current_ai_move]
            self.current_ai_move += 1
            return move
        return None
        
    def should_override_ai(self):
        """Check if tutorial should override AI."""
        return self.active and self.current_ai_move < len(self.ai_move_sequence)
        
    def validate_player_move(self, from_row, from_col, to_row, to_col):
        """Validate player move against tutorial restrictions."""
        if not self.active or not self.waiting_for_action:
            return True
            
        # Check piece selection restrictions
        if not self.can_select_piece(from_row, from_col):
            print(f"Tutorial: Can't move that piece! Only specific pieces allowed.")
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "move":
            expected_from = step.get("from_square")
            expected_to = step.get("to_square")
            
            if expected_from and expected_to:
                actual_from = (from_col, from_row)
                actual_to = (to_col, to_row)
                
                if actual_from != expected_from or actual_to != expected_to:
                    print(f"Tutorial: Wrong move! Expected {expected_from}→{expected_to}, got {actual_from}→{actual_to}")
                    return False
                    
        return True
        
    def stop_tutorial(self):
        """Stop tutorial."""
        self.active = False
        self.highlight_squares = []
        self.instruction_text = ""
        self.allowed_pieces = []
        self.forbidden_squares = []
        
    def _show_current_step(self):
        """Show current step."""
        if self.current_step >= len(self.tutorial_steps):
            self._complete_tutorial()
            return
            
        step = self.tutorial_steps[self.current_step]
        self.instruction_text = step["instruction"]
        self.highlight_squares = step.get("highlight", [])
        self.waiting_for_action = True
        
        # Update restrictions for this step
        self._update_restrictions()
        
        print(f"Tutorial Step {self.current_step}: {step['instruction']}")
        
    def _complete_tutorial(self):
        """Complete tutorial."""
        self.tutorial_complete = True
        self.active = False
        self.instruction_text = "Tutorial complete! You're now a tactical master!"
        self.highlight_squares = []
        self.allowed_pieces = []
        self.forbidden_squares = []
        
    def handle_piece_select(self, row, col):
        """Handle piece selection."""
        if not self.active or not self.waiting_for_action:
            return False
            
        # Check restrictions first
        if not self.can_select_piece(row, col):
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "piece_select":
            target = step.get("target_piece")
            if target and (col, row) == target:
                self._advance_step()
                return True
                
        return False
        
    def handle_move(self, from_row, from_col, to_row, to_col):
        """Handle moves."""
        if not self.active or not self.waiting_for_action:
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "move":
            from_target = step.get("from_square")
            to_target = step.get("to_square")
            
            if (from_target and (from_col, from_row) == from_target and 
                to_target and (to_col, to_row) == to_target):
                self._advance_step()
                return True
                
        return False
        
    def handle_ai_move(self):
        """Handle AI moves."""
        if not self.active:
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "ai_move":
            pygame.time.set_timer(pygame.USEREVENT + 2, 800)
            return True
            
        return False
        
    def handle_ai_move_complete(self):
        """Handle AI move complete."""
        if not self.active:
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "ai_move":
            self._advance_step()
            return True
            
        return False
        
    def force_check_ai_move(self):
        """Force check AI move."""
        if not self.active:
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "ai_move":
            self._advance_step()
            return True
            
        return False
        
    def handle_powerup_select(self, powerup_key):
        """Handle powerup selection."""
        if not self.active or not self.waiting_for_action:
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "powerup_select":
            target = step.get("target_powerup")
            if target == powerup_key:
                self._advance_step()
                return True
                
        return False
        
    def handle_powerup_use(self, powerup_type, row, col):
        """Handle powerup use."""
        if not self.active or not self.waiting_for_action:
            return False
            
        step = self.tutorial_steps[self.current_step]
        
        if step.get("wait_for") == "powerup_use":
            target_type = step.get("powerup_type")
            target_square = step.get("target_square")
            
            # Check powerup type matches
            if target_type != powerup_type:
                return False
                
            # Check target square if specified
            if target_square and (col, row) != target_square:
                print(f"Tutorial: Wrong target! Click the highlighted square.")
                return False
                
            self._advance_step()
            return True
                
        return False
        
    def handle_arms_dealer_visit(self):
        """Handle arms dealer visit."""
        if not self.active:
            return
            
        step = self.tutorial_steps[self.current_step]
        if step.get("wait_for") == "arms_dealer_visit":
            self._advance_step()
            
    def handle_tutorial_gift_complete(self):
        """Handle tutorial gift - unlock everything and show it."""
        if not self.active:
            return
            
        step = self.tutorial_steps[self.current_step] 
        if step.get("wait_for") == "tutorial_gift_complete":
            # Give massive points
            if hasattr(self.powerup_system, 'points'):
                self.powerup_system.points["white"] = 9999
                
            # Unlock ALL powerups using the new function
            import config
            config.unlock_all_powerups_for_tutorial()
            
            print("Tutorial: ALL WEAPONS UNLOCKED AND VISIBLE IN UI!")
                
            self._advance_step()
    
    def _advance_step(self):
        """Advance to next step."""
        if self.current_step < len(self.tutorial_steps):
            step = self.tutorial_steps[self.current_step]
            if "completion_text" in step:
                print(f"Tutorial: {step['completion_text']}")
                
        self.current_step += 1
        self.waiting_for_action = False
        
        # Update restrictions for new step
        self._update_restrictions()
        
        # Show next step
        pygame.time.set_timer(pygame.USEREVENT + 1, 200)
        
    def handle_timer_event(self):
        """Handle timer events."""
        self._show_current_step()
        
    def get_current_instruction(self):
        """Get current instruction."""
        return self.instruction_text
        
    def get_highlight_squares(self):
        """Get highlight squares."""
        return self.highlight_squares
        
    def get_highlight_powerup(self):
        """Get the powerup that should be highlighted."""
        if self.active and self.current_step < len(self.tutorial_steps):
            step = self.tutorial_steps[self.current_step]
            return step.get("highlight_powerup", None)
        return None
        
    def is_waiting_for_action(self):
        """Check if waiting for action."""
        return self.active and self.waiting_for_action
        
    def should_show_hints(self):
        """Check if should show hints."""
        return self.active and not self.tutorial_complete

    def check_timeout(self):
        """Check timeout."""
        return False
        
    def handle_move_start(self, from_row, from_col):
        """Handle when a piece is picked up to move."""
        return False
        
    def get_allowed_pieces(self):
        """Get list of pieces that can be moved."""
        return self.allowed_pieces if self.active else []