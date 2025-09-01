# Multi-MEmu Clash Royale Bot

A modular Python bot for automating Clash Royale gameplay across multiple MEmu emulator instances.

## Project Structure

The bot has been refactored into multiple organized modules:

```
MultiEmu/
├── main.py              # Main entry point and coordination
├── config.py            # Configuration constants and settings
├── emulator_bot.py      # Main EmulatorBot class
├── battle_logic.py      # Battle-specific game logic
├── battle_runner.py     # Battle loop coordination
├── detection.py         # Image detection utilities
├── emulator_utils.py    # MEmu detection and ADB utilities
├── requirements.txt     # Dependencies documentation
├── README.md           # This file
├── templates/          # Template images for detection
│   ├── Battle.png
│   ├── InBattle.png
│   ├── OK.png
│   ├── PlayAgain.png
│   ├── 2xElixir.png
│   ├── upgrade_possible.png
│   ├── upgrade_button.png
│   ├── Confirm.png
│   └── ElixirBar/      # Elixir detection images
└── screenshots_MEmu_X/ # Screenshot directories (auto-created)
```

## Module Responsibilities

### `main.py`
- Entry point for the application
- Command-line argument handling
- Multi-threading coordination
- Graceful shutdown handling

### `config.py`
- All configuration constants
- Coordinate definitions
- File paths and thresholds
- Timing parameters

### `emulator_bot.py`
- Main `EmulatorBot` class
- ADB communication
- Screenshot capture
- Template matching interface
- High-level bot actions

### `battle_logic.py`
- Battle-specific game mechanics
- Elixir detection
- Card playing logic
- Battle state detection

### `battle_runner.py`
- Battle loop coordination
- Adaptive battle strategy
- Battle phase management
- Recovery mechanisms

### `detection.py`
- Image detection utilities
- Template matching algorithms
- Pixel-based detection
- Debug utilities

### `emulator_utils.py`
- MEmu instance detection
- ADB connection management
- Device communication utilities

## Usage

### Battle Mode (Default)
```bash
python main.py
```

### Card Upgrade Mode
```bash
python main.py --upgrade
# or
python main.py -u
```

### Help
```bash
python main.py --help
```

## Dependencies

Install required dependencies:
```bash
pip install opencv-python numpy
```

## Features

- **Multi-emulator support**: Run bots on multiple MEmu instances simultaneously
- **Adaptive battle strategy**: Intelligent card playing based on elixir and battle phase
- **Robust detection**: Multiple detection methods for reliable gameplay
- **Auto-upgrade**: Automatic card upgrade functionality
- **Graceful shutdown**: Clean exit with Ctrl+C
- **Modular architecture**: Easy to maintain and extend

## Configuration

All bot settings can be modified in `config.py`:
- MEmu port numbers
- Card positions
- Play area coordinates
- Detection thresholds
- Timing parameters

## Requirements

- Windows with MEmu emulator
- ADB (Android Debug Bridge) installed and in PATH
- Python 3.6+
- OpenCV and NumPy libraries
- Template images in the `templates/` folder

## Getting Started

1. Install MEmu emulator and start your instances
2. Install Python dependencies: `pip install opencv-python numpy`
3. Ensure ADB is installed and accessible
4. Place template images in the `templates/` folder
5. Run the bot: `python main.py`

## Benefits of Modular Structure

- **Maintainability**: Easy to find and fix issues
- **Extensibility**: Simple to add new features
- **Testing**: Individual modules can be tested separately
- **Readability**: Clear separation of concerns
- **Reusability**: Components can be reused in other projects
