#!/bin/bash
# Filmbot UI Installation Script
# Complete setup for Filmbot Recording Appliance on Raspberry Pi
# This script installs everything needed for a fresh Raspberry Pi OS installation

set -e

echo "=== Filmbot Recording Appliance - Complete Installation ==="
echo ""
echo "This script will install:"
echo "  - Blackmagic Desktop Video drivers"
echo "  - Python dependencies and virtual environment"
echo "  - Filmbot UI application"
echo "  - Auto-login and auto-start configuration"
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

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    DEB_ARCH="arm64"
elif [ "$ARCH" = "armv7l" ]; then
    DEB_ARCH="armhf"
else
    echo "Error: Unsupported architecture: $ARCH"
    exit 1
fi

echo "Detected architecture: $ARCH ($DEB_ARCH)"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-full python3-pip python3-venv libgl1 libglib2.0-0 \
    libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libdbus-1-3 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-shape0 v4l-utils alsa-utils wget curl \
    ffmpeg rclone parted

# Install Blackmagic Desktop Video drivers
echo ""
echo "Installing Blackmagic Desktop Video drivers..."

# Check if already installed
if dpkg -l | grep -q desktopvideo; then
    echo "Blackmagic Desktop Video already installed, skipping..."
else
    DESKTOP_VIDEO_VERSION="12.9"
    DESKTOP_VIDEO_URL="https://sw.blackmagicdesign.com/DesktopVideo/v${DESKTOP_VIDEO_VERSION}/Blackmagic_Desktop_Video_Linux_${DESKTOP_VIDEO_VERSION}.tar.gz"

    echo "Downloading Desktop Video ${DESKTOP_VIDEO_VERSION}..."
    cd /tmp
    wget -q --show-progress "${DESKTOP_VIDEO_URL}" -O desktopvideo.tar.gz || {
        echo "Warning: Could not download Blackmagic drivers automatically"
        echo "Please download manually from: https://www.blackmagicdesign.com/support"
        echo "Continuing without Blackmagic drivers..."
    }

    if [ -f desktopvideo.tar.gz ]; then
        echo "Extracting..."
        tar -xzf desktopvideo.tar.gz

        # Find the .deb file for our architecture
        DEB_FILE=$(find . -name "desktopvideo_*_${DEB_ARCH}.deb" | head -n 1)

        if [ -n "$DEB_FILE" ]; then
            echo "Installing $DEB_FILE..."
            sudo dpkg -i "$DEB_FILE" || true
            sudo apt-get install -f -y
            echo "Blackmagic Desktop Video installed successfully!"
        else
            echo "Warning: Could not find .deb file for architecture $DEB_ARCH"
        fi

        # Cleanup
        rm -rf /tmp/Blackmagic_Desktop_Video_Linux_*
        rm -f /tmp/desktopvideo.tar.gz
    fi
fi

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/filmbot-appliance/ui
sudo chown -R $USER:$USER /opt/filmbot-appliance/ui

# Copy files
echo "Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp "$SCRIPT_DIR"/*.py /opt/filmbot-appliance/ui/
cp "$SCRIPT_DIR"/requirements.txt /opt/filmbot-appliance/ui/

# Copy recording and sync scripts
echo "Installing recording scripts..."
sudo cp "$SCRIPT_DIR"/record-atem.sh /opt/filmbot-appliance/
sudo cp "$SCRIPT_DIR"/sync-drive.sh /opt/filmbot-appliance/
sudo chmod +x /opt/filmbot-appliance/record-atem.sh
sudo chmod +x /opt/filmbot-appliance/sync-drive.sh
sudo chown filmbot:filmbot /opt/filmbot-appliance/*.sh

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

# Configure auto-login
echo ""
echo "Configuring auto-login for $USER..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

echo ""
echo "=== Installation Complete ==="
echo ""
echo "IMPORTANT: Before using Filmbot, you must:"
echo ""
echo "1. Set up NVMe storage (if not already done):"
echo "   sudo ./setup-nvme.sh"
echo ""
echo "2. Configure rclone for Google Drive:"
echo "   rclone config"
echo "   - Create a new remote (e.g., 'filmbot-drive')"
echo "   - Choose 'Google Drive'"
echo "   - Follow the authentication steps"
echo ""
echo "3. Reboot the Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "After reboot, the Filmbot UI will start automatically."
echo "Follow the setup wizard to configure devices and schedules."
echo ""
echo "Manual controls:"
echo "  Start UI:   sudo systemctl start filmbot-ui.service"
echo "  Stop UI:    sudo systemctl stop filmbot-ui.service"
echo "  Status:     sudo systemctl status filmbot-ui.service"
echo "  Logs:       sudo journalctl -u filmbot-ui.service -f"
echo ""

# Check if NVMe is already mounted
if mount | grep -q "/mnt/nvme"; then
    echo "✓ NVMe drive is already mounted at /mnt/nvme"
    echo ""
else
    echo "⚠ NVMe drive not detected. Run setup-nvme.sh before rebooting."
    echo ""
fi

# Check if rclone is configured
if rclone listremotes 2>/dev/null | grep -q .; then
    echo "✓ rclone remotes configured:"
    rclone listremotes
    echo ""
else
    echo "⚠ No rclone remotes configured. Run 'rclone config' before using."
    echo ""
fi

read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi

