#!/usr/bin/env python3
"""
Comprehensive ACB v2.0 example with command-line arguments.

This example demonstrates:
- Command-line argument parsing
- Connection with error handling
- Sensor recalibration with user confirmation
- Velocity control with monitoring
- Clean shutdown
"""

import sys
import time
import argparse
from src.open_actuator import ACBv2, USBInterface, CommandMode


def main():
    """Comprehensive example with command-line arguments."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ACB v2.0 Comprehensive Example")
    parser.add_argument("port", nargs="?", default="/dev/ttyUSB0", 
                       help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("baudrate", nargs="?", type=int, default=2000000,
                       help="Baud rate (default: 2000000)")
    parser.add_argument("--mode", choices=["human", "binary", "simplefoc"], 
                       default="human", help="Communication mode (default: human)")
    
    args = parser.parse_args()
    
    # Map mode strings to CommandMode enum
    mode_map = {
        "human": CommandMode.HUMAN_READABLE,
        "binary": CommandMode.HIGH_SPEED_BINARY,
        "simplefoc": CommandMode.SIMPLEFOC
    }
    
    print("ACB v2.0 Comprehensive Example")
    print("=" * 40)
    print(f"Port: {args.port}")
    print(f"Baud Rate: {args.baudrate}")
    print(f"Mode: {args.mode}")
    print()
    
    # Create USB interface and ACB v2 actuator
    usb_interface = USBInterface(args.port, args.baudrate)
    actuator = ACBv2(usb_interface)
    
    # Set communication mode
    actuator.interface.command_mode = mode_map[args.mode]
    
    try:
        # Connect
        print("Connecting to actuator...")
        if not actuator.connect():
            print("❌ Failed to connect to actuator")
            print("Please check:")
            print("  - Port is correct and device is connected")
            print("  - No other software is using the port")
            print("  - Device is powered on")
            return 1
        print("✅ Successfully connected!")
        
        # Get initial state
        print("\nGetting initial state...")
        position = actuator.get_position()
        velocity = actuator.get_velocity()
        print(f"Initial Position: {position:.2f}°" if position is not None else "Position: N/A")
        print(f"Initial Velocity: {velocity:.2f}°/s" if velocity is not None else "Velocity: N/A")
        
        # Recalibrate sensors
        print("\n⚠️  WARNING: Recalibration will disable the motor!")
        print("   Make sure the actuator is in a safe position!")
        
        response = input("Continue with recalibration? (y/N): ").strip().lower()
        if response != 'y':
            print("Recalibration cancelled by user")
            return 0
        
        print("Starting sensor recalibration...")
        if not actuator.recalibrate_sensors():
            print("❌ Sensor recalibration failed!")
            return 1
        print("✅ Recalibration completed successfully!")
        
        # Set velocity to 1000
        print("\nSetting velocity to 1000°/s...")
        if not actuator.set_velocity(1000.0):
            print("❌ Failed to set velocity!")
            return 1
        print("✅ Velocity set to 1000°/s!")
        
        # Monitor for a few seconds
        print("\nMonitoring for 3 seconds...")
        start_time = time.time()
        try:
            while time.time() - start_time < 3.0:
                position = actuator.get_position()
                velocity = actuator.get_velocity()
                print(f"\rPosition: {position:.2f}° | Velocity: {velocity:.2f}°/s", 
                      end="", flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        print()  # New line
        
        # Stop the actuator
        print("\nStopping actuator...")
        if actuator.stop():
            print("✅ Actuator stopped")
        else:
            print("❌ Failed to stop actuator")
        
        # Get final state
        print("\nFinal state:")
        position = actuator.get_position()
        velocity = actuator.get_velocity()
        print(f"Final Position: {position:.2f}°" if position is not None else "Position: N/A")
        print(f"Final Velocity: {velocity:.2f}°/s" if velocity is not None else "Velocity: N/A")
        
        print("\n✅ Example completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Example interrupted by user")
        print("Stopping actuator...")
        actuator.stop()
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        return 1
        
    finally:
        # Always disconnect
        print("\nDisconnecting from actuator...")
        actuator.disconnect()
        print("✅ Disconnected")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
