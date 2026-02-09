#!/bin/bash
# Sovereign Sentinel - Cloudflare Tunnel Setup Script
# Run this script on Oracle VPS to establish permanent tunnel

set -e

echo "🛡️  Sovereign Sentinel - Cloudflare Tunnel Setup"
echo "================================================"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Installing..."
    curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
    echo "✅ cloudflared installed"
fi

# Login to Cloudflare (interactive)
echo ""
echo "📝 Step 1: Login to Cloudflare..."
echo "   This will open a browser. Please authorize the tunnel."
cloudflared tunnel login

# Create named tunnel
echo ""
echo "🔧 Step 2: Creating named tunnel 'sovereign-api'..."
if cloudflared tunnel list | grep -q "sovereign-api"; then
    echo "   ℹ️  Tunnel 'sovereign-api' already exists, skipping creation"
else
    cloudflared tunnel create sovereign-api
    echo "✅ Tunnel created"
fi

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep sovereign-api | awk '{print $1}')
echo "   Tunnel ID: ${TUNNEL_ID}"

# Copy config file
echo ""
echo "📋 Step 3: Setting up tunnel configuration..."
mkdir -p ~/.cloudflared
cp cloudflare-tunnel-config.yml ~/.cloudflared/config.yml
echo "✅ Config copied to ~/.cloudflared/config.yml"

# Route DNS
echo ""
echo "🌐 Step 4: Setting up DNS route..."
echo "   Creating CNAME: api.sovereign-sentinel.pages.dev → ${TUNNEL_ID}.cfargotunnel.com"
cloudflared tunnel route dns sovereign-api api.sovereign-sentinel.pages.dev || echo "   ℹ️  DNS route may already exist"

# Install systemd service
echo ""
echo "⚙️  Step 5: Installing systemd service..."
sudo cloudflared service install
sudo systemctl enable cloudflared
echo "✅ System service installed and enabled"

# Create systemd override to use our config
echo ""
echo "🔧 Step 6: Configuring systemd service..."
sudo mkdir -p /etc/systemd/system/cloudflared.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/cloudflared.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/ubuntu/.cloudflared/config.yml run sovereign-api
EOF
sudo systemctl daemon-reload
echo "✅ Systemd service configured"

# Start the tunnel
echo ""
echo "🚀 Step 7: Starting tunnel..."
sudo systemctl restart cloudflared
sleep 3
sudo systemctl status cloudflared --no-pager

echo ""
echo "================================================"
echo "✅ Cloudflare Tunnel Setup Complete!"
echo ""
echo "Your API is now accessible at:"
echo "   https://api.sovereign-sentinel.pages.dev"
echo ""
echo "Tunnel status:"
echo "   sudo systemctl status cloudflared"
echo ""
echo "View logs:"
echo "   sudo journalctl -u cloudflared -f"
echo ""
echo "Test endpoint:"
echo "   curl https://api.sovereign-sentinel.pages.dev/api/dashboard"
echo "================================================"
