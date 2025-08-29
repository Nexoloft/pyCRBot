import random
import time
import subprocess
import cv2
import os
from concurrent.futures import ThreadPoolExecutor
import signal

# MEmu emulator default ports (can be configured)
MEMU_PORTS = [21503, 21513, 21521, 21523, 21531, 21533, 21541, 21543, 21551, 21553]  # Supports up to 10 MEmu instances

# Card coordinates
CARD_SLOTS = [
    (141, 537),   # Card 1
    (209, 537),   # Card 2
    (277, 537),   # Card 3
    (342, 537)    # Card 4
]

# Play area coordinates
PLAY_AREA = {
    "min_x": 57,
    "max_x": 360,
    "min_y": 416,
    "max_y": 472
}

# Reference images
REF_IMAGES = {
    "ok_button": "templates/OK.png",
    "battle_button": "templates/Battle.png",
    "in_battle": "templates/InBattle.png",
    "play_again": "templates/PlayAgain.png"
}

# Confidence threshold for image matching
CONFIDENCE_THRESHOLD = 0.8

# Timeout for inactivity (30 seconds)
INACTIVITY_TIMEOUT = 30

# Global variable to handle graceful shutdown
shutdown_requested = False

class EmulatorBot:
    """Bot instance for a single emulator"""
    def __init__(self, device_id, instance_name):
        self.device_id = device_id
        self.instance_name = instance_name
        self.screenshots_dir = f"screenshots_{instance_name}"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.running = True

    def restart_app(self):
        """Restart Clash Royale app on this emulator instance"""
        try:
            print(f"[{self.instance_name}] Restarting Clash Royale app...")
            # Force stop the app
            subprocess.run(f"adb -s {self.device_id} shell am force-stop com.supercell.clashroyale", shell=True, capture_output=True)
            time.sleep(2)
            # Start the app
            subprocess.run(f"adb -s {self.device_id} shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp", shell=True, capture_output=True)
            print(f"[{self.instance_name}] App restarted, waiting for battle to start...")
            
            # Wait for battle detection with fallback mechanism after restart
            restart_time = time.time()
            fallback_triggered = False
            
            while time.time() - restart_time < 20:  # Max 20 seconds wait after restart
                if shutdown_requested or not self.running:
                    return False
                    
                if self.is_in_battle():
                    print(f"[{self.instance_name}] ✓ Battle detected after app restart!")
                    return True
                
                # Check if 10 seconds have passed and we haven't triggered fallback yet
                if time.time() - restart_time >= 10 and not fallback_triggered:
                    print(f"[{self.instance_name}] No battle detected 10 seconds after restart, trying fallback clicks...")
                    if self.fallback_click_sequence():
                        return True  # Battle found after fallback
                    fallback_triggered = True
                
                time.sleep(1)
            
            return True
        except Exception as e:
            print(f"[{self.instance_name}] Error restarting app: {e}")
            return False

    def take_screenshot(self):
        """Take screenshot via ADB and load it into memory for this emulator instance"""
        try:
            screenshot_path = os.path.join(self.screenshots_dir, "screenshot.png")
            
            # Remove old screenshot file if it exists to ensure fresh capture
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            # Capture screenshot with specific device
            result = subprocess.run(f"adb -s {self.device_id} shell screencap /sdcard/screenshot.png", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[{self.instance_name}] Failed to capture screenshot: {result.stderr}")
                return None
                
            # Small delay to ensure screenshot is ready on device
            time.sleep(0.05)
                
            # Download screenshot with specific device
            result = subprocess.run(f"adb -s {self.device_id} pull /sdcard/screenshot.png {screenshot_path}", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[{self.instance_name}] Failed to download screenshot: {result.stderr}")
                return None
                
            # Load image
            if not os.path.exists(screenshot_path):
                print(f"[{self.instance_name}] Screenshot file not found after download")
                return None
                
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                print(f"[{self.instance_name}] Failed to load screenshot image")
                return None
                
            return screenshot
        except Exception as e:
            print(f"[{self.instance_name}] Error taking screenshot: {e}")
            return None

    def find_template(self, template_name, screenshot=None, confidence=CONFIDENCE_THRESHOLD):
        """Find a template image within a screenshot"""
        if screenshot is None:
            screenshot = self.take_screenshot()
            if screenshot is None:
                return None, None
        
        # Load template image
        template_path = REF_IMAGES[template_name]
        if not os.path.exists(template_path):
            print(f"[{self.instance_name}] Template image not found: {template_path}")
            return None, None
            
        template = cv2.imread(template_path)
        if template is None:
            print(f"[{self.instance_name}] Failed to load template: {template_path}")
            return None, None
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Check if match is above confidence threshold
        if max_val >= confidence:
            # Calculate center of matched area
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y), max_val
        else:
            return None, max_val

    def tap_screen(self, x, y):
        """Send a tap command to this emulator via ADB"""
        try:
            result = subprocess.run(f'adb -s {self.device_id} shell input tap {x} {y}', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"[{self.instance_name}] Failed to tap screen at ({x}, {y}): {result.stderr}")
                return False
        except Exception as e:
            print(f"[{self.instance_name}] Error tapping screen: {e}")
            return False

    def play_card(self):
        """Select and place a random card (only if in battle)"""
        # First check if we're still in battle
        if not self.is_in_battle():
            return False
        
        # Select a random card
        card_pos = random.choice(CARD_SLOTS)
        
        if not self.tap_screen(card_pos[0], card_pos[1]):
            return False
        
        time.sleep(0.1)
        
        # Generate a random position within the play area
        place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
        place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
        
        if not self.tap_screen(place_x, place_y):
            return False
        
        return True

    def wait_for_battle_end(self):
        """Wait until battle end screen is detected by looking for PlayAgain or OK button"""
        print(f"[{self.instance_name}] Waiting for battle to end...")
        start_time = time.time()
        
        while time.time() - start_time < 120:  # Max 2 minutes wait
            if shutdown_requested or not self.running:
                return False
            
            # First check for PlayAgain button
            play_again_position, play_again_confidence = self.find_template("play_again")
            if play_again_position:
                print(f"[{self.instance_name}] Battle end detected (PlayAgain button found) with confidence: {play_again_confidence:.2f}")
                print(f"[{self.instance_name}] Clicking PlayAgain button...")
                self.tap_screen(play_again_position[0], play_again_position[1])
                return True
                
            # Then check for OK button as fallback
            ok_position, ok_confidence = self.find_template("ok_button")
            if ok_position:
                print(f"[{self.instance_name}] Battle end detected (OK button found) with confidence: {ok_confidence:.2f}")
                return True
            
            # Wait before checking again
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout waiting for battle to end")
        return False

    def handle_post_battle(self):
        """Handle the post-battle sequence using image recognition"""
        print(f"[{self.instance_name}] Handling post-battle sequence...")
        
        # First check if PlayAgain button is still visible and click it
        play_again_position, play_again_confidence = self.find_template("play_again")
        if play_again_position:
            print(f"[{self.instance_name}] Clicking PlayAgain button (confidence: {play_again_confidence:.2f})")
            self.tap_screen(play_again_position[0], play_again_position[1])
            time.sleep(1.5)  # Wait for transition
        else:
            # If no PlayAgain button, look for OK button
            ok_position, ok_confidence = self.find_template("ok_button")
            if ok_position:
                print(f"[{self.instance_name}] Clicking OK button (confidence: {ok_confidence:.2f})")
                self.tap_screen(ok_position[0], ok_position[1])
                time.sleep(1.5)  # Wait for transition
            else:
                print(f"[{self.instance_name}] Neither PlayAgain nor OK button found, trying fallback position")
                self.tap_screen(540, 1100)  # Fallback OK position
                time.sleep(1.5)
        
        # Wait a moment and look for Battle button
        time.sleep(1)
        
        # Click Battle button
        battle_position, battle_confidence = self.find_template("battle_button")
        if battle_position:
            print(f"[{self.instance_name}] Clicking Battle button (confidence: {battle_confidence:.2f})")
            self.tap_screen(battle_position[0], battle_position[1])
            return True
        else:
            print(f"[{self.instance_name}] Battle button not found")
            return False

    def start_first_battle(self):
        """Click battle button to start the first battle from home page"""
        print(f"[{self.instance_name}] Looking for Battle button to start first battle...")
        
        # Look for battle button for up to 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            if shutdown_requested or not self.running:
                return False
                
            battle_position, confidence = self.find_template("battle_button")
            if battle_position:
                print(f"[{self.instance_name}] Found Battle button (confidence: {confidence:.2f}), clicking to start battle...")
                self.tap_screen(battle_position[0], battle_position[1])
                return True
            
            print(f"[{self.instance_name}] Battle button not found, waiting...")
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout: Could not find Battle button on home page")
        return False

    def check_pixel_color(self, x, y, expected_color=(255, 255, 255), tolerance=30):
        """Check if pixel at (x, y) matches expected color within tolerance"""
        screenshot = self.take_screenshot()
        if screenshot is None:
            return False
        
        # Get screenshot dimensions
        height, width = screenshot.shape[:2]
        
        # Check if coordinates are within bounds
        if y >= height or x >= width:
            print(f"[{self.instance_name}] Pixel coordinates ({x}, {y}) out of bounds for screenshot size ({width}x{height})")
            return False
        
        # Get pixel color (BGR format in OpenCV)
        pixel_bgr = screenshot[y, x]
        pixel_rgb = (int(pixel_bgr[2]), int(pixel_bgr[1]), int(pixel_bgr[0]))  # Convert BGR to RGB as integers
        
        # Check if pixel is within tolerance of expected color
        for i in range(3):
            diff = abs(pixel_rgb[i] - expected_color[i])
            if diff > tolerance:
                return False
        
        return True

    def is_in_battle(self):
        """Check if we're in battle by looking for InBattle.png template"""
        position, confidence = self.find_template("in_battle")
        if position:
            print(f"[{self.instance_name}] In battle detected (confidence: {confidence:.2f})")
            return True
        return False

    def fallback_click_sequence(self):
        """Click at (96, 1316) five times with 3-second intervals as fallback, then check for battle"""
        print(f"[{self.instance_name}] Performing fallback click sequence at (96, 1316)...")
        for i in range(5):
            if shutdown_requested or not self.running:
                return False
            print(f"[{self.instance_name}] Fallback click {i+1}/5")
            self.tap_screen(96, 1316)
            if i < 4:  # Don't wait after the last click
                time.sleep(3)
        
        # After completing fallback clicks, wait and check for battle
        print(f"[{self.instance_name}] Fallback clicks completed, checking for battle...")
        fallback_check_start = time.time()
        
        while time.time() - fallback_check_start < 10:  # Check for 10 seconds after fallback
            if shutdown_requested or not self.running:
                return False
                
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle detected after fallback clicks!")
                return True
            
            time.sleep(1)
        
        print(f"[{self.instance_name}] No battle detected after fallback clicks")
        return False

    def wait_for_battle_start(self):
        """Wait for battle to start by detecting InBattle.png template"""
        print(f"[{self.instance_name}] Waiting for battle to start (looking for InBattle.png)...")
        start_time = time.time()
        fallback_triggered = False
        
        while time.time() - start_time < 30:  # Max 30 seconds wait
            if shutdown_requested or not self.running:
                return False
                
            if self.is_in_battle():
                print(f"[{self.instance_name}] ✓ Battle started! InBattle.png detected")
                return True
            
            # Check if 10 seconds have passed and we haven't triggered fallback yet
            if time.time() - start_time >= 10 and not fallback_triggered:
                print(f"[{self.instance_name}] No battle detected after 10 seconds, trying fallback clicks...")
                if self.fallback_click_sequence():
                    return True  # Battle found after fallback
                fallback_triggered = True
            else:
                print(f"[{self.instance_name}] InBattle.png not found yet, waiting...")
            
            # Wait before checking again
            time.sleep(1)
        
        print(f"[{self.instance_name}] Timeout waiting for battle to start")
        return False

    def run_bot_loop(self):
        """Main bot loop for this emulator instance"""
        print(f"[{self.instance_name}] Starting bot loop...")
        game_round = 1
        first_battle = True
        
        try:
            while self.running and not shutdown_requested:
                print(f"[{self.instance_name}] --- Starting round {game_round} ---")
                last_activity_time = time.time()
                
                # For the first battle, start from home page
                if first_battle:
                    if not self.start_first_battle():
                        print(f"[{self.instance_name}] Failed to start first battle from home page")
                        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                            print(f"[{self.instance_name}] No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                            self.restart_app()
                            last_activity_time = time.time()
                            continue
                        break
                    first_battle = False
                    last_activity_time = time.time()
                
                # Wait for battle to actually start (elixir bar appears)
                if not self.wait_for_battle_start():
                    print(f"[{self.instance_name}] Battle didn't start properly, trying to recover...")
                    if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                        print(f"[{self.instance_name}] No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        self.restart_app()
                        last_activity_time = time.time()
                        first_battle = True
                        continue
                    # Try clicking battle button as fallback
                    self.tap_screen(540, 1200)  # Battle button approximate position
                    time.sleep(1)
                    continue
                
                last_activity_time = time.time()
                
                # Now play cards during battle until OK button appears
                cards_played = 0
                print(f"[{self.instance_name}] Playing cards until battle ends...")
                battle_start_time = time.time()
                
                while self.running and not shutdown_requested:
                    # Check if PlayAgain button is visible (battle ended) - priority check
                    play_again_position, play_again_confidence = self.find_template("play_again")
                    if play_again_position:
                        print(f"[{self.instance_name}] Battle ended! PlayAgain button detected (confidence: {play_again_confidence:.2f})")
                        print(f"[{self.instance_name}] Clicking PlayAgain button...")
                        self.tap_screen(play_again_position[0], play_again_position[1])
                        last_activity_time = time.time()
                        break
                    
                    # Check if OK button is visible (battle ended) - fallback check
                    ok_position, ok_confidence = self.find_template("ok_button")
                    if ok_position:
                        print(f"[{self.instance_name}] Battle ended! OK button detected (confidence: {ok_confidence:.2f})")
                        last_activity_time = time.time()
                        break
                    
                    # Check if we're still in battle using pixel detection
                    if not self.is_in_battle():
                        print(f"[{self.instance_name}] Battle ended - white pixel no longer detected")
                        last_activity_time = time.time()
                        break
                    
                    # Check for inactivity timeout during battle
                    if time.time() - battle_start_time > INACTIVITY_TIMEOUT:
                        print(f"[{self.instance_name}] Battle seems stuck for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        self.restart_app()
                        last_activity_time = time.time()
                        first_battle = True
                        break
                    
                    if self.play_card():
                        cards_played += 1
                        print(f"[{self.instance_name}] Successfully played card {cards_played}")
                        last_activity_time = time.time()
                        battle_start_time = time.time()  # Reset battle timer on successful card play
                        delay = random.uniform(0.2, 0.5)
                        time.sleep(delay)
                    else:
                        print(f"[{self.instance_name}] Failed to play card, continuing...")
                        time.sleep(0.5)  # Short delay before trying again
                
                if shutdown_requested or not self.running:
                    break
                
                print(f"[{self.instance_name}] Finished battle after playing {cards_played} cards")
                
                # Wait for battle to end using image recognition
                if self.wait_for_battle_end():
                    # Handle post-battle with image recognition
                    if self.handle_post_battle():
                        print(f"[{self.instance_name}] Successfully handled post-battle sequence")
                    else:
                        print(f"[{self.instance_name}] Failed to handle post-battle, trying fallback...")
                        # Fallback: click approximate positions
                        self.tap_screen(540, 1100)  # OK button approximate position
                        time.sleep(1)
                        self.tap_screen(540, 1200)  # Battle button approximate position
                else:
                    print(f"[{self.instance_name}] Failed to detect battle end, trying to recover...")
                    # Try clicking common positions as fallback
                    self.tap_screen(540, 1100)  # OK button approximate position
                    time.sleep(1)
                    self.tap_screen(540, 1200)  # Battle button approximate position
                
                # Wait for new game to start with fallback mechanism
                print(f"[{self.instance_name}] Waiting for next battle to start...")
                next_battle_start_time = time.time()
                fallback_triggered = False
                
                while time.time() - next_battle_start_time < 20:  # Max 20 seconds wait for next battle
                    if shutdown_requested or not self.running:
                        break
                        
                    if self.is_in_battle():
                        print(f"[{self.instance_name}] ✓ Next battle started!")
                        break
                    
                    # Check if 10 seconds have passed and we haven't triggered fallback yet
                    if time.time() - next_battle_start_time >= 10 and not fallback_triggered:
                        print(f"[{self.instance_name}] No battle detected after 10 seconds, trying fallback clicks...")
                        if self.fallback_click_sequence():
                            break  # Battle found after fallback, exit waiting loop
                        fallback_triggered = True
                    
                    time.sleep(1)
                
                game_round += 1
                
        except Exception as e:
            print(f"[{self.instance_name}] Bot loop error: {e}")
        finally:
            print(f"[{self.instance_name}] Bot loop stopped")

    def stop(self):
        """Stop this bot instance"""
        self.running = False


def detect_memu_instances():
    """Detect running MEmu instances and return their device IDs"""
    try:
        # First check if ADB is available
        result = subprocess.run("adb version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: ADB (Android Debug Bridge) is not installed or not in PATH!")
            print("Please install ADB and add it to your system PATH.")
            print("You can download ADB from: https://developer.android.com/studio/releases/platform-tools")
            return []
        
        available_instances = []
        
        # Check each potential MEmu port
        for i, port in enumerate(MEMU_PORTS):
            device_id = f"127.0.0.1:{port}"
            print(f"Checking for MEmu instance on port {port}...")
            
            # Try to connect to this port
            result = subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                # Verify the device is actually responsive
                test_result = subprocess.run(f"adb -s {device_id} shell echo test", shell=True, capture_output=True, text=True)
                if test_result.returncode == 0 and "test" in test_result.stdout:
                    instance_name = f"MEmu_{i+1}"  # Use sequential numbering
                    available_instances.append((device_id, instance_name))
                    print(f"✓ Found responsive MEmu instance: {instance_name} ({device_id})")
                else:
                    print(f"✗ MEmu instance on port {port} not responsive")
            else:
                print(f"✗ No MEmu instance found on port {port}")
        
        return available_instances
        
    except Exception as e:
        print(f"Error detecting MEmu instances: {e}")
        return []


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\nShutdown signal received. Stopping all bots...")
    shutdown_requested = True


def main():
    """Main function to coordinate multiple emulator bots"""
    global shutdown_requested
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Multi-MEmu Clash Royale Bot")
    print("=" * 40)
    
    # Verify template images exist
    missing_templates = []
    for name, path in REF_IMAGES.items():
        if not os.path.exists(path):
            missing_templates.append(f"{name}: {path}")
    
    if missing_templates:
        print("ERROR: Missing template images:")
        for template in missing_templates:
            print(f"  - {template}")
        print("\nPlease ensure all template images are in the correct location.")
        return
    
    # Detect available MEmu instances
    instances = detect_memu_instances()
    if not instances:
        print("No MEmu instances found. Please start MEmu and try again.")
        return
    
    print(f"\nFound {len(instances)} MEmu instance(s). Starting bots...")
    
    # Create bot instances
    bots = []
    for device_id, instance_name in instances:
        bot = EmulatorBot(device_id, instance_name)
        bots.append(bot)
    
    # Start bot threads
    with ThreadPoolExecutor(max_workers=len(bots)) as executor:
        try:
            # Submit bot tasks
            futures = [executor.submit(bot.run_bot_loop) for bot in bots]
            
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


if __name__ == "__main__":
    main()
