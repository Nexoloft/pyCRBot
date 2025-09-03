# 🎁 Battlepass Claiming Mode

## Overview
The new **Battlepass Mode** automatically claims battlepass rewards using template matching and strategic clicking.

## How It Works
1. **Initial Clicking**: Continuously clicks at position `(114, 271)` to progress through the battlepass
2. **Reward Detection**: Monitors for the `ClaimRewards.png` template to appear
3. **Claim Process**: When ClaimRewards button is detected:
   - Clicks the ClaimRewards button
   - Waits 2 seconds 
   - Keeps clicking at `(114, 271)` until another ClaimRewards button appears
   - **15-Second Timeout**: If no new ClaimRewards button is found within 15 seconds, the script ends
4. **Loop**: Repeats this process until timeout or no more rewards are available

## Usage

### Using run.py (Recommended)
```cmd
python run.py --battlepass
```

### Using main.py (Legacy)
```cmd
python main.py --battlepass
```

### Using GUI
1. Launch GUI: `python run.py --gui`
2. Select "Battlepass Mode - Automatically claim battlepass rewards"
3. Click "Start Bot"

## Configuration
- **Click Position**: `(114, 271)` - The main progression area
- **Template**: `ClaimRewards.png` - Must be in `templates/` directory
- **Wait Time**: 2 seconds after claiming each reward
- **Timeout**: 15 seconds maximum waiting for next ClaimRewards button
- **Max Initial Attempts**: 100 clicks maximum before giving up on finding first reward
- **Click Interval**: 0.1 seconds between initial progression clicks, 0.5 seconds when waiting for next reward

## Template Requirements
Make sure you have `templates/ClaimRewards.png` - this should be a screenshot of the claim rewards button that appears when a battlepass reward is ready to claim.

## Features
- **Multi-Instance Support**: Can run on multiple MEmu emulators simultaneously
- **Safe Clicking**: Maximum click attempts to prevent infinite loops
- **Comprehensive Logging**: Detailed status updates and claim counting
- **Thread-Safe**: Runs in separate threads for GUI mode
- **Graceful Shutdown**: Responds to Ctrl+C interruption

## Tips
1. Position your game on the battlepass screen before starting
2. Ensure the ClaimRewards.png template accurately matches your game's claim button
3. The bot will automatically stop when no more rewards are detected
4. Use `--status` to check if your MEmu instances are ready before starting

## Example Output
```
🎁 BATTLEPASS MODE: Will claim battlepass rewards on 1 MEmu instance(s)
Starting battlepass claiming bots...
All 1 battlepass claiming bots started! Press Ctrl+C to stop.

[MEmu_1] Starting automatic battlepass claiming sequence...
[MEmu_1] Clicking at (114, 271) to progress battlepass...
[MEmu_1] Claim #1: Found ClaimRewards button (confidence: 0.95) after 15 clicks
[MEmu_1] Successfully clicked ClaimRewards button
[MEmu_1] Looking for next ClaimRewards button...
[MEmu_1] Found next ClaimRewards button (confidence: 0.92) after 3.2 seconds
[MEmu_1] Claim #2: Found ClaimRewards button (confidence: 0.92) after 8 clicks
[MEmu_1] Successfully clicked ClaimRewards button
[MEmu_1] Looking for next ClaimRewards button...
[MEmu_1] No ClaimRewards button found after 15 seconds timeout
[MEmu_1] Ending battlepass claiming sequence
[MEmu_1] Auto battlepass claiming sequence finished. Total claims: 2
```

## Architecture
The battlepass claiming functionality is implemented in:
- `emulator_bot.py` - Main `auto_claim_battlepass()` method
- `emulator_bot_new.py` - Duplicate implementation for consistency
- `main.py` - `run_battlepass_mode()` function and mode handling
- `run.py` - Command line argument parsing
- `gui.py` - GUI interface integration
