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
  - Tabbed layout (System, Devices, Drive, Schedules, Integrations)
    designed for the 4.3" touchscreen so no scrolling is needed
  - Change video/audio devices and ATEM IP
  - Modify Google Drive settings
  - Add/remove recording schedules
  - View system information
  - Update device name
  - Configure email alerts and ProPresenter integration

- **ProPresenter Integration**: Trigger recordings from slide notes
  - Supports ProPresenter 6 (Stage Display WebSocket) and
    ProPresenter 7 (REST API)
  - Slide notes containing `[START_RECORD]` start a recording;
    `[STOP_RECORD]` stops the active recording
  - Runs as a lightweight, event-driven `filmbot-propresenter.service`
    on the Pi

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

Copy the top-level Python files and the `ui/` subdirectory (which contains
the ProPresenter listener) to `/opt/filmbot-appliance/ui/`:

```bash
sudo mkdir -p /opt/filmbot-appliance/ui/ui
cd /opt/filmbot-appliance/ui
# Copy files from this repository
cp /path/to/Filmbot/*.py .
cp /path/to/Filmbot/ui/*.py ui/
cp /path/to/Filmbot/requirements.txt .
```

The bundled `install.sh` performs these steps automatically.

### 4. Install Python Dependencies

```bash
cd /opt/filmbot-appliance/ui
python3 -m pip install -r requirements.txt
```

### 5. Make main.py Executable

```bash
chmod +x /opt/filmbot-appliance/ui/main.py
```

### 6. Install Systemd Services

Install both the UI service and the ProPresenter listener service:

```bash
sudo cp filmbot-ui.service /etc/systemd/system/
sudo cp systemd/filmbot-propresenter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable filmbot-ui.service
sudo systemctl enable filmbot-propresenter.service
```

### 7. Configure Permissions

The UI needs sudo access to manage systemd timers and the ProPresenter
listener service. Add to sudoers:

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
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl restart filmbot-propresenter.service
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl start filmbot-propresenter.service
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl stop filmbot-propresenter.service
filmbot ALL=(ALL) NOPASSWD: /bin/systemctl is-active filmbot-propresenter.service
```

### 8. Start the Services

```bash
sudo systemctl start filmbot-ui.service
sudo systemctl start filmbot-propresenter.service
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
├── settings.py             # Settings screen (tabbed layout)
├── email_notify.py         # Email alert helper
├── requirements.txt        # Python dependencies
└── ui/                     # Auxiliary services
    └── propresenter_listener.py   # ProPresenter 6/7 listener
```

Systemd unit files live in the repo under `systemd/` and are installed to
`/etc/systemd/system/`:

- `filmbot-ui.service` — touchscreen UI
- `systemd/filmbot-propresenter.service` — ProPresenter slide-tag listener
- `systemd/filmbot-health.{service,timer}` — periodic health check
- `systemd/filmbot-daily-report.{service,timer}` — daily email report

## ProPresenter Integration

Filmbot can start and stop recordings when specific tags appear in a
ProPresenter slide's notes. It is a read-only listener — it never sends
commands back to ProPresenter.

**Setup on the ProPresenter machine**

- ProPresenter 6: enable *Preferences → Network → Enable Network* and
  turn on *Stage Display App*. Set a Stage Display password.
- ProPresenter 7: enable *Preferences → Network → Enable Network* so the
  REST API is reachable on the LAN.

**Setup on the Filmbot appliance**

1. Open the touchscreen UI and go to **Settings → Integrations →
   🎬 ProPresenter**.
2. Choose the version (`ProPresenter 6` or `ProPresenter 7`).
3. Enter the ProPresenter machine's IP address and port
   (defaults: PP6 Stage Display = `50001`, PP7 REST API = `1025`).
4. For ProPresenter 6, enter the Stage Display password.
5. Tap **Save**. The `filmbot-propresenter.service` restarts automatically
   with the new settings.

**Authoring slides**

Add `[START_RECORD]` to the slide notes of any slide that should begin a
recording, and `[STOP_RECORD]` to the slide that should end it. When the
operator advances to that slide during a service, Filmbot triggers the
matching action. Repeated firings of the same slide are ignored — only
transitions to a new slide trigger a start/stop.

**Verifying the listener**

```bash
sudo systemctl status filmbot-propresenter.service
sudo journalctl -u filmbot-propresenter.service -f
tail -f /var/log/filmbot-propresenter.log
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

