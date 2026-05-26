#!/bin/bash
# Install Network Watchdog for Filmbot

echo "Installing network watchdog..."

# Copy the watchdog script
sudo cp network-watchdog.sh /opt/filmbot-appliance/
sudo chmod +x /opt/filmbot-appliance/network-watchdog.sh
sudo chown filmbot:filmbot /opt/filmbot-appliance/network-watchdog.sh

# Create log file
sudo touch /var/log/filmbot-network.log
sudo chown filmbot:filmbot /var/log/filmbot-network.log

# Create systemd service
sudo tee /etc/systemd/system/filmbot-network-watchdog.service > /dev/null << 'EOF'
[Unit]
Description=Filmbot Network Watchdog
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=filmbot
ExecStart=/opt/filmbot-appliance/network-watchdog.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer (runs every 2 minutes)
sudo tee /etc/systemd/system/filmbot-network-watchdog.timer > /dev/null << 'EOF'
[Unit]
Description=Filmbot Network Watchdog Timer
Requires=filmbot-network-watchdog.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=2min
AccuracySec=30s

[Install]
WantedBy=timers.target
EOF

# Add sudo permissions for network operations
sudo tee /etc/sudoers.d/filmbot-network > /dev/null << 'EOF'
filmbot ALL=(ALL) NOPASSWD: /sbin/ip link set wlan* down
filmbot ALL=(ALL) NOPASSWD: /sbin/ip link set wlan* up
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl restart NetworkManager
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl restart systemd-resolved
EOF

# Reload systemd and enable the timer
sudo systemctl daemon-reload
sudo systemctl enable filmbot-network-watchdog.timer
sudo systemctl start filmbot-network-watchdog.timer

echo ""
echo "✓ Network watchdog installed and started"
echo ""
echo "The watchdog will:"
echo "  - Check network connectivity every 2 minutes"
echo "  - Automatically reconnect WiFi if connection is lost"
echo "  - Fix DNS issues by restarting systemd-resolved"
echo "  - Log all activity to /var/log/filmbot-network.log"
echo ""
echo "To check status:"
echo "  systemctl status filmbot-network-watchdog.timer"
echo ""
echo "To view logs:"
echo "  tail -f /var/log/filmbot-network.log"
echo ""
