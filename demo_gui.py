#!/usr/bin/env python3
"""
Demo of the new console GUI system
"""

import time
import threading
from console_display import console_display
from logger import Logger

def demo_emulator(name, battle_count=3):
    """Simulate an emulator running battles"""
    logger = Logger(name, use_console_display=True)
    
    logger.change_status("Starting up...")
    time.sleep(2)
    
    for battle in range(battle_count):
        logger.change_status(f"Searching for battle {battle + 1}...")
        time.sleep(1)
        
        logger.change_status(f"In battle {battle + 1}")
        
        # Simulate battle activity
        for i in range(10):
            logger.log(f"Playing card {i + 1}")
            logger.add_card_played()
            time.sleep(0.5)
        
        # Random win/loss
        import random
        if random.choice([True, False]):
            logger.add_win()
            logger.change_status("Victory!")
        else:
            logger.add_loss()
            logger.change_status("Defeat...")
        
        time.sleep(1)
    
    logger.change_status("Session complete")
    logger.log_summary()

def main():
    """Demo the console display with multiple emulators"""
    print("🤖 pyCRBot Console GUI Demo")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Start console display
    console_display.start_display()
    
    # Create threads for multiple emulators
    threads = []
    emulator_names = ["MEmu_1", "MEmu_2", "MEmu_3"]
    
    for name in emulator_names:
        thread = threading.Thread(target=demo_emulator, args=(name, 3))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Stop display and show final summary
    console_display.stop_display()
    console_display.print_final_summary()

if __name__ == "__main__":
    main()
