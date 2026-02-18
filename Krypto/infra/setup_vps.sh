#!/bin/bash

# Krypto VPS Setup Script (Ubuntu ARM64)
set -e

# Ensure we are in the repo root
cd "$(dirname "$0")/.."

echo "--- 🚀 Starting Krypto VPS Setup ---"

# 1. Update System
echo "--- 📦 Updating System ---"
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release python3-pip python3-venv

# 2. Install Docker (ARM64)
if ! command -v docker &> /dev/null
then
    echo "--- 🐳 Installing Docker (via convenience script) ---"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Enable Docker for non-root user
    sudo usermod -aG docker $USER
    echo "⚠️  User added to docker group. You may need to re-login for this to take effect."
else
    echo "--- ✅ Docker already installed ---"
fi

# 3. Setup Python Dependencies
echo "--- 🐍 Installing Python Dependencies ---"
pip3 install -r requirements.txt

# 4. Start Redis
echo "--- 🗄️ Starting Redis (ARM64) ---"
cd infra
sudo docker compose -f docker-compose.arm64.yml up -d
cd ..

# 5. Setup Systemd Services
echo "--- ⚙️ Configuring Systemd ---"
sudo cp infra/systemd/*.service /etc/systemd/system/

sudo systemctl daemon-reload

# Enable Services
sudo systemctl enable krypto-manager.service
sudo systemctl enable krypto-janitor.service

# Enable specific agents
sudo systemctl enable krypto-agent@orb.service
sudo systemctl enable krypto-agent@grid.service
# Add more agents as needed:
# sudo systemctl enable krypto-agent@dca.service

echo "--- 🏁 Setup Complete! ---"
echo "To start everything:"
echo "sudo systemctl start krypto-manager"
echo "sudo systemctl start krypto-agent@orb"
echo "..."
