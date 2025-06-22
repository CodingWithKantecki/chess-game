"""
Asset Loading and Management
"""

import pygame
import os
from config import *

class AssetManager:
    def __init__(self):
        self.pieces_original = {}  # Store original images
        self.pieces = {}  # Scaled versions
        self.board_texture_original = None
        self.board_texture = None
        self.parallax_layers_original = []
        self.parallax_layers = []
        self.sounds = {}
        self.explosion_frames = []  # Store explosion animation frames
        self.revolver_image = None  # Store revolver image
        self.jet_frames = []  # Store jet animation frames
        self.tariq_image = None  # Store Tariq character image
        self.arms_background = None  # Store arms dealer background
        self.cockpit_view = None  # Store cockpit view for chopper gunner
        self.chopper_activation_overlay = None  # Store chopper activation overlay
        
    def load_all(self):
        """Load all game assets."""
        print("Loading game assets...")
        self.load_pieces()
        self.load_board()
        self.load_backgrounds()
        self.load_sounds()
        self.load_explosion_frames()
        self.load_revolver()
        self.load_jet_frames()
        self.load_tariq()
        self.load_arms_background()
        self.load_cockpit_view()
        self.load_chopper_activation_overlay()
        print("Assets loaded!")
        
    def load_pieces(self):
        """Load chess piece images."""
        for piece_code, filename in PIECE_IMAGES.items():
            filepath = os.path.join(ASSETS_DIR, filename)
            
            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath).convert_alpha()
                    # Store original
                    self.pieces_original[piece_code] = img
                    # Scale piece to fit square
                    img = self.scale_piece(img)
                    self.pieces[piece_code] = img
                    print(f"✓ Loaded {piece_code}")
                except:
                    fallback = self.create_fallback_piece(piece_code)
                    self.pieces_original[piece_code] = fallback
                    self.pieces[piece_code] = fallback
            else:
                fallback = self.create_fallback_piece(piece_code)
                self.pieces_original[piece_code] = fallback
                self.pieces[piece_code] = fallback
                
    def scale_piece(self, img):
        """Scale piece image to fit square."""
        # Get bounds and trim transparent pixels
        rect = img.get_bounding_rect()
        trimmed = img.subsurface(rect).copy()
        
        # Scale to 80% of square size
        size = int(SQUARE_SIZE * 0.8)
        aspect = trimmed.get_width() / trimmed.get_height()
        
        if aspect > 1:
            w = size
            h = int(size / aspect)
        else:
            h = size
            w = int(size * aspect)
            
        scaled = pygame.transform.scale(trimmed, (w, h))
        
        # Center on transparent surface
        final = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        final.fill((0, 0, 0, 0))
        x = (SQUARE_SIZE - w) // 2
        y = (SQUARE_SIZE - h) // 2
        final.blit(scaled, (x, y))
        
        return final
        
    def create_fallback_piece(self, piece_code):
        """Create simple piece if image missing."""
        surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        
        # Draw circle
        color = WHITE if piece_code[0] == 'w' else BLACK
        center = SQUARE_SIZE // 2
        radius = int(SQUARE_SIZE * 0.4)
        pygame.draw.circle(surface, color, (center, center), radius)
        pygame.draw.circle(surface, (128, 128, 128), (center, center), radius, 2)
        
        # Draw letter
        font = pygame.font.Font(None, 32)
        text = font.render(piece_code[1], True, (128, 128, 128))
        text_rect = text.get_rect(center=(center, center))
        surface.blit(text, text_rect)
        
        return surface
        
    def load_board(self):
        """Load board texture."""
        for texture in BOARD_TEXTURES:
            filepath = os.path.join(ASSETS_DIR, texture)
            if os.path.exists(filepath):
                try:
                    self.board_texture_original = pygame.image.load(filepath)
                    self.board_texture = pygame.transform.scale(
                        self.board_texture_original, (BOARD_SIZE, BOARD_SIZE))
                    print(f"✓ Loaded board texture")
                    return
                except:
                    pass
        print("! Using default board")
        
    def load_backgrounds(self):
        """Load parallax backgrounds."""
        print(f"\nLoading parallax backgrounds from {ASSETS_DIR}...")
        print(f"Looking for {len(PARALLAX_LAYERS)} layers")
        
        loaded_count = 0
        for i, layer in enumerate(PARALLAX_LAYERS):
            filepath = os.path.join(ASSETS_DIR, layer["file"])
            print(f"  Checking for {layer['file']}... ", end="")
            
            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath).convert_alpha()
                    print(f"✓ Loaded (size: {img.get_width()}x{img.get_height()})")
                    
                    # Store original
                    self.parallax_layers_original.append({
                        "image": img,
                        "speed": layer["speed"],
                        "original_width": img.get_width(),
                        "original_height": img.get_height()
                    })
                    
                    # Scale to window height
                    aspect = img.get_width() / img.get_height()
                    new_h = HEIGHT
                    new_w = int(new_h * aspect)
                    scaled = pygame.transform.scale(img, (new_w, new_h))
                    
                    self.parallax_layers.append({
                        "image": scaled,
                        "speed": layer["speed"],
                        "width": new_w,
                        "x": 0
                    })
                    loaded_count += 1
                except Exception as e:
                    print(f"✗ Error: {str(e)}")
            else:
                print(f"✗ File not found")
                
        print(f"\nLoaded {loaded_count}/{len(PARALLAX_LAYERS)} parallax layers")
        print(f"parallax_layers list has {len(self.parallax_layers)} items\n")
                    
    def load_sounds(self):
        """Load sound effects and music."""
        # Load music
        music_path = os.path.join(ASSETS_DIR, MUSIC_FILE)
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                print("✓ Loaded music")
            except:
                pass
                
        # Load capture sound
        capture_path = os.path.join(ASSETS_DIR, CAPTURE_SOUND)
        if os.path.exists(capture_path):
            try:
                self.sounds['capture'] = pygame.mixer.Sound(capture_path)
                # Don't set volume here - let game.py handle it
                print("✓ Loaded capture sound")
            except:
                pass
                
        # Load bomb sound for airstrike
        bomb_path = os.path.join(ASSETS_DIR, "bombsound.mp3")
        if os.path.exists(bomb_path):
            try:
                self.sounds['bomb'] = pygame.mixer.Sound(bomb_path)
                # Don't set volume here - let game.py handle it
                print("✓ Loaded bomb sound")
            except:
                pass
                
        # Load minigun sound
        minigun_path = os.path.join(ASSETS_DIR, "minigun.mp3")
        if os.path.exists(minigun_path):
            try:
                self.sounds['minigun'] = pygame.mixer.Sound(minigun_path)
                print("✓ Loaded minigun sound")
            except:
                pass
                
        # Load helicopter sound
        helicopter_path = os.path.join(ASSETS_DIR, "helicopter.mp3")
        if os.path.exists(helicopter_path):
            try:
                self.sounds['helicopter'] = pygame.mixer.Sound(helicopter_path)
                print("✓ Loaded helicopter sound")
            except:
                pass
                
        # Load helicopter blade sound
        helicopter_blade_path = os.path.join(ASSETS_DIR, "helicopta.wav")
        if os.path.exists(helicopter_blade_path):
            try:
                self.sounds['helicopter_blade'] = pygame.mixer.Sound(helicopter_blade_path)
                print("✓ Loaded helicopter blade sound")
            except Exception as e:
                print(f"✗ Error loading helicopter blade sound: {str(e)}")
        else:
            print(f"✗ helicopta.wav not found at {helicopter_blade_path}")
                
    def load_explosion_frames(self):
        """Load explosion animation frames."""
        print("\nLoading explosion animation frames...")
        
        for i in range(1, 8):  # frame1.png through frame7.png
            filename = f"frame{i}.png"
            filepath = os.path.join(ASSETS_DIR, filename)
            
            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath).convert_alpha()
                    self.explosion_frames.append(img)
                    print(f"✓ Loaded {filename}")
                except Exception as e:
                    print(f"✗ Error loading {filename}: {str(e)}")
            else:
                print(f"✗ {filename} not found")
                
        print(f"Loaded {len(self.explosion_frames)}/7 explosion frames")
        
    def load_revolver(self):
        """Load revolver image."""
        revolver_path = os.path.join(ASSETS_DIR, "revolver.png")
        if os.path.exists(revolver_path):
            try:
                self.revolver_image = pygame.image.load(revolver_path).convert_alpha()
                print("✓ Loaded revolver image")
            except Exception as e:
                print(f"✗ Error loading revolver: {str(e)}")
        else:
            print("✗ Revolver image not found")
            
    def load_jet_frames(self):
        """Load jet animation frames."""
        print("\nLoading jet animation frames...")
        
        # Load the jet frames in order
        jet_files = [
            "frame_0_delay-0.2s.png",
            "frame_1_delay-0.14s.png",
            "frame_2_delay-0.14s.png",
            "frame_3_delay-0.2s.png"
        ]
        
        for filename in jet_files:
            filepath = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath).convert_alpha()
                    self.jet_frames.append(img)
                    print(f"✓ Loaded {filename}")
                except Exception as e:
                    print(f"✗ Error loading {filename}: {str(e)}")
            else:
                print(f"✗ {filename} not found")
                
        print(f"Loaded {len(self.jet_frames)}/4 jet frames")
        
    def load_tariq(self):
        """Load Tariq character image."""
        tariq_path = os.path.join(ASSETS_DIR, "Tariq Steele.png")
        if os.path.exists(tariq_path):
            try:
                self.tariq_image = pygame.image.load(tariq_path).convert_alpha()
                print("✓ Loaded Tariq character")
            except Exception as e:
                print(f"✗ Error loading Tariq: {str(e)}")
        else:
            print("✗ Tariq image not found")
            
    def load_arms_background(self):
        """Load arms dealer background."""
        bg_path = os.path.join(ASSETS_DIR, "arms_background.png")
        if os.path.exists(bg_path):
            try:
                self.arms_background = pygame.image.load(bg_path).convert()
                print("✓ Loaded arms dealer background")
            except Exception as e:
                print(f"✗ Error loading arms background: {str(e)}")
        else:
            print("✗ Arms dealer background not found")
            
    def load_cockpit_view(self):
        """Load cockpit view for chopper gunner."""
        cockpit_path = os.path.join(ASSETS_DIR, "cockpit_view.png")
        if os.path.exists(cockpit_path):
            try:
                self.cockpit_view = pygame.image.load(cockpit_path).convert_alpha()
                print("✓ Loaded cockpit view")
            except Exception as e:
                print(f"✗ Error loading cockpit view: {str(e)}")
        else:
            print("✗ Cockpit view not found")
            
    def load_chopper_activation_overlay(self):
        """Load chopper activation overlay."""
        overlay_path = os.path.join(ASSETS_DIR, "copter2.png")
        if os.path.exists(overlay_path):
            try:
                self.chopper_activation_overlay = pygame.image.load(overlay_path).convert_alpha()
                print("✓ Loaded chopper activation overlay")
            except Exception as e:
                print(f"✗ Error loading chopper activation overlay: {str(e)}")
        else:
            print("✗ copter2.png not found")