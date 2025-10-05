"""
Main entry point for the Open Actuator application.

This module provides the main entry point for running the GUI application
and can be used as a command-line interface as well.
"""

import sys
import argparse
from typing import Optional

from .gui.main import ActuatorGUI


def main() -> None:
    """
    Main entry point for the Open Actuator application.
    
    Parses command line arguments and starts the appropriate interface.
    """
    parser = argparse.ArgumentParser(description="Open Actuator Control Software")
    parser.add_argument(
        "--port", 
        type=str, 
        help="Serial port to connect to (e.g., /dev/ttyUSB0 or COM3)"
    )
    parser.add_argument(
        "--baudrate", 
        type=int, 
        default=2000000,
        help="Serial baud rate (default: 115200)"
    )
    parser.add_argument(
        "--mode",
        choices=["human", "binary", "simplefoc"],
        default="human",
        help="Communication mode (default: human)"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        default=True,
        help="Start GUI interface (default)"
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Disable GUI interface"
    )
    
    args = parser.parse_args()
    
    if args.no_gui:
        print("Command-line interface not yet implemented")
        print("Use --gui to start the graphical interface")
        sys.exit(1)
    
    # Start GUI application
    app = ActuatorGUI()
    
    # Set initial connection parameters if provided
    if args.port:
        app.port_var.set(args.port)
    if args.baudrate:
        app.baudrate_var.set(str(args.baudrate))
    
    # Set communication mode
    mode_map = {
        "human": "Human Readable",
        "binary": "High Speed Binary", 
        "simplefoc": "SimpleFOC"
    }
    if args.mode in mode_map:
        app.mode_var.set(mode_map[args.mode])
    
    # Run the application
    app.run()


if __name__ == "__main__":
    main()

