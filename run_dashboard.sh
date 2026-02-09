#!/bin/bash
# Load credentials
eval $(grep 'export TRADING212' ~/.bashrc | tail -2)
eval $(grep 'export TELEGRAM' ~/.bashrc | tail -2)

# Run Flask dashboard
cd ~
python3 app.py
