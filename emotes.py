"""
AI Emote System for Chess Game
Shows AI emotions and reactions based on game events
"""

import pygame
import random
import math
import config

class EmoteSystem:
    def __init__(self, screen, renderer):
        self.screen = screen
        self.renderer = renderer
        self.current_emote = None
        self.emote_start_time = 0
        self.emote_duration = 3000  # 3 seconds
        
        # AI personality based on difficulty
        self.personalities = {
            "easy": "friendly",
            "medium": "competitive", 
            "hard": "serious",
            "very_hard": "intimidating"
        }
        
        # Emote triggers and responses - Removed emojis
        self.emote_library = {
            "capture_pawn": {
                "friendly": ["Nice move!", "Good job!", "Well played!"],
                "competitive": ["That's all you got?", "Wow a pawn...", "Congrats on the basics"],
                "serious": ["Insignificant.", "Waste of a turn.", "...really?"],
                "intimidating": ["My grandma plays better", "Did you learn chess yesterday?", "That's embarrassing"]
            },
            "capture_major": {
                "friendly": ["Oh no!", "You got me!", "Clever!"],
                "competitive": ["Lucky noob", "Won't save you", "Fluke shot"],
                "serious": ["Temporary advantage.", "Irrelevant.", "You'll regret that."],
                "intimidating": ["I'll end your bloodline", "Your family watches you fail", "Uninstall chess"]
            },
            "ai_captures": {
                "friendly": ["Sorry!", "Had to do it!", "Oops!"],
                "competitive": ["Get rekt", "Sit down kid", "EZ clap"],
                "serious": ["Deleted.", "Predictable.", "As expected."],
                "intimidating": ["Trash player", "Go back to checkers", "Why even try?"]
            },
            "player_check": {
                "friendly": ["Oh dear!", "Uh oh!", "Danger!"],
                "competitive": ["Scared yet?", "Shaking?", "Run coward!"],
                "serious": ["Inevitable.", "Resistance futile.", "Submit."],
                "intimidating": ["Crawl like the worm you are", "Cry to mommy", "I own you"]
            },
            "player_blunder": {
                "friendly": ["Are you sure?", "Ooh, careful!", "Hmm..."],
                "competitive": ["LMAOOOOO", "Bronze player?", "Thanks for the free win"],
                "serious": ["IQ: Room temperature.", "Brain.exe stopped.", "404: Skill not found."],
                "intimidating": ["Actual bot", "Parents must be proud", "Delete the game"]
            },
            "ai_winning": {
                "friendly": ["Good game!", "I'm ahead!", "Lucky me!"],
                "competitive": ["2 EZ 4 ME", "Get destroyed", "Not even trying"],
                "serious": ["Skill gap: Insurmountable.", "Outclassed.", "Natural selection."],
                "intimidating": ["Stay in bronze forever", "I own your soul", "Worthless opponent"]
            },
            "ai_losing": {
                "friendly": ["You're good!", "Help!", "Oh boy..."],
                "competitive": ["Lag", "Mouse slipped", "Lucky RNG"],
                "serious": ["Anomaly detected.", "Statistical outlier.", "Temporary."],
                "intimidating": ["Enjoy it while it lasts", "I'll remember this", "You just signed your death warrant"]
            },
            "player_streak_3": {
                "friendly": ["You're on fire!", "Wow, 3 in a row!", "Impressive!"],
                "competitive": ["Tryhard detected", "Touch grass", "Still gonna lose"],
                "serious": ["Streak: Meaningless.", "False confidence.", "Preparing counter."],
                "intimidating": ["3-0 to 3-15 incoming", "Peak luck", "Your mom helps you?"]
            },
            "player_streak_5": {
                "friendly": ["5 kills! Amazing!", "You're unstoppable!", "Teach me!"],
                "competitive": ["Sweat more", "No life?", "Still hardstuck"],
                "serious": ["Anomaly will correct.", "Regression imminent.", "Unsustainable."],
                "intimidating": ["Virgin streak", "Go shower", "Parents disappointed"]
            },
            "player_streak_broken": {
                "friendly": ["Oops! There goes your streak", "It happens!", "You'll get another!"],
                "competitive": ["HAHAHA NOOB", "Reality check", "Back to bronze"],
                "serious": ["Predictable outcome.", "Order restored.", "Skill issue confirmed."],
                "intimidating": ["Knew you'd choke", "All that for nothing", "Waste of oxygen"]
            },
            "ai_streak_3": {
                "friendly": ["Oh my, 3 captures!", "I'm doing well!", "Sorry about this!"],
                "competitive": ["Free game", "Skill diff", "You're done"],
                "serious": ["Operating normally.", "Domination phase.", "Working as intended."],
                "intimidating": ["Bend the knee", "I am your god", "Cry more"]
            },
            "ai_powerup": {
                "friendly": ["Time for a powerup!", "Let me try this!", "Hope this works!"],
                "competitive": ["Overkill time", "You're cooked", "Say goodbye"],
                "serious": ["Termination protocol.", "Maximum efficiency.", "Endgame."],
                "intimidating": ["Prepare to be violated", "Your ancestors weep", "Uninstall after this"]
            },
            "game_start": {
                "friendly": ["Let's have fun!", "Good luck!", "May the best player win!"],
                "competitive": ["FF at 5 mins?", "Ready to get owned?", "EZ game incoming"],
                "serious": ["Analyzing weakness...", "Victory: Assured.", "Commencing domination."],
                "intimidating": ["Last game ever?", "I'll make you quit chess", "Your funeral starts now"]
            },
            "checkmate": {
                "friendly": ["Good game!", "That was fun!", "Well played!"],
                "competitive": ["EZ CLAP", "Get good kid", "Skill issue"],
                "serious": ["Expected outcome.", "Skill gap confirmed.", "Delete chess."],
                "intimidating": ["Stay hardstuck", "Uninstall life", "Absolute trash"]
            }
        }
        
        # Queue for multiple emotes
        self.emote_queue = []
        self.last_emote_type = None
        
    def trigger_emote(self, event_type, ai_difficulty, force=False):
        """Trigger an appropriate emote based on game event."""
        # Don't spam the same emote type
        if not force and event_type == self.last_emote_type:
            return
            
        # Limit emote frequency
        current_time = pygame.time.get_ticks()
        if hasattr(self, 'last_emote_time'):
            if current_time - self.last_emote_time < 2000:  # 2 second cooldown
                return
        
        personality = self.personalities.get(ai_difficulty, "competitive")
        
        if event_type in self.emote_library:
            emotes = self.emote_library[event_type].get(personality, [])
            if emotes:
                # Add to queue instead of replacing
                self.emote_queue.append({
                    "text": random.choice(emotes),
                    "type": event_type
                })
                self.last_emote_type = event_type
                self.last_emote_time = current_time
                
                # Start showing if not already showing
                if not self.current_emote:
                    self._show_next_emote()
                    
    def _show_next_emote(self):
        """Show the next emote from the queue."""
        if self.emote_queue:
            emote_data = self.emote_queue.pop(0)
            self.current_emote = {
                "text": emote_data["text"],
                "start_time": pygame.time.get_ticks(),
                "position": self._get_emote_position(),
                "type": emote_data["type"]
            }
            self.emote_start_time = pygame.time.get_ticks()
                
    def _get_emote_position(self):
        """Calculate where to show the emote (top right corner)."""
        # Position in top right corner, away from game elements
        return (config.WIDTH - 300, 100)
                
    def update(self):
        """Update emote display."""
        if self.current_emote:
            elapsed = pygame.time.get_ticks() - self.current_emote["start_time"]
            if elapsed > self.emote_duration:
                self.current_emote = None
                # Show next emote if any
                self._show_next_emote()
                
    def draw(self):
        """Draw the current emote."""
        if not self.current_emote:
            return
            
        # Calculate fade in/out
        elapsed = pygame.time.get_ticks() - self.current_emote["start_time"]
        alpha = 255
        
        if elapsed < 300:  # Fade in
            alpha = int(255 * (elapsed / 300))
        elif elapsed > self.emote_duration - 300:  # Fade out
            alpha = int(255 * ((self.emote_duration - elapsed) / 300))
            
        # Create speech bubble
        text = self.current_emote["text"]
        font = self.renderer.pixel_fonts['medium']
        text_surface = font.render(text, True, (0, 0, 0))
        
        # Bubble dimensions
        padding = 15
        bubble_width = text_surface.get_width() + padding * 2
        bubble_height = text_surface.get_height() + padding * 2
        
        # Create bubble surface
        bubble_surface = pygame.Surface((bubble_width + 20, bubble_height + 20), pygame.SRCALPHA)
        
        # Get emote type for color coding
        emote_type = self.current_emote.get("type", "")
        
        # Color based on emote type
        if "winning" in emote_type or "streak" in emote_type and "broken" not in emote_type:
            bubble_color = (200, 255, 200)  # Green tint
        elif "losing" in emote_type or "blunder" in emote_type:
            bubble_color = (255, 200, 200)  # Red tint
        elif "check" in emote_type:
            bubble_color = (255, 255, 200)  # Yellow tint
        else:
            bubble_color = (255, 255, 255)  # White
            
        # Draw bubble background with color
        bubble_rect = pygame.Rect(5, 5, bubble_width, bubble_height)
        # Draw filled rect without alpha in color (use surface alpha instead)
        pygame.draw.rect(bubble_surface, bubble_color, 
                        bubble_rect, border_radius=10)
        # Draw border
        pygame.draw.rect(bubble_surface, (0, 0, 0), 
                        bubble_rect, 3, border_radius=10)
        
        # Draw tail pointing to AI side
        tail_points = [
            (bubble_width - 15, bubble_height + 5),
            (bubble_width - 25, bubble_height + 20),
            (bubble_width - 35, bubble_height + 5)
        ]
        pygame.draw.polygon(bubble_surface, bubble_color, tail_points)
        pygame.draw.lines(bubble_surface, (0, 0, 0), False, 
                        [(tail_points[0][0], tail_points[0][1] - 1),
                         tail_points[1],
                         (tail_points[2][0], tail_points[2][1] - 1)], 3)
        
        # Blit text onto bubble
        text_surface.set_alpha(alpha)
        bubble_surface.blit(text_surface, (5 + padding, 5 + padding))
        
        # Set alpha for the entire bubble surface
        bubble_surface.set_alpha(alpha)
        
        # Draw on screen with slight bounce animation
        x, y = self.current_emote["position"]
        bounce = math.sin(elapsed / 200) * 5
        
        self.screen.blit(bubble_surface, (x, y + bounce))
        
    def clear(self):
        """Clear all emotes."""
        self.current_emote = None
        self.emote_queue = []
        self.last_emote_type = None