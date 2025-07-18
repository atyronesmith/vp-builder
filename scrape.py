#!/usr/bin/env python3
"""
Alias for scrap.py - Web scraper with the proper name.
"""

import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Import and run the main function from scrap.py
sys.path.insert(0, script_dir)
from scrap import main

if __name__ == '__main__':
    main()