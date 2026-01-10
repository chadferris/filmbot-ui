# Filmbot UI - Deployment Guide

## Quick Start (Raspberry Pi)

### 1. Transfer Files to Raspberry Pi

```bash
# On your development machine
scp -r Filmbot/* filmbot@<raspberry-pi-ip>:/home/filmbot/filmbot-ui/
```

### 2. Run Installation Script

```bash
# On the Raspberry Pi
ssh filmbot@<raspberry-pi-ip>
cd ~/filmbot-ui
chmod +x install.sh
./install.sh
```

### 3. Start the UI

```bash
sudo systemctl start filmbot-ui.service
```

The UI will now be running on the touchscreen!

---

## Development Testing (Local Machine)

### Install Dependencies

```bash
cd Filmbot
pip install -r requirements.txt
```

### Run Test Suite

```bash
chmod +x test_ui.py
python3 test_ui.py
```

This will test each component individually.

### Run Full Application

```bash
python3 main.py
```

**Note**: Video preview will fail without `/dev/video5`, but all other features work.

---

## Production Deployment Checklist

### Before Deployment

- [ ] Test on development machine with `test_ui.py`
- [ ] Verify all Python dependencies install correctly
- [ ] Test wizard flow completely
- [ ] Test live view (without video if needed)
- [ ] Test settings screen

### On Raspberry Pi

- [ ] Ensure ATEM Mini is connected via USB
- [ ] Verify `/dev/video5` exists: `ls -l /dev/video5`
- [ ] Verify audio device: `arecord -l` (should show hw:2,0)
- [ ] Ensure rclone is configured: `rclone config`
- [ ] Test rclone connection: `rclone lsd filmbot-drive:`
- [ ] Verify NVMe is mounted: `df -h /mnt/nvme`
- [ ] Ensure recordings directory exists: `mkdir -p /mnt/nvme/recordings`

### Installation

- [ ] Run `install.sh` as filmbot user
- [ ] Verify service is enabled: `systemctl is-enabled filmbot-ui.service`
- [ ] Start service: `sudo systemctl start filmbot-ui.service`
- [ ] Check status: `sudo systemctl status filmbot-ui.service`
- [ ] View logs: `sudo journalctl -u filmbot-ui.service -f`

### Post-Installation

- [ ] Complete first-boot wizard on touchscreen
- [ ] Test Google Drive connection in wizard
- [ ] Add at least one recording schedule
- [ ] Verify schedule creates systemd timer: `systemctl list-timers filmbot-record-*`
- [ ] Test manual recording trigger (optional)
- [ ] Verify sync is working: `tail -f /var/log/filmbot-rclone.log`

---

## Important Configuration Notes

### Systemd Manager Dry-Run Mode

**CRITICAL**: The systemd manager is currently in `dry_run=True` mode for safety.

To enable actual systemd service creation, edit these files:

**wizard.py** (line ~405):
```python
# Change from:
systemd_mgr = SystemdManager(dry_run=True)
# To:
systemd_mgr = SystemdManager(dry_run=False)
```

**settings.py** (line ~32):
```python
# Change from:
self.systemd_mgr = SystemdManager(dry_run=True)
# To:
self.systemd_mgr = SystemdManager(dry_run=False)
```

### Fullscreen Mode

To enable fullscreen on the touchscreen, edit **main.py** (line ~30):

```python
# Uncomment:
self.showFullScreen()
```

### Touch Events

To enable touch event synthesis, edit **main.py** (line ~73):

```python
# Uncomment:
app.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, True)
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
sudo journalctl -u filmbot-ui.service -n 100 --no-pager

# Check if Python dependencies are installed
python3 -c "import PySide6; print('OK')"
python3 -c "import cv2; print('OK')"
```

### Video Preview Black Screen

```bash
# Verify video device
ls -l /dev/video5
v4l2-ctl --list-devices

# Test video capture
ffmpeg -f v4l2 -i /dev/video5 -frames:v 1 test.jpg
```

### Schedules Not Creating

1. Check dry_run mode is disabled (see above)
2. Verify sudo permissions: `sudo -l`
3. Check systemd logs: `sudo journalctl -u filmbot-record-*.timer`

### Touch Not Working

```bash
# Check touchscreen device
ls -l /dev/input/event*

# Test touch events
evtest
```

---

## Creating Master Image for Cloning

### 1. Complete Setup

- Install and configure everything
- Test all functionality
- Complete first-boot wizard
- Verify recordings work
- Verify sync works

### 2. Prepare for Imaging

```bash
# Optional: Clear config to force wizard on new units
sudo rm /opt/filmbot-appliance/config.json

# Clear logs
sudo journalctl --vacuum-time=1d

# Clear bash history
history -c
```

### 3. Shutdown

```bash
sudo poweroff
```

### 4. Create Image

Remove microSD card and create image:

```bash
# On imaging machine
sudo dd if=/dev/sdX of=filmbot-master-v1.0.img bs=4M status=progress conv=fsync

# Compress for storage
gzip filmbot-master-v1.0.img
```

### 5. Deploy to New Units

```bash
# Flash to new cards
gunzip -c filmbot-master-v1.0.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

Each new unit will boot into the first-boot wizard for organization-specific configuration.

---

## Version History

- **v1.0** - Initial release
  - First-boot wizard
  - Live monitoring view
  - Settings screen
  - Video preview
  - Schedule management
  - Google Drive sync configuration

