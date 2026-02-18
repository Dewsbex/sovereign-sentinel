#!/bin/bash
# AI Brain Setup Script for Oracle VPS
# Handles installation of systemd services and dependencies

# 1. Install Dependencies
echo "Installing Python dependencies..."
# Assuming requirements are in parent dir or locally defined
pip3 install python-dotenv requests 

# 2. Copy Systemd Services
echo "Installing Systemd Services..."
sudo cp AI_Brain/infrastructure/systemd/krypto-engine.service /etc/systemd/system/
sudo cp AI_Brain/infrastructure/systemd/krypto-heartbeat.service /etc/systemd/system/

# 3. Reload & Enable
echo "Reloading Systemd..."
sudo systemctl daemon-reload

echo "Enabling Services..."
sudo systemctl enable krypto-engine
sudo systemctl enable krypto-heartbeat

# 4. Start Services (User verification needed first usually, but automated setup implies starting)
echo "Starting Services..."
sudo systemctl start krypto-heartbeat
# Engine might need manual start or config check
# sudo systemctl start krypto-engine

echo "Setup Complete. Services active."
