# Filmbot Recording Appliance - Touchscreen UI

Python-based touchscreen application for the Filmbot recording appliance running on Raspberry Pi 5 with a 4.3" touchscreen.

## Features

- **First-Boot Setup Wizard**: Guides users through initial configuration
  - Video and audio device selection (auto-detected)
  - Google Drive authentication and folder setup
  - Recording schedule configuration
  - Device naming

- **Live Monitoring View**: Main operational screen
  - Real-time video preview from ATEM Mini
  - Recording status indicator
  - Next scheduled recording display
  - Google Drive sync status
  - Local storage usage

- **Settings Screen**: Post-setup configuration
  - Change video/audio devices
  - Modify Google Drive settings
  - Add/remove recording schedules
  - View system information
  - Update device name

## Requirements

- Raspberry Pi 5 (8GB RAM recommended)
- Raspberry Pi OS (64-bit, Debian 13 Bookworm)
- Python 3.11+
- 4.3" DSI touchscreen (800×480)
- Blackmagic ATEM Mini connected via USB

## Installation

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv libgl1-mesa-glx libglib2.0-0 \
    libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libdbus-1-3
```

### 2. Create Application Directory

```bash
sudo mkdir -p /opt/filmbot-appliance/ui
sudo chown filmbot:filmbot /opt/filmbot-appliance/ui
```

### 3. Copy Application Files

Copy all Python files to `/opt/filmbot-appliance/ui/`:

```bash
cd /opt/filmbot-appliance/ui
# Copy files from this repository
cp /path/to/Filmbot/*.py .
cp /path/to/Filmbot/requirements.txt .
```

### 4. Install Python Dependencies

```bash
cd /opt/filmbot-appliance/ui
python3 -m pip install -r requirements.txt
```

### 5. Make main.py Executable

```bash
chmod +x /opt/filmbot-appliance/ui/main.py
```

### 6. Install Systemd Service

```bash
sudo cp filmbot-ui.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable filmbot-ui.service
```

### 7. Configure Permissions

The UI needs sudo access to manage systemd timers. Add to sudoers:

```bash
sudo visudo -f /etc/sudoers.d/filmbot
```

Add these lines:

```
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl enable filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl disable filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl start filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl stop filmbot-record-*.timer
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl is-active filmbot-record-*.service
```

### 8. Start the UI

```bash
sudo systemctl start filmbot-ui.service
```

Check status:

```bash
sudo systemctl status filmbot-ui.service
```

View logs:

```bash
sudo journalctl -u filmbot-ui.service -f
```

## Development & Testing

### Running Locally (Without Raspberry Pi)

The application can be tested on a development machine:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python3 main.py
```

**Note**: Some features will be limited:
- Video preview will fail (no `/dev/video5`)
- Systemd integration will be in dry-run mode
- Storage paths will fall back to `~/.filmbot/`

### Configuration File

The application stores configuration in `/opt/filmbot-appliance/config.json` (or `~/.filmbot/config.json` in development).

Example configuration:

```json
{
  "initialized": true,
  "google_drive": {
    "remote": "filmbot-drive:",
    "folder": "McDonough-Teaching"
  },
  "devices": {
    "video_device": "/dev/video5",
    "audio_device": "hw:2,0"
  },
  "schedules": [
    {
      "id": "service-1",
      "day_of_week": "sunday",
      "start_time": "09:20",
      "duration_minutes": 60,
      "enabled": true
    }
  ],
  "device_name": "HeadlessHorseman"
}
```

## File Structure

```
/opt/filmbot-appliance/ui/
├── main.py                 # Application entry point
├── config_manager.py       # Configuration file management
├── systemd_manager.py      # Systemd timer generation
├── video_preview.py        # Video capture widget
├── live_view.py            # Main monitoring screen
├── wizard.py               # First-boot setup wizard
├── settings.py             # Settings screen
├── requirements.txt        # Python dependencies
└── filmbot-ui.service      # Systemd service file
```

## Troubleshooting

### UI doesn't start

Check service status:
```bash
sudo systemctl status filmbot-ui.service
sudo journalctl -u filmbot-ui.service -n 50
```

### No video preview

Verify ATEM is connected:
```bash
ls -l /dev/video*
v4l2-ctl --list-devices
```

### Touch input not working

Ensure touchscreen is properly configured in `/boot/config.txt`:
```
dtoverlay=vc4-kms-dsi-7inch
```

### Schedules not creating

Check systemd manager dry_run mode in `systemd_manager.py` and `settings.py`. Set `dry_run=False` for production.

## Deployment & Cloning

### Creating Master Image

1. Complete setup on one Raspberry Pi
2. Test all functionality
3. Shut down: `sudo poweroff`
4. Remove microSD card
5. Create image:
   ```bash
   sudo dd if=/dev/sdX of=filmbot-master.img bs=4M status=progress
   ```

### Deploying to New Units

1. Flash `filmbot-master.img` to new microSD cards using Raspberry Pi Imager
2. Insert card and boot Raspberry Pi
3. First-boot wizard will appear (config.json can be reset if needed)
4. Complete organization-specific setup

## License

Proprietary - Filmbot Recording Appliance

