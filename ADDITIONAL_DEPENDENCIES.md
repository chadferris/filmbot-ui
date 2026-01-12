# Additional Dependencies for Filmbot

This document lists all additional packages and dependencies that have been added beyond the base `install.sh` script.

## System Packages (apt)

### Network and Firewall
- **iptables-persistent** - Saves iptables rules across reboots
  ```bash
  sudo apt-get install -y iptables-persistent
  ```

### Python ATEM Control
- **PyATEMMax** - Python library for controlling Blackmagic ATEM switchers
  ```bash
  pip install PyATEMMax
  ```

## Python Packages (pip/venv)

Add to `requirements.txt`:
```
PySide6>=6.6.0
opencv-python>=4.8.0
psutil>=5.9.0
PyATEMMax>=0.3.0
```

## System Configuration

### IP Forwarding for ATEM Network Access

**Purpose:** Allows access to ATEM Mini from Mac/other computers on WiFi network when ATEM is connected via Ethernet to Pi.

**Configuration:**
1. Enable IP forwarding in `/etc/sysctl.conf`:
   ```
   net.ipv4.ip_forward=1
   ```

2. iptables rules (saved to `/etc/iptables/rules.v4`):
   ```bash
   # Forward UDP port 9910 (ATEM control protocol)
   iptables -t nat -A PREROUTING -i wlan0 -p udp --dport 9910 -j DNAT --to-destination 192.168.100.2:9910
   iptables -t nat -A POSTROUTING -o eth0 -p udp --dport 9910 -d 192.168.100.2 -j MASQUERADE
   iptables -A FORWARD -i wlan0 -o eth0 -p udp --dport 9910 -d 192.168.100.2 -j ACCEPT
   iptables -A FORWARD -i eth0 -o wlan0 -p udp --sport 9910 -s 192.168.100.2 -j ACCEPT
   ```

**Automated Setup:**
```bash
sudo ./setup_atem_forwarding.sh
```

## Network Configuration

### Ethernet (eth0)
- **IP Address:** 192.168.100.3
- **Subnet:** 255.255.255.0
- **Purpose:** Direct connection to ATEM Mini

### WiFi (wlan0)
- **IP Address:** 192.168.1.91 (DHCP - may vary)
- **Purpose:** Connection to local network and internet

### ATEM Mini
- **IP Address:** 192.168.100.2
- **Protocol:** UDP port 9910
- **Connection:** Ethernet to Pi

## File Structure Updates

### New Files
- `setup_atem_forwarding.sh` - Automated ATEM network setup script
- `ATEM_NETWORK_SETUP.md` - Documentation for ATEM network access
- `ADDITIONAL_DEPENDENCIES.md` - This file

### Modified Files
None - all changes are additive

## Installation Order for New Devices

1. **Base Filmbot Installation**
   ```bash
   ./install.sh
   sudo ./setup-nvme.sh
   ```

2. **Install Additional Dependencies**
   ```bash
   # Install iptables-persistent
   sudo apt-get install -y iptables-persistent
   
   # Install PyATEMMax in venv
   cd /opt/filmbot-appliance/ui
   source venv/bin/activate
   pip install PyATEMMax
   deactivate
   ```

3. **Configure ATEM Network Access**
   ```bash
   sudo ./setup_atem_forwarding.sh
   ```

4. **Configure rclone**
   ```bash
   rclone config
   ```

5. **Reboot**
   ```bash
   sudo reboot
   ```

## Verification Commands

### Check IP Forwarding
```bash
sysctl net.ipv4.ip_forward
# Should return: net.ipv4.ip_forward = 1
```

### Check iptables Rules
```bash
sudo iptables -t nat -L -n -v
# Should show DNAT and MASQUERADE rules for port 9910
```

### Check ATEM Connectivity
```bash
# From Pi
ping -c 2 192.168.100.2

# From Mac (after setup)
# In ATEM Software Control, connect to Pi's WiFi IP (e.g., 192.168.1.91)
```

### Check PyATEMMax Installation
```bash
cd /opt/filmbot-appliance/ui
source venv/bin/activate
python -c "import PyATEMMax; print('PyATEMMax version:', PyATEMMax.__version__)"
deactivate
```

## Notes

- **ATEM Protocol:** Uses UDP, not TCP. This is critical for iptables rules.
- **IP Addresses:** May need adjustment based on your network configuration
- **Persistence:** All configurations persist across reboots when properly saved
- **No Impact:** These changes don't affect existing Filmbot functionality

## Troubleshooting

### PyATEMMax Import Error
```bash
# Ensure you're in the venv
cd /opt/filmbot-appliance/ui
source venv/bin/activate
pip install PyATEMMax
```

### ATEM Not Accessible from Mac
```bash
# Verify iptables rules are loaded
sudo iptables -t nat -L -n -v

# Verify IP forwarding is enabled
sysctl net.ipv4.ip_forward

# Check ATEM is reachable from Pi
ping 192.168.100.2
```

### Rules Don't Persist After Reboot
```bash
# Ensure iptables-persistent is installed
sudo apt-get install -y iptables-persistent

# Save rules manually
sudo netfilter-persistent save
```

---

**Last Updated:** 2026-01-12

