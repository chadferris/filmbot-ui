#!/bin/bash
# Filmbot UI Installation Script
# Run this on the Raspberry Pi to install the touchscreen UI

set -e

echo "=== Filmbot UI Installation ==="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Do not run this script as root"
    echo "Run as the filmbot user: ./install.sh"
    exit 1
fi

# Check if filmbot user
if [ "$USER" != "filmbot" ]; then
    echo "Warning: This script should be run as the 'filmbot' user"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-full python3-pip python3-venv libgl1 libglib2.0-0 \
    libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libdbus-1-3 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-shape0 v4l-utils alsa-utils

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/filmbot-appliance/ui
sudo chown -R $USER:$USER /opt/filmbot-appliance/ui

# Copy files
echo "Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp "$SCRIPT_DIR"/*.py /opt/filmbot-appliance/ui/
cp "$SCRIPT_DIR"/requirements.txt /opt/filmbot-appliance/ui/

# Create virtual environment
echo "Creating Python virtual environment..."
cd /opt/filmbot-appliance/ui
python3 -m venv venv

# Install Python dependencies
echo "Installing Python dependencies..."
./venv/bin/pip install -r requirements.txt

# Make main.py executable
chmod +x /opt/filmbot-appliance/ui/main.py

# Install systemd service
echo "Installing systemd service..."
sudo cp "$SCRIPT_DIR"/filmbot-ui.service /etc/systemd/system/
sudo systemctl daemon-reload

# Configure sudoers
echo "Configuring sudo permissions..."
sudo tee /etc/sudoers.d/filmbot > /dev/null <<EOF
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl enable filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl disable filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl start filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl stop filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl is-active filmbot-record-*.service
EOF

sudo chmod 0440 /etc/sudoers.d/filmbot

# Enable service
echo "Enabling filmbot-ui service..."
sudo systemctl enable filmbot-ui.service

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start the UI now:"
echo "  sudo systemctl start filmbot-ui.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status filmbot-ui.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u filmbot-ui.service -f"
echo ""
echo "The UI will start automatically on next boot."

