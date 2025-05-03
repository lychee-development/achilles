#!/usr/bin/env python3
"""
Simple entry point script for Achilles
"""

import sys
import os

# Add the current directory to sys.path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import main

if __name__ == "__main__":
    main() 