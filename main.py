"""
Main entry point for the Multi-MEmu Clash Royale Bot
"""

import os
import sys
import time
import signal
import subprocess
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
    print("  python main.py --battlepass # Run battlepass claiming bot")
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


def run_battlepass_mode(instances):
    """Run the bot in battlepass claiming mode"""
    print(f"\n🎁 BATTLEPASS MODE: Will claim battlepass rewards on {len(instances)} MEmu instance(s)")
    print("Starting battlepass claiming bots...")
    
    # Create bot instances for claiming battlepass
    bots = []
    for device_id, instance_name in instances:
        bot = EmulatorBot(device_id, instance_name)
        bots.append(bot)
    
    # Start battlepass threads
    with ThreadPoolExecutor(max_workers=len(bots)) as executor:
        try:
            # Submit battlepass claiming tasks
            futures = [executor.submit(bot.auto_claim_battlepass) for bot in bots]
            
            print(f"All {len(bots)} battlepass claiming bots started! Press Ctrl+C to stop.")
            
            # Wait for completion or shutdown
            while not shutdown_requested:
                time.sleep(1)
                
                # Check if all futures completed
                completed = [f for f in futures if f.done()]
                if len(completed) == len(futures):
                    print("All battlepass claiming bots completed their tasks.")
                    break
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            # Stop all bots
            print("Stopping all battlepass claiming bots...")
            for bot in bots:
                bot.stop()
            
            # Wait for threads to finish
            print("Waiting for battlepass claiming bots to finish...")
            executor.shutdown(wait=True)
            
            print("All battlepass claiming bots stopped. Goodbye!")


def run_battle_mode(instances, max_battles=0):
    """Run the bot in battle mode"""
    print(f"\n⚔️ BATTLE MODE: Found {len(instances)} MEmu instance(s). Starting battle bots...")
    if max_battles > 0:
        print(f"🎯 Battle limit: {max_battles} per emulator")
    
    # Create bot instances
    bots = []
    battle_runners = []
    for i, instance in enumerate(instances):
        # Handle both old and new instance formats
        if isinstance(instance, dict):
            if 'device_id' in instance and 'instance_name' in instance:
                # New format with proper device_id and instance_name
                device_id = instance['device_id']
                instance_name = instance['instance_name']
            else:
                # Legacy format - convert index/port to proper device_id
                device_id = instance.get('index', i)
                port = instance.get('port', 21503)
                device_id = f"127.0.0.1:{port}"
                instance_name = f"MEmu_{i + 1}"
            bot = EmulatorBot(device_id, instance_name)
        else:
            # Legacy format (device_id, instance_name)
            device_id, instance_name = instance
            bot = EmulatorBot(device_id, instance_name)
        
        runner = BattleRunner(bot, lambda: shutdown_requested, max_battles=max_battles)
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
                    remaining = len(futures) - len(completed)
                    print(f"{len(completed)} bot(s) finished unexpectedly, {remaining} still running")
                    
                    # Only stop all bots if ALL bots have finished unexpectedly
                    if remaining == 0:
                        print("All bots finished unexpectedly, stopping...")
                        break
                    
                    # For partial failures, just report but continue with remaining bots
                    print("Continuing with remaining bots...")
            
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


def main(mode='battle', **kwargs):
    """
    Main function to coordinate multiple emulator bots
    
    Args:
        mode (str): 'gui', 'battle', 'upgrade', 'single', or 'multi'
        **kwargs: Additional parameters (port, num_emulators, max_battles, etc.)
    """
    global shutdown_requested
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Handle GUI mode
    if mode == 'gui':
        try:
            from gui import ClashRoyaleBotGUI
            import tkinter as tk
            root = tk.Tk()
            ClashRoyaleBotGUI()  # GUI manages its own root
            root.mainloop()
            return
        except ImportError as e:
            print(f"GUI not available: {e}")
            print("Install tkinter if needed")
            return
    
    # Handle status check mode
    if mode == 'status':
        print("📱 MEmu Emulator Status Check")
        print("=" * 50)
        
        from config import MEMU_PORTS
        from emulator_utils import test_device_responsiveness
        
        print(f"🔍 Checking {len(MEMU_PORTS)} potential MEmu ports...")
        
        available_count = 0
        for i, port in enumerate(MEMU_PORTS):
            device_id = f"127.0.0.1:{port}"
            instance_name = f"MEmu_{i + 1}"
            
            # Try to connect first
            subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True)
            time.sleep(0.5)
            
            # Test responsiveness
            if test_device_responsiveness(device_id):
                print(f"✅ {instance_name:8} | {device_id:15} | Ready")
                available_count += 1
            else:
                print(f"❌ {instance_name:8} | {device_id:15} | Offline/Not Running")
        
        print(f"\n📊 Summary: {available_count}/{len(MEMU_PORTS)} MEmu instances available")
        
        if available_count == 0:
            print("\n🚨 No MEmu instances found!")
            print("📋 Please start your MEmu emulators and try again.")
        else:
            print(f"\n🚀 You can run up to {available_count} bots simultaneously.")
            print(f"💡 Example: python run.py --multi {min(available_count, 4)}")
        
        return
    
    print("Multi-MEmu Clash Royale Bot")
    print("=" * 40)
    
    # Check for legacy command line arguments if no mode specified
    if mode == 'battle':
        upgrade_mode = "--upgrade" in sys.argv or "-u" in sys.argv
        battlepass_mode = "--battlepass" in sys.argv
        if "--help" in sys.argv or "-h" in sys.argv:
            print_help()
            return
        if battlepass_mode:
            mode = 'battlepass'
        elif upgrade_mode:
            mode = 'upgrade'
        else:
            mode = 'battle'
    
    # Verify template images exist
    if not verify_template_images():
        return
    
    # Handle different modes
    if mode == 'single':
        # Run single emulator
        port = kwargs.get('port', 21503)
        max_battles = kwargs.get('max_battles', 0)
        device_id = f"127.0.0.1:{port}"
        instance_name = "MEmu_1"
        
        # Try to connect to the MEmu instance
        print(f"Connecting to MEmu instance at {device_id}...")
        subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True)
        time.sleep(1)  # Give it a moment to establish connection
        
        # Validate the connection
        from emulator_utils import test_device_responsiveness
        if not test_device_responsiveness(device_id):
            print(f"❌ MEmu instance at {device_id} is offline or not responsive")
            print(f"📋 Please ensure MEmu is running on port {port} and try again")
            return
        
        print(f"✅ {instance_name} ({device_id}) - Connected and responsive")
        instances = [{'device_id': device_id, 'instance_name': instance_name, 'port': port}]
        run_battle_mode(instances, max_battles=max_battles)
        
    elif mode == 'multi':
        # Run multiple emulators
        num_emulators = kwargs.get('num_emulators', 3)
        max_battles = kwargs.get('max_battles', 0)
        
        # Get all connected and responsive devices from adb devices
        print(f"Looking for {num_emulators} available MEmu instance(s)...")
        
        try:
            result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Failed to get ADB devices list")
                return
            
            # Parse connected devices and filter out offline ones
            available_devices = []
            for line in result.stdout.split('\n'):
                if '\tdevice' in line:  # Only devices that are online (not offline)
                    device_id = line.split('\t')[0]
                    if device_id.startswith('127.0.0.1:'):  # MEmu devices
                        available_devices.append(device_id)
            
            if not available_devices:
                print("❌ No online MEmu devices found!")
                print("📋 Please ensure your MEmu emulators are running and try again.")
                return
            
            # Take only the number requested
            selected_devices = available_devices[:num_emulators]
            
            print(f"✅ Found {len(available_devices)} online MEmu device(s)")
            print(f"🚀 Using {len(selected_devices)} emulator(s):")
            
            # Create instances for the selected devices
            valid_instances = []
            for i, device_id in enumerate(selected_devices):
                instance_name = f"MEmu_{i + 1}"
                port = device_id.split(':')[1] if ':' in device_id else '21503'
                valid_instances.append({'device_id': device_id, 'instance_name': instance_name, 'port': port})
                print(f"  • {instance_name} ({device_id})")
                
        except Exception as e:
            print(f"❌ Error getting device list: {e}")
            return
        
        run_battle_mode(valid_instances, max_battles=max_battles)
        
    else:
        # Detect available MEmu instances for battle/upgrade modes
        instances = detect_memu_instances()
        if not instances:
            print("No MEmu instances found. Please start MEmu and try again.")
            return
        
        # Run in appropriate mode
        if mode == 'upgrade':
            run_upgrade_mode(instances)
        elif mode == 'battlepass':
            run_battlepass_mode(instances)
        else:
            run_battle_mode(instances)


if __name__ == "__main__":
    main()
