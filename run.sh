#!/bin/bash
# Run script for Bugzilla Tracker
# This script uses the virtual environment's python3

# Activate virtual environment if it exists, otherwise use system python3
if [ -d "venv" ]; then
    ./venv/bin/python main.py
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    ./venv/bin/python main.py
fi

