"""
Battle loop logic and game coordination - refactored with PyClashBot architecture
"""

import time
from config import INACTIVITY_TIMEOUT


class BattleRunner:
    """
    Handles the main battle loop logic using PyClashBot patterns
    """
    
    def __init__(self, bot, shutdown_check_func):
        self.bot = bot
        self.shutdown_check = shutdown_check_func
        self.instance_name = bot.instance_name
        self.logger = bot.logger
    
    def run_bot_loop(self):
        """Main bot loop for this emulator instance with enhanced strategy"""
        self.logger.change_status("Starting enhanced bot loop...")
        game_round = 1
        first_battle = True
        
        try:
            while self.bot.running and not self.shutdown_check():
                self.logger.change_status(f"--- Starting round {game_round} ---")
                last_activity_time = time.time()
                
                # For the first battle, start from home page
                if first_battle:
                    if not self.bot.start_first_battle():
                        self.logger.log("Failed to start first battle from home page")
                        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                            self.logger.log(f"No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                            self.bot.restart_app()
                            last_activity_time = time.time()
                        break
                    first_battle = False
                    last_activity_time = time.time()
                
                # Wait for battle to actually start
                if not self.bot.wait_for_battle_start(use_fallback=first_battle):
                    self.logger.log("Battle didn't start properly, trying to recover...")
                    if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                        self.logger.log(f"No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        self.bot.restart_app()
                        last_activity_time = time.time()
                        first_battle = True
                        continue
                    # Try clicking battle button as fallback
                    self.bot.tap_screen(540, 1200)  # Battle button approximate position
                    time.sleep(1)
                    continue
                
                last_activity_time = time.time()
                
                # Start battle strategy timing
                self.bot.battle_strategy.start_battle()
                
                # Enhanced battle loop with strategy
                if not self._enhanced_fight_loop():
                    self.logger.log("Battle loop failed, restarting...")
                    self.bot.restart_app()
                    last_activity_time = time.time()
                    first_battle = True
                    continue
                
                # Wait for battle to end and handle post-battle
                if not self._handle_battle_end():
                    self.logger.log("Failed to handle battle end properly")
                    self.bot.restart_app()
                    last_activity_time = time.time()
                    first_battle = True
                    continue
                
                game_round += 1
                
        except Exception as e:
            self.logger.log(f"Bot loop error: {e}")
            self.logger.add_failure()
        finally:
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
            
            if is_2x_elixir:
                # In 2x elixir, play more aggressively
                if current_elixir is None or current_elixir >= 3:
                    should_play = True
            else:
                # Use strategic elixir waiting
                target_elixir = self.bot.battle_strategy.select_elixir_amount()
                if current_elixir is not None and current_elixir >= target_elixir:
                    should_play = True
                elif self.bot.battle_strategy.should_play_aggressively():
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
                time.sleep(2)
                
                # Look for battle button to start next match
                screenshot = self.bot.take_screenshot()
                if screenshot is not None:
                    battle_pos, battle_confidence = self.bot.find_template("battle_button", screenshot)
                    if battle_pos:
                        self.logger.log("Clicking Battle button for next match...")
                        self.bot.tap_screen(battle_pos[0], battle_pos[1])
                
                return True
            
            # Click deadspace to close any popups
            self.bot.tap_screen(20, 200)
            time.sleep(1)
        
        self.logger.log("Timeout waiting for post-battle screen")
        return False
