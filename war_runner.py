"""
War mode battle loop logic for clan wars
Automatically searches for and plays clan war battles
"""

import time
from war_utils import find_available_war_battles, click_battle_if_found
from config import DEFAULT_TIMEOUTS


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
        """Main war loop - searches for available war battles and plays them (never stops)"""
        self.logger.change_status(
            "Starting clan war bot loop (continuous mode - never stops)..."
        )
        war_round = 1

        while self.bot.running and not self.shutdown_check():
            try:
                # Check battle limit
                if self.max_battles > 0 and self.battle_count >= self.max_battles:
                    self.logger.change_status(
                        f"Reached battle limit ({self.max_battles}). Stopping."
                    )
                    break

                self.logger.change_status(
                    f"--- War Round {war_round} (Battle {self.battle_count + 1}) ---"
                )

                # Search for available war battles (Sudden Death first, then Normal Battle)
                if not self._find_and_start_war_battle():
                    self.logger.log(
                        "No war battles available right now. Returning to Phase 1..."
                    )
                    time.sleep(3)
                    continue  # Loop back to Phase 1

                # Wait for battle to start (60 seconds for war battles due to longer queue times)
                self.logger.change_status(
                    "Waiting for war battle to start (queue time may be longer)..."
                )
                if not self.bot.wait_for_battle_start(use_fallback=True, timeout=60):
                    self.logger.log(
                        "War battle didn't start after 60 seconds. Restarting search..."
                    )
                    time.sleep(3)
                    continue

                # Play the battle using normal battle logic
                self.logger.change_status("War battle started! Playing battle...")
                if not self._play_war_battle():
                    self.logger.log(
                        "Battle failed or was interrupted. Continuing to next battle..."
                    )
                    time.sleep(3)
                    continue

                # Handle post-battle (click OK button)
                if not self._handle_war_battle_end():
                    self.logger.log(
                        "Failed to handle post-battle sequence. Restarting search..."
                    )
                    time.sleep(3)
                    continue

                # Battle completed successfully
                self.battle_count += 1
                self.logger.add_battle()
                self.logger.log(
                    f"✓ War battle #{self.battle_count} completed successfully!"
                )

                war_round += 1

            except Exception as e:
                self.logger.log(f"Error in war loop: {e}. Returning to Phase 1...")
                time.sleep(3)
                continue  # Always continue, never stop

        self.logger.log(
            f"War mode stopped. Total battles completed: {self.battle_count}"
        )

    def _find_and_start_war_battle(self):
        """
        Search for Sudden Death or Normal Battle buttons and click them,
        then search for and click the Battle button
        Returns True if successfully started a battle, False otherwise
        """
        self.logger.change_status("Searching for available war battles...")

        # Phase 1: Look for all battle types and randomly select one
        war_battle_found = False
        start_time = time.time()
        search_timeout = DEFAULT_TIMEOUTS.get("war_battle_search", 60)

        while time.time() - start_time < search_timeout:
            if not self.bot.running or self.shutdown_check():
                return False

            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                time.sleep(1)
                continue

            # Use the new utility function to find available battles
            available_battles = find_available_war_battles(self.bot, screenshot)

            # If we found any battles, click one
            if available_battles:
                if click_battle_if_found(self.bot, available_battles, self.logger, delay=2.0):
                    war_battle_found = True
                    break

            time.sleep(1)  # Wait before next check

        if not war_battle_found:
            self.logger.log(
                "No war battles found (Sudden Death, RampUp, Normal Battle, or Touchdown War) - will retry"
            )
            return False

        # Phase 2: Now search for the Battle button and click it (infinite retry)
        # Also continue checking for war battle buttons in case we need to reselect
        self.logger.change_status(
            "War battle selected, searching for War Battle button..."
        )
        battle_button_found = False
        battle_start_time = time.time()
        battle_timeout = DEFAULT_TIMEOUTS.get("war_battle_button", 180)

        while time.time() - battle_start_time < battle_timeout:
            if not self.bot.running or self.shutdown_check():
                return False

            elapsed = time.time() - battle_start_time
            self.logger.change_status(
                f"Looking for War Battle button... ({elapsed:.0f}s / {battle_timeout}s)"
            )

            screenshot = self.bot.take_screenshot()
            if screenshot is None:
                time.sleep(1)
                continue

            # First priority: Look for War Battle button (specific to war mode)
            battle_pos, battle_confidence = self.bot.find_template(
                "war_battle_button", screenshot
            )
            if battle_pos and battle_confidence > 0.7:
                self.logger.log(
                    f"Found War Battle button (confidence: {battle_confidence:.2f}), clicking to start war battle..."
                )
                self.bot.tap_screen(battle_pos[0], battle_pos[1])
                battle_button_found = True
                time.sleep(2)  # Wait for battle to start
                break

            # Second priority: Check if we're back at war selection screen
            available_battles = find_available_war_battles(self.bot, screenshot)

            # If we found any battles (returned to war selection), click one
            if available_battles:
                self.logger.log(
                    f"Returned to war selection - Found {len(available_battles)} battle type(s)"
                )
                click_battle_if_found(self.bot, available_battles, self.logger, delay=2.0)
                continue  # Continue searching for War Battle button

            time.sleep(1)  # Wait before next check

        if not battle_button_found:
            self.logger.log(
                f"War Battle button not found after {battle_timeout} seconds - will restart and retry"
            )
            return False

        return True

    def _play_war_battle(self):
        """
        Play the war battle using normal battle logic
        Returns True if battle completed successfully
        """
        battle_start_time = time.time()
        cards_played = 0
        not_in_battle_start = None  # Track when we first detect "not in battle"

        self.logger.change_status("Playing war battle...")

        while self.bot.running and not self.shutdown_check():
            battle_elapsed = time.time() - battle_start_time

            # Check if still in battle
            if not self.bot.is_in_battle():
                # First time detecting "not in battle"
                if not_in_battle_start is None:
                    not_in_battle_start = time.time()
                    self.logger.log(
                        "Battle end detected, waiting 15 seconds to confirm..."
                    )

                # Check if we've been "not in battle" for 15 seconds
                not_in_battle_duration = time.time() - not_in_battle_start
                if not_in_battle_duration >= 15:
                    self.logger.log(
                        f"War battle ended - not in battle for {not_in_battle_duration:.1f}s"
                    )
                    break
                else:
                    # Still waiting for confirmation
                    self.logger.change_status(
                        f"Confirming battle end... ({not_in_battle_duration:.1f}s / 15s)"
                    )
                    time.sleep(1)
                    continue
            else:
                # Back in battle, reset the timer
                if not_in_battle_start is not None:
                    self.logger.log(
                        "False alarm - still in battle, resetting end detection timer"
                    )
                    not_in_battle_start = None

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
                    self.logger.change_status(
                        f"Played card #{cards_played} in war battle"
                    )

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
        post_battle_timeout = DEFAULT_TIMEOUTS.get("post_battle", 60)
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
                self.logger.log(
                    f"Found OK button (confidence: {ok_confidence:.2f}), clicking to return to war screen..."
                )
                self.bot.tap_screen(ok_pos[0], ok_pos[1])
                time.sleep(3)  # Wait for transition back to war screen
                return True

            # Also check for Play Again button (alternative post-battle button)
            play_again_pos, pa_confidence = self.bot.find_template(
                "play_again", screenshot
            )
            if play_again_pos and pa_confidence > 0.7:
                self.logger.log(
                    f"Found Play Again button (confidence: {pa_confidence:.2f}), clicking OK instead..."
                )
                # Try to find OK button instead or click deadspace
                self.bot.tap_screen(20, 200)  # Click deadspace to close
                time.sleep(2)
                continue

            # Click deadspace to close any popups
            self.bot.tap_screen(20, 200)
            time.sleep(1)

        self.logger.log("Timeout waiting for OK button after war battle")
        return False
