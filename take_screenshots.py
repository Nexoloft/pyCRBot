"""
Script to take screenshots from all available MEmu devices
Saves screenshots to screenshots folder with device name
"""

import subprocess
import os
import time
from datetime import datetime
from config import MEMU_PORTS

def get_connected_devices():
    """Get list of connected ADB devices"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        devices = []
        for line in lines:
            if line.strip() and 'device' in line:
                device_id = line.split()[0]
                devices.append(device_id)
        return devices
    except Exception as e:
        print(f"Error getting devices: {e}")
        return []

def take_screenshot_from_device(device_id, output_folder):
    """Take a screenshot from a specific device"""
    try:
        # Create screenshots folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_name = device_id.replace(':', '_').replace('.', '_')
        filename = f"{device_name}_{timestamp}.png"
        output_path = os.path.join(output_folder, filename)
        
        print(f"Taking screenshot from {device_id}...")
        
        # Take screenshot on device
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'screencap', '-p', '/sdcard/screenshot.png'],
            check=True,
            capture_output=True
        )
        
        # Pull screenshot to PC
        subprocess.run(
            ['adb', '-s', device_id, 'pull', '/sdcard/screenshot.png', output_path],
            check=True,
            capture_output=True
        )
        
        # Clean up screenshot on device
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'rm', '/sdcard/screenshot.png'],
            check=False,
            capture_output=True
        )
        
        print(f"✓ Screenshot saved: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to take screenshot from {device_id}: {e}")
        return False
    except Exception as e:
        print(f"✗ Error with {device_id}: {e}")
        return False

def main():
    """Main function to take screenshots from all devices"""
    print("=" * 60)
    print("MEmu Screenshot Tool")
    print("=" * 60)
    
    # Get connected devices
    print("\nScanning for connected devices...")
    devices = get_connected_devices()
    
    if not devices:
        print("No devices found. Make sure MEmu instances are running.")
        return
    
    print(f"Found {len(devices)} device(s):")
    for device in devices:
        print(f"  - {device}")
    
    # Create screenshots folder
    screenshots_folder = "screenshots"
    
    print(f"\nTaking screenshots (saving to '{screenshots_folder}' folder)...")
    print("-" * 60)
    
    # Take screenshots from all devices
    success_count = 0
    for device in devices:
        if take_screenshot_from_device(device, screenshots_folder):
            success_count += 1
        time.sleep(0.5)  # Small delay between devices
    
    print("-" * 60)
    print(f"\nCompleted: {success_count}/{len(devices)} screenshots saved")
    print("=" * 60)

if __name__ == "__main__":
    main()
