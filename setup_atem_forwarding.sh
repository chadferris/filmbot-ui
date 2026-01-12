#!/bin/bash
# Setup IP forwarding so ATEM can be accessed from WiFi network
# IMPORTANT: ATEM uses UDP port 9910, not TCP!

set -e

echo "=== Setting up ATEM Network Access ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./setup_atem_forwarding.sh"
    exit 1
fi

# Install iptables-persistent if not already installed
echo "Installing iptables-persistent..."
apt-get update
apt-get install -y iptables-persistent

# Enable IP forwarding
echo "Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1

# Make it permanent
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    echo "Added to /etc/sysctl.conf"
fi

# Set up iptables rules to forward ATEM traffic (UDP port 9910)
echo "Setting up iptables rules for ATEM (UDP port 9910)..."
iptables -t nat -A PREROUTING -i wlan0 -p udp --dport 9910 -j DNAT --to-destination 192.168.100.2:9910
iptables -t nat -A POSTROUTING -o eth0 -p udp --dport 9910 -d 192.168.100.2 -j MASQUERADE
iptables -A FORWARD -i wlan0 -o eth0 -p udp --dport 9910 -d 192.168.100.2 -j ACCEPT
iptables -A FORWARD -i eth0 -o wlan0 -p udp --sport 9910 -s 192.168.100.2 -j ACCEPT

# Save iptables rules
echo "Saving iptables rules..."
netfilter-persistent save

echo ""
echo "=== Setup Complete ==="
echo ""
echo "✓ IP forwarding enabled"
echo "✓ iptables rules configured for UDP port 9910"
echo "✓ Rules saved and will persist across reboots"
echo ""
echo "You can now access ATEM from your Mac:"
echo "  - In ATEM Software Control, connect to: 192.168.1.91"
echo "  - Or use the Pi's WiFi IP address"
echo ""
echo "Network topology:"
echo "  Mac (WiFi) <--> Pi (192.168.1.91) <--> ATEM (192.168.100.2)"
echo ""

