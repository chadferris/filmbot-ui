#!/bin/bash
# Configure eth0 with static IP for ATEM communication
# This must be run during initial setup to ensure eth0 can talk to ATEM at 192.168.100.2

set -e

echo "=== Configuring ATEM Network Interface ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./setup-atem-network.sh"
    exit 1
fi

ATEM_INTERFACE="eth0"
ATEM_IP="192.168.100.3/24"
ATEM_DEVICE_IP="192.168.100.2"

echo "Configuring $ATEM_INTERFACE with static IP $ATEM_IP..."

# Configure NetworkManager to use manual IP on eth0
nmcli connection modify "Wired connection 1" ipv4.method manual 2>/dev/null || {
    # If "Wired connection 1" doesn't exist, create it
    echo "Creating new connection profile..."
    nmcli connection add type ethernet ifname $ATEM_INTERFACE con-name "ATEM Network"
    nmcli connection modify "ATEM Network" ipv4.method manual
    nmcli connection modify "ATEM Network" ipv4.addresses $ATEM_IP
    nmcli connection modify "ATEM Network" connection.autoconnect yes
    nmcli connection up "ATEM Network"
}

# If "Wired connection 1" exists, configure it
nmcli connection show "Wired connection 1" >/dev/null 2>&1 && {
    nmcli connection modify "Wired connection 1" ipv4.method manual
    nmcli connection modify "Wired connection 1" ipv4.addresses $ATEM_IP
    nmcli connection modify "Wired connection 1" connection.autoconnect yes
    nmcli connection down "Wired connection 1" 2>/dev/null || true
    nmcli connection up "Wired connection 1"
}

echo "Waiting for interface to come up..."
sleep 3

# Verify the IP is assigned
IP_ASSIGNED=$(ip addr show $ATEM_INTERFACE | grep "inet " | awk '{print $2}' | head -n1)

if [ "$IP_ASSIGNED" == "$ATEM_IP" ]; then
    echo "✓ $ATEM_INTERFACE configured with $IP_ASSIGNED"
else
    echo "✗ Failed to assign IP. Current: $IP_ASSIGNED"
    exit 1
fi

# Test ATEM connectivity
echo "Testing ATEM connectivity at $ATEM_DEVICE_IP..."
if ping -c 3 -W 2 $ATEM_DEVICE_IP >/dev/null 2>&1; then
    echo "✓ ATEM responding at $ATEM_DEVICE_IP"
else
    echo "⚠ ATEM not responding (this is OK if ATEM is powered off)"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Network configuration:"
echo "  - Interface: $ATEM_INTERFACE"
echo "  - Pi IP: $ATEM_IP"
echo "  - ATEM IP: $ATEM_DEVICE_IP"
echo "  - Autoconnect: Enabled (will persist across reboots)"
echo ""
echo "This configuration is saved in NetworkManager and will survive reboots."
echo ""
