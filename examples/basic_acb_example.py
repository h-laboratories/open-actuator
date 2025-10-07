#!/usr/bin/env python3
"""
Basic ACB v2.0 example: Connect, recalibrate, and set velocity to 1000.
"""

import sys
import time
from open_actuator import ACBv2, USBInterface


def main():
    """Basic example of ACB v2.0 usage."""
    # Connection parameters
    port = "/dev/ttyACM0"  # Change this to your port (e.g., "COM3" on Windows)
    baudrate = 2000000
    
    print("ACB v2.0 Basic Example")
    print("=" * 25)
    
    # Create interface and actuator
    usb_interface = USBInterface(port, baudrate)
    actuator = ACBv2(usb_interface)
    
    try:
        # Connect
        print(f"Connecting to {port}...")
        if not actuator.connect():
            print("❌ Connection failed!")
            return 1
        print("✅ Connected!")
        
        # Recalibrate sensors
        print("Recalibrating sensors...")
        if not actuator.recalibrate_sensors():
            print("❌ Recalibration failed!")
            return 1
        print("✅ Recalibration complete!")
        
        time.sleep(2.0)
        # Set velocity to 1000
        print("Setting velocity to 1000°/s...")
        actuator.enable()
        if not actuator.set_velocity(1000.0):
            print("❌ Failed to set velocity!")
            return 1
        print("✅ Velocity set to 1000°/s!")
        
        print("✅ Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    finally:
        # Clean up
        actuator.disconnect()
        print("Disconnected.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
