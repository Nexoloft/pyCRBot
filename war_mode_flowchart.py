"""
War Mode - Visual Reference
ASCII flowchart showing the war mode logic flow
"""

# ============================================================================
#                        WAR MODE LOGIC FLOW
# ============================================================================

"""
                    ┌──────────────────────────────┐
                    │   START WAR MODE             │
                    │   (Must be on war screen)    │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  Initialize WarRunner        │
                    │  - Set max_battles           │
                    │  - Battle count = 0          │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────▼────────────────────────────┐
        │                  WAR LOOP START                       │
        │  (while running and not shutdown and not max battles) │
        └──────────────────────────┬────────────────────────────┘
                                   │
        ╔══════════════════════════▼════════════════════════════╗
        ║         PHASE 1: FIND WAR BATTLE (30s timeout)        ║
        ╚══════════════════════════╤════════════════════════════╝
                                   │
                    ┌──────────────▼───────────────┐
                    │  Take screenshot             │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  Search for Sudden Death     │
                    │  Template: SuddenDeath.png   │
                    │  Confidence > 0.7?           │
                    └──────┬───────────────┬───────┘
                           │ Yes           │ No
                    ┌──────▼───────┐      │
                    │ Click it!    │      │
                    │ Found = True │      │
                    └──────┬───────┘      │
                           │              │
                           │      ┌───────▼──────────────────┐
                           │      │ Search for Normal Battle │
                           │      │ Template: NormalBattle.png│
                           │      │ Confidence > 0.7?        │
                           │      └───────┬──────────┬───────┘
                           │              │ Yes      │ No
                           │      ┌───────▼──────┐  │
                           │      │ Click it!    │  │
                           │      │ Found = True │  │
                           │      └───────┬──────┘  │
                           │              │         │
                    ┌──────▼──────────────▼─────────▼──────┐
                    │  War battle found?                   │
                    └──────┬───────────────────────┬───────┘
                      Yes  │                       │ No
                           │               ┌───────▼──────────┐
                           │               │ Timeout (30s)?   │
                           │               └────┬──────┬──────┘
                           │                Yes │      │ No
                           │            ┌───────▼──┐  │
                           │            │ STOP BOT │  │
                           │            └──────────┘  │
                           │                          │
                           │               ┌──────────▼─────┐
                           │               │ Wait 1 second  │
                           │               │ Retry search   │
                           │               └────────────────┘
                           │
        ╔══════════════════▼════════════════════════════════════╗
        ║       PHASE 2: FIND BATTLE BUTTON (120s timeout)      ║
        ╚══════════════════╤════════════════════════════════════╝
                           │
                    ┌──────▼──────────────────┐
                    │  Wait 2 seconds         │
                    │  (Screen transition)    │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Take screenshot        │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Search for Battle      │
                    │  Template: Battle.png   │
                    │  Confidence > 0.7?      │
                    └──────┬──────────┬───────┘
                      Yes  │          │ No
                    ┌──────▼──────┐  │
                    │ Click it!   │  │
                    └──────┬──────┘  │
                           │         │
                           │  ┌──────▼─────────────┐
                           │  │ Elapsed > 120s?    │
                           │  └──────┬──────┬──────┘
                           │    Yes  │      │ No
                           │  ┌──────▼───┐  │
                           │  │ STOP BOT │  │
                           │  └──────────┘  │
                           │                │
                           │     ┌──────────▼──────┐
                           │     │ Wait 1 second   │
                           │     │ Retry search    │
                           │     └─────────────────┘
                           │
        ╔══════════════════▼════════════════════════════════════╗
        ║      PHASE 3: PLAY BATTLE (5 min max timeout)         ║
        ╚══════════════════╤════════════════════════════════════╝
                           │
                    ┌──────▼──────────────────┐
                    │  Wait for battle start  │
                    │  Use fallback if needed │
                    └──────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │         BATTLE LOOP                 │
        │  (while in battle and < 5 minutes)  │
        └──────────────────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Take screenshot        │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Check still in battle? │
                    └──────┬──────────┬───────┘
                      Yes  │          │ No
                           │          │
                           │    ┌─────▼──────────┐
                           │    │ Battle ended   │
                           │    │ Break loop     │
                           │    └────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Detect elixir amount   │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Elixir >= 6?           │
                    └──────┬──────────┬───────┘
                      Yes  │          │ No
                    ┌──────▼──────┐  │
                    │ Play card!  │  │
                    │ strategically│ │
                    └──────┬──────┘  │
                           │         │
                    ┌──────▼─────────▼───────┐
                    │  Wait (strategy delay)  │
                    │  or 0.5s                │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Loop back to top       │
                    │  of battle loop         │
                    └─────────────────────────┘
                           │
        ╔══════════════════▼════════════════════════════════════╗
        ║       PHASE 4: POST-BATTLE CLEANUP (60s timeout)      ║
        ╚══════════════════╤════════════════════════════════════╝
                           │
                    ┌──────▼──────────────────┐
                    │  Take screenshot        │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Search for OK button   │
                    │  Template: OK.png       │
                    │  Confidence > 0.7?      │
                    └──────┬──────────┬───────┘
                      Yes  │          │ No
                    ┌──────▼──────┐  │
                    │ Click OK!   │  │
                    └──────┬──────┘  │
                           │         │
                           │  ┌──────▼─────────────┐
                           │  │ Elapsed > 60s?     │
                           │  └──────┬──────┬──────┘
                           │    Yes  │      │ No
                           │  ┌──────▼───┐  │
                           │  │ Timeout! │  │
                           │  │ Log warn │  │
                           │  └──────┬───┘  │
                           │         │      │
                           │  ┌──────▼──────▼──────┐
                           │  │ Click deadspace    │
                           │  │ Wait 1 second      │
                           │  │ Retry search       │
                           │  └────────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Wait 3 seconds         │
                    │  (Return to war screen) │
                    └──────┬──────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  Increment battle_count │
                    │  Log success            │
                    └──────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────────┐
        │  Check battle limit reached?            │
        │  or shutdown requested?                 │
        └──────┬─────────────────────┬────────────┘
          Yes  │                     │ No
    ┌──────────▼──────┐             │
    │   STOP BOT      │             │
    │   Log summary   │             │
    └─────────────────┘             │
                           ┌────────▼────────┐
                           │  Loop back to   │
                           │  WAR LOOP START │
                           └─────────────────┘
"""

# ============================================================================
#                         TIMEOUT SUMMARY
# ============================================================================

TIMEOUTS = {
    'war_battle_search': 30,      # Phase 1: Finding Sudden Death or Normal Battle
    'battle_button_search': 120,  # Phase 2: Finding Battle button
    'battle_play_max': 300,       # Phase 3: Maximum battle duration (5 minutes)
    'ok_button_search': 60,       # Phase 4: Finding OK button after battle
}

# ============================================================================
#                      TEMPLATE CONFIDENCE THRESHOLDS
# ============================================================================

CONFIDENCE_THRESHOLDS = {
    'sudden_death': 0.7,   # Minimum confidence for Sudden Death detection
    'normal_battle': 0.7,  # Minimum confidence for Normal Battle detection
    'battle_button': 0.7,  # Minimum confidence for Battle button detection
    'ok_button': 0.7,      # Minimum confidence for OK button detection
}

# ============================================================================
#                           PRIORITY ORDER
# ============================================================================

SEARCH_PRIORITY = [
    1,  # Sudden Death (highest priority)
    2,  # Normal Battle (if Sudden Death not found)
]

# ============================================================================
#                         PHASE DESCRIPTIONS
# ============================================================================

PHASES = {
    'phase_1': {
        'name': 'Find War Battle',
        'timeout': 30,
        'templates': ['sudden_death', 'normal_battle'],
        'action': 'Click war battle button',
        'on_success': 'Proceed to Phase 2',
        'on_failure': 'Stop bot',
    },
    'phase_2': {
        'name': 'Find Battle Button',
        'timeout': 120,
        'templates': ['battle_button'],
        'action': 'Click Battle button',
        'on_success': 'Proceed to Phase 3',
        'on_failure': 'Stop bot',
    },
    'phase_3': {
        'name': 'Play Battle',
        'timeout': 300,
        'templates': ['in_battle'],
        'action': 'Play cards strategically',
        'on_success': 'Proceed to Phase 4',
        'on_failure': 'Log error and proceed',
    },
    'phase_4': {
        'name': 'Post-Battle Cleanup',
        'timeout': 60,
        'templates': ['ok_button'],
        'action': 'Click OK button',
        'on_success': 'Loop back to Phase 1',
        'on_failure': 'Log warning and loop back',
    },
}

# ============================================================================
#                      STATE TRANSITIONS
# ============================================================================

"""
States and their transitions:

SEARCHING_WAR_BATTLE
  ├─ Found Sudden Death → CLICKING_WAR_BATTLE
  ├─ Found Normal Battle → CLICKING_WAR_BATTLE
  └─ Timeout (30s) → STOPPED

CLICKING_WAR_BATTLE
  └─ Click successful → SEARCHING_BATTLE_BUTTON

SEARCHING_BATTLE_BUTTON
  ├─ Found Battle → CLICKING_BATTLE_BUTTON
  └─ Timeout (120s) → STOPPED

CLICKING_BATTLE_BUTTON
  └─ Click successful → WAITING_FOR_BATTLE

WAITING_FOR_BATTLE
  ├─ Battle started → PLAYING_BATTLE
  └─ Timeout → RECOVERY_CLICKS

PLAYING_BATTLE
  ├─ Battle ended → SEARCHING_OK_BUTTON
  ├─ Timeout (5 min) → SEARCHING_OK_BUTTON
  └─ Error → SEARCHING_OK_BUTTON

SEARCHING_OK_BUTTON
  ├─ Found OK → CLICKING_OK_BUTTON
  └─ Timeout (60s) → CLICKING_OK_BUTTON (fallback)

CLICKING_OK_BUTTON
  └─ Click successful → WAITING_FOR_WAR_SCREEN

WAITING_FOR_WAR_SCREEN
  └─ 3 seconds elapsed → SEARCHING_WAR_BATTLE (loop)

STOPPED
  └─ END
"""

# ============================================================================
#                          EXAMPLE LOG OUTPUT
# ============================================================================

EXAMPLE_LOG = """
⚔️ WAR MODE: Will play clan wars on 1 MEmu instance(s)
All 1 war bots started! Press Ctrl+C to stop.

[MEmu_1] Starting clan war bot loop...
[MEmu_1] --- War Round 1 (Battle 1) ---
[MEmu_1] Searching for available war battles...
[MEmu_1] Found Sudden Death battle (confidence: 0.87), clicking...
[MEmu_1] War battle selected, searching for Battle button...
[MEmu_1] Looking for Battle button... (5s / 120s)
[MEmu_1] Looking for Battle button... (10s / 120s)
[MEmu_1] Found Battle button (confidence: 0.91), clicking to start war battle...
[MEmu_1] War battle started! Playing battle...
[MEmu_1] War Battle - Phase: early, Elapsed: 10.0s, Elixir: 7, 2x: False, Cards: 3
[MEmu_1] Played card #4 in war battle
[MEmu_1] War Battle - Phase: single, Elapsed: 20.0s, Elixir: 8, 2x: False, Cards: 8
[MEmu_1] Played card #9 in war battle
[MEmu_1] War Battle - Phase: double, Elapsed: 95.0s, Elixir: 9, 2x: True, Cards: 22
[MEmu_1] Played card #23 in war battle
[MEmu_1] War battle completed! Played 28 cards
[MEmu_1] Handling post-war-battle sequence...
[MEmu_1] Found OK button (confidence: 0.89), clicking to return to war screen...
[MEmu_1] ✓ War battle #1 completed successfully!

[MEmu_1] --- War Round 2 (Battle 2) ---
[MEmu_1] Searching for available war battles...
[MEmu_1] Found Normal Battle (confidence: 0.82), clicking...
...
"""

# ============================================================================
#                       DECISION TREE
# ============================================================================

"""
War Mode Decision Tree:

START
│
├─ Is max_battles set and reached?
│  ├─ Yes → STOP
│  └─ No → Continue
│
├─ Is shutdown requested?
│  ├─ Yes → STOP
│  └─ No → Continue
│
├─ Can find war battle (Sudden Death or Normal)?
│  ├─ Yes → Click it
│  │  │
│  │  ├─ Can find Battle button within 120s?
│  │  │  ├─ Yes → Click it
│  │  │  │  │
│  │  │  │  ├─ Did battle start?
│  │  │  │  │  ├─ Yes → Play battle
│  │  │  │  │  │  │
│  │  │  │  │  │  ├─ Elixir >= 6?
│  │  │  │  │  │  │  ├─ Yes → Play card
│  │  │  │  │  │  │  └─ No → Wait
│  │  │  │  │  │  │
│  │  │  │  │  │  ├─ Battle ended?
│  │  │  │  │  │  │  ├─ Yes → Find OK button
│  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  ├─ Found OK?
│  │  │  │  │  │  │  │  │  ├─ Yes → Click → Wait 3s → LOOP
│  │  │  │  │  │  │  │  │  └─ No → Retry or timeout → LOOP
│  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  └─ No → Continue playing
│  │  │  │  │  │
│  │  │  │  │  └─ No → Retry with fallback → STOP if still fails
│  │  │  │
│  │  │  └─ No → STOP (Battle button timeout)
│  │
│  └─ No → Retry → STOP if timeout
│
└─ END
"""
