"""
Emulator detection and ADB utilities
"""

import subprocess
from config import MEMU_PORTS


def check_adb_available():
    """Check if ADB is available in the system"""
    try:
        result = subprocess.run(
            "adb version", shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            print("ERROR: ADB (Android Debug Bridge) is not installed or not in PATH!")
            print("Please install ADB and add it to your system PATH.")
            print(
                "You can download ADB from: https://developer.android.com/studio/releases/platform-tools"
            )
            return False
        return True
    except Exception as e:
        print(f"Error checking ADB availability: {e}")
        return False


def get_connected_devices():
    """Get list of all currently connected ADB devices"""
    try:
        print("Getting list of all connected ADB devices...")
        devices_result = subprocess.run(
            "adb devices", shell=True, capture_output=True, text=True
        )
        if devices_result.returncode != 0:
            print("Failed to get ADB devices list")
            return []

        # Parse connected devices
        connected_devices = []
        for line in devices_result.stdout.split("\n"):
            if "\tdevice" in line:  # Only devices that are properly connected
                device_id = line.split("\t")[0]
                connected_devices.append(device_id)

        print(f"Found {len(connected_devices)} connected ADB device(s)")
        return connected_devices
    except Exception as e:
        print(f"Error getting connected devices: {e}")
        return []


def test_device_responsiveness(device_id):
    """Test if a device is responsive"""
    try:
        test_result = subprocess.run(
            f"adb -s {device_id} shell echo test",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return test_result.returncode == 0 and "test" in test_result.stdout
    except Exception:
        return False


def connect_to_memu_ports():
    """Try to connect to common MEmu ports"""
    available_instances = []

    print(
        "No responsive devices found via 'adb devices', trying to connect to common MEmu ports..."
    )

    # Check each potential MEmu port
    for i, port in enumerate(MEMU_PORTS):
        device_id = f"127.0.0.1:{port}"
        print(f"Checking for MEmu instance on port {port}...")

        # Try to connect to this port
        result = subprocess.run(
            f"adb connect {device_id}", shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            # Verify the device is actually responsive
            if test_device_responsiveness(device_id):
                instance_name = f"MEmu_{i + 1}"
                available_instances.append((device_id, instance_name))
                print(
                    f"✓ Found responsive MEmu instance: {instance_name} ({device_id})"
                )
            else:
                print(f"✗ MEmu instance on port {port} not responsive")
        else:
            print(f"✗ No MEmu instance found on port {port}")

    return available_instances


def detect_memu_instances():
    """Detect running MEmu instances and return their device IDs"""
    try:
        # First check if ADB is available
        if not check_adb_available():
            return []

        available_instances = []

        # First, get all currently connected devices
        connected_devices = get_connected_devices()

        # Test each connected device to see if it's responsive
        instance_counter = 1
        for device_id in connected_devices:
            print(f"Testing device: {device_id}...")

            # Verify the device is actually responsive
            if test_device_responsiveness(device_id):
                instance_name = f"MEmu_{instance_counter}"
                available_instances.append((device_id, instance_name))
                print(f"✓ Found responsive device: {instance_name} ({device_id})")
                instance_counter += 1
            else:
                print(f"✗ Device {device_id} not responsive or not an emulator")

        # If no devices found via adb devices, try connecting to common MEmu ports
        if not available_instances:
            available_instances = connect_to_memu_ports()

        return available_instances

    except Exception as e:
        print(f"Error detecting MEmu instances: {e}")
        return []


def send_adb_command(device_id, command, timeout=10):
    """Send an ADB command to a specific device"""
    try:
        full_command = f"adb -s {device_id} {command}"
        result = subprocess.run(
            full_command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)
