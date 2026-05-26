#!/bin/bash
# Filmbot Network Watchdog
# Checks internet connectivity and reconnects WiFi if needed

LOG_FILE="/var/log/filmbot-network.log"

# Function to log messages
log_message() {
    echo "$(date): $1" >> "$LOG_FILE"
}

# Check if we can reach the internet
check_internet() {
    # Try to ping Google DNS (doesn't require name resolution)
    if ping -c 2 -W 5 8.8.8.8 >/dev/null 2>&1; then
        return 0  # Internet is working
    else
        return 1  # No internet
    fi
}

# Check DNS resolution
check_dns() {
    if nslookup google.com >/dev/null 2>&1; then
        return 0  # DNS is working
    else
        return 1  # DNS is broken
    fi
}

# Main watchdog logic
log_message "Network watchdog starting check..."

if check_internet; then
    # Internet is working, check DNS
    if check_dns; then
        log_message "Network OK - Internet and DNS working"
        exit 0
    else
        # DNS is broken but internet works - restart systemd-resolved
        log_message "DNS broken, restarting systemd-resolved..."
        sudo systemctl restart systemd-resolved
        sleep 5
        if check_dns; then
            log_message "DNS fixed after restart"
            exit 0
        else
            log_message "DNS still broken after restart"
        fi
    fi
else
    # No internet - try to reconnect WiFi
    log_message "No internet detected, reconnecting WiFi..."
    
    # Get the WiFi interface name (usually wlan0)
    WIFI_INTERFACE=$(ip link show | grep -o "wlan[0-9]" | head -n 1)
    
    if [ -z "$WIFI_INTERFACE" ]; then
        log_message "ERROR: Could not find WiFi interface"
        exit 1
    fi
    
    log_message "WiFi interface: $WIFI_INTERFACE"
    
    # Restart the WiFi interface
    sudo ip link set "$WIFI_INTERFACE" down
    sleep 2
    sudo ip link set "$WIFI_INTERFACE" up
    sleep 5
    
    # Restart NetworkManager to force reconnection
    sudo systemctl restart NetworkManager
    sleep 10
    
    # Check if internet is back
    if check_internet; then
        log_message "SUCCESS: WiFi reconnected, internet restored"
        exit 0
    else
        log_message "FAILED: WiFi reconnect did not restore internet"
        exit 1
    fi
fi
