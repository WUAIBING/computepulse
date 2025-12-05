#!/usr/bin/env python3
"""
Clean invalid data from JSON files.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')

def clean_token_prices():
    """Remove token price entries with null values."""
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Original: {len(data)} records")
        
        # Filter out entries with null prices
        cleaned = [
            item for item in data
            if item.get('input_price') is not None and item.get('output_price') is not None
        ]
        
        print(f"Cleaned: {len(cleaned)} records")
        print(f"Removed: {len(data) - len(cleaned)} records")
        
        # Save cleaned data
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        
        print("Token prices cleaned successfully!")
        
    except Exception as e:
        print(f"Error cleaning token prices: {e}")

if __name__ == "__main__":
    clean_token_prices()
