"""
Unified Tutorial System
Combines simple, story, and scripted tutorials into one flexible system
"""

import config

class TutorialSystem:
    """Unified tutorial system supporting multiple tutorial modes."""
    
    def __init__(self, game, board, powerup_system):
        self.game = game
        self.board = board
        self.powerup_system = powerup_system
        
        # State management
        self.active = False
        self.current_mode = None
        self.current_step = 0
        self.waiting_for_action = False
        
        # Tutorial data for different modes
        self._init_simple_mode()
        self._init_story_mode()
        self._init_scripted_mode()
        
        # Current tutorial data
        self.steps = []
        self.ai_move_sequence = []
        self.ai_move_index = 0
        self.waiting_for = None  # For state saving compatibility
        
    def _init_simple_mode(self):
        """Initialize simple tutorial mode data."""
        self.simple_steps = [
            {
                "text": "Welcome! Click your e2 pawn.",
                "highlight": [(4, 6)],
                "action": "select_piece",
                "wait_for": "piece_select",
                "target": (4, 6)
            },
            {
                "text": "Move it to e4!",
                "highlight": [(4, 4)],
                "action": "move_to",
                "wait_for": "move",
                "from": (4, 6),
                "to": (4, 4)
            },
            {
                "text": "Good! Now click the VISIT ARMS DEALER button to get your free Shield powerup!",
                "action": "visit_arms_dealer",
                "wait_for": "arms_dealer_visit"
            },
            {
                "text": "Tariq has given you the Shield for free! Click on it to select it.",
                "action": "buy_shield",
                "wait_for": "powerup_purchase",
                "target_powerup": "shield"
            },
            {
                "text": "Perfect! The Shield is yours! Click BACK TO GAME to use it.",
                "action": "return_to_game",
                "wait_for": "return_to_game"
            },
            {
                "text": "Great! Now click the SHIELD button on the right.",
                "highlight_powerup": "shield",
                "action": "select_powerup",
                "powerup": "shield"
            },
            {
                "text": "Click your king to protect it!",
                "highlight": [(4, 7)],
                "action": "use_powerup",
                "wait_for": "powerup_use",
                "target": (4, 7)
            },
            {
                "text": "Perfect! Your king is now shielded. Play freely!",
                "action": "free_play",
                "wait_for": "none"
            },
            {
                "text": "Tutorial complete! You've mastered the Shield powerup!",
                "action": "complete",
                "wait_for": "none"
            }
        ]
        
    def _init_story_mode(self):
        """Initialize story mode tutorial data."""
        self.story_steps = [
            # PHASE 1: Opening Development
            {
                "instruction": "Welcome to Checkmate Protocol! Control the center with your e2 pawn.",
                "highlight_squares": [(4, 6)],
                "wait_for": "piece_select",
                "target_piece": (4, 6),
                "allowed_pieces": [(4, 6)],  # Only e2 pawn can move
                "completion_text": "Good! Center control is key in chess."
            },
            {
                "instruction": "Move your pawn to e4 - this controls key central squares!",
                "highlight_squares": [(4, 4)],
                "wait_for": "move",
                "from_square": (4, 6),
                "to_square": (4, 4),
                "expected_move": ((4, 6), (4, 4)),
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
                "highlight_squares": [(6, 7)],
                "wait_for": "piece_select",
                "target_piece": (6, 7),
                "allowed_pieces": [(6, 7)],  # Only g1 knight
                "completion_text": "Good choice!"
            },
            {
                "instruction": "Move to f3 - knights control the center best from here!",
                "highlight_squares": [(5, 5)],
                "wait_for": "move",
                "from_square": (6, 7),
                "to_square": (5, 5),
                "expected_move": ((6, 7), (5, 5)),
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
                "highlight_squares": [(5, 5)],
                "wait_for": "piece_select", 
                "target_piece": (5, 5),
                "allowed_pieces": [(5, 5)],
                "completion_text": "Ready to capture!"
            },
            {
                "instruction": "Capture the black pawn on e5! Knights can jump!",
                "highlight_squares": [(4, 3)],
                "wait_for": "move",
                "from_square": (5, 5),
                "to_square": (4, 3),
                "expected_move": ((5, 5), (4, 3)),
                "completion_text": "CAPTURE! +1 point! Points buy powerups!"
            },
            
            # PHASE 4: Strategic Arms Acquisition
            {
                "instruction": "Now you have 1 point from capturing! Let's get WEAPONS! Click 'VISIT ARMS DEALER'!",
                "wait_for": "arms_dealer_visit",
                "completion_text": "Time to meet Tariq!"
            },
            {
                "instruction": "🎁 TUTORIAL GIFT: Tariq is giving you the Shield powerup for free! Beat enemies to earn cash for more weapons!",
                "wait_for": "tutorial_gift_complete",
                "completion_text": "Shield unlocked! Win battles to unlock more powerups!"
            },
            {
                "instruction": "Return to dominate the battlefield! Click 'BACK TO GAME'!",
                "wait_for": "return_to_game",
                "completion_text": "Back to tactical chess!"
            },
            
            # PHASE 5: Defensive Tactics - Shield Usage
            {
                "instruction": "Your knight on e5 is in enemy territory. Click the SHIELD button (blue shield icon) for protection!",
                "wait_for": "powerup_select",
                "target_powerup": "shield",
                "highlight_powerup": "shield",
                "completion_text": "Shield ready! Choose your protected piece."
            },
            {
                "instruction": "Shield your brave knight on e5! Click on it!",
                "highlight_squares": [(4, 3)],
                "wait_for": "powerup_use",
                "powerup_type": "shield",
                "target_square": (4, 3),
                "completion_text": "Knight protected! 3 turns of invulnerability."
            },
            {
                "instruction": "Enemy tries to attack your pawn but fails...",
                "wait_for": "ai_move",
                "completion_text": "Shield deflected their attack! Defensive success."
            },
            
            # PHASE 6: Tutorial Complete - Free Play
            {
                "instruction": "🎯 EXCELLENT! You've mastered the basics! All powerups unlocked - experiment freely!",
                "wait_for": "none",
                "completion_text": "🏆 TUTORIAL COMPLETE! Enjoy free play with all powerups!"
            }
        ]
        
        # STRATEGIC AI SEQUENCE - Simple tutorial moves
        # Note: These are stored as ((from_col, from_row), (to_col, to_row))
        self.story_ai_moves = [
            ((4, 1), (4, 3)),      # 1. e7-e5 (black plays e5 in response to e4)
            ((3, 1), (3, 2)),      # 2. d7-d6 (black develops, e5 pawn stays there)
            ((0, 1), (0, 2)),      # 3. a7-a6 (safe move after knight captures on e5)
            ((7, 1), (7, 2)),      # 4. h7-h6 (another safe move during shield demo)
        ]
        
    def _init_scripted_mode(self):
        """Initialize scripted tutorial mode data."""
        self.scripted_steps = [
            {
                "type": "message",
                "instruction": "Welcome to Checkmate Protocol! Let me teach you the basics.",
                "duration": 1.5
            },
            {
                "type": "player_move",
                "instruction": "Start by moving your e2 pawn to e4.",
                "highlight_from": (4, 6),
                "highlight_to": (4, 4),
                "expected_from": (4, 6),
                "expected_to": (4, 4)
            },
            {
                "type": "ai_move",
                "instruction": "Watch your opponent's move...",
                "ai_from": (4, 1),
                "ai_to": (4, 3)
            },
            # ... more scripted steps
        ]
        
    def start(self, mode="simple"):
        """Start tutorial with specified mode."""
        self.active = True
        self.current_mode = mode
        self.current_step = 0
        self.waiting_for_action = False
        self.ai_move_index = 0
        
        # Reset tutorial powerups at start
        config.reset_tutorial_powerups()
        
        # Load appropriate steps based on mode
        if mode == "simple":
            self.steps = self.simple_steps
            self.ai_move_sequence = []
            # Don't give points at start - wait for arms dealer
            self.powerup_system.points["white"] = 0
            pass
        elif mode == "story":
            self.steps = self.story_steps
            self.ai_move_sequence = self.story_ai_moves
            # Reset board for story tutorial
            powerup_ref = self.board.powerup_system  # Save reference
            self.board.reset()
            self.board.set_powerup_system(powerup_ref)  # Restore reference
            # Don't give points at start - wait for arms dealer
            self.powerup_system.points["white"] = 0
            self.powerup_system.points["black"] = 0
        elif mode == "scripted":
            self.steps = self.scripted_steps
            self.ai_move_sequence = []
            self.board.reset()
            self.powerup_system.points["white"] = 20
            self.powerup_system.points["black"] = 0
            # Process first step if it's a message
            self._advance_step()
            
        # Set global tutorial state
        config.tutorial_active = True
        
    def get_current_instruction(self):
        """Get current instruction text."""
        if not self.active or self.current_step >= len(self.steps):
            return ""
            
        step = self.steps[self.current_step]
        
        # Handle different key names for instruction text
        if "text" in step:
            return step["text"]
        elif "instruction" in step:
            return step["instruction"]
        else:
            return ""
            
    def get_highlight_squares(self):
        """Get squares to highlight."""
        if not self.active or self.current_step >= len(self.steps):
            return []
            
        step = self.steps[self.current_step]
        
        # Handle different modes
        if self.current_mode == "simple":
            return step.get("highlight", [])
        elif self.current_mode == "story":
            return step.get("highlight_squares", [])
        elif self.current_mode == "scripted":
            highlights = []
            if step.get("type") == "player_move":
                if "highlight_from" in step:
                    highlights.append(step["highlight_from"])
                if "highlight_to" in step:
                    highlights.append(step["highlight_to"])
            return highlights
            
        return []
        
    def get_highlight_powerup(self):
        """Get powerup to highlight."""
        if not self.active or self.current_step >= len(self.steps):
            return None
            
        step = self.steps[self.current_step]
        return step.get("highlight_powerup", None)
        
    def handle_click(self, pos, square_pos=None):
        """Handle click events during tutorial."""
        if not self.active:
            return False
            
        step = self.steps[self.current_step] if self.current_step < len(self.steps) else {}
        
        # Handle click to continue for steps with wait_for="none"
        if step.get("wait_for") == "none" and square_pos is None:
            self._advance_step()
            return True
                
        return False
        
    def handle_piece_select(self, row, col):
        """Handle piece selection."""
        if not self.active:
            return
            
        pos = (col, row)  # Convert to (x, y) format
        step = self.steps[self.current_step]
        
        if self.current_mode == "simple":
            if step.get("wait_for") == "piece_select" and pos == step.get("target"):
                self._advance_step()
        elif self.current_mode == "story":
            if step.get("wait_for") == "piece_select":
                target = step.get("target_piece")
                if target and pos == target:
                    self._advance_step()
                elif pos in step.get("allowed_pieces", []):
                    self._advance_step()
                    
    def handle_move(self, from_row, from_col, to_row, to_col):
        """Handle piece movement."""
        if not self.active:
            return
            
        from_pos = (from_col, from_row)
        to_pos = (to_col, to_row)
        step = self.steps[self.current_step]
        
        # TUTORIAL FIX: Track if this is a player move that completes
        move_completed = False
        
        # Simple mode validation
        if self.current_mode == "simple":
            if step.get("wait_for") == "move":
                if from_pos == step.get("from") and to_pos == step.get("to"):
                    self._advance_step()
                    
        # Story mode validation
        elif self.current_mode == "story":
            if step.get("wait_for") == "move":
                expected = step.get("expected_move")
                if expected and from_pos == expected[0] and to_pos == expected[1]:
                    move_completed = True
                    self._advance_step()
                    # After advancing, check if next step is waiting for AI
                    if self.current_step < len(self.steps):
                        next_step = self.steps[self.current_step]
                        if next_step.get("wait_for") == "ai_move":
                            pass  # Now waiting for AI move
                            # The board's complete_move should switch turns, but let's verify
                            if self.board.current_turn == "white":
                                pass  # Turn is still white after player move
                                
        # TUTORIAL FIX: Update shields after player moves too
        # This ensures shields count down properly in tutorial
        if move_completed and self.powerup_system and len(self.powerup_system.shielded_pieces) > 0:
            # Count this as half a turn (player's turn)
            # The other half will happen after AI moves
            pass  # Player move completed, shield countdown pending AI move
                    
        # Scripted mode validation
        elif self.current_mode == "scripted":
            if step.get("type") == "player_move":
                if (from_pos == (step["expected_from"]) and 
                    to_pos == (step["expected_to"])):
                    self._advance_step()
                    
    def handle_powerup_select(self, powerup_key):
        """Handle powerup selection."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        
        # Story mode powerup selection
        if self.current_mode == "story" and step.get("wait_for") == "powerup_select":
            target = step.get("target_powerup")
            if target == powerup_key:
                self.waiting_for_action = True
                self._advance_step()
                return True
        # Simple mode powerup selection
        elif step.get("action") == "select_powerup" and powerup_key == step.get("powerup"):
            self.waiting_for_action = True
            self._advance_step()
            return True
            
        return False
            
    def handle_powerup_use(self, powerup_key, row, col):
        """Handle powerup usage."""
        if not self.active:
            return
            
        target_square = (col, row)  # Convert to (x, y) format
        step = self.steps[self.current_step]
        
        if step.get("wait_for") == "powerup_use":
            # For story mode, check powerup type and target square
            if self.current_mode == "story":
                target_type = step.get("powerup_type")
                expected_target = step.get("target_square")
                
                # Check powerup type matches
                if target_type and target_type != powerup_key:
                    return False
                    
                # Check target square if specified
                if expected_target and target_square != expected_target:
                    return False
                    
                self.waiting_for_action = False
                self._advance_step()
                
                # After powerup use, check if next step is waiting for AI move
                # If so, we need to switch turns so AI can move
                if self.current_step < len(self.steps):
                    next_step = self.steps[self.current_step]
                    if next_step.get("wait_for") == "ai_move":
                        # In tutorial, using a powerup counts as your turn
                        self.board.current_turn = "black"
                        pass  # Switching to AI turn after powerup use
                
                return True
            else:
                # Simple mode logic
                if target_square == step.get("target"):
                    self.waiting_for_action = False
                    self._advance_step()
                
    def handle_arms_dealer_visit(self):
        """Handle arms dealer visit."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        
        if step.get("wait_for") == "arms_dealer_visit":
            # Give player points and unlock shield when visiting arms dealer
            if self.current_mode == "simple":
                self.powerup_system.points["white"] = 999
            elif self.current_mode == "story":
                self.powerup_system.points["white"] = 100
            
            # Now unlock shield powerup when visiting arms dealer
            config.unlock_all_powerups_for_tutorial()  # This now only unlocks shield
            self._advance_step()
            
            # Don't automatically advance through the gift step - let the player see the message!
            
    def handle_powerup_purchase(self, powerup_key):
        """Handle powerup purchase."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        
        if step.get("wait_for") == "powerup_purchase":
            if powerup_key == step.get("target_powerup"):
                # Shield already unlocked when visiting arms dealer
                self._advance_step()
                
    def handle_back_to_game(self):
        """Handle returning from arms dealer."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        
        # First handle the gift complete step if we're on it
        if step.get("wait_for") == "tutorial_gift_complete":
            self._advance_step()
            # Now check the next step
            if self.current_step < len(self.steps):
                step = self.steps[self.current_step]
        
        if step.get("wait_for") == "return_to_game":
            self._advance_step()
            
    def handle_ai_move_complete(self):
        """Handle AI move completion."""
        if not self.active:
            return
            
        step = self.steps[self.current_step] if self.current_step < len(self.steps) else {}
        
        # Story mode AI move completion
        if self.current_mode == "story" and step.get("wait_for") == "ai_move":
            pass  # AI move completed, advancing tutorial
            
            # TUTORIAL FIX: Force shield update after AI moves
            # In normal games, shields update when turns switch
            # In tutorial, we need to manually update them
            if self.powerup_system and len(self.powerup_system.shielded_pieces) > 0:
                pass  # Manually updating shields after AI turn
                self.powerup_system.update_shields()
            
            self._advance_step()
            return True
            
        # Advance for scripted AI moves
        if self.current_mode == "scripted":
            if step.get("type") == "ai_move":
                self._advance_step()
                return True
                
        return False
                
    def should_override_ai(self):
        """Check if tutorial should override AI moves."""
        if not self.active:
            pass  # Not active
            return False
            
        # Story mode has scripted AI sequence
        if self.current_mode == "story":
            pass  # Story mode override check
            if self.ai_move_index < len(self.ai_move_sequence):
                step = self.steps[self.current_step] if self.current_step < len(self.steps) else {}
                pass  # Current step check
                # Only override if we're actually waiting for an AI move
                if step.get("wait_for") == "ai_move":
                    pass  # Overriding AI move
                    return True
                else:
                    pass  # Not overriding
            else:
                pass  # No more AI moves
            
        # Scripted mode controls specific AI moves
        if self.current_mode == "scripted":
            step = self.steps[self.current_step]
            return step.get("type") == "ai_move"
            
        return False
        
    def get_next_ai_move(self):
        """Get next AI move for tutorial."""
        if not self.active:
            return None
            
        if self.current_mode == "story":
            # CRITICAL: First AI move MUST be e7-e5 for tutorial to work
            if self.ai_move_index == 0:
                # Force e7-e5 move (e=col 4, rank 7=row 1, rank 5=row 3)
                move = ((4, 1), (4, 3))  # e7 to e5
                pass  # Forcing first AI move
                self.ai_move_index += 1
                return move
            elif self.ai_move_index < len(self.ai_move_sequence):
                move = self.ai_move_sequence[self.ai_move_index]
                pass  # Tutorial AI move
                self.ai_move_index += 1
                return move
                
        elif self.current_mode == "scripted":
            step = self.steps[self.current_step]
            if step.get("type") == "ai_move":
                return (step["ai_from"], step["ai_to"])
                
        return None
        
    def validate_player_move(self, from_row, from_col, to_row, to_col):
        """Validate if a player move is allowed."""
        if not self.active:
            return True
            
        from_pos = (from_col, from_row)
        to_pos = (to_col, to_row)
        step = self.steps[self.current_step]
        
        # Simple mode validation
        if self.current_mode == "simple":
            if step.get("wait_for") == "move":
                return from_pos == step.get("from") and to_pos == step.get("to")
                
        # Story mode validation
        elif self.current_mode == "story":
            if step.get("wait_for") == "move":
                expected = step.get("expected_move")
                if expected:
                    return from_pos == expected[0] and to_pos == expected[1]
                    
        # Scripted mode validation
        elif self.current_mode == "scripted":
            if step.get("type") == "player_move":
                return (from_pos == step["expected_from"] and 
                        to_pos == step["expected_to"])
                
        return True
        
    def can_select_piece(self, pos):
        """Check if a piece can be selected."""
        if not self.active:
            return True
            
        if self.current_step >= len(self.steps):
            return True
            
        step = self.steps[self.current_step]
        
        # Story mode restrictions
        if self.current_mode == "story":
            # Check if we're waiting for piece selection
            if step.get("wait_for") == "piece_select":
                # Check target piece first
                target = step.get("target_piece")
                if target:
                    return pos == target
                    
                # Check allowed pieces list
                allowed = step.get("allowed_pieces", [])
                if allowed:
                    return pos in allowed
                    
        return True
        
    def is_complete(self):
        """Check if tutorial is complete."""
        if not self.active:
            return False
            
        if self.current_mode == "simple":
            return self.current_step >= len(self.steps) - 1
        else:
            return self.current_step >= len(self.steps)
    
    @property
    def tutorial_complete(self):
        """Property for backward compatibility."""
        return self.is_complete()
            
    def complete(self):
        """Complete the tutorial."""
        self.active = False
        config.tutorial_active = False
        
        # Keep powerups unlocked after tutorial
        if self.current_mode in ["simple", "story"]:
            # Don't reset powerups - keep them all unlocked
            # Don't give points after completion
            if self.current_mode == "story":
                pass  # Points already given during tutorial
            return
            
        # Only reset for other modes (if any)
        config.reset_tutorial_powerups()
        
    def _advance_step(self):
        """Advance to next tutorial step."""
        # Show completion text for current step before advancing
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if "completion_text" in step and self.current_mode == "story":
                pass  # Step completed
        
        
        # Advance step
        if self.current_step < len(self.steps):
            self.current_step += 1
            self.waiting_for_action = False
            
            # Complete tutorial if we've reached the end
            if self.is_complete():
                self.complete()
            else:
                # Handle automatic steps
                if self.current_step < len(self.steps):
                    step = self.steps[self.current_step]
                    if self.current_mode == "scripted" and step.get("type") == "message":
                        # Auto-advance message steps
                        self._advance_step()
                    elif self.current_mode == "story":
                        # Set up next step for story mode
                        import pygame
                        pygame.time.set_timer(pygame.USEREVENT + 1, 200)
                    
    def is_active(self):
        """Check if tutorial is active."""
        return self.active
        
    def get_mode(self):
        """Get current tutorial mode."""
        return self.current_mode if self.active else None
    
    # Compatibility methods for story mode features
    def force_check_ai_move(self):
        """Force check AI move - story mode compatibility."""
        if not self.active:
            return False
            
        step = self.steps[self.current_step] if self.current_step < len(self.steps) else {}
        
        if self.current_mode == "story" and step.get("wait_for") == "ai_move":
            self._advance_step()
            return True
            
        return False
    
    def handle_timer_event(self):
        """Handle timer events - story mode compatibility."""
        if self.active and self.current_mode == "story":
            # Show current step instruction
            if self.current_step < len(self.steps):
                step = self.steps[self.current_step]
                pass  # Story tutorial instruction
                
        return True
    
    def handle_ai_move(self):
        """Handle AI move - story mode compatibility."""
        pass
    
    def check_timeout(self):
        """Check for timeout - story mode compatibility."""
        pass
    
    def handle_points_gained(self):
        """Handle points gained - story mode compatibility."""
        pass
    
    def handle_move_start(self, row, col):
        """Handle move start - story mode compatibility."""
        pass
    
    def handle_click_anywhere(self):
        """Handle click anywhere events - story mode compatibility."""
        pass
    
    def handle_at_arms_dealer(self):
        """Handle arriving at arms dealer - story mode compatibility."""
        if self.current_mode == "story":
            # Find and handle the tutorial gift step
            if self.current_step < len(self.steps):
                step = self.steps[self.current_step]
                if step.get("type") == "tutorial_gift":
                    # Don't unlock powerups here - wait for arms dealer visit
                    # Give free points for tutorial
                    self.powerup_system.points["white"] = 100
    
    def handle_tutorial_gift_complete(self):
        """Handle tutorial gift completion - story mode compatibility."""
        if not self.active:
            return
            
        step = self.steps[self.current_step] if self.current_step < len(self.steps) else {}
        
        if step.get("wait_for") == "tutorial_gift_complete":
            # Give points for story mode
            if self.current_mode == "story":
                self.powerup_system.points["white"] = 100  # Give points but don't unlock shield yet
            
            self._advance_step()
        elif self.current_mode == "simple":
            self._advance_step()
    
    @property
    def tutorial_steps(self):
        """Alias for steps - backward compatibility."""
        return self.steps
    
    @property
    def steps_completed(self):
        """Steps completed list - story mode compatibility."""
        if not hasattr(self, '_steps_completed'):
            self._steps_completed = []
        return self._steps_completed
    
    @steps_completed.setter
    def steps_completed(self, value):
        """Set steps completed list."""
        self._steps_completed = value

# Compatibility aliases for backward compatibility
SimpleTutorial = TutorialSystem
StoryTutorial = TutorialSystem
ScriptedTutorial = TutorialSystem