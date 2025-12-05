#!/usr/bin/env python3
"""
Test script to fetch annual AI energy consumption data
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the fetch function
from scripts.fetch_prices_optimized import fetch_annual_energy_history

if __name__ == "__main__":
    print("Testing Annual Energy Data Fetch...")
    print("=" * 60)
    fetch_annual_energy_history()
    print("=" * 60)
    print("Test completed!")
