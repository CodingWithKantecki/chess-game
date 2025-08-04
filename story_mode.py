"""
Story Mode for Chess Game
Campaign with chapters, special battles, and progression
"""

import json
import os
import config
import time
from datetime import datetime

class StoryMode:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StoryMode, cls).__new__(cls)
            cls._instance._initialized = False
            print("StoryMode: Creating new instance")
        else:
            print("StoryMode: Returning existing instance")
        return cls._instance
    
    def __init__(self):
        # Only initialize once to preserve state
        if hasattr(self, '_initialized') and self._initialized:
            print("StoryMode: Already initialized, skipping init")
            print(f"StoryMode: Current state - completed_battles: {self.completed_battles}, unlocked_chapters: {self.unlocked_chapters}")
            return
        print("StoryMode: Initializing for the first time")
        self._initialized = True
            
        self.current_chapter = 0
        self.current_battle = 0
        self.completed_battles = []
        # Start with only first chapter unlocked
        self.unlocked_chapters = [True, False, False, False, False]
        
        # Story chapters with battles
        self.chapters = [
            {
                "id": "chapter_1",
                "title": "The Recruit",
                "intro": [
                    "Fresh out of the Chess Academy, you've been assigned",
                    "to the elite Checkmate Protocol unit.",
                    "",
                    "Your commander wants to test your skills",
                    "before sending you into real combat...",
                ],
                "battles": [
                    {
                        "id": "tutorial_bot",
                        "opponent": "Training Bot Alpha",
                        "difficulty": "easy",
                        "portrait": "BOT",
                        "affiliation": "HELIX ACADEMY",
                        "rank": "TRAINING UNIT",
                        "threat_level": "MINIMAL",
                        "classification": "TUTORIAL",
                        "specialization": "Basic Tactics Training",
                        "pre_battle": [
                            "TRAINING BOT: GREETINGS, RECRUIT.",
                            "TRAINING BOT: I AM PROGRAMMED TO TEST BASIC TACTICS.",
                            "TRAINING BOT: SHOW ME YOUR ACADEMY TRAINING."
                        ],
                        "victory": [
                            "TRAINING BOT: ADEQUATE PERFORMANCE.",
                            "TRAINING BOT: YOU MAY PROCEED TO ADVANCED TRAINING."
                        ],
                        "defeat": [
                            "TRAINING BOT: INSUFFICIENT SKILL DETECTED.",
                            "TRAINING BOT: RECOMMEND ADDITIONAL PRACTICE."
                        ],
                        "special_rules": {
                            "player_starting_points": 0,
                            "tutorial_hints": True
                        },
                        "reward_money": 100
                    },
                    {
                        "id": "sergeant_mills",
                        "opponent": "Sergeant Mills", 
                        "difficulty": "easy",
                        "portrait": "SGT",
                        "affiliation": "HELIX DEFENSE FORCE",
                        "rank": "SERGEANT",
                        "threat_level": "LOW",
                        "classification": "FRIENDLY",
                        "specialization": "Field Combat Training",
                        "pre_battle": [
                            "SGT. MILLS: So you're the new recruit?",
                            "SGT. MILLS: The academy may have taught you the basics,",
                            "SGT. MILLS: but real combat is different.",
                            "SGT. MILLS: Let's see if you can handle pressure!"
                        ],
                        "victory": [
                            "SGT. MILLS: Not bad, rookie!",
                            "SGT. MILLS: You might just survive out there.",
                            "SGT. MILLS: Welcome to Checkmate Protocol!"
                        ],
                        "defeat": [
                            "SGT. MILLS: You're not ready for the field.",
                            "SGT. MILLS: Hit the training room and try again!"
                        ],
                        "special_rules": {
                            "enemy_starting_powerup": "shield",
                            "enemy_starting_points": 2  # Chapter 1: 0-2 points
                        },
                        "reward_money": 200
                    }
                ]
            },
            {
                "id": "chapter_2",
                "title": "First Blood",
                "intro": [
                    "Your unit has been deployed to the contested border.",
                    "Enemy forces have been spotted moving through the area.",
                    "",
                    "This is no longer training.",
                    "This is war.",
                ],
                "battles": [
                    {
                        "id": "enemy_scout",
                        "opponent": "Enemy Scout",
                        "difficulty": "medium",
                        "portrait": "SCT",
                        "pre_battle": [
                            "ENEMY SCOUT: You shouldn't have come here!",
                            "ENEMY SCOUT: This territory belongs to us now.",
                            "ENEMY SCOUT: Prepare to be eliminated!"
                        ],
                        "victory": [
                            "ENEMY SCOUT: Impossible!",
                            "ENEMY SCOUT: Command will hear about this...",
                            "*The scout retreats into the shadows*"
                        ],
                        "defeat": [
                            "ENEMY SCOUT: Too easy.",
                            "ENEMY SCOUT: Your unit chose poorly sending you."
                        ],
                        "special_rules": {
                            "enemy_starting_points": 3,  # Chapter 2: 3-5 points (reduced from 10)
                            "fog_of_war": True
                        },
                        "reward_money": 300
                    },
                    {
                        "id": "commander_vex",
                        "opponent": "Commander Vex",
                        "difficulty": "medium",
                        "portrait": "CMD",
                        "pre_battle": [
                            "CMDR. VEX: So, you're the one who defeated my scout.",
                            "CMDR. VEX: I've studied your moves. Your patterns.",
                            "CMDR. VEX: Your little victories end here!",
                            "CMDR. VEX: Prepare to face a real strategist!"
                        ],
                        "victory": [
                            "CMDR. VEX: This... this is impossible!",
                            "CMDR. VEX: My strategies were perfect!",
                            "CMDR. VEX: Mark my words - this isn't over!",
                            "*Commander Vex retreats with his remaining forces*"
                        ],
                        "defeat": [
                            "CMDR. VEX: As expected.",
                            "CMDR. VEX: You're not ready for real warfare.",
                            "CMDR. VEX: Tell your commanders to send someone better."
                        ],
                        "special_rules": {
                            "enemy_starting_points": 5,  # Chapter 2: 3-5 points
                            "turbo_mode": True,
                            "ai_aggression": 1.5
                        },
                        "reward_money": 500
                    }
                ]
            },
            {
                "id": "chapter_3",
                "title": "The Arms Race",
                "intro": [
                    "Intelligence reports indicate the enemy has acquired",
                    "new experimental weapons from a mysterious supplier.",
                    "",
                    "You're introduced to Tariq, a weapons dealer",
                    "who might be able to even the odds...",
                ],
                "battles": [
                    {
                        "id": "weapons_tester",
                        "opponent": "Dr. Kriegspiel",
                        "difficulty": "hard",
                        "portrait": "DR",
                        "pre_battle": [
                            "DR. KRIEGSPIEL: Ah, a test subject arrives!",
                            "DR. KRIEGSPIEL: You're just in time to experience",
                            "DR. KRIEGSPIEL: my latest weapons technology!",
                            "DR. KRIEGSPIEL: FOR SCIENCE!"
                        ],
                        "victory": [
                            "DR. KRIEGSPIEL: Fascinating data!",
                            "DR. KRIEGSPIEL: Your survival was... unexpected.",
                            "DR. KRIEGSPIEL: I must recalibrate my formulas!",
                            "*Dr. Kriegspiel flees with his research*"
                        ],
                        "defeat": [
                            "DR. KRIEGSPIEL: Another successful experiment!",
                            "DR. KRIEGSPIEL: Your defeat provides valuable data.",
                            "DR. KRIEGSPIEL: Thank you for your contribution to science!"
                        ],
                        "special_rules": {
                            "enemy_starting_points": 5,  # Chapter 3: 5-8 points
                            "enemy_starting_powerup": "gun",
                            "random_airstrikes": True,
                            "enemy_bonus_points_per_turn": 1  # Reduced from 2
                        },
                        "reward_money": 800
                    },
                    {
                        "id": "tariq_test",
                        "opponent": "Tariq's Champion",
                        "difficulty": "hard",
                        "portrait": "CHP",
                        "pre_battle": [
                            "TARIQ: My friend, before we do business...",
                            "TARIQ: You must prove you can handle my merchandise.",
                            "TARIQ: Face my champion. Show me your worth.",
                            "CHAMPION: I never lose. Prepare yourself."
                        ],
                        "victory": [
                            "TARIQ: Impressive! Most impressive!",
                            "TARIQ: You have earned my respect, and my catalog.",
                            "TARIQ: My finest weapons are now available to you.",
                            "CHAMPION: I... I have been bested. Well fought."
                        ],
                        "defeat": [
                            "TARIQ: Perhaps you need more... basic equipment?",
                            "TARIQ: Come back when you are ready for real power.",
                            "CHAMPION: As expected. None can match me."
                        ],
                        "special_rules": {
                            "enemy_starting_points": 8,  # Chapter 3: 5-8 points
                            "player_starting_points": 5,  # Player gets some too
                            "both_start_with_powerups": True,
                            "high_stakes": True
                        },
                        "reward_money": 1000
                    }
                ]
            },
            {
                "id": "chapter_4",
                "title": "The Final Protocol",
                "intro": [
                    "The enemy's supreme leader has challenged you",
                    "to single combat. Winner takes all.",
                    "",
                    "Everything has led to this moment.",
                    "The fate of the war rests on this final match.",
                ],
                "battles": [
                    {
                        "id": "general_nexus",
                        "opponent": "General Nexus",
                        "difficulty": "very_hard",
                        "portrait": "GEN",
                        "pre_battle": [
                            "GENERAL NEXUS: So, you're the one they call",
                            "GENERAL NEXUS: the 'Hero of Checkmate Protocol.'",
                            "GENERAL NEXUS: You've caused me considerable trouble.",
                            "GENERAL NEXUS: But your journey ends here.",
                            "GENERAL NEXUS: I am inevitable. I am supreme.",
                            "GENERAL NEXUS: Bow before your emperor!"
                        ],
                        "victory": [
                            "GENERAL NEXUS: No... This cannot be!",
                            "GENERAL NEXUS: I am... I am defeated.",
                            "GENERAL NEXUS: You have won this war, but at what cost?",
                            "GENERAL NEXUS: Perhaps... perhaps there is hope after all.",
                            "",
                            "CONGRATULATIONS!",
                            "You have completed the Checkmate Protocol campaign!",
                            "The war is over. You are victorious."
                        ],
                        "defeat": [
                            "GENERAL NEXUS: As I predicted.",
                            "GENERAL NEXUS: You were never going to win.",
                            "GENERAL NEXUS: Your resistance ends now.",
                            "GENERAL NEXUS: Submit to the new order!"
                        ],
                        "special_rules": {
                            "boss_battle": True,
                            "enemy_starting_points": 12,  # Chapter 4: 8-12 points (reduced from 25)
                            "player_starting_points": 8,   # Player gets some too (reduced from 15)
                            "nexus_special_ability": True,
                            "dramatic_music": True
                        },
                        "reward_money": 5000
                    }
                ]
            },
            {
                "id": "epilogue",
                "title": "Epilogue: New Threats",
                "intro": [
                    "With General Nexus defeated, peace returns to the land.",
                    "But rumors speak of new threats emerging...",
                    "",
                    "Coming in future updates:",
                    "- New chapters with unique enemies",
                    "- Multiplayer campaigns",
                    "- Custom battle creator",
                    "",
                    "Thank you for playing Checkmate Protocol!"
                ],
                "battles": []
            }
        ]
        
        # Load progress
        self.load_progress()
        
    def load_progress(self):
        """Load progress from global state."""
        story_progress = config.get_story_progress()
        self.current_chapter = story_progress.get('current_chapter', 0)
        self.current_battle = story_progress.get('current_battle', 0)
        self.completed_battles = story_progress.get('completed_battles', [])
        self.unlocked_chapters = story_progress.get('unlocked_chapters', [True, False, False, False, False])
        print(f"[STORY LOAD] Loaded from global state: battles={self.completed_battles}, chapters={self.unlocked_chapters}")
            
    def save_progress(self):
        """Simple save - just print for now."""
        print(f"[SAVE DISABLED] Would save: battles={self.completed_battles}, chapters={self.unlocked_chapters}")
        return True
            
    def reset_progress(self):
        """Reset story progress to beginning."""
        self.current_chapter = 0
        self.current_battle = 0
        self.completed_battles = []
        # Start with only first chapter unlocked
        self.unlocked_chapters = [True, False, False, False, False]
        # Save the reset state
        self.save_progress()
        
    def get_current_chapter(self):
        """Get current chapter data."""
        if 0 <= self.current_chapter < len(self.chapters):
            return self.chapters[self.current_chapter]
        return None
        
    def get_current_battle(self):
        """Get current battle data."""
        chapter = self.get_current_chapter()
        if chapter and 0 <= self.current_battle < len(chapter["battles"]):
            return chapter["battles"][self.current_battle]
        return None
        
    def complete_battle(self, battle_id, won=True):
        """Mark a battle as completed."""
        print(f"\n=== STORY MODE BATTLE COMPLETION ===")
        print(f"StoryMode instance id: {id(self)}")
        print(f"Completing battle: {battle_id}")
        print(f"Won: {won}")
        print(f"Current state - chapter: {self.current_chapter}, battle: {self.current_battle}")
        print(f"Completed battles before: {self.completed_battles}")
        
        # Special handling for enemy_scout to ensure it completes properly
        if battle_id == "enemy_scout":
            print("SPECIAL HANDLING FOR ENEMY SCOUT BATTLE!")
        
        # Add to completed battles using global state
        if battle_id not in self.completed_battles:
            self.completed_battles.append(battle_id)
            # Update global state
            config.complete_story_battle(battle_id)
            print(f"Added {battle_id} to completed battles")
        else:
            print(f"{battle_id} was already in completed battles")
            
        print(f"Completed battles after: {self.completed_battles}")
            
        if won:
            # Find which chapter contains this battle
            chapter_index = None
            target_chapter = None
            for idx, chapter in enumerate(self.chapters):
                for battle in chapter["battles"]:
                    if battle["id"] == battle_id:
                        chapter_index = idx
                        target_chapter = chapter
                        break
                if chapter_index is not None:
                    break
                    
            if target_chapter is None:
                print(f"ERROR: Battle {battle_id} not found in any chapter!")
                return
                
            print(f"Battle {battle_id} belongs to chapter {chapter_index}: {target_chapter['id']}")
            print(f"Chapter battles: {[b['id'] for b in target_chapter['battles']]}")
            
            # Check if all battles in the chapter are complete
            all_complete = all(battle['id'] in self.completed_battles for battle in target_chapter['battles'])
            print(f"All battles complete in chapter {chapter_index}: {all_complete}")
            
            if all_complete:
                print(f"Chapter {chapter_index} ({target_chapter['id']}) is COMPLETE!")
                print(f"Current unlocked_chapters: {self.unlocked_chapters}")
                
                # Unlock next chapter
                if chapter_index + 1 < len(self.unlocked_chapters):
                    self.unlocked_chapters[chapter_index + 1] = True
                    # Update global state
                    config.unlock_story_chapter(chapter_index + 1)
                    print(f"UNLOCKED chapter {chapter_index + 1}!")
                    print(f"New unlocked_chapters: {self.unlocked_chapters}")
                    
                    # Special case for Chapter 2 completion
                    if chapter_index == 1:  # Chapter 2 (0-indexed)
                        print("Chapter 2 completed! Chapter 3 'The Arms Race' should now be unlocked!")
                    # Special case for final chapter completion
                    elif chapter_index == 3:  # Chapter 4 (0-indexed)
                        print("CONGRATULATIONS! You have completed the main campaign!")
                        print("The Epilogue chapter is now available.")
                else:
                    print("No more chapters to unlock")
                    
        print("=== END BATTLE COMPLETION ===\n")
                
        # Save progress with robust verification
        saved_battles = self.completed_battles[:]  # Keep a copy
        saved_chapters = self.unlocked_chapters[:]
        
        success = self.save_progress()
        
        if success:
            # Double-check by reloading
            self.load_progress()
            if battle_id in self.completed_battles:
                print(f"✓ Battle {battle_id} completion confirmed!")
                self._log_completion_success(battle_id)
            else:
                print(f"✗ ERROR: {battle_id} not found after reload!")
                # Restore and retry
                self.completed_battles = saved_battles
                self.unlocked_chapters = saved_chapters
                self.save_progress()
        else:
            print(f"✗ ERROR: Failed to save {battle_id} completion!")
            # Try emergency save
            self._emergency_save(battle_id, saved_battles, saved_chapters)
            
    def _log_completion_success(self, battle_id):
        """Logging disabled."""
        pass
            
    def _emergency_save(self, battle_id, battles, chapters):
        """Emergency save disabled."""
        pass
        
    def get_chapter_progress(self, chapter_index):
        """Get completion percentage for a chapter."""
        if 0 <= chapter_index < len(self.chapters):
            chapter = self.chapters[chapter_index]
            if not chapter["battles"]:
                return 100  # Epilogue or no battles
                
            completed = 0
            for battle in chapter["battles"]:
                if battle["id"] in self.completed_battles:
                    completed += 1
                    
            return int((completed / len(chapter["battles"])) * 100)
        return 0
        
    def is_battle_completed(self, battle_id):
        """Check if a battle has been completed."""
        return battle_id in self.completed_battles
    
    def is_battle_unlocked(self, chapter_index, battle_index):
        """Check if a battle is unlocked based on sequential completion."""
        # First battle of first chapter is always unlocked
        if chapter_index == 0 and battle_index == 0:
            return True
            
        # For other battles, check if the previous battle in the chapter is completed
        if battle_index > 0:
            # Check previous battle in same chapter
            previous_battle = self.chapters[chapter_index]["battles"][battle_index - 1]
            is_completed = self.is_battle_completed(previous_battle["id"])
            print(f"Checking unlock for battle {battle_index} in chapter {chapter_index}")
            print(f"Previous battle: {previous_battle['id']}, completed: {is_completed}")
            return is_completed
        else:
            # First battle of a chapter - check if last battle of previous chapter is completed
            if chapter_index > 0:
                previous_chapter = self.chapters[chapter_index - 1]
                last_battle = previous_chapter["battles"][-1]
                is_completed = self.is_battle_completed(last_battle["id"])
                print(f"Checking unlock for first battle of chapter {chapter_index}")
                print(f"Last battle of previous chapter: {last_battle['id']}, completed: {is_completed}")
                return is_completed
        
        return False
        
    def get_total_progress(self):
        """Get overall story completion percentage."""
        total_battles = 0
        completed_battles = 0
        
        for chapter in self.chapters:
            for battle in chapter["battles"]:
                total_battles += 1
                if battle["id"] in self.completed_battles:
                    completed_battles += 1
                    
        if total_battles == 0:
            return 100
            
        return int((completed_battles / total_battles) * 100)
        
    def apply_battle_rules(self, battle_data, board, powerup_system, ai=None):
        """Apply special rules for a story battle."""
        rules = battle_data.get("special_rules", {})
        
        # Starting points
        if "player_starting_points" in rules:
            powerup_system.points["white"] = rules["player_starting_points"]
        if "enemy_starting_points" in rules:
            powerup_system.points["black"] = rules["enemy_starting_points"]
            
        # Starting powerups
        if "enemy_starting_powerup" in rules:
            # Give AI enough points to use the powerup
            powerup = rules["enemy_starting_powerup"]
            if powerup in powerup_system.powerups:
                powerup_system.points["black"] += powerup_system.powerups[powerup]["cost"]
                
        # Both start with powerups
        if rules.get("both_start_with_powerups"):
            for color in ["white", "black"]:
                powerup_system.points[color] = 20
                
        # Bonus points per turn
        if "enemy_bonus_points_per_turn" in rules:
            # This would need to be checked each turn in the game loop
            pass
            
        # AI aggression multiplier
        if "ai_aggression" in rules and ai:
            # Modify AI behavior to be more aggressive
            if hasattr(ai, 'aggression_multiplier'):
                ai.aggression_multiplier = rules["ai_aggression"]
                
        # Boss battle rules
        if rules.get("boss_battle"):
            # Could add special boss abilities here
            pass
            
        return rules