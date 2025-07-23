"""
Simple, working tutorial that guarantees every move works correctly.
"""

class SimpleTutorial:
    def __init__(self, game, board, powerup_system):
        self.game = game
        self.board = board
        self.powerup_system = powerup_system
        self.active = False
        self.current_step = 0
        
        # Simple sequence - each step is guaranteed to work
        self.steps = [
            {
                "text": "Welcome! Click your e2 pawn.",
                "highlight": [(4, 6)],  # e2
                "action": "select_piece",
                "wait_for": "piece_select",
                "target": (4, 6)
            },
            {
                "text": "Move it to e4!",
                "highlight": [(4, 4)],  # e4
                "action": "move_to",
                "wait_for": "move",
                "from": (4, 6),
                "to": (4, 4)
            },
            {
                "text": "Good! Now click the VISIT ARMS DEALER button.",
                "action": "visit_arms_dealer",
                "wait_for": "arms_dealer_visit"
            },
            {
                "text": "Click on the SHIELD powerup to buy it (1 point).",
                "action": "buy_shield",
                "wait_for": "powerup_purchase",
                "target_powerup": "shield"
            },
            {
                "text": "Great! You bought your first powerup! All powerups are now unlocked for the tutorial. Click BACK TO GAME to continue.",
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
                "text": "Click your e4 pawn to shield it!",
                "highlight": [(4, 4)],
                "action": "use_powerup",
                "target": (4, 4)
            },
            {
                "text": "Perfect! This is how you buy and use powerups! You have unlimited points to test them out. Click anywhere to continue.",
                "action": "click_to_continue",
                "wait_for": "click_anywhere"
            },
            {
                "text": "Tutorial complete! You can now play freely with all powerups unlocked. Click anywhere to continue.",
                "action": "complete",
                "wait_for": "click_anywhere"
            }
        ]
        
        # Place a black piece for demo
        self.demo_piece_placed = False
        
    def start(self):
        """Start tutorial."""
        self.active = True
        self.current_step = 0
        self.demo_piece_placed = False
        
        # Reset board
        self.board.reset()
        
        # Reset points at start - will be given when visiting arms dealer
        self.powerup_system.points["white"] = 0
        self.powerup_system.points["black"] = 0
        
        # No powerups at start
        import config
        config.tutorial_unlocked_powerups = []
        
        print("SimpleTutorial: Started!")
    
    def start_tutorial(self):
        """Alias for start() for compatibility."""
        self.start()
        
    def get_current_text(self):
        """Get instruction text."""
        if self.active and self.current_step < len(self.steps):
            text = self.steps[self.current_step]["text"]
            return text
        return ""
        
    def get_highlights(self):
        """Get squares to highlight."""
        if not self.active or self.current_step >= len(self.steps):
            return []
            
        step = self.steps[self.current_step]
        return step.get("highlight", [])
        
    def get_highlight_powerup(self):
        """Get powerup to highlight."""
        if not self.active or self.current_step >= len(self.steps):
            return None
            
        step = self.steps[self.current_step]
        return step.get("highlight_powerup")
        
    def can_select_piece(self, row, col):
        """Check if piece can be selected."""
        if not self.active:
            return True
            
        step = self.steps[self.current_step]
        if step.get("action") == "select_piece":
            target = step.get("target")
            return (col, row) == target
            
        return True
        
    def can_move_to(self, from_row, from_col, to_row, to_col):
        """Check if move is allowed."""
        if not self.active:
            return True
            
        step = self.steps[self.current_step]
        if step.get("action") == "move_to":
            expected_from = step.get("from")
            expected_to = step.get("to")
            return ((from_col, from_row) == expected_from and 
                    (to_col, to_row) == expected_to)
        
        # After tutorial steps that require specific moves, allow any move
        if self.current_step > 1:
            return True
                    
        return False
        
    def handle_piece_selected(self, row, col):
        """Handle when piece is selected."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("action") == "select_piece":
            if (col, row) == step.get("target"):
                self.advance()
                
    def handle_move_made(self, from_row, from_col, to_row, to_col):
        """Handle when move is made."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("action") == "move_to":
            self.advance()
            
    def handle_arms_dealer_clicked(self):
        """Handle arms dealer button click."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("action") == "visit_arms_dealer":
            # Don't unlock any powerups yet - player must buy shield first
            import config
            config.tutorial_unlocked_powerups = []
            # Give player points for tutorial - MUST be set here AND maintained
            self.powerup_system.points["white"] = 999
            print(f"SimpleTutorial: Gave player 999 points for tutorial")
            self.advance()
            
    def handle_at_arms_dealer(self):
        """Handle being at arms dealer."""
        if not self.active:
            return
            
        # Since we removed the at_arms_dealer step, this shouldn't be called
        print("SimpleTutorial: handle_at_arms_dealer called (deprecated)")
            
    def handle_back_to_game(self):
        """Handle returning from arms dealer."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("action") == "return_to_game":
            self.advance()
            # Make sure we're showing the next instruction
            print(f"SimpleTutorial: Returned from arms dealer, now at step {self.current_step}")
            
            # Force the tutorial to become active and show instructions
            if self.current_step < len(self.steps):
                self.active = True
                print(f"SimpleTutorial: Next instruction: {self.steps[self.current_step]['text']}")
            
    def handle_powerup_selected(self, powerup):
        """Handle powerup selection."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("action") == "select_powerup":
            if powerup == step.get("powerup"):
                self.advance()
                
    def handle_powerup_used(self, row, col):
        """Handle powerup use."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("action") == "use_powerup":
            if (col, row) == step.get("target"):
                self.advance()
                
    def handle_click_anywhere(self):
        """Handle click anywhere to continue."""
        if not self.active:
            return
            
        step = self.steps[self.current_step]
        if step.get("wait_for") == "click_anywhere":
            self.advance()
            print("SimpleTutorial: Player clicked to continue")
                
    def advance(self):
        """Move to next step."""
        print(f"SimpleTutorial: Advancing from step {self.current_step}")
        self.current_step += 1
        
        if self.current_step >= len(self.steps):
            print("SimpleTutorial: Tutorial complete!")
            self.complete()
        else:
            print(f"SimpleTutorial: Now at step {self.current_step} - {self.steps[self.current_step]['text']}")
            print(f"SimpleTutorial: Waiting for: {self.steps[self.current_step].get('wait_for', 'none')}")
            
    def _advance_step(self):
        """Compatibility method for game.py"""
        self.advance()
            
    def complete(self):
        """Complete tutorial."""
        self.active = False
        print("SimpleTutorial: COMPLETE!")
        # Ensure player keeps unlimited points after tutorial
        self.powerup_system.points["white"] = 999
        self.powerup_system.points["black"] = 0
        print("SimpleTutorial: Player keeps 999 points to experiment with powerups")
        
    def is_active(self):
        return self.active
        
    # Compatibility methods for game.py
    def should_override_ai(self):
        """No AI moves in simple tutorial."""
        return False
        
    def handle_ai_move(self):
        pass
        
    def handle_move_start(self, row, col):
        pass
        
    def check_timeout(self):
        pass
        
    def force_check_ai_move(self):
        pass
        
    def handle_points_gained(self):
        pass
        
    def handle_timer_event(self):
        pass
        
    def handle_ai_move_complete(self):
        pass
        
    def validate_player_move(self, from_row, from_col, to_row, to_col):
        """Validate moves."""
        # If tutorial is not active, allow all moves
        if not self.active:
            return True
        return self.can_move_to(from_row, from_col, to_row, to_col)
        
    def handle_piece_select(self, row, col):
        """Handle piece selection."""
        self.handle_piece_selected(row, col)
        return False
        
    def handle_move(self, from_row, from_col, to_row, to_col):
        """Handle move."""
        self.handle_move_made(from_row, from_col, to_row, to_col)
        
    def handle_arms_dealer_visit(self):
        """Handle arms dealer visit."""
        self.handle_arms_dealer_clicked()
        
    def handle_tutorial_gift_complete(self):
        """Handle gift - deprecated since we removed this step."""
        print("SimpleTutorial: handle_tutorial_gift_complete called (deprecated)")
        
    def handle_powerup_select(self, powerup):
        """Handle powerup select."""
        self.handle_powerup_selected(powerup)
        return True
        
    def handle_powerup_use(self, powerup_type, row, col):
        """Handle powerup use."""
        self.handle_powerup_used(row, col)
        return True
        
    def get_current_instruction(self):
        """Get instruction text."""
        return self.get_current_text()
        
    def get_highlight_squares(self):
        """Get highlights."""
        return self.get_highlights()
        
    def should_show_hints(self):
        """Always show hints in tutorial."""
        return self.active
        
    @property
    def tutorial_complete(self):
        """Check if complete."""
        return not self.active and self.current_step >= len(self.steps)
        
    @property
    def tutorial_steps(self):
        """Compatibility property."""
        return self.steps