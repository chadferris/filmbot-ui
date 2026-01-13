#!/bin/bash
# Setup Filmbot Health Monitoring System

set -e

echo "=========================================="
echo "Filmbot Health Monitoring Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

INSTALL_DIR="/opt/filmbot-appliance"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if filmbot is installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Error: Filmbot not found at $INSTALL_DIR"
    echo "Please run install.sh first"
    exit 1
fi

echo "Installing health monitoring system..."
echo ""

# Copy health check scripts
echo "→ Copying health check scripts..."
cp "$SCRIPT_DIR/health_check.py" "$INSTALL_DIR/ui/"
cp "$SCRIPT_DIR/email_notify.py" "$INSTALL_DIR/ui/"
cp "$SCRIPT_DIR/config_manager.py" "$INSTALL_DIR/ui/"
chmod +x "$INSTALL_DIR/ui/health_check.py"

# Install psutil if not already installed
echo "→ Installing Python dependencies..."
"$INSTALL_DIR/ui/venv/bin/pip" install psutil --quiet

# Install systemd services
echo "→ Installing systemd services..."
cp "$SCRIPT_DIR/systemd/filmbot-health.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/filmbot-health.timer" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/filmbot-daily-report.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/filmbot-daily-report.timer" /etc/systemd/system/

# Reload systemd
echo "→ Reloading systemd..."
systemctl daemon-reload

# Enable and start timers
echo "→ Enabling health check timer (runs every 5 minutes)..."
systemctl enable filmbot-health.timer
systemctl start filmbot-health.timer

echo "→ Enabling daily report timer (runs at 8 AM)..."
systemctl enable filmbot-daily-report.timer
systemctl start filmbot-daily-report.timer

echo ""
echo "=========================================="
echo "Health Monitoring Installation Complete!"
echo "=========================================="
echo ""
echo "Services installed:"
echo "  • filmbot-health.timer - Runs health checks every 5 minutes"
echo "  • filmbot-daily-report.timer - Sends daily report at 8 AM"
echo ""
echo "To configure email alerts:"
echo "  1. Generate Gmail app password:"
echo "     https://myaccount.google.com/apppasswords"
echo "  2. Configure in Filmbot UI Settings"
echo "     OR edit /opt/filmbot-appliance/config.json"
echo ""
echo "Useful commands:"
echo "  • Test health check:"
echo "    sudo -u filmbot $INSTALL_DIR/ui/venv/bin/python3 $INSTALL_DIR/ui/health_check.py --test"
echo ""
echo "  • Send test daily report:"
echo "    sudo -u filmbot $INSTALL_DIR/ui/venv/bin/python3 $INSTALL_DIR/ui/health_check.py --daily-report"
echo ""
echo "  • Check timer status:"
echo "    systemctl status filmbot-health.timer"
echo "    systemctl status filmbot-daily-report.timer"
echo ""
echo "  • View logs:"
echo "    journalctl -u filmbot-health.service -f"
echo ""

