# Filmbot UI - Quick Start Guide

## Pre-Deployment Checklist

Before transferring files, verify on the Raspberry Pi:

```bash
# 1. Check ATEM video device
ls -l /dev/video5

# 2. Check audio device
arecord -l | grep -i "card 2"

# 3. Check NVMe mount
df -h /mnt/nvme

# 4. Check recordings directory
ls -ld /mnt/nvme/recordings

# 5. Check rclone configuration
rclone config show

# 6. Test rclone connection
rclone lsd filmbot-drive:
```

## Installation Steps

### Step 1: Transfer Files

From your local machine:

```bash
# Create temporary directory on Pi
ssh filmbot@<pi-ip> "mkdir -p ~/filmbot-ui-install"

# Transfer all files
scp -r /Users/chadferris/Filmbot/* filmbot@<pi-ip>:~/filmbot-ui-install/
```

### Step 2: Run Installation

SSH into the Pi:

```bash
ssh filmbot@<pi-ip>
cd ~/filmbot-ui-install
chmod +x install.sh
./install.sh
```

The installer will:
- Install system dependencies (apt packages)
- Install Python dependencies (PySide6, opencv-python, psutil,
  websocket-client)
- Copy top-level Python files to `/opt/filmbot-appliance/ui/` and the
  auxiliary `ui/` subdirectory (which contains `propresenter_listener.py`)
  to `/opt/filmbot-appliance/ui/ui/`
- Configure sudoers for systemd access
- Install and enable the `filmbot-ui` and `filmbot-propresenter` systemd
  services

### Step 3: Enable Production Mode

**IMPORTANT**: Before starting, enable production mode:

```bash
cd /opt/filmbot-appliance/ui

# Edit wizard.py - change dry_run to False
nano wizard.py
# Find line ~405: systemd_mgr = SystemdManager(dry_run=True)
# Change to: systemd_mgr = SystemdManager(dry_run=False)

# Edit settings.py - change dry_run to False
nano settings.py
# Find line ~32: self.systemd_mgr = SystemdManager(dry_run=True)
# Change to: self.systemd_mgr = SystemdManager(dry_run=False)

# Optional: Enable fullscreen in main.py
nano main.py
# Find line ~30 and uncomment: self.showFullScreen()
```

### Step 4: Start the UI

```bash
sudo systemctl start filmbot-ui.service
```

### Step 5: Monitor Startup

```bash
# Check service status
sudo systemctl status filmbot-ui.service

# Watch logs in real-time
sudo journalctl -u filmbot-ui.service -f
```

## Expected Behavior

1. **First Boot**: Setup wizard should appear on touchscreen
2. **Wizard Flow**:
   - Welcome screen → Click "Start Setup"
   - Drive setup → Enter remote and folder → Test connection
   - Schedule setup → Add schedules → Click "Next"
   - Finish → Click "Finish"
3. **After Wizard**: Live view with video preview should appear
4. **Settings**: The Settings screen uses a tabbed layout
   (System / Devices / Drive / Schedules / Integrations) so nothing
   scrolls off the 4.3" touchscreen

## ProPresenter Integration (Optional)

To trigger recordings from ProPresenter slide notes:

1. On the ProPresenter machine, enable network access:
   - **PP6**: *Preferences → Network → Enable Network* and turn on
     *Stage Display App* (set a password).
   - **PP7**: *Preferences → Network → Enable Network* (REST API).
2. On the Filmbot touchscreen, open **Settings → Integrations →
   🎬 ProPresenter** and enter:
   - Version (`ProPresenter 6` or `ProPresenter 7`)
   - IP address of the ProPresenter machine
   - Port (PP6 Stage Display default `50001`, PP7 REST default `1025`)
   - Password (PP6 Stage Display password; leave blank for PP7)
3. Tap **Save** — the `filmbot-propresenter.service` restarts and picks
   up the new settings.
4. In your ProPresenter document, add `[START_RECORD]` to the slide notes
   of the slide that should begin recording, and `[STOP_RECORD]` to the
   slide that should end it.

Verify the listener is running:

```bash
sudo systemctl status filmbot-propresenter.service
sudo journalctl -u filmbot-propresenter.service -f
tail -f /var/log/filmbot-propresenter.log
```

## Troubleshooting

### Service fails to start

```bash
# Check detailed error
sudo journalctl -u filmbot-ui.service -n 50 --no-pager

# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Permission issues: check /opt/filmbot-appliance/ui ownership
# - Display issues: check DISPLAY and QT_QPA_PLATFORM environment
```

### No video preview

```bash
# Verify video device
ls -l /dev/video5
v4l2-ctl --list-devices

# Check if device is accessible
ffmpeg -f v4l2 -i /dev/video5 -frames:v 1 /tmp/test.jpg
```

### Schedules not creating

```bash
# Verify dry_run is disabled in wizard.py and settings.py
grep "dry_run" /opt/filmbot-appliance/ui/wizard.py
grep "dry_run" /opt/filmbot-appliance/ui/settings.py

# Check sudo permissions
sudo -l -U filmbot | grep systemctl
```

### Touch not working

```bash
# Check if running in fullscreen/EGLFS mode
ps aux | grep filmbot-ui

# Verify touchscreen device
ls -l /dev/input/event*
```

### ProPresenter listener not triggering

```bash
# Confirm the service is running
sudo systemctl status filmbot-propresenter.service

# Tail the listener log for connection or auth errors
sudo journalctl -u filmbot-propresenter.service -f
tail -f /var/log/filmbot-propresenter.log

# Verify current configuration
python3 -c "from config_manager import ConfigManager; \
    print(ConfigManager().get_propresenter_config())"

# After changing settings via the UI, the service auto-restarts.
# To restart manually:
sudo systemctl restart filmbot-propresenter.service
```

Common issues:
- Wrong IP/port or firewall blocking the ProPresenter machine
- PP6 Stage Display password mismatch (check listener log for
  "authentication rejected")
- PP7 network API not enabled in ProPresenter preferences
- Slide notes typed with the wrong casing — tags are literal and
  case-sensitive: `[START_RECORD]` and `[STOP_RECORD]`

## Post-Installation Testing

After wizard completes:

```bash
# 1. Verify config was created
cat /opt/filmbot-appliance/config.json

# 2. Check if timers were created
systemctl list-timers filmbot-record-*

# 3. Verify timer files exist
ls -l /etc/systemd/system/filmbot-record-*.timer
ls -l /etc/systemd/system/filmbot-record-*.service

# 4. Check sync log
tail -f /var/log/filmbot-rclone.log

# 5. Test manual recording (optional)
sudo systemctl start filmbot-record-service-1.service
```

## Quick Commands Reference

```bash
# Start UI
sudo systemctl start filmbot-ui.service

# Stop UI
sudo systemctl stop filmbot-ui.service

# Restart UI
sudo systemctl restart filmbot-ui.service

# View logs
sudo journalctl -u filmbot-ui.service -f

# Check status
sudo systemctl status filmbot-ui.service

# Disable autostart
sudo systemctl disable filmbot-ui.service

# Enable autostart
sudo systemctl enable filmbot-ui.service

# Reset configuration (force wizard)
sudo rm /opt/filmbot-appliance/config.json
sudo systemctl restart filmbot-ui.service

# ProPresenter listener
sudo systemctl start filmbot-propresenter.service
sudo systemctl stop filmbot-propresenter.service
sudo systemctl restart filmbot-propresenter.service
sudo systemctl status filmbot-propresenter.service
sudo journalctl -u filmbot-propresenter.service -f
```

## Next Steps After Successful Installation

1. Complete the setup wizard on the touchscreen
2. Add your recording schedules
3. Test a manual recording
4. Verify sync to Google Drive works
5. Let it run through a scheduled recording cycle
6. Monitor logs for any issues

## Getting Help

If you encounter issues:

1. Check logs: `sudo journalctl -u filmbot-ui.service -n 100`
2. Verify hardware: ATEM connected, video device exists
3. Check permissions: filmbot user has access to required files
4. Test components individually with `test_ui.py`

