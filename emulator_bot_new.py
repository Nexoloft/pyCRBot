"""
Main EmulatorBot class - refactored with PyClashBot architecture
"""

import time
import random
from emulators import MemuController
from detection import ImageDetector
from battle_logic import BattleLogic
from battle_strategy import BattleStrategy
from logger import Logger
from config import (
    CONFIDENCE_THRESHOLD, CARD_SELECTION_DELAY, CARD_COMBO_DELAY,
    FALLBACK_POSITIONS, SCREENSHOT_DELAY, CLASH_ROYALE_PACKAGE, CARD_SLOTS
)


class EmulatorBot:
    """
    Refactored Bot instance for a single emulator using PyClashBot architecture
    """
    
    def __init__(self, device_id, instance_name):
        self.device_id = device_id
        self.instance_name = instance_name
        self.running = True
        
        # Initialize logger first
        self.logger = Logger(instance_name, timed=True)
        
        # Initialize emulator controller
        self.emulator = MemuController(device_id, instance_name)
        
        # Initialize components
        self.detector = ImageDetector(instance_name)
        self.battle_logic = BattleLogic(instance_name, self.detector)
        self.battle_strategy = BattleStrategy()
        
        self.logger.log("Bot initialized successfully")
    
    def stop(self):
        """Stop this bot instance"""
        self.running = False
        self.emulator.stop()
        self.logger.log("Bot stopped")
        self.logger.log_summary()
    
    def take_screenshot(self):
        """Take screenshot using emulator controller"""
        return self.emulator.screenshot()
    
    def tap_screen(self, x, y, clicks=1, interval=0.1):
        """Send a tap command using emulator controller"""
        return self.emulator.click(x, y, clicks, interval)
    
    def restart_app(self):
        """Restart Clash Royale app using emulator controller"""
        self.logger.change_status("Restarting Clash Royale app...")
        success = self.emulator.restart_app(CLASH_ROYALE_PACKAGE)
        if success:
            self.logger.add_restart()
            self.logger.log("App restarted successfully")
            
            # Wait for battle detection with fallback mechanism after restart
            restart_time = time.time()
            fallback_triggered = False
            
            while time.time() - restart_time < 30:  # Max 30 seconds wait after restart
                if not self.running:
                    return False
                    
                if self.is_in_battle():
                    self.logger.log("✓ Battle detected after app restart!")
                    return True
                
                # Check if 10 seconds have passed and we haven't triggered fallback yet
                if time.time() - restart_time >= 10 and not fallback_triggered:
                    self.logger.log("No battle detected 10 seconds after restart, trying fallback clicks...")
                    if self.fallback_click_sequence():
                        return True  # Battle found after fallback
                    fallback_triggered = True
                
                time.sleep(1)
        else:
            self.logger.add_failure()
            self.logger.log("Failed to restart app")
        return success
    
    def is_in_battle(self):
        """Check if we're in battle using battle logic"""
        screenshot = self.take_screenshot()
        if screenshot is None:
            return False
        return self.battle_logic.is_in_battle(screenshot)
    
    def find_template(self, template_name, screenshot=None, confidence=CONFIDENCE_THRESHOLD):
        """Find a template image within a screenshot"""
        if screenshot is None:
            screenshot = self.take_screenshot()
            if screenshot is None:
                return None, None
        return self.detector.find_template(template_name, screenshot, confidence)
    
    def wait_for_battle_start(self, use_fallback=True):
        """Wait for battle to start with improved detection and fallback mechanisms"""
        self.logger.change_status("Waiting for battle to start...")
        start_time = time.time()
        fallback_triggered = False
        
        while time.time() - start_time < 30:  # Max 30 seconds wait
            if not self.running:
                return False
                
            # Primary check: is in battle
            if self.is_in_battle():
                self.logger.log("✓ Battle started! Battle detected")
                time.sleep(1)  # Brief stabilization wait
                return True
            
            # Check if 10 seconds have passed without battle detection (only if fallback is enabled)
            elapsed = time.time() - start_time
            if use_fallback and elapsed >= 10 and not fallback_triggered:
                self.logger.log("No battle detected after 10 seconds, trying fallback clicks...")
                if self.fallback_click_sequence():
                    return True  # Battle found after fallback
                fallback_triggered = True
            
            # Secondary check: Click deadspace to handle potential UI blocks (only if fallback is enabled)
            if use_fallback and elapsed >= 5:  # After 5 seconds, start clicking deadspace
                if random.randint(0, 2) == 0:  # 33% chance each cycle
                    self.tap_screen(20, 200)  # Deadspace click to handle UI
            
            self.logger.change_status(f"Battle not detected yet, waiting... ({elapsed:.1f}s)")
            time.sleep(1)
        
        self.logger.log("Timeout waiting for battle to start")
        return False
    
    def fallback_click_sequence(self):
        """Click at fallback position multiple times as fallback, then check for battle"""
        self.logger.log("Performing fallback click sequence...")
        fallback_position = FALLBACK_POSITIONS.get('battle_start', (96, 1316))
        
        for i in range(5):  # Reduced from 10 to 5 for faster recovery
            if not self.running:
                return False
            
            self.logger.log(f"Fallback click {i+1}/5")
            self.tap_screen(fallback_position[0], fallback_position[1])
            
            # Check if battle started during the click sequence
            if self.is_in_battle():
                self.logger.log(f"✓ Battle detected during fallback click {i+1}!")
                return True
            
            if i < 4:  # Don't wait after the last click
                time.sleep(2)  # Reduced from 3 to 2 seconds
                
                # Check again after the wait
                if self.is_in_battle():
                    self.logger.log(f"✓ Battle detected after fallback click {i+1} wait!")
                    return True
        
        self.logger.log("No battle detected after fallback clicks")
        return False
    
    def start_first_battle(self):
        """Click battle button to start the first battle from home page"""
        self.logger.change_status("Looking for Battle button to start first battle...")
        
        # Look for battle button for up to 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            if not self.running:
                return False
                
            screenshot = self.take_screenshot()
            if screenshot is None:
                continue
                
            battle_position, confidence = self.find_template("battle_button", screenshot)
            if battle_position:
                self.logger.log(f"Found Battle button (confidence: {confidence:.2f}), clicking to start battle...")
                self.tap_screen(battle_position[0], battle_position[1])
                return True
            
            self.logger.change_status("Battle button not found, waiting...")
            time.sleep(1)
        
        self.logger.log("Timeout: Could not find Battle button on home page")
        return False
    
    def play_card_strategically(self):
        """Play a card using sophisticated strategy from BattleStrategy"""
        screenshot = self.take_screenshot()
        if screenshot is None:
            return False
        
        # Check which cards are available
        available_cards = self.battle_logic.check_which_cards_are_available(screenshot)
        if not available_cards:
            self.logger.change_status("No cards ready yet...")
            return False
        
        # Use battle strategy to select card
        card_index = self.battle_strategy.select_card_index(available_cards)
        play_position = self.battle_strategy.get_strategic_play_position()
        
        self.logger.change_status(f"Playing card {card_index} at {play_position}")
        
        # Click the card
        if not self.tap_screen(CARD_SLOTS[card_index][0], CARD_SLOTS[card_index][1]):
            return False
        
        time.sleep(CARD_SELECTION_DELAY)
        
        # Play the card
        if not self.tap_screen(play_position[0], play_position[1]):
            return False
        
        self.logger.add_card_played()
        return True
    
    def wait_for_elixir_strategic(self, target_elixir=None):
        """Wait for elixir using battle strategy"""
        if target_elixir is None:
            target_elixir = self.battle_strategy.select_elixir_amount()
        
        self.logger.change_status(f"Waiting for {target_elixir} elixir...")
        start_time = time.time()
        
        while time.time() - start_time < 30:  # 30 second timeout
            if not self.running or not self.is_in_battle():
                return False
                
            screenshot = self.take_screenshot()
            if screenshot is None:
                continue
                
            current_elixir = self.battle_logic.detect_elixir_amount(screenshot)
            if current_elixir is not None and current_elixir >= target_elixir:
                self.logger.log(f"Have {current_elixir} elixir (needed {target_elixir})")
                return True
            
            time.sleep(0.5)
        
        return False
    
    def auto_upgrade_cards(self):
        """Automatically upgrade cards using template matching"""
        self.logger.change_status("Starting automatic card upgrade sequence...")
        
        upgrade_count = 0
        
        while self.running:
            screenshot = self.take_screenshot()
            if screenshot is None:
                continue
                
            # Look for upgrade_possible.png
            upgrade_possible_pos, confidence = self.find_template("upgrade_possible", screenshot)
            
            if upgrade_possible_pos:
                upgrade_count += 1
                self.logger.log(f"Upgrade #{upgrade_count}: Found upgrade_possible (confidence: {confidence:.2f})")
                
                # Click upgrade_possible
                if not self.tap_screen(upgrade_possible_pos[0], upgrade_possible_pos[1]):
                    self.logger.log("Failed to click upgrade_possible, continuing...")
                    continue
                
                time.sleep(1)
                
                # Look for and click upgrade_button (first time)
                screenshot = self.take_screenshot()
                upgrade_button_pos, button_confidence = self.find_template("upgrade_button", screenshot)
                if upgrade_button_pos:
                    self.logger.log(f"Found upgrade_button (confidence: {button_confidence:.2f}), clicking...")
                    self.tap_screen(upgrade_button_pos[0], upgrade_button_pos[1])
                    time.sleep(0.5)
                    
                    # Look for and click upgrade_button (second time)
                    screenshot = self.take_screenshot()
                    upgrade_button_pos2, button_confidence2 = self.find_template("upgrade_button", screenshot)
                    if upgrade_button_pos2:
                        self.logger.log(f"Found upgrade_button again (confidence: {button_confidence2:.2f}), clicking...")
                        self.tap_screen(upgrade_button_pos2[0], upgrade_button_pos2[1])
                        time.sleep(1)
                        self.logger.add_card_upgraded()
                else:
                    self.logger.log("Upgrade button not found, continuing...")
                    continue
                
                # Look for and click Confirm button
                screenshot = self.take_screenshot()
                confirm_pos, confirm_confidence = self.find_template("confirm", screenshot)
                if confirm_pos:
                    self.logger.log(f"Found Confirm button (confidence: {confirm_confidence:.2f}), clicking...")
                    self.tap_screen(confirm_pos[0], confirm_pos[1])
                    time.sleep(1)
                
                # Click at (20, 254) until upgrade_possible.png is detected again
                click_attempts = 0
                max_click_attempts = 20  # Reduced from 30
                
                while click_attempts < max_click_attempts and self.running:
                    self.tap_screen(20, 254)
                    click_attempts += 1
                    time.sleep(0.5)  # Faster clicking
                    
                    # Check if upgrade_possible is detected again
                    screenshot = self.take_screenshot()
                    if screenshot is not None:
                        next_upgrade_pos, next_confidence = self.find_template("upgrade_possible", screenshot)
                        if next_upgrade_pos:
                            self.logger.log(f"Found next upgrade after {click_attempts} clicks")
                            break
                
            else:
                self.logger.log("No more upgrades available")
                break
        
        self.logger.log(f"Auto upgrade sequence finished. Total upgrades: {upgrade_count}")
        return upgrade_count
