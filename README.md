# 🎮 Clash Royale Multi-Bot Controller

**Clash Royale Multi-Bot Controller** is an advanced automation tool that allows you to automate your Clash Royale gameplay on Windows using multiple MEmu emulator instances. The bot uses sophisticated image recognition, strategic battle AI, and emulator control to perform comprehensive automation.

_Refactored with PyClashBot architecture patterns for enhanced performance and reliability._

## 🎁 Battlepass Claiming Mode (Auto Rewards)

The bot can automatically claim Battle Pass rewards using fast template matching.

Quick start:
```cmd
python run.py --battlepass
```
Or via legacy entry:
```cmd
python main.py --battlepass
```
GUI: launch with `python run.py --gui`, pick "Battlepass Mode - Automatically claim battlepass rewards", then Start.

How it works:
1. Repeatedly clicks at (114, 271) to advance the pass track
2. Detects `ClaimRewards.png` template
3. On detection: clicks button, waits 2s, resumes searching
4. Stops when no new rewards show within timeout

Defaults:
- Max initial search clicks: 100
- Wait between progression clicks: 0.1s (0.5s while waiting for next reward)
- Next reward timeout: 15s
- Template: `templates/ClaimRewards.png` (ensure present)

Logging shows each claim count and confidence. Sequence ends cleanly when finished.

Legacy cleanup: Deprecated duplicate files (battle_runner_new.py, emulator_bot_new.py) and standalone test scripts have been removed to reduce noise. Use the canonical modules and pytest `tests/` for validation.

## ✨ Key Features

### 🏗️ **Modern Architecture**
- **Modular Design**: Clean separation of concerns with dedicated modules
- **Multi-Emulator Support**: Abstract emulator interface supporting MEmu (easily extensible)
- **Strategic Battle AI**: PyClashBot-inspired battle strategy with phase-based elixir management
- **Smart Card Selection**: Intelligent card selection avoiding recently played cards
- **Comprehensive Logging**: Professional statistics tracking and error handling

### 🎯 **Battle Intelligence** 
- **Battle Phase System**: Early/Single/Double/Triple elixir phases with different strategies
- **Dynamic Elixir Management**: Smart elixir threshold adjustment based on battle progression
- **Strategic Positioning**: Intelligent card placement favoring bridges and strategic positions
- **Adaptive Timing**: Phase-based card play delays for optimal performance

### 🔧 **Automation Features**
- **Multi-Instance Support**: Run multiple bots simultaneously across MEmu instances
- **Battle Automation**: Automated 1v1 battles with sophisticated strategy
- **Card Upgrades**: Automatic card upgrade sequence
- **Template Matching**: Robust image recognition with fallback mechanisms
- **Recovery Systems**: Automatic app restart and error recovery

### 🖥️ **User Interface**
- **GUI Mode**: Easy-to-use graphical interface (recommended)
- **CLI Mode**: Command-line interface for advanced users
- **Real-time Statistics**: Live battle statistics and performance metrics
- **Status Monitoring**: Detailed logging and status updates

## 🚀 Setup Instructions

### Prerequisites
1. **MEmu Emulator**: Download and install [MEmu 9.2.5.0](https://www.memuplay.com/)
2. **Python 3.8+**: Install from [python.org](https://python.org)
3. **ADB Tools**: Ensure ADB is in your system PATH

### Installation
1. **Clone/Download** this repository
2. **Install dependencies**:
   ```bash
   pip install opencv-python numpy
   ```
3. **Setup MEmu**:
   - Create MEmu instances and install Clash Royale
   - Complete the tutorial manually
   - Ensure Clash Royale is set to English language

### Template Images
Ensure all template images are present in the `templates/` folder:
- `Battle.png`, `OK.png`, `PlayAgain.png`, `InBattle.png`
- `upgrade_possible.png`, `upgrade_button.png`, `Confirm.png`
- `2xElixir.png`
- `ClaimRewards.png` (for battlepass mode)

## 🎯 Usage

### GUI Mode (Recommended)
```bash
python run.py --gui
```
- User-friendly interface
- Real-time status updates
- Easy mode switching
- Instance management

### CLI Mode
```bash
# Battle mode
python run.py

# Upgrade mode  
python run.py --upgrade

# Battlepass mode
python run.py --battlepass

# Show help
python run.py --help
```

## 🏗️ Architecture Overview

```
pyCRBot/
├── emulators/          # Emulator controllers
│   ├── base.py         # Abstract emulator interface
│   └── memu.py         # MEmu implementation
├── battle_strategy.py  # Strategic battle AI
├── battle_logic.py     # Game mechanics detection
├── battle_runner.py    # Main battle loop coordination
├── detection.py        # Image recognition utilities
├── emulator_bot.py     # Main bot class
├── logger.py           # Statistics and logging
├── config.py           # Configuration constants
├── gui.py              # GUI interface
├── main.py             # CLI interface
└── run.py              # Enhanced entry point
```

### Key Components

**🤖 EmulatorBot**: Main bot instance with emulator abstraction
```python
bot = EmulatorBot(device_id, instance_name)
bot.play_card_strategically()  # Uses battle strategy
```

**⚔️ BattleStrategy**: Sophisticated battle intelligence
```python
strategy = BattleStrategy()
strategy.start_battle()
elixir_target = strategy.select_elixir_amount()  # Phase-based
card_index = strategy.select_card_index(available_cards)  # Smart selection
```

**📊 Logger**: Comprehensive statistics tracking
```python
logger = Logger(instance_name)
logger.add_win()  # Track wins/losses
logger.add_card_played()  # Track performance
logger.log_summary()  # Session statistics
```

**🔍 Detection**: Multi-method image recognition
```python
detector = ImageDetector(instance_name)
position, confidence = detector.find_template("battle_button")
```

## 📊 Battle Strategy Details

### Phase-Based Elixir Management
- **Early (0-7s)**: Conservative play, wait for higher elixir
- **Single (7-90s)**: Balanced elixir distribution  
- **Double (90-200s)**: Favor 7-8 elixir plays
- **Triple (200s+)**: Aggressive 7-8 elixir, avoid 9

### Smart Card Selection
- Avoids recently played cards (tracks last 3)
- Falls back to least recent if all cards were played
- Ensures varied gameplay patterns

### Strategic Positioning
- Bridge plays for aggressive pushes
- Defensive positioning in early game
- Full area utilization in late game

## 🔧 Configuration

Edit `config.py` to customize:
```python
# Timing adjustments
CARD_SELECTION_DELAY = 0.15
INACTIVITY_TIMEOUT = 30

# Battle areas
PLAY_AREA = {"min_x": 57, "max_x": 360, "min_y": 416, "max_y": 472}

# Template confidence
CONFIDENCE_THRESHOLD = 0.8
```

## 📈 Statistics Tracking

The bot tracks comprehensive statistics:
- **Battle Stats**: Wins, losses, win rate, cards played
- **Performance**: Runtime, failures, restarts
- **Collection**: Chests opened, cards upgraded

## ⚠️ Troubleshooting

### Common Issues
1. **No instances detected**: Ensure MEmu is running and ADB is working
2. **Template not found**: Check template images exist and are correct
3. **Bot stuck**: Restart app recovery should handle most issues
4. **Poor performance**: Adjust `CONFIDENCE_THRESHOLD` in config

### Debug Mode
Enable detailed logging by modifying logger verbosity in code.

## 🤝 Contributing

Contributions welcome! The modular architecture makes it easy to:
- Add new emulator support (extend `BaseEmulatorController`)
- Enhance battle strategies (modify `BattleStrategy`)
- Improve detection methods (extend `ImageDetector`)

## ⚠️ Disclaimer

This tool is for educational purposes. Ensure compliance with Clash Royale's Terms of Service. The developers are not responsible for any consequences from using this software.

---

**Enhanced with PyClashBot architecture patterns for superior performance and reliability**

_Automate your Clash Royale experience with intelligence and strategy!_
