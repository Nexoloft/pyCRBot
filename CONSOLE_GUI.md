# Console GUI Feature

The pyCRBot now includes a clean console GUI that replaces the chaotic flood of log messages with a organized dashboard view.

## Features

- **Real-time Status Display**: See the current status of all emulators at a glance
- **Statistics Tracking**: View battles, wins/losses, cards played, and restarts for each emulator
- **Clean Interface**: No more console flooding - only the latest status is shown
- **Runtime Tracking**: See how long each emulator has been running
- **Final Summary**: Get a comprehensive summary when shutting down

## How to Use

### GUI Mode (Default)
```bash
python main.py
```

The console will clear and show a dashboard like this:
```
==================================================================================================
🤖 Clash Royale Multi-Bot Dashboard - 12:34:56
==================================================================================================
✅ MEmu_1     | Runtime: 00:15:23 | Battles: 12  | W/L: 8/4 (66.7%) | Cards: 156  | Restarts: 1
   In battle #13 - playing cards...

⚔️ MEmu_2     | Runtime: 00:15:20 | Battles: 11  | W/L: 7/4 (63.6%) | Cards: 142  | Restarts: 0
   Waiting for matchmaking...

🔄 MEmu_3     | Runtime: 00:15:18 | Battles: 10  | W/L: 6/4 (60.0%) | Cards: 128  | Restarts: 2
   Restarting Clash Royale app...

==================================================================================================
Press Ctrl+C to stop all bots
==================================================================================================
```

### Classic Mode (No GUI)
```bash
python main.py --no-gui
```

This will use the traditional text logging format if you prefer the old style or need to debug issues.

## Status Icons

- ✅ Normal operation
- ⚔️ Currently in battle
- ⏳ Waiting/idle
- 🔄 Restarting app
- ❌ Error state
- 🔴 Stopped/offline

## Demo

To see the console GUI in action without running actual bots:
```bash
python demo_gui.py
```

This will simulate 3 emulators running battles to demonstrate the interface.
