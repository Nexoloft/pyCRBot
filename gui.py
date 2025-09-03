"""
Simple GUI interface for the Clash Royale Bot
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from main import detect_memu_instances, verify_template_images, run_battle_mode, run_upgrade_mode, run_battlepass_mode


class ClashRoyaleBotGUI:
    """Simple GUI for the Clash Royale Bot"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Clash Royale Multi-Bot Controller")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Variables
        self.bot_running = False
        self.bot_thread = None
        self.instances = []
        
        # Create GUI elements
        self.create_widgets()
        self.refresh_instances()
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main title
        title_label = tk.Label(
            self.root, 
            text="Clash Royale Multi-Bot Controller", 
            font=("Arial", 16, "bold"),
            fg="blue"
        )
        title_label.pack(pady=10)
        
        # Instances frame
        instances_frame = ttk.LabelFrame(self.root, text="Available MEmu Instances", padding=10)
        instances_frame.pack(fill="x", padx=20, pady=10)
        
        self.instances_listbox = tk.Listbox(instances_frame, height=6)
        self.instances_listbox.pack(fill="x")
        
        refresh_btn = ttk.Button(instances_frame, text="Refresh Instances", command=self.refresh_instances)
        refresh_btn.pack(pady=5)
        
        # Mode selection frame
        mode_frame = ttk.LabelFrame(self.root, text="Bot Mode", padding=10)
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        self.mode_var = tk.StringVar(value="battle")
        
        battle_radio = ttk.Radiobutton(
            mode_frame, 
            text="Battle Mode - Automatically play battles", 
            variable=self.mode_var, 
            value="battle"
        )
        battle_radio.pack(anchor="w")
        
        upgrade_radio = ttk.Radiobutton(
            mode_frame, 
            text="Upgrade Mode - Automatically upgrade cards", 
            variable=self.mode_var, 
            value="upgrade"
        )
        upgrade_radio.pack(anchor="w")
        
        battlepass_radio = ttk.Radiobutton(
            mode_frame, 
            text="Battlepass Mode - Automatically claim battlepass rewards", 
            variable=self.mode_var, 
            value="battlepass"
        )
        battlepass_radio.pack(anchor="w")
        
        # Control buttons frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(
            control_frame, 
            text="Start Bot", 
            command=self.start_bot,
            style="Accent.TButton"
        )
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ttk.Button(
            control_frame, 
            text="Stop Bot", 
            command=self.stop_bot,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.status_text = tk.Text(status_frame, height=10, wrap="word")
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial status
        self.log_status("GUI initialized. Click 'Refresh Instances' to detect MEmu emulators.")
    
    def refresh_instances(self):
        """Refresh the list of available MEmu instances"""
        self.log_status("Detecting MEmu instances...")
        
        try:
            # Verify templates first
            if not verify_template_images():
                self.log_status("❌ Template images missing! Check templates folder.")
                return
            
            # Detect instances
            self.instances = detect_memu_instances()
            
            # Update listbox
            self.instances_listbox.delete(0, tk.END)
            
            if self.instances:
                for device_id, instance_name in self.instances:
                    self.instances_listbox.insert(tk.END, f"{instance_name} ({device_id})")
                self.log_status(f"✅ Found {len(self.instances)} MEmu instance(s)")
            else:
                self.instances_listbox.insert(tk.END, "No MEmu instances found")
                self.log_status("❌ No MEmu instances found. Start MEmu and try again.")
                
        except Exception as e:
            self.log_status(f"❌ Error detecting instances: {e}")
    
    def start_bot(self):
        """Start the bot in selected mode"""
        if not self.instances:
            messagebox.showerror("Error", "No MEmu instances available. Please refresh instances.")
            return
        
        if self.bot_running:
            messagebox.showwarning("Warning", "Bot is already running!")
            return
        
        mode = self.mode_var.get()
        self.log_status(f"🚀 Starting bot in {mode} mode with {len(self.instances)} instance(s)...")
        
        # Disable start button, enable stop button
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.bot_running = True
        
        # Start bot in separate thread
        if mode == "battle":
            self.bot_thread = threading.Thread(target=self._run_battle_mode, daemon=True)
        elif mode == "upgrade":
            self.bot_thread = threading.Thread(target=self._run_upgrade_mode, daemon=True)
        elif mode == "battlepass":
            self.bot_thread = threading.Thread(target=self._run_battlepass_mode, daemon=True)
        
        self.bot_thread.start()
    
    def stop_bot(self):
        """Stop the bot"""
        if not self.bot_running:
            return
        
        self.log_status("🛑 Stopping bot...")
        self.bot_running = False
        
        # Reset button states
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        self.log_status("✅ Bot stopped")
    
    def _run_battle_mode(self):
        """Run battle mode in thread"""
        try:
            run_battle_mode(self.instances)
        except Exception as e:
            self.log_status(f"❌ Error in battle mode: {e}")
        finally:
            self.root.after(0, self.stop_bot)  # Update GUI from main thread
    
    def _run_upgrade_mode(self):
        """Run upgrade mode in thread"""
        try:
            run_upgrade_mode(self.instances)
        except Exception as e:
            self.log_status(f"❌ Error in upgrade mode: {e}")
        finally:
            self.root.after(0, self.stop_bot)  # Update GUI from main thread
    
    def _run_battlepass_mode(self):
        """Run battlepass mode in thread"""
        try:
            run_battlepass_mode(self.instances)
        except Exception as e:
            self.log_status(f"❌ Error in battlepass mode: {e}")
        finally:
            self.root.after(0, self.stop_bot)  # Update GUI from main thread
    
    def log_status(self, message):
        """Add a status message to the text widget"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, formatted_message)
        self.status_text.see(tk.END)
        self.status_text.update()
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_bot()


def main_gui():
    """Launch the GUI version of the bot"""
    try:
        app = ClashRoyaleBotGUI()
        app.run()
    except Exception as e:
        print(f"GUI Error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main_gui()
