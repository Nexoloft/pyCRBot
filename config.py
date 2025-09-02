"""
Configuration file for Clash Royale Bot
Contains all constants, coordinates, and settings
"""

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
    "play_again": "templates/PlayAgain.png",
    "upgrade_possible": "templates/upgrade_possible.png",
    "upgrade_button": "templates/upgrade_button.png",
    "confirm": "templates/Confirm.png",
    "2xElixir": "templates/2xElixir.png"
}

# Confidence threshold for image matching
CONFIDENCE_THRESHOLD = 0.8

# Timeout for inactivity (30 seconds)
INACTIVITY_TIMEOUT = 30

# Timing delays
CARD_SELECTION_DELAY = 0.15
CARD_COMBO_DELAY = 0.4
SCREENSHOT_DELAY = 0.05
ELIXIR_CHECK_INTERVAL = 2
DOUBLE_ELIXIR_CHECK_INTERVAL = 3

# Fallback positions for different situations
FALLBACK_POSITIONS = {
    "battle_start": (96, 1316),
    "deadspace": (20, 200),
    "battle_button": (540, 1200)
}

# Elixir detection coordinates
ELIXIR_COORDS = [
    [149, 613],  # 1 elixir
    [175, 613],  # 2 elixir  
    [200, 613],  # 3 elixir
    [223, 613],  # 4 elixir
    [249, 613],  # 5 elixir
    [274, 613],  # 6 elixir
    [299, 613],  # 7 elixir
    [323, 613],  # 8 elixir
    [347, 613],  # 9 elixir
    [371, 613],  # 10 elixir
]

# Purple color variants for elixir detection
PURPLE_COLORS = [
    [240, 137, 244],  # Primary purple
    [232, 63, 242],   # Alternative purple (from PyClashBot)
    [231, 57, 242],   # Another variant
]

# Battle detection pixel coordinates and colors
BATTLE_PIXELS_1V1 = {
    "pixels": [
        [49, 515],   # Battle UI elements
        [77, 518],
        [52, 530],
        [77, 530],
        [115, 618],  # Purple elixir area
    ],
    "colors": [
        [255, 255, 255],
        [255, 255, 255], 
        [255, 255, 255],
        [255, 255, 255],
        [232, 63, 242],
    ]
}

BATTLE_PIXELS_2V2 = {
    "pixels": [
        [53, 515],
        [80, 518], 
        [52, 531],
        [76, 514],
        [114, 615],
    ],
    "colors": [
        [255, 255, 255],
        [255, 255, 255],
        [255, 255, 255], 
        [255, 255, 255],
        [231, 57, 242],
    ]
}

# Post-battle button detection pixels
POST_BATTLE_PIXELS = {
    "pixels": [
        [178, 545],
        [239, 547], 
        [214, 553],
        [201, 554],
    ],
    "colors": [
        [255, 187, 104],
        [255, 187, 104],
        [255, 255, 255],
        [255, 255, 255],
    ]
}

# Fallback positions
FALLBACK_POSITIONS = {
    "ok_button": (540, 1100),
    "battle_button": (540, 1200),
    "post_battle_button": (200, 550),
    "deadspace": (20, 200),
    "fallback_click": (96, 1316),
    "card_scroll": (20, 254)
}

# Color tolerance for pixel matching
COLOR_TOLERANCE = 25
ELIXIR_COLOR_TOLERANCE = 35

# Timing constants
CARD_SELECTION_DELAY = 0.15
CARD_COMBO_DELAY = 0.4
BATTLE_CHECK_INTERVAL = 0.5
ELIXIR_CHECK_INTERVAL = 2.0
DOUBLE_ELIXIR_CHECK_INTERVAL = 3.0
SCREENSHOT_DELAY = 0.05
