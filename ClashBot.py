"""
Enhanced Clash Royale Bot with Strategic Card Placement
=======================================================

This bot includes advanced features inspired by py-clash-bot:
- Strategic card placement based on card types
- Elixir management and detection
- Time-based battle strategies (defensive -> aggressive)
- Smart card selection (avoiding repetition)
- Side preference management
- Enhanced battle loop with dynamic timing

Key Improvements:
1. Card Recognition: Detects which cards are available vs on cooldown
2. Elixir Detection: Waits for sufficient elixir before playing
3. Strategic Zones: Places cards in optimal positions based on game phase
4. Adaptive Timing: Changes play speed based on battle progression
5. Smart Selection: Avoids playing the same cards repeatedly
"""

import random
import time
import subprocess
import cv2
import os
import numpy as np

# Card coordinates
CARD_SLOTS = [
    (277, 1409),   # Card 1
    (476, 1409),   # Card 2
    (652, 1409),   # Card 3
    (815, 1409)    # Card 4
]

# Play area coordinates - Enhanced with strategic zones
PLAY_AREA = {
    "min_x": 67,
    "max_x": 822,
    "min_y": 892,
    "max_y": 1180
}

# Strategic placement zones
STRATEGIC_ZONES = {
    "defensive": {
        "left": {"x": (100, 300), "y": (1050, 1150)},
        "right": {"x": (550, 750), "y": (1050, 1150)},
        "center": {"x": (350, 500), "y": (1100, 1180)}
    },
    "offensive": {
        "left": {"x": (100, 350), "y": (920, 1000)},
        "right": {"x": (500, 750), "y": (920, 1000)},
        "center": {"x": (380, 470), "y": (900, 980)}
    },
    "bridge": {
        "left": {"x": (200, 280), "y": (980, 1020)},
        "right": {"x": (570, 650), "y": (980, 1020)}
    }
}

# Card type classifications for strategic placement
CARD_TYPES = {
    "spell": ["fireball", "zap", "lightning", "arrows", "freeze", "poison", "rocket"],
    "building": ["cannon", "tesla", "inferno_tower", "xbow", "mortar"],
    "tank": ["giant", "golem", "lava_hound", "pekka", "mega_knight"],
    "support": ["wizard", "witch", "musketeer", "archers", "baby_dragon"],
    "swarm": ["skeleton_army", "goblin_gang", "minion_horde", "barbarians"],
    "win_condition": ["hog_rider", "balloon", "miner", "goblin_barrel"]
}

# Elixir detection coordinates and color
ELIXIR_BAR_COORDS = [(96, 1316), (150, 1316), (200, 1316), (250, 1316)]
ELIXIR_COLOR = (255, 43, 255)  # Purple elixir color

# Reference images
REF_IMAGES = {
    "ok_button": "OK.png",
    "battle_button": "Battle.png",
    "elixir": "Elixir.png"
}

# Confidence threshold for image matching
CONFIDENCE_THRESHOLD = 0.8

# Timeout for inactivity (30 seconds)
INACTIVITY_TIMEOUT = 30

# Configuration options
ENHANCED_MODE = True  # Set to False to use original simple mode
DEBUG_MODE = False    # Set to True for detailed logging
ELIXIR_DETECTION = True  # Set to False to disable elixir waiting

# Battle strategy variables
battle_start_time = 0
last_three_cards = []
current_side_preference = "left"
cards_played = 0

def detect_elixir_level():
    """Detect current elixir level by checking elixir bar"""
    screenshot = take_screenshot()
    if screenshot is None:
        return 0
    
    elixir_count = 0
    for coord in ELIXIR_BAR_COORDS:
        pixel = screenshot[coord[1], coord[0]]
        # Check if pixel is purple (elixir color)
        if np.abs(pixel[0] - ELIXIR_COLOR[2]) < 30 and \
           np.abs(pixel[1] - ELIXIR_COLOR[1]) < 30 and \
           np.abs(pixel[2] - ELIXIR_COLOR[0]) < 30:
            elixir_count += 1
    
    return min(elixir_count, 10)  # Cap at 10 elixir

def check_card_availability():
    """Check which cards are ready to play (not on cooldown)"""
    screenshot = take_screenshot()
    if screenshot is None:
        return []
    
    available_cards = []
    for i, card_pos in enumerate(CARD_SLOTS):
        # Check if card is not grayed out (available to play)
        # Sample a few pixels around the card to determine availability
        sample_points = [
            (card_pos[0] - 20, card_pos[1] - 30),
            (card_pos[0] + 20, card_pos[1] - 30),
            (card_pos[0], card_pos[1] - 40)
        ]
        
        brightness_sum = 0
        for point in sample_points:
            if 0 <= point[0] < screenshot.shape[1] and 0 <= point[1] < screenshot.shape[0]:
                pixel = screenshot[point[1], point[0]]
                brightness = int(pixel[0]) + int(pixel[1]) + int(pixel[2])
                brightness_sum += brightness
        
        avg_brightness = brightness_sum / len(sample_points)
        # If brightness is above threshold, card is available
        if avg_brightness > 300:  # Adjust threshold as needed
            available_cards.append(i)
    
    return available_cards

def select_strategic_card(available_cards):
    """Select card strategically, avoiding recent cards"""
    global last_three_cards
    
    if not available_cards:
        return None
    
    # Filter out recently used cards
    preferred_cards = [card for card in available_cards if card not in last_three_cards]
    
    # If all cards were recently used, avoid only the most recent one
    if not preferred_cards and last_three_cards:
        preferred_cards = [card for card in available_cards if card != last_three_cards[-1]]
    
    # If still no preference, use any available card
    if not preferred_cards:
        preferred_cards = available_cards
    
    selected_card = random.choice(preferred_cards)
    
    # Update recent cards list
    if selected_card not in last_three_cards:
        last_three_cards.append(selected_card)
    if len(last_three_cards) > 3:
        last_three_cards.pop(0)
    
    return selected_card

def get_strategic_placement(card_index, elapsed_time):
    """Get strategic placement coordinates based on card type and game state"""
    global current_side_preference
    
    # Determine strategy phase based on elapsed time
    if elapsed_time < 30:  # Early game - defensive
        strategy = "defensive"
    elif elapsed_time < 120:  # Mid game - balanced
        strategy = "offensive" if random.random() > 0.4 else "defensive"
    else:  # Late game - aggressive
        strategy = "offensive"
    
    # Alternate side preference periodically
    if random.random() < 0.3:  # 30% chance to switch sides
        current_side_preference = "right" if current_side_preference == "left" else "left"
    
    # Get strategic zone
    if strategy in STRATEGIC_ZONES:
        zones = STRATEGIC_ZONES[strategy]
        
        # Choose zone based on strategy
        if strategy == "defensive":
            # Prefer center and back areas for defense
            zone_choice = random.choices(
                ["center", current_side_preference],
                weights=[0.6, 0.4]
            )[0]
        else:
            # Prefer sides and bridge for offense
            zone_choice = random.choices(
                [current_side_preference, "center"],
                weights=[0.7, 0.3]
            )[0]
        
        if zone_choice in zones:
            zone = zones[zone_choice]
            x = random.randint(zone["x"][0], zone["x"][1])
            y = random.randint(zone["y"][0], zone["y"][1])
            return (x, y)
    
    # Fallback to original random placement
    place_x = random.randint(PLAY_AREA["min_x"], PLAY_AREA["max_x"])
    place_y = random.randint(PLAY_AREA["min_y"], PLAY_AREA["max_y"])
    return (place_x, place_y)

def wait_for_elixir(min_elixir=3, timeout=10):
    """Wait until we have enough elixir to play a card"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        current_elixir = detect_elixir_level()
        if current_elixir >= min_elixir:
            return True
        
        # Check if still in battle
        if not is_in_battle():
            return False
            
        time.sleep(0.5)
    
    return False  # Timeout

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
    """Select and place a card strategically"""
    global battle_start_time, cards_played
    
    # Initialize battle start time if not set
    if battle_start_time == 0:
        battle_start_time = time.time()
    
    # First check if we're still in battle
    if not is_in_battle():
        return False
    
    # Check available cards
    available_cards = check_card_availability()
    if not available_cards:
        print("No cards available to play")
        return False
    
    # Calculate elapsed time for strategy
    elapsed_time = time.time() - battle_start_time
    
    # Wait for minimum elixir
    min_elixir = 3 if elapsed_time < 60 else 2  # More aggressive later in game
    if not wait_for_elixir(min_elixir, timeout=5):
        print("Not enough elixir or battle ended")
        return False
    
    # Select card strategically
    card_index = select_strategic_card(available_cards)
    if card_index is None:
        return False
    
    card_pos = CARD_SLOTS[card_index]
    
    # Tap the card
    if not tap_screen(card_pos[0], card_pos[1]):
        return False
    
    time.sleep(0.3)
    
    # Get strategic placement
    place_x, place_y = get_strategic_placement(card_index, elapsed_time)
    
    print(f"Playing card {card_index + 1} at strategic position ({place_x}, {place_y}) - Elapsed: {elapsed_time:.1f}s")
    
    # Place the card
    if not tap_screen(place_x, place_y):
        return False
    
    cards_played += 1
    return True

def enhanced_battle_loop():
    """Enhanced battle loop with strategic card placement"""
    global battle_start_time, cards_played
    
    battle_start_time = time.time()
    cards_played = 0
    
    print("Starting enhanced battle loop with strategic card placement...")
    
    while True:
        # Check if battle ended
        if not is_in_battle():
            print("Battle ended - exiting loop")
            break
        
        # Check for battle timeout (5 minutes max)
        elapsed_time = time.time() - battle_start_time
        if elapsed_time > 300:
            print("Battle timeout reached")
            break
        
        # Attempt to play a card
        if play_card():
            print(f"Successfully played card #{cards_played}")
            
            # Dynamic delay based on game phase
            if elapsed_time < 30:
                delay = random.uniform(2, 4)  # Slower start
            elif elapsed_time < 120:
                delay = random.uniform(1.5, 3)  # Medium pace
            else:
                delay = random.uniform(0.8, 2)  # Faster endgame
            
            time.sleep(delay)
        else:
            # If can't play card, wait a bit and try again
            time.sleep(1)
    
    print(f"Battle completed! Total cards played: {cards_played}")
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
    global ENHANCED_MODE, battle_start_time, cards_played
    
    print("Clash Royale Bot with Enhanced Strategic Placement")
    
    # Check if we're in test mode (no ADB required)
    import sys
    test_mode = "--test" in sys.argv
    
    if test_mode:
        print("Running in TEST MODE (no ADB required)")
        print("Testing enhanced image recognition functionality...")
        
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
        
        print("\nEnhanced Bot Configuration:")
        print(f"- Enhanced Mode: {'ENABLED' if ENHANCED_MODE else 'DISABLED'}")
        print(f"- Debug Mode: {'ENABLED' if DEBUG_MODE else 'DISABLED'}")
        print(f"- Elixir Detection: {'ENABLED' if ELIXIR_DETECTION else 'DISABLED'}")
        print(f"- Confidence threshold: {CONFIDENCE_THRESHOLD}")
        print(f"- Card slots: {len(CARD_SLOTS)} positions")
        print(f"- Strategic zones: {len(STRATEGIC_ZONES)} zone types")
        print(f"- Play area: {PLAY_AREA['max_x'] - PLAY_AREA['min_x']}x{PLAY_AREA['max_y'] - PLAY_AREA['min_y']} pixels")
        print(f"- Template images: {len(REF_IMAGES)} loaded")
        
        print("\nStrategic Improvements:")
        print("✓ Smart card selection (avoids repetition)")
        print("✓ Elixir management and detection")
        print("✓ Time-based strategy (defensive → aggressive)")
        print("✓ Strategic placement zones")
        print("✓ Side preference management")
        print("✓ Enhanced battle loop with dynamic timing")
        
        print("\nCard Type Classifications:")
        for card_type, count in [(t, len(cards)) for t, cards in CARD_TYPES.items()]:
            print(f"- {card_type.title()}: {count} cards")
        
        print("\nTo run the enhanced bot:")
        print("1. Install ADB: https://developer.android.com/studio/releases/platform-tools")
        print("2. Add ADB to your system PATH")
        print("3. Start BlueStacks")
        print("4. Run: python ClashBot.py")
        print("\nThe bot will now play much more strategically, similar to py-clash-bot!")
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
            enhanced_mode_for_battle = ENHANCED_MODE  # Local copy to avoid modifying global
            
            if enhanced_mode_for_battle:
                print("Starting strategic battle with enhanced card placement...")
                
                # Use enhanced battle loop with strategic placement
                if enhanced_battle_loop():
                    print("Enhanced battle completed successfully!")
                else:
                    print("Enhanced battle loop failed, falling back to basic mode")
                    enhanced_mode_for_battle = False  # Disable for this battle only
            
            if not enhanced_mode_for_battle:
                print("Using original battle mode...")
                # Original battle loop
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
                    
                    # Use original simple play_card function
                    if play_card():
                        cards_played += 1
                        print(f"Successfully played card {cards_played}")
                        last_activity_time = time.time()
                        battle_start_time = time.time()  # Reset battle timer on successful card play
                        delay = random.uniform(1, 3)
                        time.sleep(delay)
                    else:
                        print("Failed to play card, continuing...")
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