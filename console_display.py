"""
Console display manager for a GUI-like experience
"""

import os
import time
import threading
from typing import Dict
from datetime import datetime


class ConsoleDisplay:
    """
    Manages a clean console display that acts like a GUI
    Shows status for multiple emulators without flooding the console
    """

    def __init__(self):
        self.emulator_data = {}
        self.display_active = False
        self.update_thread = None
        self.lock = threading.Lock()
        self.last_update = time.time()
        self.update_interval = 1.0  # Update every second

    def add_emulator(self, instance_name: str):
        """Add an emulator to track"""
        with self.lock:
            self.emulator_data[instance_name] = {
                "status": "Initializing...",
                "battles": 0,
                "wins": 0,
                "losses": 0,
                "cards_played": 0,
                "restarts": 0,
                "last_message": "Starting up...",
                "runtime": "00:00:00",
                "start_time": time.time(),
                "active": True,
            }

    def update_emulator_status(self, instance_name: str, status: str):
        """Update emulator status"""
        with self.lock:
            if instance_name in self.emulator_data:
                self.emulator_data[instance_name]["status"] = status
                self.emulator_data[instance_name]["last_message"] = status

    def update_emulator_stats(self, instance_name: str, **kwargs):
        """Update emulator statistics"""
        with self.lock:
            if instance_name in self.emulator_data:
                for key, value in kwargs.items():
                    if key in self.emulator_data[instance_name]:
                        self.emulator_data[instance_name][key] = value

    def log_message(self, instance_name: str, message: str):
        """Log a message for an emulator"""
        with self.lock:
            if instance_name in self.emulator_data:
                self.emulator_data[instance_name]["last_message"] = message

    def remove_emulator(self, instance_name: str):
        """Mark emulator as inactive"""
        with self.lock:
            if instance_name in self.emulator_data:
                self.emulator_data[instance_name]["active"] = False
                self.emulator_data[instance_name]["status"] = "Stopped"

    def start_display(self):
        """Start the console display"""
        self.display_active = True
        self.update_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.update_thread.start()

    def stop_display(self):
        """Stop the console display"""
        self.display_active = False
        if self.update_thread:
            self.update_thread.join(timeout=2)

    def _display_loop(self):
        """Main display loop that updates the console"""
        while self.display_active:
            try:
                current_time = time.time()
                if current_time - self.last_update >= self.update_interval:
                    self._refresh_display()
                    self.last_update = current_time
                time.sleep(0.1)
            except Exception:
                # Don't let display errors crash the program
                pass

    def _refresh_display(self):
        """Refresh the console display"""
        with self.lock:
            # Clear screen (works on Windows)
            os.system("cls" if os.name == "nt" else "clear")

            # Header
            current_time = datetime.now().strftime("%H:%M:%S")
            print("=" * 100)
            print(f"🤖 Clash Royale Multi-Bot Dashboard - {current_time}")
            print("=" * 100)

            if not self.emulator_data:
                print("No emulators running...")
                return

            # Calculate runtime for each emulator
            for name, data in self.emulator_data.items():
                if data["active"]:
                    elapsed = time.time() - data["start_time"]
                    hours = int(elapsed // 3600)
                    minutes = int((elapsed % 3600) // 60)
                    seconds = int(elapsed % 60)
                    data["runtime"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Sort emulators by name for consistent display
            sorted_emulators = sorted(self.emulator_data.items())

            # Display each emulator
            for name, data in sorted_emulators:
                self._display_emulator_row(name, data)

            # Footer with controls
            print("=" * 100)
            print("Press Ctrl+C to stop all bots")
            print("=" * 100)

    def _display_emulator_row(self, name: str, data: Dict):
        """Display a single emulator's information"""
        # Status indicator
        if not data["active"]:
            status_icon = "🔴"
        elif "battle" in data["status"].lower() or "fighting" in data["status"].lower():
            status_icon = "⚔️"
        elif "waiting" in data["status"].lower():
            status_icon = "⏳"
        elif "restart" in data["status"].lower():
            status_icon = "🔄"
        elif "error" in data["status"].lower() or "fail" in data["status"].lower():
            status_icon = "❌"
        else:
            status_icon = "✅"

        # Calculate win rate
        total_battles = data["wins"] + data["losses"]
        if total_battles > 0:
            win_rate = (data["wins"] / total_battles) * 100
            win_rate_str = f"{win_rate:.1f}%"
        else:
            win_rate_str = "N/A"

        # Format the row
        print(
            f"{status_icon} {name:<10} | Runtime: {data['runtime']} | "
            f"Battles: {total_battles:<3} | W/L: {data['wins']}/{data['losses']} ({win_rate_str:<6}) | "
            f"Cards: {data['cards_played']:<4} | Restarts: {data['restarts']}"
        )

        # Show current activity (truncated to fit)
        activity = data["last_message"]
        if len(activity) > 90:
            activity = activity[:87] + "..."
        print(f"   {activity}")
        print()

    def print_final_summary(self):
        """Print a final summary when shutting down"""
        with self.lock:
            os.system("cls" if os.name == "nt" else "clear")
            print("=" * 100)
            print("🏁 FINAL SESSION SUMMARY")
            print("=" * 100)

            total_battles = 0
            total_wins = 0
            total_losses = 0
            total_cards = 0
            total_restarts = 0

            for name, data in sorted(self.emulator_data.items()):
                battles = data["wins"] + data["losses"]
                total_battles += battles
                total_wins += data["wins"]
                total_losses += data["losses"]
                total_cards += data["cards_played"]
                total_restarts += data["restarts"]

                # Calculate individual stats
                if battles > 0:
                    win_rate = (data["wins"] / battles) * 100
                    win_rate_str = f"{win_rate:.1f}%"
                else:
                    win_rate_str = "N/A"

                print(
                    f"📱 {name:<10} | Runtime: {data['runtime']} | "
                    f"Battles: {battles:<3} | W/L: {data['wins']}/{data['losses']} ({win_rate_str:<6}) | "
                    f"Cards: {data['cards_played']:<4} | Restarts: {data['restarts']}"
                )

            print("-" * 100)

            # Overall totals
            if total_battles > 0:
                overall_win_rate = (total_wins / total_battles) * 100
                overall_win_rate_str = f"{overall_win_rate:.1f}%"
            else:
                overall_win_rate_str = "N/A"

            print(
                f"🏆 TOTALS        | Battles: {total_battles:<3} | "
                f"W/L: {total_wins}/{total_losses} ({overall_win_rate_str:<6}) | "
                f"Cards: {total_cards:<4} | Restarts: {total_restarts}"
            )

            print("=" * 100)
            print("Thank you for using pyCRBot! 🎮")
            print("=" * 100)


# Global instance
console_display = ConsoleDisplay()
