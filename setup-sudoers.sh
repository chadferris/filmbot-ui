#!/bin/bash
# Setup sudoers permissions for filmbot user
# This allows the UI to configure network interfaces and manage systemd services

set -e

echo "=== Setting up sudoers permissions for filmbot user ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./setup-sudoers.sh"
    exit 1
fi

# Create sudoers file for filmbot
sudo tee /etc/sudoers.d/filmbot > /dev/null << 'EOF'
# Filmbot appliance sudoers configuration
# Allows filmbot user to manage network and systemd without password

# Systemd timer management
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl enable filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl disable filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl start filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl stop filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl is-active filmbot-record-*.service

# File management for systemd timers
filmbot ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/systemd/system/filmbot-record-*.service
filmbot ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/systemd/system/filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/rm /etc/systemd/system/filmbot-record-*.service
filmbot ALL=(ALL) NOPASSWD: /bin/rm /etc/systemd/system/filmbot-record-*.timer

# Network management
filmbot ALL=(ALL) NOPASSWD: /sbin/ip link set wlan* down
filmbot ALL=(ALL) NOPASSWD: /sbin/ip link set wlan* up
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl restart NetworkManager
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl restart systemd-resolved

# NetworkManager configuration (for ATEM interface setup)
filmbot ALL=(ALL) NOPASSWD: /usr/bin/nmcli connection modify *
filmbot ALL=(ALL) NOPASSWD: /usr/bin/nmcli connection up *
filmbot ALL=(ALL) NOPASSWD: /usr/bin/nmcli connection down *
EOF

echo "✓ Sudoers configuration created at /etc/sudoers.d/filmbot"
echo ""
echo "Permissions granted:"
echo "  - Systemd timer management (filmbot-record-*)"
echo "  - Network interface configuration (nmcli)"
echo "  - NetworkManager restart"
echo "  - systemd-resolved restart"
echo ""
