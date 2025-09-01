"""
Example usage of the modular bot components
This demonstrates how to use individual components
"""

from emulator_bot import EmulatorBot
from emulator_utils import detect_memu_instances
from config import REF_IMAGES

def example_single_bot():
    """Example of using a single bot instance"""
    print("Detecting MEmu instances...")
    instances = detect_memu_instances()
    
    if not instances:
        print("No MEmu instances found!")
        return
    
    # Use the first available instance
    device_id, instance_name = instances[0]
    print(f"Using instance: {instance_name} ({device_id})")
    
    # Create bot
    bot = EmulatorBot(device_id, instance_name)
    
    # Take a screenshot
    screenshot = bot.take_screenshot()
    if screenshot is not None:
        print("Screenshot captured successfully!")
    
    # Check if in battle
    in_battle = bot.is_in_battle()
    print(f"In battle: {in_battle}")
    
    # Check elixir amount
    elixir = bot.detect_elixir_amount()
    print(f"Current elixir: {elixir}")
    
    # Debug current screen
    bot.debug_current_screen()
    
    # Clean up
    bot.stop()

def example_template_detection():
    """Example of template detection"""
    from detection import ImageDetector
    import cv2
    
    # Create detector
    detector = ImageDetector("test_instance")
    
    # Load a test screenshot (you would get this from bot.take_screenshot())
    # screenshot = cv2.imread("test_screenshot.png")
    
    # Find templates
    # for template_name in REF_IMAGES.keys():
    #     position, confidence = detector.find_template(template_name, screenshot)
    #     if position:
    #         print(f"Found {template_name} at {position} (confidence: {confidence:.2f})")

def example_battle_logic():
    """Example of battle logic usage"""
    from battle_logic import BattleLogic
    from detection import ImageDetector
    
    detector = ImageDetector("test_instance")
    battle_logic = BattleLogic("test_instance", detector)
    
    # Example usage (you would pass actual screenshot)
    # screenshot = some_screenshot
    # elixir = battle_logic.detect_elixir_amount(screenshot)
    # is_2x = battle_logic.detect_2x_elixir(screenshot)
    # in_battle = battle_logic.is_in_battle(screenshot)
    
    print("Battle logic component initialized")

if __name__ == "__main__":
    print("Multi-MEmu Bot - Component Examples")
    print("=" * 40)
    
    print("\n1. Single Bot Example:")
    example_single_bot()
    
    print("\n2. Template Detection Example:")
    example_template_detection()
    
    print("\n3. Battle Logic Example:")
    example_battle_logic()
    
    print("\nFor full bot operation, run: python main.py")
