# Clash Royale Multi-Bot Controller

A simple and effective automation tool for Clash Royale using MEmu emulators.

## Prerequisites

1.  **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
2.  **MEmu Emulator**: [Download MEmu](https://www.memuplay.com/)
    *   **IMPORTANT**: You must create an emulator instance with the following resolution:
        *   **Width**: 419
        *   **Height**: 633
        *   **DPI**: 160
3.  **ADB**: Ensure ADB is in your system PATH (usually included with MEmu).

## Installation

1.  Clone or download this repository.
2.  Open a terminal in the project folder.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

### Command Line Interface (CLI)

To run the bot on a single emulator (headless mode):
```bash
python run.py --headless
```

To run on multiple emulators (e.g., 3 instances):
```bash
python run.py --multi 3
```

To run the Clan War mode:
```bash
python run.py --war
```

To run the Battle Pass claim mode:
```bash
python run.py --battlepass
```

### Graphical User Interface (GUI)

To use the visual selector for emulators:
```bash
python run.py --gui
```

## Notes

*   Ensure your template images are in the `templates/` folder.
*   The bot will automatically handle game restarts and basic errors.
