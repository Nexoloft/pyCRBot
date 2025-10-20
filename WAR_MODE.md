# Clan War Mode

## Overview
The War mode is designed to automatically play clan war battles in Clash Royale. The bot will continuously search for available war battles (Sudden Death or Normal Battle), click them, wait for the Battle button, play the battle using the normal battle logic, and then click OK to return to the war screen.

## How It Works

### Phase 1: Search for War Battles
The bot searches for available war battles on the clan war screen:
1. **Sudden Death** (checked first, higher priority)
   - Template: `templates/SuddenDeath.png`
   - If found, clicks it immediately
2. **Normal Battle** (checked second)
   - Template: `templates/NormalBattle.png`
   - If found, clicks it

Search timeout: **30 seconds**

### Phase 2: Click Battle Button
After selecting a war battle type, the bot searches for the Battle button:
- Template: `templates/WarBattle.png` (war-specific Battle button)
- Continuously searches and clicks when found
- Timeout: **120 seconds** (2 minutes)
- If not found after timeout, the script stops

### Phase 3: Play Battle
The bot uses the normal battle logic to play cards:
- Detects elixir amount
- Plays cards strategically when elixir >= 6
- Monitors battle status
- Battle timeout: **5 minutes** max

### Phase 4: Post-Battle Cleanup
After the battle ends, the bot:
- Searches for the OK button (`templates/OK.png`)
- Clicks OK to return to the war screen
- Waits 3 seconds for transition
- Loops back to Phase 1 to search for the next war battle

## Usage

### Method 1: Using run.py (Recommended)
```bash
# Run war mode on all available MEmu instances
python run.py --war

# Run with specific number of battles
python run.py --war --battles 5
```

### Method 2: Using main.py
```bash
# Run war mode
python main.py --war

# Run war mode without GUI
python main.py --war --no-gui
```

### Method 3: From Python Code
```python
from main import main

# Run war mode
main('war')

# Run with custom settings
main('war', no_gui=False)
```

## Configuration

### Required Templates
Ensure these template images exist in the `templates/` folder:
- `NormalBattle.png` - Normal war battle button
- `SuddenDeath.png` - Sudden death war battle button
- `WarBattle.png` - War-specific Battle button to start the match
- `OK.png` - OK button after battle ends
- `InBattle.png` - In-battle detection template

### Battle Settings
The war mode uses the same battle configuration as normal battles:
- Card slots: Defined in `config.py`
- Play area: Defined in `config.py`
- Elixir detection: Pixel-based detection
- Battle strategy: Strategic card placement

## Features

✅ **Automatic War Battle Detection**
- Prioritizes Sudden Death battles
- Falls back to Normal Battles
- 30-second search timeout

✅ **Robust Battle Button Search**
- Continuously searches for up to 120 seconds
- Stops gracefully if Battle button isn't found

✅ **Full Battle Logic**
- Uses normal battle AI
- Strategic card placement
- Elixir management
- 2x elixir detection

✅ **Post-Battle Handling**
- Automatically clicks OK button
- Returns to war screen
- Loops to find next battle

✅ **Multi-Emulator Support**
- Run on multiple MEmu instances simultaneously
- Each instance operates independently
- Separate battle counters

## Stopping the Bot

Press `Ctrl+C` to gracefully stop the war bot. The bot will:
1. Stop searching for new battles
2. Complete current battle if in progress
3. Clean up resources
4. Display summary statistics

## Battle Limits

You can set a maximum number of battles per emulator:
```bash
# Stop after 10 war battles
python run.py --war --battles 10
```

Without a limit, the bot will run indefinitely until:
- All war battles are completed
- The script is manually stopped (Ctrl+C)
- An error occurs

## Troubleshooting

### Bot Can't Find War Battles
- Ensure you're on the clan war screen before starting
- Check that `NormalBattle.png` and `SuddenDeath.png` templates exist
- Verify template images match your game's graphics

### Battle Button Not Found
- The bot will wait up to 120 seconds for the Battle button
- If not found, check that `Battle.png` template is accurate
- Ensure no popups are blocking the Battle button

### Bot Stuck After Battle
- Check that `OK.png` template exists and matches your game
- The bot may be waiting for the OK button to appear
- Verify post-battle screen shows the OK button

### Bot Not Playing Cards
- This uses the same battle logic as normal mode
- Check elixir detection is working (logs show elixir level)
- Verify card slot coordinates in `config.py`

## Technical Details

### File Structure
```
war_runner.py        # Main war mode logic
main.py              # Updated with war mode support
config.py            # Updated with new templates
run.py               # Updated with --war flag
templates/
  ├── NormalBattle.png
  ├── SuddenDeath.png
  ├── Battle.png
  └── OK.png
```

### War Runner Class
```python
class WarRunner:
    def run_war_loop(self):
        # Main loop that orchestrates war battles
        
    def _find_and_start_war_battle(self):
        # Phase 1 & 2: Find and start war battle
        
    def _play_war_battle(self):
        # Phase 3: Play the battle
        
    def _handle_war_battle_end(self):
        # Phase 4: Post-battle cleanup
```

## Logs and Monitoring

The war mode provides detailed logging:
- War round number
- Battle count
- Template detection confidence scores
- Battle phase and elapsed time
- Elixir levels
- Cards played count
- Success/failure messages

Example log output:
```
⚔️ WAR MODE: Will play clan wars on 1 MEmu instance(s)
All 1 war bots started! Press Ctrl+C to stop.
[MEmu_1] --- War Round 1 (Battle 1) ---
[MEmu_1] Found Sudden Death battle (confidence: 0.85), clicking...
[MEmu_1] Found Battle button (confidence: 0.92), clicking to start war battle...
[MEmu_1] War battle started! Playing battle...
[MEmu_1] War Battle - Phase: early, Elapsed: 10.0s, Elixir: 8, 2x: False, Cards: 5
[MEmu_1] War battle completed! Played 25 cards
[MEmu_1] Found OK button (confidence: 0.88), clicking to return to war screen...
[MEmu_1] ✓ War battle #1 completed successfully!
```

## Notes

- The bot assumes you're already on the clan war screen
- Sudden Death battles are prioritized over Normal Battles
- Each war battle follows the same AI logic as normal battles
- The bot will continue looping until stopped or all battles are complete
- Multiple emulators can run war mode simultaneously
