#!/usr/bin/env python3
"""
Test script to demonstrate the offline device handling fix
"""

import subprocess
import time
from emulator_utils import test_device_responsiveness

def test_device_detection():
    """Test the device detection and validation"""
    print("🔍 Testing MEmu Device Detection & Validation")
    print("=" * 55)
    
    # Get ADB devices
    result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
    print("📱 Current ADB devices:")
    print(result.stdout)
    
    # Test common MEmu ports
    test_ports = [21503, 21513, 21521, 21523]
    print("🧪 Testing specific MEmu ports:")
    
    working_devices = []
    offline_devices = []
    
    for port in test_ports:
        device_id = f"127.0.0.1:{port}"
        print(f"\n🔌 Testing {device_id}...")
        
        # Try to connect
        connect_result = subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True, text=True)
        time.sleep(0.5)
        
        # Test responsiveness
        if test_device_responsiveness(device_id):
            working_devices.append(device_id)
            print(f"✅ {device_id} - WORKING")
        else:
            offline_devices.append(device_id)
            print(f"❌ {device_id} - OFFLINE/NOT RESPONSIVE")
    
    print(f"\n📊 Summary:")
    print(f"✅ Working devices: {len(working_devices)}")
    for device in working_devices:
        print(f"   • {device}")
    
    print(f"❌ Offline devices: {len(offline_devices)}")
    for device in offline_devices:
        print(f"   • {device}")
    
    print(f"\n🚀 You can safely run up to {len(working_devices)} bots simultaneously!")
    
    if len(working_devices) >= 2:
        print(f"💡 Example: python run.py --multi {len(working_devices)}")
    elif len(working_devices) == 1:
        print("💡 Example: python run.py --headless")
    else:
        print("⚠️  No working emulators found. Please start MEmu and try again.")

if __name__ == "__main__":
    test_device_detection()
