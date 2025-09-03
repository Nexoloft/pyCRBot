import random
import time
import subprocess
import cv2
import os
import sys
from concurrent.futures import ThreadPoolExecutor
import signal

# MEmu emulator default ports (can be configured)
MEMU_PORTS = [21503, 21513, 21521, 21523, 21531, 21533, 21541, 21543, 21551, 21553]  # Supports up to 10 MEmu instances

# Card coordinates
CARD_SLOTS = [
    (141, 537),   # Card 1
    (209, 537),   # Card 2
    (277, 537),   # Card 3
    (342, 537)    # Card 4
]

# Play area coordinates
PLAY_AREA = {
    "min_x": 57,
    "max_x": 360,
    "min_y": 416,
    "max_y": 472
}

# Bridge y-range (centered around reported bridge Y = 287). Adjust band if placement off.
# Smaller Y = higher on screen. PLAY_AREA currently covers only backline (416-472), so this extends forward.
BRIDGE_Y_RANGE = (279, 295)

# Reference images
REF_IMAGES = {
    "ok_button": "templates/OK.png",
    "battle_button": "templates/Battle.png",
    "in_battle": "templates/InBattle.png",
    "play_again": "templates/PlayAgain.png",
    "upgrade_possible": "templates/upgrade_possible.png",
    "upgrade_button": "templates/upgrade_button.png",
    "confirm": "templates/Confirm.png",
    "2xElixir": "templates/2xElixir.png"
}

# Confidence threshold for image matching
CONFIDENCE_THRESHOLD = 0.8

# Timeout for inactivity (30 seconds)
INACTIVITY_TIMEOUT = 30

# Global variable to handle graceful shutdown
shutdown_requested = False

class EmulatorBot:
    """Bot instance for a single emulator"""
    def __init__(self, device_id, instance_name):
        self.device_id = device_id
        self.instance_name = instance_name
        self.screenshots_dir = f"screenshots_{instance_name}"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.running = True

    def restart_app(self):
        """Restart Clash Royale app on this emulator instance"""
        try:
            print(f"[{self.instance_name}] Restarting Clash Royale app...")
            # Force stop the app
            subprocess.run(f"adb -s {self.device_id} shell am force-stop com.supercell.clashroyale", shell=True, capture_output=True)
            time.sleep(2)
            # Start the app
            subprocess.run(f"adb -s {self.device_id} shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp", shell=True, capture_output=True)
            print(f"[{self.instance_name}] App restarted, waiting for battle to start...")
            
            # Wait for battle detection with fallback mechanism after restart
            restart_time = time.time()
            fallback_triggered = False
            
            while time.time() - restart_time < 30:  # Max 30 seconds wait after restart
                if shutdown_requested or not self.running:
                    return False
                    
                if self.is_in_battle():
                    print(f"[{self.instance_name}] ✓ Battle detected after app restart!")
                    return True
                
                # Check if 10 seconds have passed and we haven't triggered fallback yet
                if time.time() - restart_time >= 10 and not fallback_triggered:
                    print(f"[{self.instance_name}] No battle detected 10 seconds after restart, trying fallback clicks...")
                    if self.fallback_click_sequence():
                        return True  # Battle found after fallback
                    fallback_triggered = True
                
                time.sleep(1)
            
            return True
        except Exception as e:
            print(f"[{self.instance_name}] Error restarting app: {e}")
            return False

    def take_screenshot(self):
        """Take screenshot via ADB and load it into memory for this emulator instance"""
        try:
            screenshot_path = os.path.join(self.screenshots_dir, "screenshot.png")
            
            # Remove old screenshot file if it exists to ensure fresh capture
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            # Capture screenshot with specific device
            result = subprocess.run(f"adb -s {self.device_id} shell screencap /sdcard/screenshot.png", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[{self.instance_name}] Failed to capture screenshot: {result.stderr}")
                return None
                
            # Small delay to ensure screenshot is ready on device
            time.sleep(0.05)
                
            # Download screenshot with specific device
            result = subprocess.run(f"adb -s {self.device_id} pull /sdcard/screenshot.png {screenshot_path}", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[{self.instance_name}] Failed to download screenshot: {result.stderr}")
                return None
                
            # Load image
            if not os.path.exists(screenshot_path):
                print(f"[{self.instance_name}] Screenshot file not found after download")
                return None
                
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                print(f"[{self.instance_name}] Failed to load screenshot image")
                return None
                
            return screenshot
        except Exception as e:
            print(f"[{self.instance_name}] Error taking screenshot: {e}")
            return None

    def find_template(self, template_name, screenshot=None, confidence=CONFIDENCE_THRESHOLD):
        """Find a template image within a screenshot"""
        if screenshot is None:
            screenshot = self.take_screenshot()
            if screenshot is None:
                return None, None
        
        # Load template image
        template_path = REF_IMAGES[template_name]
        if not os.path.exists(template_path):
            print(f"[{self.instance_name}] Template image not found: {template_path}")
            return None, None
            
        template = cv2.imread(template_path)
        if template is None:
            print(f"[{self.instance_name}] Failed to load template: {template_path}")
            return None, None
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Check if match is above confidence threshold
        if max_val >= confidence:
            # Calculate center of matched area
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y), max_val
        else:
            return None, max_val

    def tap_screen(self, x, y):
        """Send a tap command to this emulator via ADB"""
        try:
            result = subprocess.run(f'adb -s {self.device_id} shell input tap {x} {y}', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"[{self.instance_name}] Failed to tap screen at ({x}, {y}): {result.stderr}")
                return False
        except Exception as e:
            print(f"[{self.instance_name}] Error tapping screen: {e}")
            return False

    def play_card(self, check_elixir=False):
        """Select and place a random card with improved logic"""
        # First check if we're still in battle
        if not self.is_in_battle():
            return False
        
        # Optionally check elixir before playing
        if check_elixir:
            current_elixir = self.detect_elixir_amount()
            if current_elixir is not None:
                print(f"[{self.instance_name}] Elixir before playing card: {current_elixir}")
                # Don't play if we have very low elixir
                if current_elixir < 3:
                    print(f"[{self.instance_name}] Too low elixir ({current_elixir}), waiting...")
                    return False
        
        # Select a random card with some variety
        card_pos = random.choice(CARD_SLOTS)

        if not self.tap_screen(card_pos[0], card_pos[1]):
            return False

        time.sleep(0.15)  # Slightly longer wait for card selection

        # Generate placement (centralized logic)
        place_x, place_y, placement_type = self._generate_play_position()

        if not self.tap_screen(place_x, place_y):
            return False

        print(f"[{self.instance_name}] Played card at ({place_x}, {place_y}) [{placement_type}]")
        return True

    def play_double_card_combo(self, wait_for_elixir_first=True):
        """Place two cards quickly. Optionally wait for elixir if not already >=8."""
        # First check if we're still in battle
        if not self.is_in_battle():
            return False

        if wait_for_elixir_first:
            print(f"[{self.instance_name}] Waiting for 8 elixir to play double card combo...")
            if not self.wait_for_elixir(target_elixir=8, timeout=30):
                print(f"[{self.instance_name}] Failed to get 8 elixir for combo")
                return False

        # Generate a single strategic position for both cards (favor bridge)
        if random.randint(0, 1) == 0:
            place_x = random.choice([120, 300])
            place_y = random.randint(*BRIDGE_Y_RANGE)
            placement_type = "bridge"
        else:
            place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
            place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
            placement_type = "backline"

        print(f"[{self.instance_name}] Playing combo at ({place_x}, {place_y}) [{placement_type}]")

        # Play first card
        card1_pos = random.choice(CARD_SLOTS)
        if not self.tap_screen(card1_pos[0], card1_pos[1]):
            return False

        time.sleep(0.15)

        if not self.tap_screen(place_x, place_y):
            return False

        time.sleep(0.4)  # Proper delay between cards

        # Play second card from a DIFFERENT slot
        available_card_slots = [slot for slot in CARD_SLOTS if slot != card1_pos]
        card2_pos = random.choice(available_card_slots)
        if not self.tap_screen(card2_pos[0], card2_pos[1]):
            return False

        time.sleep(0.15)

        if not self.tap_screen(place_x, place_y):
            return False

        print(f"[{self.instance_name}] Double card combo played successfully!")
        return True

    def _generate_play_position(self):
        """Centralized generation of a strategic placement.
        Returns (x, y, placement_type)."""
        # 40% chance bridge, else random backline within PLAY_AREA.
        if random.random() < 0.4:
            place_x = random.choice([120, 300])
            place_y = random.randint(*BRIDGE_Y_RANGE)
            return place_x, place_y, "bridge"
        else:
            place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
            place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
            return place_x, place_y, "backline"

    def _should_play_combo(self, battle_phase, is_2x_elixir):
        """Probabilistic decision for attempting a combo outside deterministic 2x path."""
        if is_2x_elixir:
            return True  # already handled deterministically when elixir >=8
        if battle_phase == "late":
            return random.random() < 0.25  # 25%
        if battle_phase == "mid":
            return random.random() < 0.15  # 15%
        return random.random() < 0.10  # early 10%

    def debug_current_screen(self):
        """Debug method to check what templates are currently visible"""
        print(f"[{self.instance_name}] DEBUG: Checking current screen for templates...")
        
        # Check all our key templates
        templates_to_check = ["play_again", "ok_button", "battle_button", "in_battle", "confirm"]
        
        for template_name in templates_to_check:
            position, confidence = self.find_template(template_name)
            if position:
                print(f"[{self.instance_name}] DEBUG: Found {template_name} at {position} (confidence: {confidence:.2f})")
            else:
                if confidence is not None:
                    print(f"[{self.instance_name}] DEBUG: {template_name} not found (best confidence: {confidence:.2f})")
                else:
                    print(f"[{self.instance_name}] DEBUG: {template_name} not found (no confidence)")
        
        # Check if we're in battle
        in_battle = self.is_in_battle()
        print(f"[{self.instance_name}] DEBUG: In battle: {in_battle}")
        
        # Check post-battle button
        post_battle_button = self.find_post_battle_button()
        if post_battle_button:
            print(f"[{self.instance_name}] DEBUG: Post-battle button found at: {post_battle_button}")
        else:
            print(f"[{self.instance_name}] DEBUG: No post-battle button found")

    def find_post_battle_button(self):
        """Find and return coordinates for post-battle exit/OK button using multiple methods"""
        screenshot = self.take_screenshot()
        if screenshot is None:
            return None
            
        # Method 1: Template detection for PlayAgain button (highest priority)
        play_again_position, play_again_confidence = self.find_template("play_again")
        if play_again_position and play_again_confidence is not None and play_again_confidence > 0.7:
            print(f"[{self.instance_name}] Post-battle PlayAgain button found (template confidence: {play_again_confidence:.2f})")
            return play_again_position
            
        # Method 2: Template detection for OK button
        ok_position, ok_confidence = self.find_template("ok_button")
        if ok_position and ok_confidence is not None and ok_confidence > 0.7:
            print(f"[{self.instance_name}] Post-battle OK button found (template confidence: {ok_confidence:.2f})")
            return ok_position
            
        # Method 3: Fast pixel-based detection (from PyClashBot)
        try:
            pixels = [
                screenshot[178][545],
                screenshot[239][547], 
                screenshot[214][553],
                screenshot[201][554],
            ]
            colors = [
                [255, 187, 104],
                [255, 187, 104],
                [255, 255, 255],
                [255, 255, 255],
            ]
            
            if self._all_pixels_match(pixels, colors, tolerance=25):
                print(f"[{self.instance_name}] Post-battle button found (pixel detection)")
                return (200, 550)
        except (IndexError, TypeError):
            pass
            
        # Method 4: Look for other common post-battle UI elements
        # Check for "Confirm" button which sometimes appears
        confirm_position, confirm_confidence = self.find_template("confirm")
        if confirm_position and confirm_confidence is not None and confirm_confidence > 0.7:
            print(f"[{self.instance_name}] Post-battle Confirm button found (template confidence: {confirm_confidence:.2f})")
            return confirm_position
            
        return None

    def wait_for_battle_end(self):
        """Wait until battle end screen is detected with multiple fallback methods"""
        print(f"[{self.instance_name}] Waiting for battle to end...")
        start_time = time.time()
        
        while time.time() - start_time < 120:  # Max 2 minutes wait
            if shutdown_requested or not self.running:
                return False
            
            # First priority: Look for post-battle button (most reliable)
            button_position = self.find_post_battle_button()
            if button_position:
                print(f"[{self.instance_name}] Battle end detected, clicking post-battle button at {button_position}...")
                self.tap_screen(button_position[0], button_position[1])
                time.sleep(3)  # Wait for click to register and transition
                return True
            
            # Second priority: Check if we're no longer in battle
            if not self.is_in_battle():
                print(f"[{self.instance_name}] Battle ended - no longer in battle, waiting for post-battle screen...")
                # Wait for post-battle screen to appear
                for wait_attempt in range(5):  # Wait up to 5 seconds
                    time.sleep(1)
                    button_position = self.find_post_battle_button()
                    if button_position:
                        print(f"[{self.instance_name}] Found post-battle button after waiting, clicking it...")
                        self.tap_screen(button_position[0], button_position[1])
                        time.sleep(3)
                        return True
                
                # If no button found after waiting, try template-specific detection
                play_again_position, _ = self.find_template("play_again")
                if play_again_position:
                    print(f"[{self.instance_name}] Found PlayAgain button, clicking it...")
                    self.tap_screen(play_again_position[0], play_again_position[1])
                    time.sleep(3)
                    return True
                    
                ok_position, _ = self.find_template("ok_button")
                if ok_position:
                    print(f"[{self.instance_name}] Found OK button, clicking it...")
                    self.tap_screen(ok_position[0], ok_position[1])
                    time.sleep(3)
                    return True
                
                print(f"[{self.instance_name}] Battle ended but no post-battle button found")
                return True  # Battle ended even if no button was found
            
            # Wait before checking again
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout waiting for battle to end")
        return False

    def handle_post_battle(self):
        """Handle the post-battle sequence with multiple fallback methods"""
        print(f"[{self.instance_name}] Handling post-battle sequence...")
        
        # First, ensure we're not still in battle
        for _ in range(5):  # Try up to 5 times
            if not self.is_in_battle():
                break
            time.sleep(1)
        
        # Look for and click post-battle button
        button_position = self.find_post_battle_button()
        if button_position:
            print(f"[{self.instance_name}] Clicking post-battle button...")
            self.tap_screen(button_position[0], button_position[1])
            time.sleep(2)
        else:
            # Fallback: click common OK button position
            print(f"[{self.instance_name}] No post-battle button found, trying fallback position")
            self.tap_screen(540, 1100)  # Fallback OK position
            time.sleep(2)
        
        # Wait for transition and look for Battle button
        time.sleep(1)
        
        # Try to find and click Battle button
        for attempt in range(3):  # Try up to 3 times
            battle_position, battle_confidence = self.find_template("battle_button")
            if battle_position:
                print(f"[{self.instance_name}] Clicking Battle button (confidence: {battle_confidence:.2f})")
                self.tap_screen(battle_position[0], battle_position[1])
                return True
            
            if attempt < 2:  # Don't wait after last attempt
                print(f"[{self.instance_name}] Battle button not found, waiting... (attempt {attempt + 1}/3)")
                time.sleep(2)
        
        # Final fallback: click approximate battle button position
        print(f"[{self.instance_name}] Battle button not found, trying fallback position")
        self.tap_screen(540, 1200)  # Battle button approximate position
        return False

    def start_first_battle(self):
        """Click battle button to start the first battle from home page"""
        print(f"[{self.instance_name}] Looking for Battle button to start first battle...")
        
        # Look for battle button for up to 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            if shutdown_requested or not self.running:
                return False
                
            battle_position, confidence = self.find_template("battle_button")
            if battle_position:
                print(f"[{self.instance_name}] Found Battle button (confidence: {confidence:.2f}), clicking to start battle...")
                self.tap_screen(battle_position[0], battle_position[1])
                return True
            
            print(f"[{self.instance_name}] Battle button not found, waiting...")
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout: Could not find Battle button on home page")
        return False

    def check_pixel_color(self, x, y, expected_color=(255, 255, 255), tolerance=30):
        """Check if pixel at (x, y) matches expected color within tolerance"""
        screenshot = self.take_screenshot()
        if screenshot is None:
            return False
        
        # Get screenshot dimensions
        height, width = screenshot.shape[:2]
        
        # Check if coordinates are within bounds
        if y >= height or x >= width:
            print(f"[{self.instance_name}] Pixel coordinates ({x}, {y}) out of bounds for screenshot size ({width}x{height})")
            return False
        
        # Get pixel color (BGR format in OpenCV)
        pixel_bgr = screenshot[y, x]
        pixel_rgb = (int(pixel_bgr[2]), int(pixel_bgr[1]), int(pixel_bgr[0]))  # Convert BGR to RGB as integers
        
        # Check if pixel is within tolerance of expected color
        for i in range(3):
            diff = abs(pixel_rgb[i] - expected_color[i])
            if diff > tolerance:
                return False
        
        return True

    def detect_2x_elixir(self):
        """Detect if 2x elixir mode is active using template matching"""
        position, confidence = self.find_template("2xElixir")
        if position:
            print(f"[{self.instance_name}] 2x Elixir detected! (confidence: {confidence:.2f})")
            return True
        return False

    def detect_elixir_amount(self):
        """Detect current elixir amount using multiple detection methods"""
        screenshot = self.take_screenshot()
        if screenshot is None:
            return None
        
        # Method 1: Template-based detection (more reliable)
        elixir_coords = [
            [149, 613],  # 1 elixir
            [175, 613],  # 2 elixir  
            [200, 613],  # 3 elixir
            [223, 613],  # 4 elixir
            [249, 613],  # 5 elixir
            [274, 613],  # 6 elixir
            [299, 613],  # 7 elixir
            [323, 613],  # 8 elixir
            [347, 613],  # 9 elixir
            [371, 613],  # 10 elixir
        ]
        
        # Purple color for elixir (more precise detection)
        purple_colors = [
            [240, 137, 244],  # Primary purple
            [232, 63, 242],   # Alternative purple (from PyClashBot)
            [231, 57, 242],   # Another variant
        ]
        
        # Check from highest elixir to lowest to find the maximum
        for elixir_level in range(10, 0, -1):
            x_position, y_position = elixir_coords[elixir_level - 1]
            
            # Check if pixel at this position matches any purple variant
            try:
                pixel = screenshot[y_position, x_position]
                pixel_bgr = [int(pixel[0]), int(pixel[1]), int(pixel[2])]
                pixel_rgb = [pixel_bgr[2], pixel_bgr[1], pixel_bgr[0]]  # Convert BGR to RGB
                
                for purple_color in purple_colors:
                    if self._pixel_matches_color_rgb(pixel_rgb, purple_color, tolerance=35):
                        print(f"[{self.instance_name}] Elixir detected: {elixir_level} (purple pixel at {x_position}, {y_position})")
                        return elixir_level
                        
            except (IndexError, TypeError):
                continue
        
        # If no purple pixels found, elixir is 0
        print(f"[{self.instance_name}] Elixir detected: 0 (no purple pixels found)")
        return 0
        
    def _pixel_matches_color_rgb(self, pixel_rgb, expected_color, tolerance=25):
        """Check if a pixel (in RGB format) matches an expected color within tolerance"""
        try:
            for i in range(3):
                if abs(pixel_rgb[i] - expected_color[i]) > tolerance:
                    return False
            return True
        except (IndexError, TypeError):
            return False

    def count_elixir(self, target_elixir):
        """Check if we have at least the target amount of elixir"""
        current_elixir = self.detect_elixir_amount()
        if current_elixir is None:
            return False
        return current_elixir >= target_elixir

    def wait_for_elixir(self, target_elixir=4, timeout=40):
        """Wait for a specific amount of elixir with improved logic"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if shutdown_requested or not self.running:
                return False
                
            # Check if we're still in battle
            if not self.is_in_battle():
                print(f"[{self.instance_name}] Not in battle anymore while waiting for elixir")
                return False
                
            # Check current elixir
            current_elixir = self.detect_elixir_amount()
            if current_elixir is not None:
                if current_elixir >= target_elixir:
                    print(f"[{self.instance_name}] Have {current_elixir} elixir (needed {target_elixir})")
                    return True
                    
            time.sleep(0.5)  # Check twice per second
            
        print(f"[{self.instance_name}] Timeout waiting for {target_elixir} elixir")
        return False

    def is_in_battle(self):
        """Check if we're in battle using multiple detection methods"""
        # Method 1: Template detection (existing)
        position, confidence = self.find_template("in_battle")
        if position:
            print(f"[{self.instance_name}] In battle detected (template confidence: {confidence:.2f})")
            return True
            
        # Method 2: Pixel-based detection (from PyClashBot)
        screenshot = self.take_screenshot()
        if screenshot is None:
            return False
            
        # Check multiple specific pixels that appear during battle (1v1 and 2v2)
        try:
            # 1v1 battle pixels (white pixels in battle UI)
            pixels_1v1 = [
                screenshot[49][515],   # Battle UI elements
                screenshot[77][518],
                screenshot[52][530],
                screenshot[77][530],
                screenshot[115][618],  # Purple elixir area
            ]
            
            # 2v2 battle pixels 
            pixels_2v2 = [
                screenshot[53][515],
                screenshot[80][518], 
                screenshot[52][531],
                screenshot[76][514],
                screenshot[114][615],
            ]
            
            colors_1v1 = [
                [255, 255, 255],
                [255, 255, 255], 
                [255, 255, 255],
                [255, 255, 255],
                [232, 63, 242],
            ]
            
            colors_2v2 = [
                [255, 255, 255],
                [255, 255, 255],
                [255, 255, 255], 
                [255, 255, 255],
                [231, 57, 242],
            ]
            
            # Check if all pixels match for 1v1 battle
            if self._all_pixels_match(pixels_1v1, colors_1v1, tolerance=35):
                print(f"[{self.instance_name}] In 1v1 battle detected (pixel check)")
                return True
                
            # Check if all pixels match for 2v2 battle  
            if self._all_pixels_match(pixels_2v2, colors_2v2, tolerance=35):
                print(f"[{self.instance_name}] In 2v2 battle detected (pixel check)")
                return True
                
        except (IndexError, TypeError):
            # Fall back to template detection if pixel check fails
            pass
            
        return False
        
    def _all_pixels_match(self, pixels, colors, tolerance=25):
        """Helper method to check if all pixels match expected colors within tolerance"""
        if len(pixels) != len(colors):
            return False
            
        for pixel, expected_color in zip(pixels, colors):
            if not self._pixel_matches_color(pixel, expected_color, tolerance):
                return False
        return True
        
    def _pixel_matches_color(self, pixel, expected_color, tolerance=25):
        """Check if a pixel matches an expected color within tolerance"""
        try:
            # Convert BGR to RGB for comparison
            pixel_rgb = [int(pixel[2]), int(pixel[1]), int(pixel[0])]
            for i in range(3):
                if abs(pixel_rgb[i] - expected_color[i]) > tolerance:
                    return False
            return True
        except (IndexError, TypeError):
            return False

    def fallback_click_sequence(self):
        """Click at (96, 1316) fifteen times with 4-second intervals as fallback, then check for battle"""
        print(f"[{self.instance_name}] Performing enhanced fallback click sequence at (96, 1316)...")
        for i in range(15):
            if shutdown_requested or not self.running:
                return False
            
            print(f"[{self.instance_name}] Fallback click {i+1}/15")
            self.tap_screen(96, 1316)
            
            # Check if battle started during the click sequence
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle detected during fallback click {i+1}!")
                return True
            
            if i < 14:  # Don't wait after the last click
                time.sleep(4)
                
                # Check again after the wait
                if self.is_in_battle():
                    print(f"[{self.instance_name}] ✓ Battle detected after fallback click {i+1} wait!")
                    return True
        
        # After completing fallback clicks, wait and check for battle
        print(f"[{self.instance_name}] Fallback clicks completed, checking for battle...")
        fallback_check_start = time.time()
        
        while time.time() - fallback_check_start < 15:  # Check for 15 seconds after fallback
            if shutdown_requested or not self.running:
                return False
                
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle detected after fallback clicks!")
                return True
            
            time.sleep(1)
        
        print(f"[{self.instance_name}] No battle detected after enhanced fallback clicks")
        return False

    def auto_upgrade_cards(self):
        """Automatically upgrade cards using template matching"""
        print(f"[{self.instance_name}] Starting automatic card upgrade sequence...")
        
        upgrade_count = 0
        
        while self.running and not shutdown_requested:
            # Look for upgrade_possible.png
            upgrade_possible_pos, confidence = self.find_template("upgrade_possible")
            
            if upgrade_possible_pos:
                upgrade_count += 1
                print(f"[{self.instance_name}] Upgrade #{upgrade_count}: Found upgrade_possible (confidence: {confidence:.2f})")
                
                # Click upgrade_possible
                if not self.tap_screen(upgrade_possible_pos[0], upgrade_possible_pos[1]):
                    print(f"[{self.instance_name}] Failed to click upgrade_possible, continuing...")
                    continue
                
                # Wait 1 second then look for upgrade_button (first time)
                time.sleep(1)
                print(f"[{self.instance_name}] Looking for upgrade_button (first time)...")
                
                # Look for upgrade_button.png and click it (first time)
                upgrade_button_pos, button_confidence = self.find_template("upgrade_button")
                if upgrade_button_pos:
                    print(f"[{self.instance_name}] Found upgrade_button (confidence: {button_confidence:.2f}), clicking...")
                    self.tap_screen(upgrade_button_pos[0], upgrade_button_pos[1])
                    time.sleep(0.5)
                    
                    # Look for upgrade_button.png and click it (second time)
                    print(f"[{self.instance_name}] Looking for upgrade_button (second time)...")
                    upgrade_button_pos2, button_confidence2 = self.find_template("upgrade_button")
                    if upgrade_button_pos2:
                        print(f"[{self.instance_name}] Found upgrade_button again (confidence: {button_confidence2:.2f}), clicking...")
                        self.tap_screen(upgrade_button_pos2[0], upgrade_button_pos2[1])
                        time.sleep(1)
                else:
                    print(f"[{self.instance_name}] Upgrade button not found (first attempt), continuing...")
                    continue
                
                # Look for Confirm.png and click it
                confirm_pos, confirm_confidence = self.find_template("confirm")
                if confirm_pos:
                    print(f"[{self.instance_name}] Found Confirm button (confidence: {confirm_confidence:.2f}), clicking...")
                    self.tap_screen(confirm_pos[0], confirm_pos[1])
                    time.sleep(1)
                else:
                    print(f"[{self.instance_name}] Confirm button not found, continuing...")                # Click at (20, 254) until upgrade_possible.png is detected again
                print(f"[{self.instance_name}] Clicking at (20, 254) until next upgrade is found...")
                click_attempts = 0
                max_click_attempts = 30  # Prevent infinite clicking
                
                while click_attempts < max_click_attempts and self.running and not shutdown_requested:
                    self.tap_screen(20, 254)
                    click_attempts += 1
                    
                    # Check if upgrade_possible is detected again
                    next_upgrade_pos, next_confidence = self.find_template("upgrade_possible")
                    if next_upgrade_pos:
                        print(f"[{self.instance_name}] Found next upgrade after {click_attempts} clicks")
                        break
                
                if click_attempts >= max_click_attempts:
                    print(f"[{self.instance_name}] Reached maximum click attempts at (20, 254)")
                
            else:
                print(f"[{self.instance_name}] No more upgrades available (upgrade_possible.png not found)")
                print(f"[{self.instance_name}] Total upgrades completed: {upgrade_count}")
                break
        
        print(f"[{self.instance_name}] Auto upgrade sequence finished. Total upgrades: {upgrade_count}")

    def wait_for_battle_start(self, use_fallback=True):
        """Wait for battle to start with improved detection and fallback mechanisms"""
        print(f"[{self.instance_name}] Waiting for battle to start...")
        start_time = time.time()
        fallback_triggered = False
        
        while time.time() - start_time < 30:  # Max 30 seconds wait
            if shutdown_requested or not self.running:
                return False
                
            # Primary check: is in battle
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle started! Battle detected")
                time.sleep(1)  # Brief stabilization wait
                return True
            
            # Check if 10 seconds have passed without battle detection (only if fallback is enabled)
            elapsed = time.time() - start_time
            if use_fallback and elapsed >= 10 and not fallback_triggered:
                print(f"[{self.instance_name}] No battle detected after 10 seconds, trying fallback clicks...")
                if self.fallback_click_sequence():
                    return True  # Battle found after fallback
                fallback_triggered = True
            
            # Secondary check: Click deadspace to handle potential UI blocks (only if fallback is enabled)
            if use_fallback and elapsed >= 5:  # After 5 seconds, start clicking deadspace
                if random.randint(0, 2) == 0:  # 33% chance each cycle
                    self.tap_screen(20, 200)  # Deadspace click to handle UI
            
            print(f"[{self.instance_name}] Battle not detected yet, waiting... ({elapsed:.1f}s)")
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout waiting for battle to start")
        return False

    def run_bot_loop(self):
        """Main bot loop for this emulator instance"""
        print(f"[{self.instance_name}] Starting bot loop...")
        game_round = 1
        first_battle = True
        
        try:
            while self.running and not shutdown_requested:
                print(f"[{self.instance_name}] --- Starting round {game_round} ---")
                last_activity_time = time.time()
                
                # For the first battle, start from home page
                if first_battle:
                    if not self.start_first_battle():
                        print(f"[{self.instance_name}] Failed to start first battle from home page")
                        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                            print(f"[{self.instance_name}] No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                            self.restart_app()
                            last_activity_time = time.time()
                            continue
                        break
                    first_battle = False
                    last_activity_time = time.time()
                
                # Wait for battle to actually start (elixir bar appears)
                if not self.wait_for_battle_start(use_fallback=first_battle):
                    print(f"[{self.instance_name}] Battle didn't start properly, trying to recover...")
                    if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                        print(f"[{self.instance_name}] No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        self.restart_app()
                        last_activity_time = time.time()
                        first_battle = True
                        continue
                    # Try clicking battle button as fallback
                    self.tap_screen(540, 1200)  # Battle button approximate position
                    time.sleep(1)
                    continue
                
                last_activity_time = time.time()
                
                # Now use adaptive strategy during battle based on elixir mode with improved logic
                combos_played = 0
                single_cards_played = 0
                print(f"[{self.instance_name}] Starting adaptive battle strategy...")
                battle_start_time = time.time()
                last_elixir_check = time.time()
                last_2x_check = time.time()
                last_card_play = time.time()
                is_2x_elixir = False
                battle_phase = "early"  # early, mid, late
                
                while self.running and not shutdown_requested:
                    current_time = time.time()
                    battle_elapsed = current_time - battle_start_time
                    
                    # Update battle phase based on time
                    if battle_elapsed < 60:
                        battle_phase = "early"
                    elif battle_elapsed < 120:
                        battle_phase = "mid"
                    else:
                        battle_phase = "late"
                    
                    # Check for 2x elixir mode every 3 seconds
                    if current_time - last_2x_check >= 3:
                        is_2x_elixir = self.detect_2x_elixir()
                        last_2x_check = current_time
                    
                    # Check elixir amount every 2 seconds during battle
                    current_elixir = None
                    if current_time - last_elixir_check >= 2:
                        current_elixir = self.detect_elixir_amount()
                        if current_elixir is not None:
                            elixir_mode = "2x" if is_2x_elixir else "1x"
                            print(f"[{self.instance_name}] Current elixir: {current_elixir} ({elixir_mode} mode, {battle_phase} phase)")
                        last_elixir_check = current_time
                    
                    # Priority check: Look for post-battle buttons first (battle ended)
                    post_battle_button = self.find_post_battle_button()
                    if post_battle_button:
                        print(f"[{self.instance_name}] Battle ended! Post-battle button detected, clicking it...")
                        self.tap_screen(post_battle_button[0], post_battle_button[1])
                        last_activity_time = current_time
                        time.sleep(2)  # Wait for button click to register
                        break
                    
                    # Secondary check: Look for battle end by checking if we're still in battle
                    if not self.is_in_battle():
                        print(f"[{self.instance_name}] Battle ended - no longer in battle (no post-battle button found yet)")
                        # Wait a moment for post-battle screen to appear, then check again
                        time.sleep(2)
                        post_battle_button = self.find_post_battle_button()
                        if post_battle_button:
                            print(f"[{self.instance_name}] Found post-battle button after waiting, clicking it...")
                            self.tap_screen(post_battle_button[0], post_battle_button[1])
                            last_activity_time = current_time
                            time.sleep(2)
                        else:
                            print(f"[{self.instance_name}] No post-battle button found after waiting, debugging...")
                            self.debug_current_screen()
                        break
                    
                    # Check for inactivity timeout during battle
                    if current_time - battle_start_time > INACTIVITY_TIMEOUT:
                        print(f"[{self.instance_name}] Battle seems stuck for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        self.restart_app()
                        last_activity_time = current_time
                        first_battle = True
                        break
                    
                    # Card playing logic with improved timing
                    time_since_last_play = current_time - last_card_play
                    min_play_interval = 1.0 if is_2x_elixir else 1.5  # Faster plays in 2x elixir
                    
                    if time_since_last_play >= min_play_interval:
                        card_played = False

                        # Always refresh elixir if we haven't recently
                        if current_elixir is None:
                            current_elixir = self.detect_elixir_amount()

                        if is_2x_elixir:
                            # Deterministic attempt: play combo when >=8, else fallback single
                            if current_elixir is None:
                                print(f"[{self.instance_name}] Combo skipped: elixir read failed (2x mode)")
                            elif current_elixir >= 8:
                                if self.play_double_card_combo(wait_for_elixir_first=False):
                                    combos_played += 1
                                    print(f"[{self.instance_name}] Combo #{combos_played} (2x mode)")
                                    card_played = True
                                    last_card_play = current_time
                                    battle_start_time = current_time
                                else:
                                    print(f"[{self.instance_name}] Combo attempt failed to execute (2x mode)")
                            elif current_elixir >= 4:
                                if self.play_card(check_elixir=True):
                                    single_cards_played += 1
                                    print(f"[{self.instance_name}] Single card #{single_cards_played} (2x fallback)")
                                    card_played = True
                                    last_card_play = current_time
                                    battle_start_time = current_time
                            else:
                                print(f"[{self.instance_name}] Skip play: only {current_elixir} elixir (2x mode)")
                        else:
                            # Normal mode: probabilistic early combo attempts when >=8 elixir
                            if current_elixir is None:
                                print(f"[{self.instance_name}] Elixir read failed (normal mode)")
                            elif current_elixir >= 8 and self._should_play_combo(battle_phase, is_2x_elixir):
                                if self.play_double_card_combo(wait_for_elixir_first=False):
                                    combos_played += 1
                                    print(f"[{self.instance_name}] Combo #{combos_played} (normal mode, {battle_phase} phase)")
                                    card_played = True
                                    last_card_play = current_time
                                    battle_start_time = current_time
                                else:
                                    print(f"[{self.instance_name}] Combo attempt failed (normal mode)")
                            else:
                                # Single card logic
                                target_elixir = 4 if battle_phase != "late" else 3
                                if current_elixir is not None and current_elixir >= target_elixir:
                                    if self.play_card(check_elixir=True):
                                        single_cards_played += 1
                                        print(f"[{self.instance_name}] Single card #{single_cards_played} (normal {battle_phase})")
                                        card_played = True
                                        last_card_play = current_time
                                        battle_start_time = current_time
                                else:
                                    if current_elixir is not None:
                                        print(f"[{self.instance_name}] Waiting: {current_elixir} elixir (<{target_elixir}) normal {battle_phase}")

                        if not card_played:
                            time.sleep(0.5)  # Small delay before re-attempt
                    else:
                        # Wait before next play attempt
                        time.sleep(0.5)
                
                if shutdown_requested or not self.running:
                    break
                
                print(f"[{self.instance_name}] Finished battle - Combos: {combos_played}, Single cards: {single_cards_played}")
                
                # Wait for battle to end using improved detection
                if self.wait_for_battle_end():
                    print(f"[{self.instance_name}] Battle end detected, handling post-battle sequence...")
                    # Handle post-battle with image recognition
                    if self.handle_post_battle():
                        print(f"[{self.instance_name}] Successfully handled post-battle sequence")
                    else:
                        print(f"[{self.instance_name}] Failed to handle post-battle, trying fallback...")
                        # Fallback: click approximate positions
                        self.tap_screen(540, 1100)  # OK button approximate position
                        time.sleep(2)
                        self.tap_screen(540, 1200)  # Battle button approximate position
                else:
                    print(f"[{self.instance_name}] Failed to detect battle end properly, trying to recover...")
                    # Try clicking common positions as fallback
                    for attempt in range(3):
                        # Look for any post-battle button one more time
                        post_battle_button = self.find_post_battle_button()
                        if post_battle_button:
                            print(f"[{self.instance_name}] Found post-battle button in recovery, clicking it... (attempt {attempt + 1})")
                            self.tap_screen(post_battle_button[0], post_battle_button[1])
                            time.sleep(2)
                            break
                        else:
                            print(f"[{self.instance_name}] No post-battle button found in recovery attempt {attempt + 1}")
                            self.tap_screen(540, 1100)  # OK button approximate position
                            time.sleep(1)
                    
                    time.sleep(1)
                    self.tap_screen(540, 1200)  # Battle button approximate position
                
                # Wait for new game to start (no fallback sequence needed after Play Again)
                print(f"[{self.instance_name}] Waiting for next battle to start...")
                next_battle_start_time = time.time()
                
                while time.time() - next_battle_start_time < 30:  # Max 30 seconds wait for next battle
                    if shutdown_requested or not self.running:
                        break
                        
                    if self.is_in_battle():
                        print(f"[{self.instance_name}] ✓ Next battle started!")
                        break
                    
                    # Just wait - no fallback sequence needed after clicking Play Again
                    # The game should automatically start matchmaking
                    elapsed = time.time() - next_battle_start_time
                    print(f"[{self.instance_name}] Waiting for matchmaking... ({elapsed:.1f}s)")
                    time.sleep(2)
                
                # If we still haven't found a battle after 30 seconds, there might be an issue
                if not self.is_in_battle():
                    print(f"[{self.instance_name}] No battle found after 30 seconds, checking for UI issues...")
                    # Check if we're stuck on home screen and need to click Battle button
                    battle_position, _ = self.find_template("battle_button")
                    if battle_position:
                        print(f"[{self.instance_name}] Found Battle button, clicking it...")
                        self.tap_screen(battle_position[0], battle_position[1])
                    else:
                        print(f"[{self.instance_name}] No Battle button found, continuing to next round...")
                
                game_round += 1
                
        except Exception as e:
            print(f"[{self.instance_name}] Bot loop error: {e}")
        finally:
            print(f"[{self.instance_name}] Bot loop stopped")

    def stop(self):
        """Stop this bot instance"""
        self.running = False


def detect_memu_instances():
    """Detect running MEmu instances and return their device IDs"""
    try:
        # First check if ADB is available
        result = subprocess.run("adb version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: ADB (Android Debug Bridge) is not installed or not in PATH!")
            print("Please install ADB and add it to your system PATH.")
            print("You can download ADB from: https://developer.android.com/studio/releases/platform-tools")
            return []
        
        available_instances = []
        
        # First, get all currently connected devices
        print("Getting list of all connected ADB devices...")
        devices_result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
        if devices_result.returncode != 0:
            print("Failed to get ADB devices list")
            return []
        
        # Parse connected devices
        connected_devices = []
        for line in devices_result.stdout.split('\n'):
            if '\tdevice' in line:  # Only devices that are properly connected
                device_id = line.split('\t')[0]
                connected_devices.append(device_id)
        
        print(f"Found {len(connected_devices)} connected ADB device(s)")
        
        # Test each connected device to see if it's responsive
        instance_counter = 1
        for device_id in connected_devices:
            print(f"Testing device: {device_id}...")
            
            # Verify the device is actually responsive
            test_result = subprocess.run(f"adb -s {device_id} shell echo test", shell=True, capture_output=True, text=True, timeout=5)
            if test_result.returncode == 0 and "test" in test_result.stdout:
                instance_name = f"MEmu_{instance_counter}"
                available_instances.append((device_id, instance_name))
                print(f"✓ Found responsive device: {instance_name} ({device_id})")
                instance_counter += 1
            else:
                print(f"✗ Device {device_id} not responsive or not an emulator")
        
        # If no devices found via adb devices, try connecting to common MEmu ports
        if not available_instances:
            print("No responsive devices found via 'adb devices', trying to connect to common MEmu ports...")
            
            # Check each potential MEmu port
            for i, port in enumerate(MEMU_PORTS):
                device_id = f"127.0.0.1:{port}"
                print(f"Checking for MEmu instance on port {port}...")
                
                # Try to connect to this port
                result = subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    # Verify the device is actually responsive
                    test_result = subprocess.run(f"adb -s {device_id} shell echo test", shell=True, capture_output=True, text=True, timeout=5)
                    if test_result.returncode == 0 and "test" in test_result.stdout:
                        instance_name = f"MEmu_{len(available_instances)+1}"
                        available_instances.append((device_id, instance_name))
                        print(f"✓ Found responsive MEmu instance: {instance_name} ({device_id})")
                    else:
                        print(f"✗ MEmu instance on port {port} not responsive")
                else:
                    print(f"✗ No MEmu instance found on port {port}")
        
        return available_instances
        
    except Exception as e:
        print(f"Error detecting MEmu instances: {e}")
        return []


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\nShutdown signal received. Stopping all bots...")
    shutdown_requested = True


def main():
    """Main function to coordinate multiple emulator bots"""
    global shutdown_requested
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Multi-MEmu Clash Royale Bot")
    print("=" * 40)
    
    # Check for upgrade mode argument
    upgrade_mode = "--upgrade" in sys.argv or "-u" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage:")
        print("  python ClashBot.py              # Run normal battle bot")
        print("  python ClashBot.py --upgrade    # Run card upgrade bot")
        print("  python ClashBot.py -u           # Run card upgrade bot (short)")
        print("  python ClashBot.py --help       # Show this help")
        return
    
    # Verify template images exist
    missing_templates = []
    for name, path in REF_IMAGES.items():
        if not os.path.exists(path):
            missing_templates.append(f"{name}: {path}")
    
    if missing_templates:
        print("ERROR: Missing template images:")
        for template in missing_templates:
            print(f"  - {template}")
        print("\nPlease ensure all template images are in the correct location.")
        return
    
    # Detect available MEmu instances
    instances = detect_memu_instances()
    if not instances:
        print("No MEmu instances found. Please start MEmu and try again.")
        return
    
    if upgrade_mode:
        print(f"\n🔧 UPGRADE MODE: Will upgrade cards on {len(instances)} MEmu instance(s)")
        print("Starting card upgrade bots...")
        
        # Create bot instances for upgrading
        bots = []
        for device_id, instance_name in instances:
            bot = EmulatorBot(device_id, instance_name)
            bots.append(bot)
        
        # Start upgrade threads
        with ThreadPoolExecutor(max_workers=len(bots)) as executor:
            try:
                # Submit upgrade tasks
                futures = [executor.submit(bot.auto_upgrade_cards) for bot in bots]
                
                print(f"All {len(bots)} upgrade bots started! Press Ctrl+C to stop.")
                
                # Wait for completion or shutdown
                while not shutdown_requested:
                    time.sleep(1)
                    
                    # Check if all futures completed
                    completed = [f for f in futures if f.done()]
                    if len(completed) == len(futures):
                        print("All upgrade bots finished!")
                        break
                
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received")
            finally:
                # Stop all bots
                print("Stopping all upgrade bots...")
                for bot in bots:
                    bot.stop()
                
                # Wait for threads to finish
                print("Waiting for upgrade bots to finish...")
                executor.shutdown(wait=True)
                
                print("All upgrade bots stopped. Goodbye!")
        return
    
    print(f"\n⚔️ BATTLE MODE: Found {len(instances)} MEmu instance(s). Starting battle bots...")
    
    # Create bot instances
    bots = []
    for device_id, instance_name in instances:
        bot = EmulatorBot(device_id, instance_name)
        bots.append(bot)
    
    # Start bot threads
    with ThreadPoolExecutor(max_workers=len(bots)) as executor:
        try:
            # Submit bot tasks
            futures = [executor.submit(bot.run_bot_loop) for bot in bots]
            
            print(f"All {len(bots)} bots started! Press Ctrl+C to stop.")
            
            # Wait for completion or shutdown
            while not shutdown_requested:
                time.sleep(1)
                
                # Check if any futures completed (which shouldn't happen normally)
                completed = [f for f in futures if f.done()]
                if completed:
                    print(f"{len(completed)} bot(s) finished unexpectedly")
                    break
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            # Stop all bots
            print("Stopping all bots...")
            for bot in bots:
                bot.stop()
            
            # Wait for threads to finish
            print("Waiting for bots to finish...")
            executor.shutdown(wait=True)
            
            print("All bots stopped. Goodbye!")


if __name__ == "__main__":
    main()
