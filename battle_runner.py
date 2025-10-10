"""
Battle loop logic and game coordination - refactored with PyClashBot architecture
"""

import time
from config import INACTIVITY_TIMEOUT


class BattleRunner:
    """
    Handles the main battle loop logic using PyClashBot patterns
    """
    
    def __init__(self, bot, shutdown_check_func, max_battles=0):
        self.bot = bot
        self.shutdown_check = shutdown_check_func
        self.max_battles = max_battles
        self.battle_count = 0
        self.instance_name = bot.instance_name
        self.logger = bot.logger
    
    def run_bot_loop(self):
        """Main bot loop for this emulator instance with enhanced strategy"""
        self.logger.change_status("Starting enhanced bot loop...")
        game_round = 1
        first_battle = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.bot.running and not self.shutdown_check():
            try:
                # Check battle limit
                if self.max_battles > 0 and self.battle_count >= self.max_battles:
                    self.logger.change_status(f"Reached battle limit ({self.max_battles}). Stopping.")
                    break
                    
                self.logger.change_status(f"--- Starting round {game_round} (Battle {self.battle_count + 1}) ---")
                last_activity_time = time.time()
                
                # For the first battle, start from home page
                if first_battle:
                    if not self.bot.start_first_battle():
                        self.logger.log("Failed to start first battle from home page")
                        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                            self.logger.log(f"No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                            self.bot.restart_app()
                            last_activity_time = time.time()
                        continue  # Continue trying instead of breaking the loop
                    first_battle = False
                    last_activity_time = time.time()
                
                # Wait for battle to actually start
                if not self.bot.wait_for_battle_start(use_fallback=True):
                    self.logger.log("Battle didn't start properly, trying to recover...")
                    
                    # Try additional recovery steps before checking timeout
                    recovery_attempts = 0
                    max_recovery_attempts = 3
                    
                    while recovery_attempts < max_recovery_attempts and self.bot.running and not self.shutdown_check():
                        recovery_attempts += 1
                        self.logger.log(f"Recovery attempt {recovery_attempts}/{max_recovery_attempts}")
                        
                        # Try clicking battle button as fallback
                        self.bot.tap_screen(21, 511)  # Battle button fallback position
                        time.sleep(2)
                        
                        # After fallback clicks, look for battle icon and click it
                        self.logger.log("Looking for battle icon after fallback clicks...")
                        screenshot = self.bot.take_screenshot()
                        if screenshot is not None:
                            battle_pos, battle_confidence = self.bot.find_template("battle_button", screenshot)
                            if battle_pos:
                                self.logger.log(f"Found battle icon (confidence: {battle_confidence:.2f}), clicking to start battle...")
                                self.bot.tap_screen(battle_pos[0], battle_pos[1])
                                time.sleep(2)
                        
                        # Check if battle started after recovery click
                        if self.bot.wait_for_battle_start(use_fallback=False):
                            self.logger.log("✓ Battle started after recovery click!")
                            break
                        
                        # Try different recovery positions
                        if recovery_attempts == 2:
                            self.logger.log("Trying additional recovery clicks...")
                            self.bot.tap_screen(21, 511)  # Alternative fallback position
                            time.sleep(1)
                            self.bot.tap_screen(21, 511)  # Another alternative fallback position
                            time.sleep(2)
                            
                            # After final fallback clicks, look for battle icon again
                            self.logger.log("Looking for battle icon after final fallback clicks...")
                            screenshot = self.bot.take_screenshot()
                            if screenshot is not None:
                                battle_pos, battle_confidence = self.bot.find_template("battle_button", screenshot)
                                if battle_pos:
                                    self.logger.log(f"Found battle icon (confidence: {battle_confidence:.2f}), clicking to start battle...")
                                    self.bot.tap_screen(battle_pos[0], battle_pos[1])
                                    time.sleep(2)
                    else:
                        # If recovery failed, check timeout
                        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                            self.logger.log(f"No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                            self.bot.restart_app()
                            last_activity_time = time.time()
                            first_battle = True
                        continue
                
                last_activity_time = time.time()
                
                # Start battle strategy timing
                self.bot.battle_strategy.start_battle()
                self.battle_count += 1  # Increment battle counter
                self.logger.log(f"Battle {self.battle_count} started!")
                
                # Enhanced battle loop with strategy
                battle_loop_attempts = 0
                max_battle_loop_attempts = 2
                
                while battle_loop_attempts < max_battle_loop_attempts:
                    battle_loop_attempts += 1
                    self.logger.log(f"Battle loop attempt {battle_loop_attempts}/{max_battle_loop_attempts}")
                    
                    if self._enhanced_fight_loop():
                        break
                    else:
                        self.logger.log(f"Battle loop failed (attempt {battle_loop_attempts}/{max_battle_loop_attempts})")
                        if battle_loop_attempts < max_battle_loop_attempts:
                            self.logger.log("Retrying battle loop...")
                            time.sleep(2)  # Brief pause before retry
                        else:
                            self.logger.log("Battle loop failed after all attempts, restarting...")
                            self.bot.restart_app()
                            last_activity_time = time.time()
                            first_battle = True
                            continue
                
                # Wait for battle to end and handle post-battle
                battle_end_attempts = 0
                max_battle_end_attempts = 3
                
                while battle_end_attempts < max_battle_end_attempts:
                    battle_end_attempts += 1
                    self.logger.log(f"Battle end attempt {battle_end_attempts}/{max_battle_end_attempts}")
                    
                    if self._handle_battle_end():
                        self.logger.log("Successfully handled post-battle sequence")
                        break
                    else:
                        self.logger.log("Issues with post-battle sequence, retrying...")
                        if battle_end_attempts < max_battle_end_attempts:
                            # Try some recovery clicks before next attempt
                            self.bot.tap_screen(21, 511)  # OK button fallback
                            time.sleep(1)
                            self.bot.tap_screen(21, 511)  # Battle button fallback
                            time.sleep(2)
                        else:
                            self.logger.log("Failed to handle battle end after all attempts, restarting app...")
                            self.bot.restart_app()
                            last_activity_time = time.time()
                            first_battle = True
                            continue
                
                game_round += 1
                consecutive_errors = 0  # Reset error counter on successful round
                
            except Exception as e:
                consecutive_errors += 1
                self.logger.log(f"Bot loop error #{consecutive_errors}: {e}")
                self.logger.add_failure()
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.log(f"Too many consecutive errors ({consecutive_errors}), stopping bot")
                    break
                
                # Try to recover from error
                self.logger.log("Attempting to recover from bot loop error...")
                try:
                    self.bot.restart_app()
                    first_battle = True
                    time.sleep(5)  # Give some time for recovery
                    self.logger.log("Recovery attempted, continuing bot loop...")
                    continue
                except Exception as recovery_error:
                    self.logger.log(f"Recovery failed: {recovery_error}")
                    break  # Exit if recovery also fails
        
        self.logger.change_status("Bot loop stopped")
    
    def _enhanced_fight_loop(self):
        """Enhanced fight loop with PyClashBot strategy patterns"""
        self.logger.change_status("Starting enhanced battle strategy...")
        battle_start_time = time.time()
        cards_played_this_battle = 0
        
        while self.bot.running and not self.shutdown_check():
            current_time = time.time()
            battle_elapsed = current_time - battle_start_time
            
            # Check if still in battle
            if not self.bot.is_in_battle():
                self.logger.log("Battle ended - no longer in battle")
                break
            
            # Check for battle timeout (5 minutes max)
            if battle_elapsed > 300:
                self.logger.log("Battle timed out after 5 minutes")
                return False
            
            # Get current battle phase and strategy
            battle_phase = self.bot.battle_strategy.get_battle_phase()
            
            # Check if we should wait for elixir or play immediately
            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                continue
            
            current_elixir = self.bot.battle_logic.detect_elixir_amount(screenshot)
            is_2x_elixir = self.bot.battle_logic.detect_2x_elixir(screenshot)
            
            # Log battle status every 10 seconds
            if int(battle_elapsed) % 10 == 0:
                self.logger.change_status(
                    f"Battle phase: {battle_phase}, Elapsed: {battle_elapsed:.1f}s, "
                    f"Elixir: {current_elixir}, 2x: {is_2x_elixir}, Cards: {cards_played_this_battle}"
                )
            
            # Determine if we should play a card
            should_play = False
            
            # Only play if we have at least 7 elixir
            if current_elixir is not None and current_elixir >= 7:
                should_play = True
            
            if should_play:
                if self.bot.play_card_strategically():
                    cards_played_this_battle += 1
                    self.logger.change_status(f"Played card #{cards_played_this_battle} this battle")
                    
                    # Add appropriate delay based on battle phase
                    delay = self.bot.battle_strategy.get_play_delay()
                    time.sleep(delay)
                else:
                    self.logger.change_status("Failed to play card, retrying...")
                    time.sleep(0.5)
            else:
                # Wait a bit before checking again
                time.sleep(0.5)
        
        self.logger.log(f"Battle completed! Played {cards_played_this_battle} cards")
        return True
    
    def _handle_battle_end(self):
        """Handle post-battle sequence with enhanced detection"""
        self.logger.change_status("Handling post-battle sequence...")
        
        # Wait for post-battle screen to appear
        post_battle_timeout = 60  # 1 minute timeout
        start_time = time.time()
        
        while time.time() - start_time < post_battle_timeout:
            if not self.bot.running or self.shutdown_check():
                return False
            
            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                continue
            
            # Check for post-battle buttons
            play_again_pos, confidence = self.bot.find_template("play_again", screenshot)
            if play_again_pos:
                self.logger.log(f"Found Play Again button (confidence: {confidence:.2f}), clicking...")
                self.bot.tap_screen(play_again_pos[0], play_again_pos[1])
                time.sleep(2)
                return True
            
            ok_pos, confidence = self.bot.find_template("ok_button", screenshot)
            if ok_pos:
                self.logger.log(f"Found OK button (confidence: {confidence:.2f}), clicking...")
                self.bot.tap_screen(ok_pos[0], ok_pos[1])
                time.sleep(3)  # Wait longer for transition to home screen
                
                # Enhanced battle button search with continuous clicking
                self.logger.log("Searching for battle button after returning to home screen...")
                battle_search_start = time.time()
                battle_search_timeout = 30  # Search for up to 30 seconds
                
                while time.time() - battle_search_start < battle_search_timeout:
                    if not self.bot.running or self.shutdown_check():
                        return False
                    
                    screenshot = self.bot.take_screenshot()
                    if screenshot is not None:
                        battle_pos, battle_confidence = self.bot.find_template("battle_button", screenshot)
                        if battle_pos:
                            self.logger.log(f"Found Battle button (confidence: {battle_confidence:.2f}), clicking for next match...")
                            self.bot.tap_screen(battle_pos[0], battle_pos[1])
                            return True
                    
                    # If battle button not found, click the screen and wait 1 second before trying again
                    self.logger.log("Battle button not found, clicking screen to refresh...")
                    self.bot.tap_screen(21, 511)  # Click screen to refresh
                    time.sleep(1)  # Wait 1 second between clicks as requested
                
                # If still no battle button found after timeout, try fallback position
                self.logger.log("Battle button search timed out, trying fallback position...")
                self.bot.tap_screen(21, 511)  # Fallback battle button position
                return True
            
            # Click deadspace to close any popups
            self.bot.tap_screen(20, 200)  # Use deadspace coordinates from config
            time.sleep(1)
        
        self.logger.log("Timeout waiting for post-battle screen")
        return False
