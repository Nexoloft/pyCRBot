"""
Logging and statistics tracking system
"""

import time
from typing import Dict, Any
from datetime import datetime


class Logger:
    """Advanced logging and statistics tracking system"""
    
    def __init__(self, instance_name: str, timed: bool = True):
        self.instance_name = instance_name
        self.timed = timed
        self.start_time = time.time() if timed else None
        self.current_status = "Initializing"
        
        # Battle statistics
        self.stats = {
            # Battle stats
            "wins": 0,
            "losses": 0,
            "total_battles": 0,
            "cards_played": 0,
            "1v1_fights": 0,
            "2v2_fights": 0,
            "trophy_road_fights": 0,
            "classic_1v1_fights": 0,
            "classic_2v2_fights": 0,
            
            # Collection stats
            "chests_opened": 0,
            "cards_upgraded": 0,
            "requests_made": 0,
            "donations_made": 0,
            
            # Bot stats
            "runtime_seconds": 0,
            "failures": 0,
            "restarts": 0,
            "last_activity": "Starting"
        }
        
        # Action system for user interaction
        self.action_needed = False
        self.action_text = ""
        self.action_callback = None
        self.errored = False

    def log(self, message: str):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.instance_name}] {message}")

    def change_status(self, status: str):
        """Change the current status and log it"""
        self.current_status = status
        self.stats["last_activity"] = status
        self.log(status)

    def get_status(self) -> str:
        """Get current status"""
        return self.current_status

    def calc_time_since_start(self) -> str:
        """Calculate time since start"""
        if not self.timed or self.start_time is None:
            return "Not timed"
        
        elapsed = time.time() - self.start_time
        self.stats["runtime_seconds"] = int(elapsed)
        
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        # Update runtime
        if self.timed and self.start_time:
            self.stats["runtime_seconds"] = int(time.time() - self.start_time)
        
        # Calculate derived stats
        total_battles = self.stats["wins"] + self.stats["losses"]
        self.stats["total_battles"] = total_battles
        
        # Calculate win rate
        if total_battles > 0:
            win_rate = (self.stats["wins"] / total_battles) * 100
            self.stats["win_rate"] = f"{win_rate:.1f}%"
        else:
            self.stats["win_rate"] = "N/A"
        
        return self.stats.copy()

    # Battle stat methods
    def add_win(self):
        """Record a win"""
        self.stats["wins"] += 1
        self.log(f"🏆 Win recorded! Total wins: {self.stats['wins']}")

    def add_loss(self):
        """Record a loss"""
        self.stats["losses"] += 1
        self.log(f"💔 Loss recorded. Total losses: {self.stats['losses']}")

    def add_card_played(self):
        """Record a card played"""
        self.stats["cards_played"] += 1

    def get_cards_played(self) -> int:
        """Get total cards played"""
        return self.stats["cards_played"]

    def add_1v1_fight(self):
        """Record a 1v1 fight"""
        self.stats["1v1_fights"] += 1

    def increment_2v2_fights(self):
        """Record a 2v2 fight"""
        self.stats["2v2_fights"] += 1

    def increment_trophy_road_fights(self):
        """Record a trophy road fight"""
        self.stats["trophy_road_fights"] += 1

    def increment_classic_1v1_fights(self):
        """Record a classic 1v1 fight"""
        self.stats["classic_1v1_fights"] += 1

    def increment_classic_2v2_fights(self):
        """Record a classic 2v2 fight"""
        self.stats["classic_2v2_fights"] += 1

    # Collection stat methods
    def add_chest_opened(self):
        """Record a chest opened"""
        self.stats["chests_opened"] += 1
        self.log(f"📦 Chest opened! Total: {self.stats['chests_opened']}")

    def add_card_upgraded(self):
        """Record a card upgrade"""
        self.stats["cards_upgraded"] += 1
        self.log(f"⬆️ Card upgraded! Total: {self.stats['cards_upgraded']}")

    def add_request_made(self):
        """Record a card request"""
        self.stats["requests_made"] += 1
        self.log(f"🤲 Card requested! Total: {self.stats['requests_made']}")

    def add_donation_made(self):
        """Record a card donation"""
        self.stats["donations_made"] += 1
        self.log(f"💝 Card donated! Total: {self.stats['donations_made']}")

    # Bot stat methods
    def add_failure(self):
        """Record a failure/error"""
        self.stats["failures"] += 1
        self.log(f"❌ Failure recorded. Total failures: {self.stats['failures']}")

    def add_restart(self):
        """Record an app restart"""
        self.stats["restarts"] += 1
        self.log(f"🔄 App restart recorded. Total restarts: {self.stats['restarts']}")

    # Action system for user interaction
    def request_user_action(self, text: str, callback_function=None):
        """Request user action with callback"""
        self.action_needed = True
        self.action_text = text
        self.action_callback = callback_function
        self.log(f"⚠️ User action needed: {text}")

    def clear_user_action(self):
        """Clear pending user action"""
        self.action_needed = False
        self.action_text = ""
        self.action_callback = None

    def log_job_dictionary(self, job_dict: Dict[str, Any]):
        """Log the job configuration"""
        self.log("Job Configuration:")
        for key, value in job_dict.items():
            if isinstance(value, bool) and value:
                self.log(f"  ✅ {key}: {value}")
            elif not isinstance(value, bool):
                self.log(f"  ⚙️ {key}: {value}")

    def log_summary(self):
        """Log a summary of statistics"""
        stats = self.get_stats()
        runtime = self.calc_time_since_start()
        
        self.log("=" * 50)
        self.log("SESSION SUMMARY")
        self.log("=" * 50)
        self.log(f"Runtime: {runtime}")
        self.log(f"Battles: {stats['total_battles']} (W: {stats['wins']}, L: {stats['losses']})")
        self.log(f"Win Rate: {stats['win_rate']}")
        self.log(f"Cards Played: {stats['cards_played']}")
        self.log(f"Chests Opened: {stats['chests_opened']}")
        self.log(f"Cards Upgraded: {stats['cards_upgraded']}")
        self.log(f"App Restarts: {stats['restarts']}")
        self.log(f"Failures: {stats['failures']}")
        self.log("=" * 50)
