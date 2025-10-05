#!/usr/bin/env python3
"""
Simple launcher script for the Open Actuator GUI.

This script provides a convenient way to start the GUI application
without needing to use the full module path.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from open_actuator.main import main

if __name__ == "__main__":
    main()

