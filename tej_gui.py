#!/usr/bin/env python3
"""
Tej AI - GUI Quick Launcher
Double-click this file to launch the Tej AI desktop application.
"""

import sys
import os

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tej.gui import launch_gui

if __name__ == "__main__":
    launch_gui()
