#!/usr/bin/env python3
"""
Test the new console display system
"""

import time
import threading
from console_display import console_display
from logger import Logger

def simulate_emulator(name, duration=30):
    """Simulate an emulator running"""
    logger = Logger(name, use_console_display=True)
    
    for i in range(duration):
        if i % 10 == 0:
            logger.change_status(f"In battle #{i//10 + 1}")
        elif i % 5 == 0:
            logger.add_win()
            logger.change_status("Post-battle sequence")
        else:
            logger.log(f"Playing cards... elixir: {i % 10}")
            logger.add_card_played()
        
        time.sleep(1)
    
    logger.log_summary()

def main():
    """Test the console display with multiple emulators"""
    console_display.start_display()
    
    # Create threads for multiple emulators
    threads = []
    emulator_names = ["MEmu_1", "MEmu_2", "MEmu_3"]
    
    for name in emulator_names:
        thread = threading.Thread(target=simulate_emulator, args=(name, 20))
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
