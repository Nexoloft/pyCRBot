"""
Utility functions for war mode operations
"""

import random


def find_available_war_battles(bot, screenshot):
    """
    Find all available war battle types in the current screenshot.
    
    Args:
        bot: EmulatorBot instance
        screenshot: Current screenshot
    
    Returns:
        list: List of tuples (battle_name, position, confidence)
    """
    battle_types = [
        ('sudden_death', 'Sudden Death'),
        ('rampup', 'RampUp'),
        ('normal_battle', 'Normal Battle'),
        ('touchdown_war', 'Touchdown War'),
        ('2x_war', '2x War'),
        # ('col_war', 'Collection War'),
        ('ragewar', 'Rage War')
    ]
    
    available = []
    for template, name in battle_types:
        pos, conf = bot.find_template(template, screenshot)
        if pos and conf > 0.7:
            available.append((name, pos, conf))
    
    return available


def select_random_battle(available_battles, logger=None):
    """
    Randomly select one battle from available battles.
    
    Args:
        available_battles: List of tuples (battle_name, position, confidence)
        logger: Optional logger instance for logging
    
    Returns:
        tuple: (battle_name, position, confidence) or None if no battles available
    """
    if not available_battles:
        return None
    
    selected = random.choice(available_battles)
    
    if logger:
        battle_names = [b[0] for b in available_battles]
        logger.log(f"Found {len(available_battles)} battle type(s): {battle_names}")
        logger.log(f"Randomly selected: {selected[0]} (confidence: {selected[2]:.2f})")
    
    return selected


def click_battle_if_found(bot, available_battles, logger=None, delay=2.0):
    """
    Select and click a random battle from available battles.
    
    Args:
        bot: EmulatorBot instance
        available_battles: List of tuples (battle_name, position, confidence)
        logger: Optional logger instance for logging
        delay: Delay after clicking in seconds
    
    Returns:
        bool: True if a battle was found and clicked, False otherwise
    """
    selected = select_random_battle(available_battles, logger)
    
    if selected:
        battle_name, battle_pos, battle_confidence = selected
        bot.tap_screen(battle_pos[0], battle_pos[1])
        import time
        time.sleep(delay)
        return True
    
    return False
