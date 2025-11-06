"""
Battle strategy and timing management
"""

import time
import random
import collections
from typing import Literal
from config import PLAY_AREA, BRIDGE_POSITIONS

# Bridge Y coordinate range for proper bridge placement
BRIDGE_Y_RANGE = (279, 295)  # Centered around Y=287


class BattleStrategy:
    """
    Manages battle timing and elixir selection strategy.

    Encapsulates sophisticated elixir selection logic that changes
    based on battle phase, eliminating the need for global variables.
    """

    def __init__(self):
        self.start_time = None
        self.elixir_amounts = [3, 4, 5, 6, 7, 8, 9]
        self.last_three_cards = collections.deque(maxlen=3)

        # Strategy weights for each battle phase
        self.phase_strategies = {
            "early": [
                0,
                0,
                0,
                0,
                0.3,
                0.3,
                0.4,
            ],  # 0-7s: Conservative, wait for more elixir
            "single": [
                0.05,
                0.05,
                0.1,
                0.15,
                0.15,
                0.3,
                0.2,
            ],  # 7-90s: Balanced distribution
            "double": [
                0.05,
                0.05,
                0.1,
                0.15,
                0.25,
                0.3,
                0.1,
            ],  # 90-200s: Favor 7-8 elixir
            "triple": [
                0.05,
                0.05,
                0.1,
                0.1,
                0.3,
                0.4,
                0,
            ],  # 200s+: Heavy favor 7-8, never 9
        }

        # Wait/play thresholds for each phase
        self.phase_thresholds = {
            "early": (6000, 9000),
            "single": (6000, 9000),
            "double": (7000, 10000),
            "triple": (8000, 11000),
        }

    def start_battle(self):
        """Call when battle begins to start timing"""
        self.start_time = time.time()
        self.last_three_cards.clear()

    def get_elapsed_time(self) -> float:
        """Get seconds elapsed since battle start"""
        return time.time() - self.start_time if self.start_time else 0

    def get_battle_phase(self) -> Literal["early", "single", "double", "triple"]:
        """Determine current battle phase based on elapsed time"""
        elapsed = self.get_elapsed_time()
        if elapsed < 7:
            return "early"
        elif elapsed < 90:
            return "single"
        elif elapsed < 200:
            return "double"
        else:
            return "triple"

    def select_elixir_amount(self) -> int:
        """Select elixir amount to wait for based on current battle phase"""
        phase = self.get_battle_phase()
        weights = self.phase_strategies[phase]
        return random.choices(self.elixir_amounts, weights=weights, k=1)[0]

    def get_thresholds(self) -> tuple[int, int]:
        """Get (WAIT_THRESHOLD, PLAY_THRESHOLD) for current battle phase"""
        phase = self.get_battle_phase()
        return self.phase_thresholds[phase]

    def select_card_index(self, available_card_indices: list[int]) -> int:
        """
        Select a card index with intelligent logic to avoid repetition.

        Args:
            available_card_indices: List of available card indices

        Returns:
            int: Selected card index
        """
        if not available_card_indices:
            raise ValueError("available_card_indices cannot be empty")

        # First preference: Cards not in the last_three_cards queue
        preferred_cards = [
            index
            for index in available_card_indices
            if index not in self.last_three_cards
        ]

        # Second preference: Cards not among the last two added to the queue
        if not preferred_cards and len(self.last_three_cards) == 3:
            preferred_cards = [
                index
                for index in available_card_indices
                if index not in list(self.last_three_cards)[-2:]
            ]

        # Third preference: Any card except the most recently added one
        if not preferred_cards and self.last_three_cards:
            preferred_cards = [
                index
                for index in available_card_indices
                if index != self.last_three_cards[-1]
            ]

        # Fallback: If all else fails, consider all cards
        if not preferred_cards:
            preferred_cards = available_card_indices

        selected_index = random.choice(preferred_cards)

        # Update the queue with the selected card
        if selected_index not in self.last_three_cards:
            self.last_three_cards.append(selected_index)

        return selected_index

    def get_strategic_play_position(self) -> tuple[int, int]:
        """
        Generate strategic play position based on battle phase and randomization.

        Returns:
            tuple[int, int]: (x, y) coordinates for card placement
        """
        phase = self.get_battle_phase()

        # Early game: More conservative placement
        if phase == "early":
            if random.randint(0, 2) == 0:  # 33% chance for bridge play
                place_x, place_y = random.choice(BRIDGE_POSITIONS)  # Left or right bridge
            else:
                # Defensive positioning
                place_x = random.randint(
                    PLAY_AREA["min_x"] + 30, PLAY_AREA["max_x"] - 30
                )
                place_y = random.randint(
                    PLAY_AREA["min_y"] + 30, PLAY_AREA["max_y"] - 10
                )

        # Late game: More aggressive placement
        elif phase in ["double", "triple"]:
            if random.randint(0, 1) == 0:  # 50% chance for bridge play
                place_x, place_y = random.choice(BRIDGE_POSITIONS)  # Bridge positions
            else:
                # Full area usage
                place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
                place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])

        # Normal game: Balanced approach
        else:
            if random.randint(0, 2) == 0:  # 33% chance for bridge play
                place_x, place_y = random.choice(BRIDGE_POSITIONS)  # Bridge positions
            else:
                place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
                place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])

        return (place_x, place_y)

    def should_play_aggressively(self) -> bool:
        """Determine if we should play more aggressively based on battle phase"""
        phase = self.get_battle_phase()
        elapsed = self.get_elapsed_time()

        # Very aggressive in final 30 seconds of any elixir phase
        if phase == "triple" or (elapsed > 170):
            return True
        elif phase == "double" and elapsed > 150:
            return True
        elif phase == "single" and elapsed > 60:
            return random.randint(0, 2) == 0  # 33% chance

        return False

    def get_play_delay(self) -> float:
        """Get appropriate delay between card plays based on battle phase"""
        phase = self.get_battle_phase()

        if phase == "early":
            return random.uniform(1.5, 2.5)
        elif phase == "single":
            return random.uniform(1.0, 2.0)
        elif phase == "double":
            return random.uniform(0.8, 1.5)
        else:  # triple
            return random.uniform(0.5, 1.2)

    def reset(self):
        """Reset the strategy for a new battle"""
        self.start_time = None
        self.last_three_cards.clear()
