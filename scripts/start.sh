#!/bin/bash

# Start the background fetcher (detached)
python scripts/fetch_prices.py &

# Start the main server (foreground)
python scripts/server.py
