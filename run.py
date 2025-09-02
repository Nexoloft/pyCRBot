#!/usr/bin/env python3
"""
Quick start script for the Clash Royale Bot
Usage:
  python run.py --gui                    # Launch GUI
  python run.py --headless              # Run single emulator headless
  python run.py --multi 3               # Run 3 emulators
"""

import sys
import argparse
from main import main


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Clash Royale Bot - PyClashBot Style")
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--gui', action='store_true', 
                           help='Launch GUI interface')
    mode_group.add_argument('--headless', action='store_true',
                           help='Run single emulator in headless mode')
    mode_group.add_argument('--multi', type=int, metavar='N',
                           help='Run N emulators (1-10)')
    mode_group.add_argument('--status', action='store_true',
                           help='Show MEmu emulator status and exit')
    
    # Optional arguments
    parser.add_argument('--port', type=int, default=21503,
                       help='MEmu port for single emulator (default: 21503)')
    parser.add_argument('--battles', type=int, default=0,
                       help='Number of battles to run (0 = infinite)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    return parser.parse_args()


def main_entry():
    """Main entry point with argument parsing"""
    args = parse_args()
    
    try:
        if args.status:
            print("🔍 Checking MEmu emulator status...")
            main('status')
            
        elif args.gui:
            print("🎮 Launching Clash Royale Bot GUI...")
            main('gui')
            
        elif args.headless:
            print(f"🤖 Starting single emulator on port {args.port}")
            print(f"⚔️  Battle limit: {'∞' if args.battles == 0 else args.battles}")
            main('single', port=args.port, max_battles=args.battles)
            
        elif args.multi:
            if not (1 <= args.multi <= 10):
                print("❌ Error: Number of emulators must be between 1 and 10")
                sys.exit(1)
            
            print(f"🚀 Starting {args.multi} emulator(s)")
            print(f"⚔️  Battle limit per emulator: {'∞' if args.battles == 0 else args.battles}")
            main('multi', num_emulators=args.multi, max_battles=args.battles)
            
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_entry()
