"""
Battle loop logic and game coordination
"""

import time
from config import INACTIVITY_TIMEOUT, ELIXIR_CHECK_INTERVAL, DOUBLE_ELIXIR_CHECK_INTERVAL


class BattleRunner:
    """Handles the main battle loop logic"""
    
    def __init__(self, bot, shutdown_check_func):
        self.bot = bot
        self.shutdown_check = shutdown_check_func
        self.instance_name = bot.instance_name
    
    def run_bot_loop(self):
        """Main bot loop for this emulator instance"""
        print(f"[{self.instance_name}] Starting bot loop...")
        game_round = 1
        first_battle = True
        
        try:
            while self.bot.running and not self.shutdown_check():
                print(f"[{self.instance_name}] --- Starting round {game_round} ---")
                last_activity_time = time.time()
                
                # For the first battle, start from home page
                if first_battle:
                    if not self.bot.start_first_battle():
                        print(f"[{self.instance_name}] Failed to start first battle from home page")
                        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                            print(f"[{self.instance_name}] No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                            self.bot.restart_app()
                            last_activity_time = time.time()
                        break
                    first_battle = False
                    last_activity_time = time.time()
                
                # Wait for battle to actually start (elixir bar appears)
                if not self.bot.wait_for_battle_start(use_fallback=first_battle):
                    print(f"[{self.instance_name}] Battle didn't start properly, trying to recover...")
                    if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                        print(f"[{self.instance_name}] No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        self.bot.restart_app()
                        last_activity_time = time.time()
                        first_battle = True
                        continue
                    # Try clicking battle button as fallback
                    self.bot.tap_screen(540, 1200)  # Battle button approximate position
                    time.sleep(1)
                    continue
                
                last_activity_time = time.time()
                
                # Run the actual battle
                battle_stats = self._run_battle()
                
                if self.shutdown_check() or not self.bot.running:
                    break
                
                print(f"[{self.instance_name}] Finished battle - Combos: {battle_stats['combos']}, Single cards: {battle_stats['single_cards']}")
                
                # Handle post-battle sequence
                if self._handle_battle_end():
                    print(f"[{self.instance_name}] Successfully handled post-battle sequence")
                else:
                    print(f"[{self.instance_name}] Issues with post-battle sequence, attempting recovery...")
                    self._attempt_recovery()
                
                # Wait for next battle
                if not self._wait_for_next_battle():
                    print(f"[{self.instance_name}] Failed to find next battle, checking for issues...")
                    self._handle_battle_start_issues()
                
                game_round += 1
                
        except Exception as e:
            print(f"[{self.instance_name}] Bot loop error: {e}")
        finally:
            print(f"[{self.instance_name}] Bot loop stopped")
    
    def _run_battle(self):
        """Run the adaptive battle strategy and return battle statistics"""
        combos_played = 0
        single_cards_played = 0
        print(f"[{self.instance_name}] Starting adaptive battle strategy...")
        battle_start_time = time.time()
        last_elixir_check = time.time()
        last_2x_check = time.time()
        last_card_play = time.time()
        is_2x_elixir = False
        battle_phase = "early"  # early, mid, late
        
        while self.bot.running and not self.shutdown_check():
            current_time = time.time()
            battle_elapsed = current_time - battle_start_time
            
            # Update battle phase based on time
            if battle_elapsed < 60:
                battle_phase = "early"
            elif battle_elapsed < 120:
                battle_phase = "mid"
            else:
                battle_phase = "late"
            
            # Check for 2x elixir mode every few seconds
            if current_time - last_2x_check >= DOUBLE_ELIXIR_CHECK_INTERVAL:
                is_2x_elixir = self.bot.detect_2x_elixir()
                last_2x_check = current_time
            
            # Check elixir amount periodically during battle
            current_elixir = None
            if current_time - last_elixir_check >= ELIXIR_CHECK_INTERVAL:
                current_elixir = self.bot.detect_elixir_amount()
                if current_elixir is not None:
                    print(f"[{self.instance_name}] Current elixir: {current_elixir}")
                last_elixir_check = current_time
            
            # Priority check: Look for post-battle buttons first (battle ended)
            post_battle_button = self.bot.find_post_battle_button()
            if post_battle_button:
                print(f"[{self.instance_name}] Battle ended! Post-battle button detected, clicking it...")
                self.bot.tap_screen(post_battle_button[0], post_battle_button[1])
                time.sleep(2)  # Wait for button click to register
                break
            
            # Secondary check: Look for battle end by checking if we're still in battle
            if not self.bot.is_in_battle():
                print(f"[{self.instance_name}] Battle ended - no longer in battle")
                # Wait a moment for post-battle screen to appear, then check again
                time.sleep(2)
                post_battle_button = self.bot.find_post_battle_button()
                if post_battle_button:
                    print(f"[{self.instance_name}] Found post-battle button after waiting, clicking it...")
                    self.bot.tap_screen(post_battle_button[0], post_battle_button[1])
                    time.sleep(2)
                else:
                    print(f"[{self.instance_name}] No post-battle button found after battle end")
                break
            
            # Check for inactivity timeout during battle
            if current_time - battle_start_time > INACTIVITY_TIMEOUT:
                print(f"[{self.instance_name}] Battle seems stuck for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                self.bot.restart_app()
                break
            
            # Card playing logic with improved timing
            time_since_last_play = current_time - last_card_play
            min_play_interval = 1.0 if is_2x_elixir else 1.5  # Faster plays in 2x elixir
            
            if time_since_last_play >= min_play_interval:
                # Decide whether to play combo or single card
                if self.bot.battle_logic.should_play_combo(battle_phase, is_2x_elixir):
                    if self.bot.play_double_card_combo():
                        combos_played += 1
                        last_card_play = current_time
                        print(f"[{self.instance_name}] Combo played! Total combos: {combos_played}")
                else:
                    # Play single card with elixir check
                    if self.bot.battle_logic.should_play_single_card(current_elixir):
                        if self.bot.play_card(check_elixir=True):
                            single_cards_played += 1
                            last_card_play = current_time
                            print(f"[{self.instance_name}] Single card played! Total single cards: {single_cards_played}")
            else:
                # Not time to play yet, just wait
                time.sleep(0.2)
        
        return {
            "combos": combos_played,
            "single_cards": single_cards_played,
            "battle_phase": battle_phase,
            "was_2x_elixir": is_2x_elixir
        }
    
    def _handle_battle_end(self):
        """Handle the battle end sequence"""
        # Wait for battle to end using improved detection
        if self.bot.wait_for_battle_end():
            print(f"[{self.instance_name}] Battle end detected, handling post-battle sequence...")
            # Handle post-battle with image recognition
            if self.bot.handle_post_battle():
                print(f"[{self.instance_name}] Post-battle sequence completed successfully")
                return True
            else:
                print(f"[{self.instance_name}] Post-battle sequence had issues")
                return False
        else:
            print(f"[{self.instance_name}] Failed to detect battle end properly")
            return False
    
    def _attempt_recovery(self):
        """Attempt to recover from post-battle issues"""
        print(f"[{self.instance_name}] Attempting recovery from post-battle issues...")
        # Try clicking common positions as fallback
        for attempt in range(3):
            print(f"[{self.instance_name}] Recovery attempt {attempt + 1}/3")
            self.bot.tap_screen(540, 1100)  # OK button fallback
            time.sleep(1)
            self.bot.tap_screen(540, 1200)  # Battle button fallback
            time.sleep(1)
        
        time.sleep(1)
        self.bot.tap_screen(540, 1200)  # Battle button approximate position
    
    def _wait_for_next_battle(self):
        """Wait for the next battle to start"""
        print(f"[{self.instance_name}] Waiting for next battle to start...")
        next_battle_start_time = time.time()
        
        while time.time() - next_battle_start_time < 30:  # Max 30 seconds wait for next battle
            if self.shutdown_check() or not self.bot.running:
                return False
                
            if self.bot.is_in_battle():
                print(f"[{self.instance_name}] ✓ Next battle started!")
                return True
            
            # Just wait - no fallback sequence needed after clicking Play Again
            # The game should automatically start matchmaking
            elapsed = time.time() - next_battle_start_time
            print(f"[{self.instance_name}] Waiting for matchmaking... ({elapsed:.1f}s)")
            time.sleep(2)
        
        return False
    
    def _handle_battle_start_issues(self):
        """Handle issues with battle start"""
        print(f"[{self.instance_name}] Handling battle start issues...")
        # Check if we're stuck on home screen and need to click Battle button
        battle_position, _ = self.bot.find_template("battle_button")
        if battle_position:
            print(f"[{self.instance_name}] Found Battle button on home screen, clicking it...")
            self.bot.tap_screen(battle_position[0], battle_position[1])
        else:
            print(f"[{self.instance_name}] No Battle button found, may need app restart")
            self.bot.restart_app()
