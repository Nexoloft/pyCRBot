import random
import time
import subprocess
import cv2
import os

# Card coordinates
CARD_SLOTS = [
    (277, 1409),   # Card 1
    (476, 1409),   # Card 2
    (652, 1409),   # Card 3
    (815, 1409)    # Card 4
]

# Play area coordinates
PLAY_AREA = {
    "min_x": 67,
    "max_x": 822,
    "min_y": 892,
    "max_y": 1180
}

# Reference images
REF_IMAGES = {
    "ok_button": "templates/OK.png",
    "battle_button": "templates/Battle.png",
    "elixir": "Elixir.png"
}

# Confidence threshold for image matching
CONFIDENCE_THRESHOLD = 0.8

# Timeout for inactivity (30 seconds)
INACTIVITY_TIMEOUT = 30

def restart_app():
    """Restart Clash Royale app"""
    try:
        print("Restarting Clash Royale app...")
        # Force stop the app
        subprocess.run("adb -s 127.0.0.1:5555 shell am force-stop com.supercell.clashroyale", shell=True, capture_output=True)
        time.sleep(2)
        # Start the app
        subprocess.run("adb -s 127.0.0.1:5555 shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp", shell=True, capture_output=True)
        print("App restarted, waiting 10 seconds for it to load...")
        time.sleep(10)
        return True
    except Exception as e:
        print(f"Error restarting app: {e}")
        return False

def connect_bluestacks():
    """Connect to BlueStacks via ADB"""
    try:
        # First check if ADB is available
        result = subprocess.run("adb version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: ADB (Android Debug Bridge) is not installed or not in PATH!")
            print("Please install ADB and add it to your system PATH.")
            print("You can download ADB from: https://developer.android.com/studio/releases/platform-tools")
            return False
        
        # Check current devices and disconnect any that aren't BlueStacks
        print("Checking for existing ADB connections...")
        devices_result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
        if devices_result.returncode == 0:
            lines = devices_result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip() and not line.startswith("127.0.0.1:5555"):
                    device = line.split()[0]
                    print(f"Disconnecting device: {device}")
                    subprocess.run(f"adb disconnect {device}", shell=True, capture_output=True)
            
        # Connect to BlueStacks
        result = subprocess.run("adb connect 127.0.0.1:5555", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully connected to BlueStacks")
            time.sleep(2)
            return True
        else:
            print(f"Failed to connect to BlueStacks: {result.stderr}")
            print("Make sure BlueStacks is running and ADB is enabled in BlueStacks settings")
            return False
    except Exception as e:
        print(f"Error connecting to BlueStacks: {e}")
        return False

def take_screenshot():
    """Take screenshot via ADB and load it into memory"""
    try:
        import time
        
        # Remove old screenshot file if it exists to ensure fresh capture
        if os.path.exists("screenshot.png"):
            os.remove("screenshot.png")
        if os.path.exists("screenshot.pn"):  # Windows ADB filename issue
            os.remove("screenshot.pn")
        
        # Capture screenshot with specific device (without -p flag to avoid Windows issues)
        result = subprocess.run("adb -s 127.0.0.1:5555 shell screencap /sdcard/screenshot.png", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to capture screenshot: {result.stderr}")
            return None
            
        # Small delay to ensure screenshot is ready on device
        time.sleep(0.1)
            
        # Download screenshot with specific device
        result = subprocess.run("adb -s 127.0.0.1:5555 pull /sdcard/screenshot.png .", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to download screenshot: {result.stderr}")
            return None
            
        # Load image
        if not os.path.exists("screenshot.png"):
            # Check if file exists with different name (Windows ADB issue)
            if os.path.exists("screenshot.pn"):
                os.rename("screenshot.pn", "screenshot.png")
            else:
                print("Screenshot file not found after download")
                return None
            
        screenshot = cv2.imread("screenshot.png")
        if screenshot is None:
            print("Failed to load screenshot image")
            return None
            
        return screenshot
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

def find_template(template_name, screenshot=None, confidence=CONFIDENCE_THRESHOLD):
    """Find a template image within a screenshot"""
    if screenshot is None:
        screenshot = take_screenshot()
        if screenshot is None:
            return None, None
    
    # Load template image
    template_path = REF_IMAGES[template_name]
    if not os.path.exists(template_path):
        print(f"Template image not found: {template_path}")
        return None, None
        
    template = cv2.imread(template_path)
    if template is None:
        print(f"Failed to load template: {template_path}")
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

def tap_screen(x, y):
    """Send a tap command to BlueStacks via ADB"""
    try:
        result = subprocess.run(f'adb -s 127.0.0.1:5555 shell input tap {x} {y}', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"Failed to tap screen at ({x}, {y}): {result.stderr}")
            return False
    except Exception as e:
        print(f"Error tapping screen: {e}")
        return False

def play_card():
    """Select and place a random card (only if in battle)"""
    # First check if we're still in battle using pixel detection
    if not is_in_battle():
        return False
    
    # Select a random card
    card_pos = random.choice(CARD_SLOTS)
    
    if not tap_screen(card_pos[0], card_pos[1]):
        return False
    
    time.sleep(0.3)
    
    # Generate a random position within the play area
    place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
    place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
    
    if not tap_screen(place_x, place_y):
        return False
    
    return True

def wait_for_battle_end():
    """Wait until battle end screen is detected by looking for OK button"""
    print("Waiting for battle to end...")
    start_time = time.time()
    
    while time.time() - start_time < 120:  # Max 2 minutes wait
        position, confidence = find_template("ok_button")
        if position:
            print(f"Battle end detected (OK button found) with confidence: {confidence:.2f}")
            return True
        
        # Wait before checking again
        time.sleep(2)
    
    print("Timeout waiting for battle to end")
    return False

def handle_post_battle():
    """Handle the post-battle sequence using image recognition"""
    print("Handling post-battle sequence...")
    
    # Click OK button
    ok_position, confidence = find_template("ok_button")
    if ok_position:
        print(f"Clicking OK button (confidence: {confidence:.2f})")
        tap_screen(ok_position[0], ok_position[1])
        time.sleep(3)  # Wait for transition
    else:
        print("OK button not found, trying fallback position")
        tap_screen(540, 1100)  # Fallback OK position
        time.sleep(3)
    
    # Wait a moment and look for Battle button
    time.sleep(2)
    
    # Click Battle button
    battle_position, confidence = find_template("battle_button")
    if battle_position:
        print(f"Clicking Battle button (confidence: {confidence:.2f})")
        tap_screen(battle_position[0], battle_position[1])
        return True
    else:
        print("Battle button not found")
        return False

def check_connection():
    """Check if BlueStacks is connected via ADB"""
    try:
        result = subprocess.run('adb -s 127.0.0.1:5555 devices', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return b"127.0.0.1:5555" in result.stdout.encode()
        else:
            return False
    except Exception:
        return False

def start_first_battle():
    """Click battle button to start the first battle from home page"""
    print("Looking for Battle button to start first battle...")
    
    # Look for battle button for up to 30 seconds
    start_time = time.time()
    while time.time() - start_time < 30:
        battle_position, confidence = find_template("battle_button")
        if battle_position:
            print(f"Found Battle button (confidence: {confidence:.2f}), clicking to start battle...")
            tap_screen(battle_position[0], battle_position[1])
            return True
        
        print("Battle button not found, waiting...")
        time.sleep(2)
    
    print("Timeout: Could not find Battle button on home page")
    return False

def check_pixel_color(x, y, expected_color=(255, 255, 255), tolerance=30):
    """Check if pixel at (x, y) matches expected color within tolerance"""
    screenshot = take_screenshot()
    if screenshot is None:
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

def is_in_battle():
    """Check if we're in battle by looking for white pixel at (96, 1316)"""
    return check_pixel_color(96, 1316, (255, 255, 255), tolerance=50)

def wait_for_battle_start():
    """Wait for battle to start by detecting white pixel at (96, 1316)"""
    print("Waiting for battle to start (looking for white pixel at 96, 1316)...")
    start_time = time.time()
    
    while time.time() - start_time < 30:  # Max 30 seconds wait
        if is_in_battle():
            print("✓ Battle started! White pixel detected at (96, 1316)")
            return True
        else:
            print("White pixel not found yet, waiting...")
        
        # Wait before checking again
        time.sleep(2)
    
    print("Timeout waiting for battle to start")
    return False

def main():
    print("Clash Royale Bot with Image Recognition")
    
    # Check if we're in test mode (no ADB required)
    import sys
    test_mode = "--test" in sys.argv
    
    if test_mode:
        print("Running in TEST MODE (no ADB required)")
        print("Testing image recognition functionality...")
        
        # Test if template images exist
        for name, path in REF_IMAGES.items():
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    print(f"✓ {name}: {path} - OK (size: {img.shape})")
                else:
                    print(f"✗ {name}: {path} - Failed to load")
            else:
                print(f"✗ {name}: {path} - File not found")
        
        print("\nConfiguration:")
        print(f"- Confidence threshold: {CONFIDENCE_THRESHOLD}")
        print(f"- Card slots: {len(CARD_SLOTS)} positions")
        print(f"- Play area: {PLAY_AREA['max_x'] - PLAY_AREA['min_x']}x{PLAY_AREA['max_y'] - PLAY_AREA['min_y']} pixels")
        print(f"- Template images: {len(REF_IMAGES)} loaded")
        
        print("\nTo run the full bot:")
        print("1. Install ADB: https://developer.android.com/studio/releases/platform-tools")
        print("2. Add ADB to your system PATH")
        print("3. Start BlueStacks")
        print("4. Run: python ClashBot.py")
        return
    
    if not connect_bluestacks():
        print("Error: Could not connect to BlueStacks")
        print("\nTip: You can run 'python ClashBot.py --test' to test image recognition without ADB")
        return
    
    print("BlueStacks connected! Bot will start in 5 seconds...")
    time.sleep(5)
    
    game_round = 1
    first_battle = True
    
    try:
        while True:
            print(f"\n--- Starting round {game_round} ---")
            last_activity_time = time.time()
            
            # For the first battle, start from home page
            if first_battle:
                if not start_first_battle():
                    print("Failed to start first battle from home page")
                    if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                        print(f"No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                        restart_app()
                        last_activity_time = time.time()
                        continue
                    break
                first_battle = False
                last_activity_time = time.time()
            
            # Wait for battle to actually start (elixir bar appears)
            if not wait_for_battle_start():
                print("Battle didn't start properly, trying to recover...")
                if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                    print(f"No activity for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                    restart_app()
                    last_activity_time = time.time()
                    first_battle = True
                    continue
                # Try clicking battle button as fallback
                tap_screen(540, 1200)  # Battle button approximate position
                time.sleep(3)
                continue
            
            last_activity_time = time.time()
            
            # Now play cards during battle until OK button appears
            cards_played = 0
            print("Playing cards until battle ends...")
            battle_start_time = time.time()
            
            while True:
                # Check if OK button is visible (battle ended)
                ok_position, confidence = find_template("ok_button")
                if ok_position:
                    print(f"Battle ended! OK button detected (confidence: {confidence:.2f})")
                    last_activity_time = time.time()
                    break
                
                # Check if we're still in battle using pixel detection
                if not is_in_battle():
                    print("Battle ended - white pixel no longer detected")
                    last_activity_time = time.time()
                    break
                
                # Check for inactivity timeout during battle
                if time.time() - battle_start_time > INACTIVITY_TIMEOUT:
                    print(f"Battle seems stuck for {INACTIVITY_TIMEOUT} seconds, restarting app...")
                    restart_app()
                    last_activity_time = time.time()
                    first_battle = True
                    break
                
                if play_card():
                    cards_played += 1
                    print(f"Successfully played card {cards_played}")
                    last_activity_time = time.time()
                    battle_start_time = time.time()  # Reset battle timer on successful card play
                    delay = random.uniform(1, 3)
                    time.sleep(delay)
                else:
                    print(f"Failed to play card, continuing...")
                    time.sleep(1)  # Short delay before trying again
            
            print(f"Finished battle after playing {cards_played} cards")
            
            # Wait for battle to end using image recognition
            if wait_for_battle_end():
                # Handle post-battle with image recognition
                if handle_post_battle():
                    print("Successfully handled post-battle sequence")
                else:
                    print("Failed to handle post-battle, trying fallback...")
                    # Fallback: click approximate positions
                    tap_screen(540, 1100)  # OK button approximate position
                    time.sleep(2)
                    tap_screen(540, 1200)  # Battle button approximate position
            else:
                print("Failed to detect battle end, trying to recover...")
                # Try clicking common positions as fallback
                tap_screen(540, 1100)  # OK button approximate position
                time.sleep(2)
                tap_screen(540, 1200)  # Battle button approximate position
            
            # Wait for new game to start
            wait_time = random.randint(10, 15)
            print(f"Waiting {wait_time} seconds for new game...")
            time.sleep(wait_time)
            
            game_round += 1
            
    except KeyboardInterrupt:
        print("\nBot stopped by user")

if __name__ == "__main__":
    main()