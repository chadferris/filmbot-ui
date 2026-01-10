# Filmbot Recording Appliance - Touchscreen UI Project

## Project Overview

Complete Python-based touchscreen application for the Filmbot recording appliance, designed to run on Raspberry Pi 5 with a 4.3" touchscreen (800×480). The application provides a complete user interface for setup, monitoring, and configuration of automated video recording from a Blackmagic ATEM Mini.

## Deliverables

### Core Application Files

1. **main.py** - Application entry point
   - Routes between wizard and live view based on initialization state
   - Manages screen transitions
   - Configures Qt application for touchscreen

2. **config_manager.py** - Configuration management
   - Reads/writes JSON configuration file
   - Validates configuration data
   - Provides API for all config operations
   - Fallback paths for development/testing

3. **systemd_manager.py** - Systemd integration
   - Generates systemd service and timer files
   - Manages recording schedules
   - Handles systemd daemon-reload and service control
   - Dry-run mode for safe testing

4. **video_preview.py** - Video capture widget
   - OpenCV-based video capture from /dev/video5
   - Threaded capture for smooth UI
   - Automatic frame scaling and aspect ratio
   - Error handling for missing video device
   - 30fps throttling for performance

5. **live_view.py** - Main monitoring screen
   - Live video preview (600×400 area)
   - Recording status indicator
   - Next scheduled recording display
   - Google Drive sync status
   - Local storage usage
   - Auto-refresh every 5 seconds

6. **wizard.py** - First-boot setup wizard
   - Welcome screen
   - Google Drive configuration with connection test
   - Recording schedule setup (multiple schedules)
   - Finish page with configuration summary
   - Page validation and navigation

7. **settings.py** - Settings/configuration screen
   - Modify Google Drive settings
   - Add/remove recording schedules
   - View system information (hostname, IP, storage)
   - Device name configuration
   - Scrollable layout for 480px height

### Supporting Files

8. **requirements.txt** - Python dependencies
   - PySide6 (Qt6 for Python)
   - opencv-python (video capture)
   - psutil (system information)

9. **filmbot-ui.service** - Systemd service file
   - Auto-start on boot
   - Runs as filmbot user
   - EGLFS platform for touchscreen
   - Auto-restart on failure

10. **install.sh** - Installation script
    - Installs system dependencies
    - Creates directory structure
    - Installs Python packages
    - Configures sudoers
    - Enables systemd service

11. **test_ui.py** - Test suite
    - Tests config manager
    - Interactive testing of wizard, live view, settings
    - Works on development machines

12. **update_sync_script.py** - Sync script updater
    - Updates sync-drive.sh with configured Drive path
    - Called when Drive configuration changes

### Documentation

13. **README.md** - Main documentation
    - Features overview
    - Installation instructions
    - Configuration details
    - Troubleshooting guide

14. **DEPLOYMENT.md** - Deployment guide
    - Quick start instructions
    - Production deployment checklist
    - Configuration notes
    - Master image creation process

15. **PROJECT_SUMMARY.md** - This file
    - Complete project overview
    - Architecture details
    - Implementation notes

## Architecture

### Screen Flow

```
[Boot] → Check config.json
         ↓
    initialized?
    ↙         ↘
  YES          NO
   ↓            ↓
[Live View] ← [Setup Wizard]
   ↓
[Settings] ← → [Live View]
```

### Configuration File Structure

```json
{
  "initialized": true/false,
  "google_drive": {
    "remote": "filmbot-drive:",
    "folder": "OrgName/BoxID"
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
  "device_name": "DeviceName"
}
```

### Systemd Integration

The UI generates systemd timer files for each recording schedule:

- **Service file**: `/etc/systemd/system/filmbot-record-{id}.service`
  - Calls `/opt/filmbot-appliance/record-atem.sh {duration_seconds}`
  
- **Timer file**: `/etc/systemd/system/filmbot-record-{id}.timer`
  - OnCalendar format: "Sun 09:20", "Mon 14:30", etc.

## Key Features

### 1. First-Boot Wizard
- Guides new installations through setup
- Tests Google Drive connectivity
- Supports multiple recording schedules
- Validates all inputs
- Generates systemd timers

### 2. Live Monitoring
- Real-time video preview from ATEM
- Visual recording indicator
- Next recording countdown
- Sync status monitoring
- Storage usage display

### 3. Settings Management
- Post-setup configuration changes
- Add/remove schedules dynamically
- Test Drive connection
- View system information
- Update device name

### 4. Touchscreen Optimized
- 800×480 resolution support
- Large touch targets (40-50px minimum)
- Clear visual hierarchy
- Scrollable content where needed
- Fullscreen mode available

## Implementation Notes

### Safety Features

1. **Dry-run mode**: Systemd manager defaults to dry_run=True
   - Prevents accidental service creation during testing
   - Must be explicitly disabled for production

2. **Fallback paths**: Development-friendly paths
   - Config: `~/.filmbot/config.json` if `/opt/filmbot-appliance/` doesn't exist
   - Recordings: `~/filmbot-recordings` if `/mnt/nvme/recordings` doesn't exist

3. **Error handling**: Graceful degradation
   - Video preview shows error message if ATEM disconnected
   - Sync status shows error if log file missing
   - Storage info shows "--" if path unavailable

### Performance Optimizations

1. **Video capture**: Threaded with 30fps throttle
2. **Status updates**: 5-second refresh interval
3. **MJPEG passthrough**: No video re-encoding (copy codec)

### Permissions

The filmbot user needs sudo access for systemd operations:
- daemon-reload
- enable/disable/start/stop timers
- Check service status

Configured via `/etc/sudoers.d/filmbot` with NOPASSWD for specific commands.

## Testing Strategy

### Development Testing
1. Run `test_ui.py` to test individual components
2. Run `main.py` to test full application flow
3. Video preview will fail (expected without hardware)
4. All other features work normally

### Raspberry Pi Testing
1. Install with `install.sh`
2. Start service: `sudo systemctl start filmbot-ui.service`
3. Complete wizard on touchscreen
4. Verify schedules created: `systemctl list-timers`
5. Test recording trigger
6. Verify sync works

## Deployment Process

### Single Unit
1. Transfer files to Pi
2. Run `install.sh`
3. Start service
4. Complete wizard

### Mass Deployment
1. Set up and test one unit completely
2. Create master image with `dd`
3. Flash to new microSD cards
4. Each unit boots into wizard for org-specific setup

## Future Enhancements

Potential improvements for future versions:

1. **Recording indicator overlay**: Visual REC badge on video preview
2. **Schedule conflict detection**: Warn about overlapping schedules
3. **Network status**: Show WiFi/Ethernet connection state
4. **Disk space warnings**: Alert when storage is low
5. **Recording history**: List of recent recordings
6. **Manual recording**: Button to start ad-hoc recording
7. **Preview recording**: Show last recorded file
8. **Remote access**: Web interface for monitoring
9. **Multi-language support**: Internationalization
10. **Dark mode**: Theme switching

## Technical Specifications

- **Language**: Python 3.11+
- **GUI Framework**: PySide6 (Qt 6)
- **Video Capture**: OpenCV with V4L2
- **Platform**: Raspberry Pi OS (Debian 13 Bookworm)
- **Display**: 800×480 DSI touchscreen
- **Video Source**: Blackmagic ATEM Mini via USB (MJPEG 1920×1080@60fps)
- **Audio Source**: ALSA hw:2,0 (48kHz stereo)

## File Sizes

Total project size: ~50KB (Python source)
With dependencies installed: ~200MB

## License

Proprietary - Filmbot Recording Appliance

---

**Project Status**: ✅ Complete and ready for deployment

**Last Updated**: 2026-01-10

