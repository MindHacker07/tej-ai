#!/usr/bin/env python3
"""
Tej AI Quick Launcher
Run this file to start Tej AI directly.
"""

import sys
import os

# Ensure we can find the tej package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tej.main import main

if __name__ == "__main__":
    main()
