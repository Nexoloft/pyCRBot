"""
Main EmulatorBot class
"""

import os
import time
import random
import cv2
from detection import ImageDetector
from battle_logic import BattleLogic
from emulator_utils import send_adb_command
from config import (
    CONFIDENCE_THRESHOLD, CARD_SELECTION_DELAY, CARD_COMBO_DELAY,
    FALLBACK_POSITIONS, SCREENSHOT_DELAY
)


class EmulatorBot:
    """Bot instance for a single emulator"""
    
    def __init__(self, device_id, instance_name):
        self.device_id = device_id
        self.instance_name = instance_name
        self.screenshots_dir = f"screenshots_{instance_name}"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.running = True
        
        # Initialize components
        self.detector = ImageDetector(instance_name)
        self.battle_logic = BattleLogic(instance_name, self.detector)
    
    def stop(self):
        """Stop this bot instance"""
        self.running = False
    
    def take_screenshot(self):
        """Take screenshot via ADB and load it into memory for this emulator instance"""
        try:
            screenshot_path = os.path.join(self.screenshots_dir, "screenshot.png")
            
            # Remove old screenshot file if it exists to ensure fresh capture
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            # Capture screenshot with specific device
            success, stdout, stderr = send_adb_command(self.device_id, "shell screencap /sdcard/screenshot.png")
            if not success:
                print(f"[{self.instance_name}] Failed to capture screenshot: {stderr}")
                return None
                
            # Small delay to ensure screenshot is ready on device
            time.sleep(SCREENSHOT_DELAY)
                
            # Download screenshot with specific device
            success, stdout, stderr = send_adb_command(self.device_id, f"pull /sdcard/screenshot.png {screenshot_path}")
            if not success:
                print(f"[{self.instance_name}] Failed to download screenshot: {stderr}")
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
        
        return self.detector.find_template(template_name, screenshot, confidence)
    
    def tap_screen(self, x, y):
        """Send a tap command to this emulator via ADB"""
        try:
            success, stdout, stderr = send_adb_command(self.device_id, f'shell input tap {x} {y}')
            if success:
                return True
            else:
                print(f"[{self.instance_name}] Failed to tap screen at ({x}, {y}): {stderr}")
                return False
        except Exception as e:
            print(f"[{self.instance_name}] Error tapping screen: {e}")
            return False
    
    def restart_app(self):
        """Restart Clash Royale app on this emulator instance"""
        try:
            print(f"[{self.instance_name}] Restarting Clash Royale app...")
            # Force stop the app
            send_adb_command(self.device_id, "shell am force-stop com.supercell.clashroyale")
            time.sleep(2)
            # Start the app
            send_adb_command(self.device_id, "shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp")
            print(f"[{self.instance_name}] App restarted, waiting for battle to start...")
            
            # Wait for battle detection with fallback mechanism after restart
            restart_time = time.time()
            fallback_triggered = False
            
            while time.time() - restart_time < 30:  # Max 30 seconds wait after restart
                if not self.running:
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
    
    def is_in_battle(self):
        """Check if we're in battle using multiple detection methods"""
        screenshot = self.take_screenshot()
        return self.battle_logic.is_in_battle(screenshot)
    
    def detect_elixir_amount(self):
        """Detect current elixir amount"""
        screenshot = self.take_screenshot()
        return self.battle_logic.detect_elixir_amount(screenshot)
    
    def detect_2x_elixir(self):
        """Detect if 2x elixir mode is active"""
        screenshot = self.take_screenshot()
        return self.battle_logic.detect_2x_elixir(screenshot)
    
    def find_post_battle_button(self):
        """Find and return coordinates for post-battle exit/OK button"""
        screenshot = self.take_screenshot()
        return self.battle_logic.find_post_battle_button(screenshot)
    
    def wait_for_elixir(self, target_elixir=4, timeout=40):
        """Wait for a specific amount of elixir"""
        return self.battle_logic.wait_for_elixir(
            target_elixir, 
            timeout, 
            self.take_screenshot,
            lambda screenshot: self.battle_logic.is_in_battle(screenshot),
            lambda: not self.running
        )
    
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
        
        # Select a random card
        card_pos = self.battle_logic.select_random_card()
        
        if not self.tap_screen(card_pos[0], card_pos[1]):
            return False
        
        time.sleep(CARD_SELECTION_DELAY)
        
        # Generate strategic position
        place_x, place_y = self.battle_logic.generate_play_position()
        
        if not self.tap_screen(place_x, place_y):
            return False
        
        print(f"[{self.instance_name}] Played card at ({place_x}, {place_y})")
        return True
    
    def play_double_card_combo(self):
        """Wait for 8 elixir and place two cards with improved timing"""
        # First check if we're still in battle
        if not self.is_in_battle():
            return False
        
        # Wait for 8 elixir with proper timeout
        print(f"[{self.instance_name}] Waiting for 8 elixir to play double card combo...")
        if not self.wait_for_elixir(target_elixir=8, timeout=30):
            print(f"[{self.instance_name}] Failed to get 8 elixir for combo")
            return False
        
        # Generate strategic position for both cards
        place_x, place_y = self.battle_logic.generate_play_position()
        
        print(f"[{self.instance_name}] Playing combo at ({place_x}, {place_y})")
        
        # Play first card
        card1_pos = self.battle_logic.select_random_card()
        if not self.tap_screen(card1_pos[0], card1_pos[1]):
            return False
        
        time.sleep(CARD_SELECTION_DELAY)
        
        if not self.tap_screen(place_x, place_y):
            return False
        
        time.sleep(CARD_COMBO_DELAY)
        
        # Play second card from a DIFFERENT slot
        card2_pos = self.battle_logic.select_random_card(exclude_slot=card1_pos)
        if not self.tap_screen(card2_pos[0], card2_pos[1]):
            return False
        
        time.sleep(CARD_SELECTION_DELAY)
        
        if not self.tap_screen(place_x, place_y):
            return False
        
        print(f"[{self.instance_name}] Double card combo played successfully!")
        return True
    
    def fallback_click_sequence(self):
        """Click at fallback position ten times with 3-second intervals, then check for battle"""
        print(f"[{self.instance_name}] Performing fallback click sequence...")
        fallback_pos = FALLBACK_POSITIONS["fallback_click"]
        
        for i in range(10):
            if not self.running:
                return False
            
            print(f"[{self.instance_name}] Fallback click {i+1}/10")
            self.tap_screen(fallback_pos[0], fallback_pos[1])
            
            # Check if battle started during the click sequence
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle detected during fallback click {i+1}!")
                return True
            
            if i < 9:  # Don't wait after the last click
                time.sleep(3)
                
                # Check again after the wait
                if self.is_in_battle():
                    print(f"[{self.instance_name}] ✓ Battle detected after fallback click {i+1} wait!")
                    return True
        
        # After completing fallback clicks, wait and check for battle
        print(f"[{self.instance_name}] Fallback clicks completed, checking for battle...")
        fallback_check_start = time.time()
        
        while time.time() - fallback_check_start < 10:  # Check for 10 seconds after fallback
            if not self.running:
                return False
                
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle detected after fallback clicks!")
                return True
            
            time.sleep(1)
        
        print(f"[{self.instance_name}] No battle detected after fallback clicks")
        return False
    
    def wait_for_battle_start(self, use_fallback=True):
        """Wait for battle to start with improved detection and fallback mechanisms"""
        print(f"[{self.instance_name}] Waiting for battle to start...")
        start_time = time.time()
        fallback_triggered = False
        
        while time.time() - start_time < 30:  # Max 30 seconds wait
            if not self.running:
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
                    deadspace_pos = FALLBACK_POSITIONS["deadspace"]
                    self.tap_screen(deadspace_pos[0], deadspace_pos[1])  # Deadspace click to handle UI
            
            print(f"[{self.instance_name}] Battle not detected yet, waiting... ({elapsed:.1f}s)")
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout waiting for battle to start")
        return False
    
    def start_first_battle(self):
        """Click battle button to start the first battle from home page"""
        print(f"[{self.instance_name}] Looking for Battle button to start first battle...")
        
        # Look for battle button for up to 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            if not self.running:
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
    
    def wait_for_battle_end(self):
        """Wait until battle end screen is detected with multiple fallback methods"""
        print(f"[{self.instance_name}] Waiting for battle to end...")
        start_time = time.time()
        
        while time.time() - start_time < 120:  # Max 2 minutes wait
            if not self.running:
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
            ok_fallback = FALLBACK_POSITIONS["ok_button"]
            self.tap_screen(ok_fallback[0], ok_fallback[1])
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
        battle_fallback = FALLBACK_POSITIONS["battle_button"]
        self.tap_screen(battle_fallback[0], battle_fallback[1])
        return False
    
    def auto_upgrade_cards(self):
        """Automatically upgrade cards using template matching"""
        print(f"[{self.instance_name}] Starting automatic card upgrade sequence...")
        
        upgrade_count = 0
        
        while self.running:
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
                    print(f"[{self.instance_name}] Confirm button not found, continuing...")
                
                # Click at card scroll position until upgrade_possible.png is detected again
                print(f"[{self.instance_name}] Clicking to scroll until next upgrade is found...")
                click_attempts = 0
                max_click_attempts = 30  # Prevent infinite clicking
                scroll_pos = FALLBACK_POSITIONS["card_scroll"]
                
                while click_attempts < max_click_attempts and self.running:
                    self.tap_screen(scroll_pos[0], scroll_pos[1])
                    click_attempts += 1
                    
                    # Check if upgrade_possible is detected again
                    next_upgrade_pos, next_confidence = self.find_template("upgrade_possible")
                    if next_upgrade_pos:
                        print(f"[{self.instance_name}] Found next upgrade after {click_attempts} clicks")
                        break
                
                if click_attempts >= max_click_attempts:
                    print(f"[{self.instance_name}] Reached maximum click attempts at scroll position")
                
            else:
                print(f"[{self.instance_name}] No more upgrades available (upgrade_possible.png not found)")
                print(f"[{self.instance_name}] Total upgrades completed: {upgrade_count}")
                break
        
        print(f"[{self.instance_name}] Auto upgrade sequence finished. Total upgrades: {upgrade_count}")
    
    def debug_current_screen(self):
        """Debug method to check what templates are currently visible"""
        screenshot = self.take_screenshot()
        if screenshot:
            self.detector.debug_current_screen(screenshot, self.find_template)
            
            # Check if we're in battle
            in_battle = self.battle_logic.is_in_battle(screenshot)
            print(f"[{self.instance_name}] DEBUG: In battle: {in_battle}")
            
            # Check post-battle button
            post_battle_button = self.battle_logic.find_post_battle_button(screenshot)
            if post_battle_button:
                print(f"[{self.instance_name}] DEBUG: Post-battle button found at: {post_battle_button}")
            else:
                print(f"[{self.instance_name}] DEBUG: No post-battle button found")
