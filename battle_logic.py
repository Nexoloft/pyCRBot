"""
Battle logic and game mechanics
"""

import time
import random
from config import (
    CARD_SLOTS, PLAY_AREA, ELIXIR_COORDS, PURPLE_COLORS, 
    BATTLE_PIXELS_1V1, BATTLE_PIXELS_2V2, POST_BATTLE_PIXELS,
    COLOR_TOLERANCE, ELIXIR_COLOR_TOLERANCE, FALLBACK_POSITIONS
)


class BattleLogic:
    """Handles battle-specific game logic"""
    
    def __init__(self, instance_name, image_detector):
        self.instance_name = instance_name
        self.detector = image_detector
    
    def detect_elixir_amount(self, screenshot):
        """Detect current elixir amount using pixel detection"""
        if screenshot is None:
            return None
        
        # Check from highest elixir to lowest to find the maximum
        for elixir_level in range(10, 0, -1):
            x_position, y_position = ELIXIR_COORDS[elixir_level - 1]
            
            # Check if pixel at this position matches any purple variant
            try:
                pixel = screenshot[y_position, x_position]
                pixel_bgr = [int(pixel[0]), int(pixel[1]), int(pixel[2])]
                pixel_rgb = [pixel_bgr[2], pixel_bgr[1], pixel_bgr[0]]  # Convert BGR to RGB
                
                for purple_color in PURPLE_COLORS:
                    if self.detector.pixel_matches_color_rgb(pixel_rgb, purple_color, tolerance=ELIXIR_COLOR_TOLERANCE):
                        print(f"[{self.instance_name}] Elixir detected: {elixir_level} (purple pixel at {x_position}, {y_position})")
                        return elixir_level
                        
            except (IndexError, TypeError):
                continue
        
        # If no purple pixels found, elixir is 0
        print(f"[{self.instance_name}] Elixir detected: 0 (no purple pixels found)")
        return 0
    
    def detect_2x_elixir(self, screenshot):
        """Detect if 2x elixir mode is active using template matching"""
        position, confidence = self.detector.find_template("2xElixir", screenshot)
        if position:
            print(f"[{self.instance_name}] 2x Elixir detected! (confidence: {confidence:.2f})")
            return True
        return False
    
    def is_in_battle(self, screenshot):
        """Check if we're in battle using multiple detection methods"""
        # Method 1: Template detection
        position, confidence = self.detector.find_template("in_battle", screenshot)
        if position:
            print(f"[{self.instance_name}] In battle detected (template confidence: {confidence:.2f})")
            return True
            
        # Method 2: Pixel-based detection
        if screenshot is None:
            return False
            
        try:
            # Check 1v1 battle pixels
            pixels_1v1 = []
            for coords in BATTLE_PIXELS_1V1["pixels"]:
                pixels_1v1.append(screenshot[coords[0]][coords[1]])
            
            if self.detector.all_pixels_match(pixels_1v1, BATTLE_PIXELS_1V1["colors"], tolerance=ELIXIR_COLOR_TOLERANCE):
                print(f"[{self.instance_name}] In 1v1 battle detected (pixel check)")
                return True
                
            # Check 2v2 battle pixels
            pixels_2v2 = []
            for coords in BATTLE_PIXELS_2V2["pixels"]:
                pixels_2v2.append(screenshot[coords[0]][coords[1]])
                
            if self.detector.all_pixels_match(pixels_2v2, BATTLE_PIXELS_2V2["colors"], tolerance=ELIXIR_COLOR_TOLERANCE):
                print(f"[{self.instance_name}] In 2v2 battle detected (pixel check)")
                return True
                
        except (IndexError, TypeError):
            # Fall back to template detection if pixel check fails
            pass
            
        return False
    
    def find_post_battle_button(self, screenshot):
        """Find and return coordinates for post-battle exit/OK button using multiple methods"""
        if screenshot is None:
            return None
            
        # Method 1: Template detection for PlayAgain button (highest priority)
        play_again_position, play_again_confidence = self.detector.find_template("play_again", screenshot)
        if play_again_position and play_again_confidence is not None and play_again_confidence > 0.7:
            print(f"[{self.instance_name}] Post-battle PlayAgain button found (template confidence: {play_again_confidence:.2f})")
            return play_again_position
            
        # Method 2: Template detection for OK button
        ok_position, ok_confidence = self.detector.find_template("ok_button", screenshot)
        if ok_position and ok_confidence is not None and ok_confidence > 0.7:
            print(f"[{self.instance_name}] Post-battle OK button found (template confidence: {ok_confidence:.2f})")
            return ok_position
            
        # Method 3: Fast pixel-based detection
        try:
            pixels = []
            for coords in POST_BATTLE_PIXELS["pixels"]:
                pixels.append(screenshot[coords[0]][coords[1]])
            
            if self.detector.all_pixels_match(pixels, POST_BATTLE_PIXELS["colors"], tolerance=COLOR_TOLERANCE):
                print(f"[{self.instance_name}] Post-battle button found (pixel detection)")
                return FALLBACK_POSITIONS["post_battle_button"]
        except (IndexError, TypeError):
            pass
            
        # Method 4: Look for Confirm button
        confirm_position, confirm_confidence = self.detector.find_template("confirm", screenshot)
        if confirm_position and confirm_confidence is not None and confirm_confidence > 0.7:
            print(f"[{self.instance_name}] Post-battle Confirm button found (template confidence: {confirm_confidence:.2f})")
            return confirm_position
            
        return None
    
    def count_elixir(self, screenshot, target_elixir):
        """Check if we have at least the target amount of elixir"""
        current_elixir = self.detect_elixir_amount(screenshot)
        if current_elixir is None:
            return False
        return current_elixir >= target_elixir
    
    def wait_for_elixir(self, target_elixir, timeout, screenshot_func, is_in_battle_func, shutdown_check_func):
        """Wait for a specific amount of elixir with improved logic"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if shutdown_check_func():
                return False
                
            # Check if we're still in battle
            screenshot = screenshot_func()
            if not is_in_battle_func(screenshot):
                print(f"[{self.instance_name}] Not in battle anymore while waiting for elixir")
                return False
                
            # Check current elixir
            current_elixir = self.detect_elixir_amount(screenshot)
            if current_elixir is not None:
                if current_elixir >= target_elixir:
                    print(f"[{self.instance_name}] Have {current_elixir} elixir (needed {target_elixir})")
                    return True
                    
            time.sleep(0.5)  # Check twice per second
            
        print(f"[{self.instance_name}] Timeout waiting for {target_elixir} elixir")
        return False
    
    def generate_play_position(self):
        """Generate a strategic position within the play area"""
        if random.randint(0, 2) == 0:  # 33% chance for bridge play
            # Bridge positions (more strategic)
            place_x = random.choice([120, 300])  # Left or right bridge
            place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
        else:
            # Random position in play area
            place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
            place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
        
        return place_x, place_y
    
    def select_random_card(self, exclude_slot=None):
        """Select a random card slot, optionally excluding one slot"""
        if exclude_slot:
            available_slots = [slot for slot in CARD_SLOTS if slot != exclude_slot]
            return random.choice(available_slots)
        else:
            return random.choice(CARD_SLOTS)
    
    def should_play_combo(self, battle_phase, is_2x_elixir):
        """Determine if we should play a combo based on battle conditions"""
        if is_2x_elixir:
            return random.randint(0, 2) == 0  # 33% chance in 2x elixir
        elif battle_phase == "late":
            return random.randint(0, 3) == 0  # 25% chance in late game
        else:
            return random.randint(0, 4) == 0  # 20% chance normally
    
    def should_play_single_card(self, current_elixir, min_elixir=3):
        """Determine if we should play a single card based on elixir"""
        if current_elixir is None:
            return True  # Play if we can't detect elixir
        return current_elixir >= min_elixir
    
    def check_which_cards_are_available(self, screenshot):
        """Check which card slots have cards available to play"""
        if screenshot is None:
            return []
        
        available_cards = []
        
        # Check each card slot for availability (simplified version)
        # In a real implementation, you'd check for visual indicators of card readiness
        for i in range(4):  # 4 card slots
            # For now, assume all cards are available (you can enhance this with actual detection)
            # You could check pixel colors around card slots to determine availability
            available_cards.append(i)
        
        return available_cards
