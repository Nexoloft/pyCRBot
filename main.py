"""
Main entry point for the Multi-MEmu Clash Royale Bot
"""

import os
import sys
import time
import signal
from concurrent.futures import ThreadPoolExecutor

from emulator_bot import EmulatorBot
from battle_runner import BattleRunner
from emulator_utils import detect_memu_instances
from config import REF_IMAGES


# Global variable to handle graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\nShutdown signal received. Stopping all bots...")
    shutdown_requested = True


def verify_template_images():
    """Verify that all required template images exist"""
    missing_templates = []
    for name, path in REF_IMAGES.items():
        if not os.path.exists(path):
            missing_templates.append(f"{name}: {path}")
    
    if missing_templates:
        print("ERROR: Missing template images:")
        for template in missing_templates:
            print(f"  - {template}")
        print("\nPlease ensure all template images are in the correct location.")
        return False
    return True


def print_help():
    """Print help information"""
    print("Usage:")
    print("  python main.py              # Run normal battle bot")
    print("  python main.py --upgrade    # Run card upgrade bot")
    print("  python main.py -u           # Run card upgrade bot (short)")
    print("  python main.py --help       # Show this help")


def run_upgrade_mode(instances):
    """Run the bot in card upgrade mode"""
    print(f"\n🔧 UPGRADE MODE: Will upgrade cards on {len(instances)} MEmu instance(s)")
    print("Starting card upgrade bots...")
    
    # Create bot instances for upgrading
    bots = []
    for device_id, instance_name in instances:
        bot = EmulatorBot(device_id, instance_name)
        bots.append(bot)
    
    # Start upgrade threads
    with ThreadPoolExecutor(max_workers=len(bots)) as executor:
        try:
            # Submit upgrade tasks
            futures = [executor.submit(bot.auto_upgrade_cards) for bot in bots]
            
            print(f"All {len(bots)} upgrade bots started! Press Ctrl+C to stop.")
            
            # Wait for completion or shutdown
            while not shutdown_requested:
                time.sleep(1)
                
                # Check if all futures completed
                completed = [f for f in futures if f.done()]
                if len(completed) == len(futures):
                    print("All upgrade bots completed their tasks.")
                    break
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            # Stop all bots
            print("Stopping all upgrade bots...")
            for bot in bots:
                bot.stop()
            
            # Wait for threads to finish
            print("Waiting for upgrade bots to finish...")
            executor.shutdown(wait=True)
            
            print("All upgrade bots stopped. Goodbye!")


def run_battle_mode(instances):
    """Run the bot in battle mode"""
    print(f"\n⚔️ BATTLE MODE: Found {len(instances)} MEmu instance(s). Starting battle bots...")
    
    # Create bot instances
    bots = []
    battle_runners = []
    for device_id, instance_name in instances:
        bot = EmulatorBot(device_id, instance_name)
        runner = BattleRunner(bot, lambda: shutdown_requested)
        bots.append(bot)
        battle_runners.append(runner)
    
    # Start bot threads
    with ThreadPoolExecutor(max_workers=len(battle_runners)) as executor:
        try:
            # Submit bot tasks
            futures = [executor.submit(runner.run_bot_loop) for runner in battle_runners]
            
            print(f"All {len(bots)} bots started! Press Ctrl+C to stop.")
            
            # Wait for completion or shutdown
            while not shutdown_requested:
                time.sleep(1)
                
                # Check if any futures completed (which shouldn't happen normally)
                completed = [f for f in futures if f.done()]
                if completed:
                    print(f"{len(completed)} bot(s) finished unexpectedly")
                    break
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            # Stop all bots
            print("Stopping all bots...")
            for bot in bots:
                bot.stop()
            
            # Wait for threads to finish
            print("Waiting for bots to finish...")
            executor.shutdown(wait=True)
            
            print("All bots stopped. Goodbye!")


def main():
    """Main function to coordinate multiple emulator bots"""
    global shutdown_requested
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Multi-MEmu Clash Royale Bot")
    print("=" * 40)
    
    # Check for command line arguments
    upgrade_mode = "--upgrade" in sys.argv or "-u" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return
    
    # Verify template images exist
    if not verify_template_images():
        return
    
    # Detect available MEmu instances
    instances = detect_memu_instances()
    if not instances:
        print("No MEmu instances found. Please start MEmu and try again.")
        return
    
    # Run in appropriate mode
    if upgrade_mode:
        run_upgrade_mode(instances)
    else:
        run_battle_mode(instances)


if __name__ == "__main__":
    main()
