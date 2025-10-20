"""
War mode battle loop logic for clan wars
Automatically searches for and plays clan war battles
"""

import time
from config import CARD_SLOTS


class WarRunner:
    """
    Handles the clan war battle loop logic
    """
    
    def __init__(self, bot, shutdown_check_func, max_battles=0):
        self.bot = bot
        self.shutdown_check = shutdown_check_func
        self.max_battles = max_battles
        self.battle_count = 0
        self.instance_name = bot.instance_name
        self.logger = bot.logger
    
    def run_war_loop(self):
        """Main war loop - searches for available war battles and plays them"""
        self.logger.change_status("Starting clan war bot loop...")
        war_round = 1
        
        while self.bot.running and not self.shutdown_check():
            try:
                # Check battle limit
                if self.max_battles > 0 and self.battle_count >= self.max_battles:
                    self.logger.change_status(f"Reached battle limit ({self.max_battles}). Stopping.")
                    break
                
                self.logger.change_status(f"--- War Round {war_round} (Battle {self.battle_count + 1}) ---")
                
                # Search for available war battles (Sudden Death first, then Normal Battle)
                if not self._find_and_start_war_battle():
                    self.logger.log("No war battles available or failed to start. Stopping...")
                    break
                
                # Wait for battle to start
                if not self.bot.wait_for_battle_start(use_fallback=True):
                    self.logger.log("Battle didn't start properly after clicking war battle")
                    continue
                
                # Play the battle using normal battle logic
                self.logger.change_status("War battle started! Playing battle...")
                if not self._play_war_battle():
                    self.logger.log("Battle failed or was interrupted")
                    continue
                
                # Handle post-battle (click OK button)
                if not self._handle_war_battle_end():
                    self.logger.log("Failed to handle post-battle sequence")
                    continue
                
                # Battle completed successfully
                self.battle_count += 1
                self.logger.add_battle()
                self.logger.log(f"✓ War battle #{self.battle_count} completed successfully!")
                
                war_round += 1
                
            except Exception as e:
                self.logger.log(f"Error in war loop: {e}")
                time.sleep(2)
        
        self.logger.log(f"War mode stopped. Total battles completed: {self.battle_count}")
    
    def _find_and_start_war_battle(self):
        """
        Search for Sudden Death or Normal Battle buttons and click them,
        then search for and click the Battle button
        Returns True if successfully started a battle, False otherwise
        """
        self.logger.change_status("Searching for available war battles...")
        
        # Phase 1: Look for Sudden Death first, then Normal Battle
        war_battle_found = False
        start_time = time.time()
        search_timeout = 30  # 30 seconds to find war battle button
        
        while time.time() - start_time < search_timeout:
            if not self.bot.running or self.shutdown_check():
                return False
            
            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                time.sleep(1)
                continue
            
            # Check for Sudden Death first (higher priority)
            sudden_death_pos, sd_confidence = self.bot.find_template("sudden_death", screenshot)
            if sudden_death_pos and sd_confidence > 0.7:
                self.logger.log(f"Found Sudden Death battle (confidence: {sd_confidence:.2f}), clicking...")
                self.bot.tap_screen(sudden_death_pos[0], sudden_death_pos[1])
                war_battle_found = True
                time.sleep(2)  # Wait for screen transition
                break
            
            # Check for Normal Battle
            normal_battle_pos, nb_confidence = self.bot.find_template("normal_battle", screenshot)
            if normal_battle_pos and nb_confidence > 0.7:
                self.logger.log(f"Found Normal Battle (confidence: {nb_confidence:.2f}), clicking...")
                self.bot.tap_screen(normal_battle_pos[0], normal_battle_pos[1])
                war_battle_found = True
                time.sleep(2)  # Wait for screen transition
                break
            
            time.sleep(1)  # Wait before next check
        
        if not war_battle_found:
            self.logger.log("No war battles found (Sudden Death or Normal Battle)")
            return False
        
        # Phase 2: Now search for the Battle button and click it
        self.logger.change_status("War battle selected, searching for War Battle button...")
        battle_button_found = False
        battle_start_time = time.time()
        battle_timeout = 1200  # 120 seconds to find and click Battle button
        
        while time.time() - battle_start_time < battle_timeout:
            if not self.bot.running or self.shutdown_check():
                return False
            
            elapsed = time.time() - battle_start_time
            self.logger.change_status(f"Looking for War Battle button... ({elapsed:.0f}s / {battle_timeout}s)")
            
            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                time.sleep(1)
                continue
            
            # Look for War Battle button (specific to war mode)
            battle_pos, battle_confidence = self.bot.find_template("war_battle_button", screenshot)
            if battle_pos and battle_confidence > 0.7:
                self.logger.log(f"Found War Battle button (confidence: {battle_confidence:.2f}), clicking to start war battle...")
                self.bot.tap_screen(battle_pos[0], battle_pos[1])
                battle_button_found = True
                time.sleep(2)  # Wait for battle to start
                break
            
            time.sleep(1)  # Wait before next check
        
        if not battle_button_found:
            self.logger.log(f"War Battle button not found after {battle_timeout} seconds. Stopping...")
            return False
        
        return True
    
    def _play_war_battle(self):
        """
        Play the war battle using normal battle logic
        Returns True if battle completed successfully
        """
        battle_start_time = time.time()
        cards_played = 0
        
        self.logger.change_status("Playing war battle...")
        
        while self.bot.running and not self.shutdown_check():
            battle_elapsed = time.time() - battle_start_time
            
            # Check if still in battle
            if not self.bot.is_in_battle():
                self.logger.log("War battle ended - no longer in battle")
                break
            
            # Check for battle timeout (5 minutes max)
            if battle_elapsed > 300:
                self.logger.log("War battle timed out after 5 minutes")
                return False
            
            # Get current battle phase and strategy
            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                continue
            
            current_elixir = self.bot.battle_logic.detect_elixir_amount(screenshot)
            is_2x_elixir = self.bot.battle_logic.detect_2x_elixir(screenshot)
            
            # Log battle status every 10 seconds
            if int(battle_elapsed) % 10 == 0:
                battle_phase = self.bot.battle_strategy.get_battle_phase()
                self.logger.change_status(
                    f"War Battle - Phase: {battle_phase}, Elapsed: {battle_elapsed:.1f}s, "
                    f"Elixir: {current_elixir}, 2x: {is_2x_elixir}, Cards: {cards_played}"
                )
            
            # Play cards when we have at least 6 elixir
            should_play = False
            if current_elixir is not None and current_elixir >= 6:
                should_play = True
            
            if should_play:
                if self.bot.play_card_strategically():
                    cards_played += 1
                    self.logger.change_status(f"Played card #{cards_played} in war battle")
                    
                    # Add appropriate delay
                    delay = self.bot.battle_strategy.get_play_delay()
                    time.sleep(delay)
                else:
                    self.logger.change_status("Failed to play card, retrying...")
                    time.sleep(0.5)
            else:
                # Wait before checking again
                time.sleep(0.5)
        
        self.logger.log(f"War battle completed! Played {cards_played} cards")
        return True
    
    def _handle_war_battle_end(self):
        """
        Handle post-war-battle sequence - click OK button and return to war screen
        Returns True if successfully handled, False otherwise
        """
        self.logger.change_status("Handling post-war-battle sequence...")
        
        # Wait for post-battle screen and OK button
        post_battle_timeout = 60  # 1 minute timeout
        start_time = time.time()
        
        while time.time() - start_time < post_battle_timeout:
            if not self.bot.running or self.shutdown_check():
                return False
            
            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                time.sleep(1)
                continue
            
            # Look for OK button
            ok_pos, ok_confidence = self.bot.find_template("ok_button", screenshot)
            if ok_pos and ok_confidence > 0.7:
                self.logger.log(f"Found OK button (confidence: {ok_confidence:.2f}), clicking to return to war screen...")
                self.bot.tap_screen(ok_pos[0], ok_pos[1])
                time.sleep(3)  # Wait for transition back to war screen
                return True
            
            # Also check for Play Again button (alternative post-battle button)
            play_again_pos, pa_confidence = self.bot.find_template("play_again", screenshot)
            if play_again_pos and pa_confidence > 0.7:
                self.logger.log(f"Found Play Again button (confidence: {pa_confidence:.2f}), clicking OK instead...")
                # Try to find OK button instead or click deadspace
                self.bot.tap_screen(20, 200)  # Click deadspace to close
                time.sleep(2)
                continue
            
            # Click deadspace to close any popups
            self.bot.tap_screen(20, 200)
            time.sleep(1)
        
        self.logger.log("Timeout waiting for OK button after war battle")
        return False
