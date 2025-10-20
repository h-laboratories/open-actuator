#!/usr/bin/env python3
"""
Basic ACB v2.0 example: Connect, recalibrate, and set velocity to 1000.
"""

import sys
import time
from open_actuator import ACBv2, USBInterface
from tqdm import tqdm

target_velocity = 500.0
velocity_tolerance = 0.1

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
        
        # Set pole pairs to 7
        if not actuator.set_pole_pairs(7):
            print("❌ Failed to set pole pairs!")
            return 1
        print("✅ Pole pairs set to 7!")


        actuator.set_min_angle(-500000)
        actuator.set_max_angle(500000)
        # Recalibrate sensors
        print("Recalibrating sensors...")
        if not actuator.recalibrate_sensors():
            print("❌ Recalibration failed!")
            return 1
        print("✅ Recalibration complete!")
        time.sleep(0.5)
        print("Saving config...")
        if not actuator.save_config():
            print("❌ Failed to save config!")
            return 1
        print("✅ Config saved!")
        
        actuator.set_velocity(0.0)
        # actuator.enable()

        print("Checking stability...")
        velocities = []
        positions = []
        for _ in tqdm(range(20), desc="Checking stability"):
            velocities.append(actuator.get_velocity())
            positions.append(actuator.get_position())
            time.sleep(0.05)
        avg_vel = sum(velocities) / len(velocities)
        avg_pos = sum(positions) / len(positions)
        vel_range = max(velocities) - min(velocities)
        pos_range = max(positions) - min(positions)

        if abs(vel_range) > 1 or abs(pos_range) > 1:
            print(f"❌ Position or velocity is unstable! Δpos={pos_range}, Δvel={vel_range}")
            return 1

        print("✅ Stability checked!")
        actuator.enable()
        actuator.reset_position()
        print(f"Setting velocity to {target_velocity}°/s...")
        if not actuator.set_velocity(target_velocity):
            print("❌ Failed to set velocity!")
            return 1
        print(f"✅ Velocity set to {target_velocity}°/s!")
        
        print("Waiting for velocity to stabilize...")
        for _ in tqdm(range(20), desc="Stabilizing"):
            time.sleep(0.1)

        velocities = []
        for _ in tqdm(range(10), desc="Collecting velocity samples"):
            vel = actuator.get_velocity()
            velocities.append(vel)
            time.sleep(0.1)
        avg_velocity = sum(velocities) / len(velocities)
        print(f"Average Velocity (10 samples): {avg_velocity}°/s")

        if avg_velocity < target_velocity * (1 - velocity_tolerance) or avg_velocity > target_velocity * (1 + velocity_tolerance):
            print("❌ Velocity is not within tolerance!")
            return 1
        print("✅ Velocity is within tolerance!")
        

        if not actuator.set_velocity(0.0):
            print("❌ Failed to set velocity to 0!")
            return 1
        print("✅ Velocity set to 0!")

        if not actuator.disable():
            print("❌ Failed to disable!")
            return 1
        print("✅ Disabled!")
        
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
