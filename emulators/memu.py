"""
MEmu emulator controller implementation
"""

import os
import time
import subprocess
import cv2
import numpy as np
from .base import BaseEmulatorController


class MemuController(BaseEmulatorController):
    """MEmu emulator controller implementation"""
    
    def __init__(self, device_id: str, instance_name: str):
        super().__init__(device_id, instance_name)
        self.screenshots_dir = f"screenshots_{instance_name}"
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def click(self, x: int, y: int, clicks: int = 1, interval: float = 0.1) -> bool:
        """Send a tap command to this emulator via ADB"""
        try:
            for _ in range(clicks):
                result = subprocess.run(
                    f'adb -s {self.device_id} shell input tap {x} {y}', 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    print(f"[{self.instance_name}] Failed to tap screen at ({x}, {y}): {result.stderr}")
                    return False
                
                if clicks > 1 and interval > 0:
                    time.sleep(interval)
                    
            return True
        except Exception as e:
            print(f"[{self.instance_name}] Error tapping screen: {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 1000) -> bool:
        """Swipe on the emulator screen"""
        try:
            result = subprocess.run(
                f'adb -s {self.device_id} shell input swipe {x1} {y1} {x2} {y2} {duration}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True
            else:
                print(f"[{self.instance_name}] Failed to swipe: {result.stderr}")
                return False
        except Exception as e:
            print(f"[{self.instance_name}] Error swiping: {e}")
            return False

    def screenshot(self) -> np.ndarray | None:
        """Take screenshot via ADB and load it into memory"""
        try:
            # First check if device is still online
            devices_result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            if f"{self.device_id}\tdevice" not in devices_result.stdout:
                if f"{self.device_id}\toffline" in devices_result.stdout:
                    print(f"[{self.instance_name}] Device is offline - attempting reconnection...")
                    # Try to reconnect
                    subprocess.run(f"adb connect {self.device_id}", shell=True, capture_output=True)
                    time.sleep(2)
                    # Check again
                    devices_result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
                    if f"{self.device_id}\tdevice" not in devices_result.stdout:
                        print(f"[{self.instance_name}] Failed to reconnect device")
                        return None
                else:
                    print(f"[{self.instance_name}] Device not found in ADB devices list")
                    return None
            
            screenshot_path = os.path.join(self.screenshots_dir, "screenshot.png")
            
            # Remove old screenshot file if it exists to ensure fresh capture
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            # Capture screenshot with specific device
            result = subprocess.run(
                f"adb -s {self.device_id} shell screencap /sdcard/screenshot.png", 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=10  # Add timeout to prevent hanging
            )
            if result.returncode != 0:
                print(f"[{self.instance_name}] Failed to capture screenshot: {result.stderr}")
                return None
                
            # Small delay to ensure screenshot is ready on device
            time.sleep(0.05)
                
            # Download screenshot with specific device
            result = subprocess.run(
                f"adb -s {self.device_id} pull /sdcard/screenshot.png {screenshot_path}", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                print(f"[{self.instance_name}] Failed to download screenshot: {result.stderr}")
                return None
                
            # Load image
            if not os.path.exists(screenshot_path):
                print(f"[{self.instance_name}] Screenshot file not found after download")
                return None
                
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                print(f"[{self.instance_name}] Failed to load screenshot image")
                return None
                
            return screenshot
        except Exception as e:
            print(f"[{self.instance_name}] Error taking screenshot: {e}")
            return None

    def start_app(self, package_name: str) -> bool:
        """Start Clash Royale app on this emulator instance"""
        try:
            print(f"[{self.instance_name}] Starting app: {package_name}")
            result = subprocess.run(
                f"adb -s {self.device_id} shell am start -n {package_name}/com.supercell.titan.GameApp", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[{self.instance_name}] Error starting app: {e}")
            return False

    def restart_app(self, package_name: str) -> bool:
        """Restart Clash Royale app on this emulator instance"""
        try:
            print(f"[{self.instance_name}] Restarting app: {package_name}")
            # Force stop the app
            subprocess.run(
                f"adb -s {self.device_id} shell am force-stop {package_name}", 
                shell=True, 
                capture_output=True
            )
            time.sleep(2)
            # Start the app
            return self.start_app(package_name)
        except Exception as e:
            print(f"[{self.instance_name}] Error restarting app: {e}")
            return False
