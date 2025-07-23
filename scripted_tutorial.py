"""
Fully scripted tutorial with predetermined moves for both sides.
Every move is guaranteed to work exactly as expected.
"""

class ScriptedTutorial:
    def __init__(self, game, board, powerup_system):
        self.game = game
        self.board = board
        self.powerup_system = powerup_system
        self.active = False
        self.current_step = 0
        
        # Complete script of all moves and actions
        self.script = [
            # Step 0: Welcome
            {
                "type": "message",
                "instruction": "Welcome to Chess Protocol! Let's start with basic moves.",
                "wait_for": "click_anywhere"
            },
            
            # Step 1: White moves e2-e4
            {
                "type": "player_move",
                "instruction": "Move your e2 pawn to e4. Click the pawn at e2.",
                "highlight_from": (4, 6),  # e2
                "highlight_to": (4, 4),    # e4
                "from": (4, 6),
                "to": (4, 4),
                "wait_for": "move"
            },
            
            # Step 2: Black moves e7-e5 (AI)
            {
                "type": "ai_move",
                "instruction": "Watch the AI respond...",
                "from": (4, 1),  # e7
                "to": (4, 3),    # e5
                "wait_for": "auto"
            },
            
            # Step 3: White moves Nf3
            {
                "type": "player_move",
                "instruction": "Develop your knight! Move it from g1 to f3.",
                "highlight_from": (6, 7),  # g1
                "highlight_to": (5, 5),    # f3
                "from": (6, 7),
                "to": (5, 5),
                "wait_for": "move"
            },
            
            # Step 4: Black moves d7-d6 (AI)
            {
                "type": "ai_move",
                "instruction": "AI develops...",
                "from": (3, 1),  # d7
                "to": (3, 2),    # d6
                "wait_for": "auto"
            },
            
            # Step 5: White captures - Nxe5!
            {
                "type": "player_move",
                "instruction": "CAPTURE! Your knight can take the pawn on e5! Click your knight.",
                "highlight_from": (5, 5),  # f3
                "highlight_to": (4, 3),    # e5
                "from": (5, 5),
                "to": (4, 3),
                "wait_for": "move",
                "capture": True,
                "points": 1
            },
            
            # Step 6: Visit Arms Dealer
            {
                "type": "action",
                "instruction": "You earned 1 point! Visit the ARMS DEALER to get powerups!",
                "highlight_button": "arms_dealer",
                "wait_for": "arms_dealer_visit"
            },
            
            # Step 7: Tutorial gift
            {
                "type": "action",
                "instruction": "🎁 TUTORIAL GIFT: All powerups unlocked for learning!",
                "wait_for": "auto",
                "unlock_all": True
            },
            
            # Step 8: Return to game
            {
                "type": "action",
                "instruction": "Click BACK TO GAME to use your new powers!",
                "highlight_button": "back",
                "wait_for": "return_to_game"
            },
            
            # Step 9: Shield tutorial
            {
                "type": "powerup",
                "instruction": "Protect your knight! Click the SHIELD button.",
                "highlight_powerup": "shield",
                "wait_for": "powerup_select"
            },
            
            # Step 10: Apply shield
            {
                "type": "powerup_use",
                "instruction": "Click your knight on e5 to shield it!",
                "highlight_square": (4, 3),  # e5
                "target": (4, 3),
                "wait_for": "powerup_use"
            },
            
            # Step 11: Black moves randomly (AI)
            {
                "type": "ai_move",
                "instruction": "Enemy moves...",
                "from": (1, 0),  # b8
                "to": (2, 2),    # c6
                "wait_for": "auto"
            },
            
            # Step 12: Gun tutorial
            {
                "type": "powerup",
                "instruction": "Time to attack! Click the GUN button.",
                "highlight_powerup": "gun",
                "wait_for": "powerup_select"
            },
            
            # Step 13: Use gun
            {
                "type": "powerup_use",
                "instruction": "Eliminate the enemy knight on c6!",
                "highlight_square": (2, 2),  # c6
                "target": (2, 2),
                "wait_for": "powerup_use"
            },
            
            # Step 14: Victory message
            {
                "type": "message",
                "instruction": "🎉 TUTORIAL COMPLETE! You've mastered Chess Protocol!",
                "wait_for": "complete"
            }
        ]
        
        # Track what pieces should be where
        self.expected_board_state = {}
        
    def start(self):
        """Start the scripted tutorial."""
        self.active = True
        self.current_step = 0
        self.board.reset()
        
        # Reset powerups
        import config
        config.reset_tutorial_powerups()
        
        self._show_current_step()
        
    def _show_current_step(self):
        """Display the current step."""
        if self.current_step >= len(self.script):
            self._complete()
            return
            
        step = self.script[self.current_step]
        print(f"Tutorial Step {self.current_step}: {step['instruction']}")
        
    def get_current_instruction(self):
        """Get instruction text for current step."""
        if self.active and self.current_step < len(self.script):
            return self.script[self.current_step]["instruction"]
        return ""
        
    def get_highlights(self):
        """Get squares to highlight."""
        if not self.active or self.current_step >= len(self.script):
            return []
            
        step = self.script[self.current_step]
        highlights = []
        
        if step["type"] == "player_move":
            if "highlight_from" in step:
                highlights.append(step["highlight_from"])
            if "highlight_to" in step:
                highlights.append(step["highlight_to"])
        elif step["type"] == "powerup_use":
            if "highlight_square" in step:
                highlights.append(step["highlight_square"])
                
        return highlights
        
    def get_highlight_powerup(self):
        """Get powerup to highlight."""
        if not self.active or self.current_step >= len(self.script):
            return None
            
        step = self.script[self.current_step]
        if step["type"] == "powerup" and "highlight_powerup" in step:
            return step["highlight_powerup"]
        return None
        
    def handle_click(self, pos):
        """Handle mouse click."""
        if not self.active:
            return False
            
        step = self.script[self.current_step]
        
        if step.get("wait_for") == "click_anywhere":
            self._advance_step()
            return True
            
        return False
        
    def handle_move(self, from_pos, to_pos):
        """Handle chess move."""
        if not self.active:
            return True  # Allow move
            
        step = self.script[self.current_step]
        
        if step["type"] == "player_move":
            # Check if this is the expected move
            expected_from = step["from"]
            expected_to = step["to"]
            
            if (from_pos[0], from_pos[1]) == expected_from and (to_pos[0], to_pos[1]) == expected_to:
                # Correct move!
                if step.get("capture") and step.get("points"):
                    # Award points
                    self.powerup_system.points["white"] += step["points"]
                self._advance_step()
                return True
            else:
                # Wrong move
                print("Tutorial: That's not the right move! Follow the golden squares.")
                return False
                
        return True  # Allow move if not in a move step
        
    def get_next_ai_move(self):
        """Get the next AI move from script."""
        if not self.active or self.current_step >= len(self.script):
            return None
            
        step = self.script[self.current_step]
        
        if step["type"] == "ai_move":
            return (step["from"], step["to"])
            
        return None
        
    def should_override_ai(self):
        """Check if AI should be overridden."""
        if not self.active or self.current_step >= len(self.script):
            return False
            
        step = self.script[self.current_step]
        return step["type"] == "ai_move"
        
    def handle_ai_move_complete(self):
        """Handle when AI move completes."""
        if not self.active:
            return
            
        step = self.script[self.current_step]
        if step["type"] == "ai_move":
            self._advance_step()
            
    def handle_arms_dealer_visit(self):
        """Handle arms dealer visit."""
        step = self.script[self.current_step]
        if step.get("wait_for") == "arms_dealer_visit":
            self._advance_step()
            
    def handle_return_from_arms_dealer(self):
        """Handle returning from arms dealer."""
        step = self.script[self.current_step]
        if step.get("wait_for") == "return_to_game":
            self._advance_step()
            
    def handle_powerup_select(self, powerup):
        """Handle powerup selection."""
        step = self.script[self.current_step]
        if step["type"] == "powerup" and step.get("highlight_powerup") == powerup:
            self._advance_step()
            
    def handle_powerup_use(self, row, col):
        """Handle powerup usage."""
        step = self.script[self.current_step]
        if step["type"] == "powerup_use":
            target = step["target"]
            if (col, row) == target:
                self._advance_step()
                
    def _advance_step(self):
        """Move to next step."""
        self.current_step += 1
        
        # Handle automatic steps
        while self.current_step < len(self.script):
            step = self.script[self.current_step]
            
            if step.get("wait_for") == "auto":
                if step.get("unlock_all"):
                    # Unlock all powerups
                    import config
                    config.unlock_all_powerups_for_tutorial()
                    self.powerup_system.points["white"] = 9999
                self.current_step += 1
            else:
                break
                
        self._show_current_step()
        
    def _complete(self):
        """Complete tutorial."""
        self.active = False
        print("Tutorial: COMPLETE! You're ready for real battles!")
        
    def is_active(self):
        """Check if tutorial is active."""
        return self.active