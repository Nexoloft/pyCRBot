# War Mode Quick Start Guide

## Prerequisites
1. ✅ MEmu emulator running with Clash Royale installed
2. ✅ Already on the **Clan War screen** in the game
3. ✅ Required templates in `templates/` folder:
   - `NormalBattle.png`
   - `SuddenDeath.png`
   - `WarBattle.png`
   - `OK.png`
   - `InBattle.png`

## Quick Start

### Option 1: Using run.py (Recommended)
```bash
# Run war mode on all available MEmu instances
python run.py --war

# Limit to 10 battles
python run.py --war --battles 10
```

### Option 2: Using main.py
```bash
# Run war mode
python main.py --war

# Without GUI console display
python main.py --war --no-gui
```

## What the Bot Does

```
1. Search for war battles (30s timeout)
   ├─ Check for Sudden Death (priority)
   └─ Check for Normal Battle

2. Click the war battle type found

3. Search for War Battle button (120s timeout)
   ├─ Also checks for Sudden Death / Normal Battle
   ├─ Auto-reselects if returned to war selection
   └─ If not found after 120s → STOP

4. Wait for battle to start (60s queue timeout)
   └─ Allows for longer matchmaking in war battles

5. Play the battle
   ├─ Use normal battle AI
   ├─ Strategic card placement
   └─ Elixir management

6. Click OK button after battle

7. Loop back to step 1
```

## Important Notes

### Before Starting
- **Must be on clan war screen** - bot does NOT navigate to war screen
- Ensure no popups are blocking the screen
- Make sure templates match your game graphics

### During Operation
- Bot will search for Sudden Death first (higher priority)
- If Battle button isn't found in 120 seconds, bot stops gracefully
- Each battle uses the same AI as normal battle mode
- Press `Ctrl+C` to stop at any time

### After Battle
- Bot automatically clicks OK to return to war screen
- Loops to find next available war battle
- Stops when no more battles are found or battle limit reached

## Timeouts

| Phase | Timeout | Action if timeout |
|-------|---------|-------------------|
| Find war battle | 30s | Stop bot |
| Find Battle button | 120s | Stop bot |
| Battle start (queue) | 60s | Skip battle, loop back |
| Battle duration | 5 min | End battle |
| Find OK button | 60s | Log warning and continue |

## Troubleshooting

### "No war battles found"
- ✅ Verify you're on the clan war screen
- ✅ Check that `NormalBattle.png` and `SuddenDeath.png` templates exist
- ✅ Ensure templates match your game's current graphics

### "Battle button not found after 120 seconds"
- ✅ Check that `WarBattle.png` template exists and is accurate
- ✅ Close any popups that might be blocking the button
- ✅ Verify screen is on the war battle selection screen

### Bot not playing cards
- ✅ This uses the same battle logic as normal mode
- ✅ Check console logs for elixir detection
- ✅ Verify card coordinates in `config.py`

### Bot stuck after battle
- ✅ Ensure `OK.png` template is accurate
- ✅ Check that post-battle screen shows the OK button
- ✅ Close any reward popups manually if needed

## Example Usage

### Run 5 war battles then stop
```bash
python run.py --war --battles 5
```

### Run war mode on specific emulator
```bash
python run.py --headless --port 21503
# Then manually switch to war mode in code
```

### Run multiple emulators in war mode
```bash
# Start multiple MEmu instances first
# Then run:
python main.py --war
```

## Console Output Example

```
⚔️ WAR MODE: Will play clan wars on 1 MEmu instance(s)
All 1 war bots started! Press Ctrl+C to stop.

[MEmu_1] Starting clan war bot loop...
[MEmu_1] --- War Round 1 (Battle 1) ---
[MEmu_1] Searching for available war battles...
[MEmu_1] Found Sudden Death battle (confidence: 0.87), clicking...
[MEmu_1] War battle selected, searching for Battle button...
[MEmu_1] Found Battle button (confidence: 0.91), clicking to start war battle...
[MEmu_1] War battle started! Playing battle...
[MEmu_1] War Battle - Phase: early, Elapsed: 10.0s, Elixir: 7, 2x: False, Cards: 3
[MEmu_1] War battle completed! Played 28 cards
[MEmu_1] Handling post-war-battle sequence...
[MEmu_1] Found OK button (confidence: 0.89), clicking to return to war screen...
[MEmu_1] ✓ War battle #1 completed successfully!

[MEmu_1] --- War Round 2 (Battle 2) ---
[MEmu_1] Searching for available war battles...
```

## Stop the Bot

Press **Ctrl+C** to gracefully stop:
```
^C
Shutdown signal received. Stopping all bots...
Stopping all war bots...
All war bots stopped. Goodbye!
```

## Tips for Best Results

1. **Template Accuracy**: Make sure your template screenshots match the current game version
2. **Screen Resolution**: Use consistent emulator resolution (419x633 default)
3. **Start Position**: Always start from the clan war screen, not home screen
4. **Monitor First Run**: Watch the first battle to ensure templates are detected correctly
5. **Battle Limits**: Use `--battles` flag to limit automated battles for testing

## Files Modified/Created

- ✅ `war_runner.py` - New war mode logic
- ✅ `config.py` - Added war templates
- ✅ `main.py` - Added war mode support
- ✅ `run.py` - Added --war flag
- ✅ `README.md` - Updated documentation
- ✅ `WAR_MODE.md` - Detailed war mode docs
- ✅ `WAR_QUICKSTART.md` - This quick start guide
