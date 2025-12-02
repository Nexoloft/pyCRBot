from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box
from collections import deque
import time
from threading import Lock

class Dashboard:
    def __init__(self):
        self.console = Console()
        self.emulators = {}
        self.lock = Lock()
        self.live = None
        self.layout = Layout()
        self.started = False

    def add_emulator(self, name):
        with self.lock:
            if name not in self.emulators:
                self.emulators[name] = {
                    "stats": {
                        "status": "Initializing",
                        "wins": 0,
                        "losses": 0,
                        "runtime": "00:00:00",
                        "battles": 0,
                        "restarts": 0
                    },
                    "logs": deque(maxlen=20)
                }
                # Re-generate layout structure when a new emulator is added
                self._update_layout_structure()

    def update_stats(self, name, key, value):
        with self.lock:
            if name in self.emulators:
                self.emulators[name]["stats"][key] = value

    def update_all_stats(self, name, stats_dict):
        with self.lock:
            if name in self.emulators:
                self.emulators[name]["stats"].update(stats_dict)

    def log(self, name, message):
        with self.lock:
            if name in self.emulators:
                timestamp = time.strftime("%H:%M:%S")
                self.emulators[name]["logs"].append(f"[{timestamp}] {message}")

    def _update_layout_structure(self):
        # Create a split for logs based on number of emulators
        # We'll use a simple vertical split (columns) for logs
        # If there are many emulators (e.g. > 3), maybe we should use a grid?
        # For now, let's stick to columns for up to 4, then maybe rows?
        # The user wants it "split up by emulator".
        pass

    def get_renderable(self):
        with self.lock:
            # 1. Stats Table
            table = Table(expand=True, box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Emulator", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Runtime", style="yellow")
            table.add_column("W/L", justify="center")
            table.add_column("Battles", justify="right")
            table.add_column("Restarts", justify="right")

            for name in sorted(self.emulators.keys()):
                stats = self.emulators[name]["stats"]
                table.add_row(
                    name,
                    stats.get("status", ""),
                    stats.get("runtime", "00:00:00"),
                    f"{stats.get('wins', 0)}/{stats.get('losses', 0)}",
                    str(stats.get("total_battles", 0)),
                    str(stats.get("restarts", 0))
                )

            # 2. Logs Area
            # We will create a Table with one row, and N columns, where each cell is a Panel of logs
            log_table = Table.grid(expand=True, padding=1)

            names = sorted(self.emulators.keys())
            if names:
                # Add columns for each emulator
                for _ in names:
                    log_table.add_column(ratio=1)

                # Add cells
                panels = []
                for name in names:
                    logs = "\n".join(self.emulators[name]["logs"])
                    panels.append(
                        Panel(
                            logs,
                            title=f"[bold]{name}[/bold]",
                            border_style="blue",
                            height=20  # Fixed height for logs
                        )
                    )
                log_table.add_row(*panels)
            else:
                log_table.add_row(Panel("Waiting for emulators...", style="dim"))

            # Combine them
            main_layout = Layout()
            main_layout.split_column(
                Layout(Panel(table, title="Dashboard", border_style="green"), size=len(names) + 6),
                Layout(log_table)
            )

            return main_layout

    def start(self):
        if not self.started:
            # Using screen=True creates a full screen application experience.
            # Live needs a callable that returns a renderable, or a renderable.
            # If we pass a callable as the first argument, it works.
            self.live = Live(self.get_renderable, refresh_per_second=4, screen=True)
            self.live.start()
            self.started = True

    def stop(self):
        if self.live:
            self.live.stop()
            self.started = False

# Global instance
dashboard = Dashboard()
