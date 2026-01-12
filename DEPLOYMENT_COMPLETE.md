# Complete Filmbot Deployment Guide

This guide covers deploying Filmbot to a new location with all features including ATEM network access.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Fresh Installation](#fresh-installation)
3. [Cloning from Master Image](#cloning-from-master-image)
4. [Network Configuration](#network-configuration)
5. [Verification](#verification)

---

## Hardware Requirements

### Required Components
- Raspberry Pi 5 (8GB RAM recommended)
- microSD card (32GB minimum)
- NVMe SSD (via PCIe HAT)
- 4.3" DSI touchscreen (800×480)
- Blackmagic ATEM Mini (any model)
- USB-C cable (Pi to ATEM)
- Ethernet cable (Pi to ATEM for network control)
- Power supply for Pi
- Power supply for ATEM

### Network Setup
- WiFi network for internet and remote access
- Ethernet port on Pi for direct ATEM connection

---

## Fresh Installation

### Step 1: Prepare Raspberry Pi OS

1. **Flash Raspberry Pi OS (64-bit, Bookworm)**
   - Use Raspberry Pi Imager
   - Enable SSH
   - Set hostname (e.g., `filmbot-location1`)
   - Configure WiFi credentials
   - Set username: `filmbot`

2. **Boot and Update**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

### Step 2: Install Filmbot

1. **Clone Repository**
   ```bash
   cd ~
   git clone https://github.com/chadferris/filmbot-ui.git Filmbot
   cd Filmbot
   ```

2. **Run Installer**
   ```bash
   chmod +x install.sh setup-nvme.sh setup_atem_forwarding.sh
   ./install.sh
   ```

   This installs:
   - System dependencies (ffmpeg, rclone, v4l-utils, alsa-utils)
   - Python virtual environment
   - PySide6, OpenCV, PyATEMMax
   - Filmbot UI application
   - Recording and sync scripts
   - Systemd service for auto-start

### Step 3: Set Up Storage

```bash
sudo ./setup-nvme.sh
```

This will:
- Format NVMe drive (⚠️ ERASES ALL DATA)
- Create ext4 filesystem
- Mount at `/mnt/nvme`
- Add to `/etc/fstab` for auto-mount
- Create `/mnt/nvme/recordings` directory

### Step 4: Configure ATEM Network Access (Optional)

**Only needed if you want to control ATEM from Mac/PC on WiFi**

```bash
sudo ./setup_atem_forwarding.sh
```

This configures:
- IP forwarding
- iptables rules for UDP port 9910
- Persistent rules across reboots

See [ATEM_NETWORK_SETUP.md](ATEM_NETWORK_SETUP.md) for details.

### Step 5: Configure Google Drive

```bash
rclone config
```

1. Choose `n` for new remote
2. Name it (e.g., `filmbot-drive`)
3. Choose `drive` for Google Drive
4. Follow authentication steps
5. Choose `q` to quit

### Step 6: Reboot

```bash
sudo reboot
```

After reboot, the Filmbot UI will start automatically on the touchscreen.

---

## Cloning from Master Image

### Creating a Master Image

1. **Set up one Pi completely** following Fresh Installation steps above

2. **Clean up before imaging**
   ```bash
   # Optional: Clear config to force wizard on new units
   sudo rm /opt/filmbot-appliance/config.json
   
   # Clear logs
   sudo journalctl --vacuum-time=1d
   
   # Clear bash history
   history -c
   
   # Shutdown
   sudo poweroff
   ```

3. **Create image**
   ```bash
   # On imaging machine (Mac/Linux)
   sudo dd if=/dev/sdX of=filmbot-master-v1.0.img bs=4M status=progress conv=fsync
   
   # Compress
   gzip filmbot-master-v1.0.img
   ```

### Deploying from Master Image

1. **Flash image to new microSD cards**
   ```bash
   gunzip -c filmbot-master-v1.0.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
   ```

2. **Boot new Pi**
   - First boot will show setup wizard
   - Configure device name, schedules, etc.

3. **Update network settings if needed**
   - WiFi credentials (if different)
   - Hostname
   - ATEM IP (if different from 192.168.100.2)

---

## Network Configuration

### Standard Setup

```
[ATEM Mini] <--USB--> [Raspberry Pi] <--WiFi--> [Router] <--Internet-->
            <--Ethernet-->
```

### IP Addresses

**Default Configuration:**
- **Pi WiFi (wlan0):** DHCP (e.g., 192.168.1.91)
- **Pi Ethernet (eth0):** 192.168.100.3
- **ATEM:** 192.168.100.2

### ATEM Connection Options

1. **USB Only** (Default)
   - ATEM appears as UVC video device
   - Used for recording
   - No network control needed

2. **USB + Ethernet** (Recommended)
   - USB for video capture
   - Ethernet for network control
   - Allows ATEM Software Control from Mac/PC
   - Requires `setup_atem_forwarding.sh`

### Accessing ATEM from Mac/PC

After running `setup_atem_forwarding.sh`:

1. Download ATEM Software Control from Blackmagic Design
2. Connect to Pi's WiFi IP (e.g., 192.168.1.91)
3. Control ATEM remotely

---

## Verification

### Check Services

```bash
# UI service
sudo systemctl status filmbot-ui.service

# Recording timers (after wizard setup)
sudo systemctl list-timers filmbot-*
```

### Check Storage

```bash
# NVMe mount
df -h /mnt/nvme

# Recordings directory
ls -la /mnt/nvme/recordings
```

### Check ATEM Connection

```bash
# Video device (USB)
v4l2-ctl --list-devices

# Network (Ethernet)
ping 192.168.100.2

# PyATEMMax
cd /opt/filmbot-appliance/ui
source venv/bin/activate
python -c "import PyATEMMax; switcher = PyATEMMax.ATEMMax(); switcher.connect('192.168.100.2'); switcher.waitForConnection(); print('Connected!' if switcher.connected else 'Failed'); switcher.disconnect()"
deactivate
```

### Check Network Forwarding

```bash
# IP forwarding enabled
sysctl net.ipv4.ip_forward

# iptables rules
sudo iptables -t nat -L -n -v
```

---

## Troubleshooting

See individual documentation files:
- [ATEM_NETWORK_SETUP.md](ATEM_NETWORK_SETUP.md) - ATEM network issues
- [ADDITIONAL_DEPENDENCIES.md](ADDITIONAL_DEPENDENCIES.md) - Dependency issues
- [FRESH_INSTALL.md](FRESH_INSTALL.md) - Installation issues
- [README.md](README.md) - General troubleshooting

---

## Quick Reference

### Important Paths
- **Application:** `/opt/filmbot-appliance/ui/`
- **Config:** `/opt/filmbot-appliance/config.json`
- **Recordings:** `/mnt/nvme/recordings/`
- **Logs:** `sudo journalctl -u filmbot-ui.service -f`

### Important Commands
```bash
# Start/stop UI
sudo systemctl start filmbot-ui.service
sudo systemctl stop filmbot-ui.service

# View logs
sudo journalctl -u filmbot-ui.service -f

# Test ATEM connection
ping 192.168.100.2

# Check video devices
v4l2-ctl --list-devices
```

---

**Last Updated:** 2026-01-12
**Version:** 1.0 with ATEM Network Support

