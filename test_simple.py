#!/usr/bin/env python3
"""
Simple test to verify the console display works
"""

import time
from logger import Logger

def test_basic_functionality():
    """Test basic console display functionality"""
    print("Testing console display...")
    
    # Create a logger with console display enabled
    logger = Logger("TEST_BOT", use_console_display=True)
    
    # Test basic logging
    logger.change_status("Initializing...")
    time.sleep(1)
    
    logger.change_status("Starting battle...")
    time.sleep(1)
    
    # Test stats updates
    logger.add_win()
    logger.add_card_played()
    logger.add_card_played()
    logger.add_card_played()
    
    logger.change_status("Battle complete!")
    time.sleep(1)
    
    # Cleanup
    logger.log_summary()
    
    print("Basic test completed!")

if __name__ == "__main__":
    test_basic_functionality()
