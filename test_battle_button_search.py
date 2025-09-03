"""
Test script to verify the new battle button search functionality
"""

import time
from unittest.mock import Mock, MagicMock
from battle_runner import BattleRunner


def test_battle_button_continuous_search():
    """Test the continuous clicking behavior when searching for battle button"""
    print("Testing continuous battle button search functionality...")
    
    # Create mock bot
    mock_bot = Mock()
    mock_bot.running = True
    mock_bot.instance_name = "test_instance"
    mock_bot.take_screenshot.return_value = "mock_screenshot"
    mock_bot.find_template.return_value = (None, 0.5)  # Simulate button not found initially
    mock_bot.tap_screen.return_value = True
    
    # Create mock logger
    mock_logger = Mock()
    mock_bot.logger = mock_logger
    
    # Create mock shutdown check
    shutdown_check = Mock(return_value=False)
    
    # Create battle runner
    battle_runner = BattleRunner(mock_bot, shutdown_check)
    
    # Test scenario: simulate finding battle button after a few clicks
    call_count = 0
    def mock_find_template(template_name, screenshot=None):
        nonlocal call_count
        call_count += 1
        if template_name == "ok_button":
            return ((100, 200), 0.9)  # OK button found
        elif template_name == "battle_button":
            if call_count > 3:  # Found after 3 attempts
                return ((540, 1200), 0.85)  # Battle button found
            else:
                return (None, 0.5)  # Not found initially
        return (None, 0.0)
    
    mock_bot.find_template.side_effect = mock_find_template
    
    # Test the handle battle end function
    print("Simulating post-battle sequence...")
    result = battle_runner._handle_battle_end()
    
    print(f"Result: {result}")
    print(f"Number of template search calls: {call_count}")
    print(f"Number of screen taps: {mock_bot.tap_screen.call_count}")
    
    # Verify behavior
    assert result == True, "Battle end handling should succeed"
    assert call_count > 3, "Should have made multiple template search attempts"
    assert mock_bot.tap_screen.call_count > 2, "Should have clicked screen multiple times"
    
    print("✓ Test passed: Continuous clicking behavior works correctly")


def test_start_first_battle_continuous_search():
    """Test the continuous clicking behavior when starting first battle"""
    print("\nTesting start first battle continuous search...")
    
    # Create mock bot
    mock_bot = Mock()
    mock_bot.running = True
    mock_bot.instance_name = "test_instance"
    mock_bot.take_screenshot.return_value = "mock_screenshot"
    mock_bot.tap_screen.return_value = True
    
    # Create mock logger
    mock_logger = Mock()
    mock_bot.logger = mock_logger
    
    # Import and test the EmulatorBot start_first_battle method
    from emulator_bot import EmulatorBot
    
    # Create a partial mock of EmulatorBot
    emulator_bot = EmulatorBot.__new__(EmulatorBot)
    emulator_bot.running = True
    emulator_bot.logger = mock_logger
    emulator_bot.take_screenshot = Mock(return_value="mock_screenshot")
    emulator_bot.tap_screen = Mock(return_value=True)
    
    # Test scenario: simulate finding battle button after a few clicks
    call_count = 0
    def mock_find_template(template_name, screenshot=None):
        nonlocal call_count
        call_count += 1
        if call_count > 2:  # Found after 2 attempts
            return ((540, 1200), 0.85)  # Battle button found
        else:
            return (None, 0.5)  # Not found initially
    
    emulator_bot.find_template = Mock(side_effect=mock_find_template)
    
    # Test the start_first_battle function
    print("Simulating first battle start...")
    result = emulator_bot.start_first_battle()
    
    print(f"Result: {result}")
    print(f"Number of template search calls: {call_count}")
    print(f"Number of screen taps: {emulator_bot.tap_screen.call_count}")
    
    # Verify behavior
    assert result == True, "Start first battle should succeed"
    assert call_count > 2, "Should have made multiple template search attempts"
    assert emulator_bot.tap_screen.call_count > 1, "Should have clicked screen multiple times"
    
    print("✓ Test passed: Start first battle continuous clicking works correctly")


if __name__ == "__main__":
    try:
        test_battle_button_continuous_search()
        test_start_first_battle_continuous_search()
        print("\n🎉 All tests passed! The implementation is working correctly.")
        print("\nKey improvements implemented:")
        print("1. When clicking OK to return to home screen, the bot now searches for the battle button")
        print("2. If battle button is not found, it clicks the screen every second to refresh")
        print("3. This continues for up to 30 seconds before falling back to a default position")
        print("4. The same behavior is applied when starting the first battle")
        print("5. All clicking includes proper 1-second intervals as requested")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
