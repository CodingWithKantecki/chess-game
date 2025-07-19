"""
Story Mode for Chess Game
Campaign with chapters, special battles, and progression
"""

import json
import os
import config

class StoryMode:
    def __init__(self):
        self.current_chapter = 0
        self.current_battle = 0
        self.save_file = "story_progress.json"
        
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
                            "player_starting_points": 5,
                            "tutorial_hints": True
                        },
                        "reward_money": 100,
                        "reward_unlocks": []
                    },
                    {
                        "id": "sergeant_mills",
                        "opponent": "Sergeant Mills", 
                        "difficulty": "easy",
                        "portrait": "SGT",
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
                            "enemy_starting_powerup": "shield"
                        },
                        "reward_money": 200,
                        "reward_unlocks": ["gun"]
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
                            "enemy_starting_points": 10,
                            "fog_of_war": True
                        },
                        "reward_money": 300,
                        "reward_unlocks": []
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
                            "turbo_mode": True,
                            "ai_aggression": 1.5
                        },
                        "reward_money": 500,
                        "reward_unlocks": ["airstrike"]
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
                            "enemy_starting_powerup": "gun",
                            "random_airstrikes": True,
                            "enemy_bonus_points_per_turn": 2
                        },
                        "reward_money": 800,
                        "reward_unlocks": ["paratroopers"]
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
                            "both_start_with_powerups": True,
                            "high_stakes": True
                        },
                        "reward_money": 1000,
                        "reward_unlocks": ["chopper"]
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
                            "enemy_starting_points": 25,
                            "player_starting_points": 15,
                            "nexus_special_ability": True,
                            "dramatic_music": True
                        },
                        "reward_money": 5000,
                        "reward_unlocks": ["victory_badge", "nexus_pieces"]
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
        """Load story mode progress from save file."""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                    self.current_chapter = data.get("current_chapter", 0)
                    self.current_battle = data.get("current_battle", 0)
                    self.completed_battles = data.get("completed_battles", [])
                    self.unlocked_chapters = data.get("unlocked_chapters", [True, False, False, False, False])
            except:
                self.reset_progress()
        else:
            self.reset_progress()
            
    def save_progress(self):
        """Save story mode progress."""
        data = {
            "current_chapter": self.current_chapter,
            "current_battle": self.current_battle,
            "completed_battles": self.completed_battles,
            "unlocked_chapters": self.unlocked_chapters
        }
        with open(self.save_file, 'w') as f:
            json.dump(data, f)
            
    def reset_progress(self):
        """Reset story progress to beginning."""
        self.current_chapter = 0
        self.current_battle = 0
        self.completed_battles = []
        self.unlocked_chapters = [True, False, False, False, False]
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
        if battle_id not in self.completed_battles:
            self.completed_battles.append(battle_id)
            
        if won:
            # Move to next battle
            self.current_battle += 1
            chapter = self.get_current_chapter()
            
            # Check if chapter is complete
            if chapter and self.current_battle >= len(chapter["battles"]):
                # Unlock next chapter
                if self.current_chapter + 1 < len(self.unlocked_chapters):
                    self.unlocked_chapters[self.current_chapter + 1] = True
                    
                # Move to next chapter
                self.current_chapter += 1
                self.current_battle = 0
                
        self.save_progress()
        
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
            # Give AI a free powerup to use
            powerup = rules["enemy_starting_powerup"]
            if powerup in powerup_system.powerups:
                powerup_system.pending_streak_rewards["black"].append({
                    "powerup": powerup,
                    "streak": 0,
                    "name": "Starting bonus"
                })
                
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