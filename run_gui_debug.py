#!/usr/bin/env python3
"""
Debug launcher script for the Open Actuator GUI.

This script provides enhanced logging and debugging capabilities
for troubleshooting communication issues.
"""

import sys
import os
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('actuator_debug.log')
    ]
)

# Enable debug logging for our modules
logging.getLogger('open_actuator').setLevel(logging.DEBUG)

from open_actuator.main import main

if __name__ == "__main__":
    print("Starting Open Actuator GUI with debug logging...")
    print("Debug log will be saved to 'actuator_debug.log'")
    print("=" * 60)
    main()
