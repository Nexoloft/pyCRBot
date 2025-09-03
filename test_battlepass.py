#!/usr/bin/env python3
"""
Simple test script to debug the battlepass claiming issue
"""

from emulator_bot import EmulatorBot

def test_single_bot():
    """Test a single bot to see what's happening"""
    print("Testing single bot battlepass claiming...")
    
    # Create a single bot instance
    bot = EmulatorBot("127.0.0.1:21523", "TestBot")
    
    try:
        print(f"Bot running state: {bot.running}")
        print("Starting battlepass claiming...")
        
        # Run the battlepass claiming
        result = bot.auto_claim_battlepass()
        
        print(f"Battlepass claiming finished. Result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bot.stop()

if __name__ == "__main__":
    test_single_bot()
