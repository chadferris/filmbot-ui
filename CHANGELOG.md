# Filmbot UI - Changelog

## Version 1.1 - 2026-01-10

### Added
- **Device Selection Feature**: Users can now select video and audio devices
  - New device detection utility (`device_detector.py`)
  - Auto-detection of V4L2 video devices using `v4l2-ctl`
  - Auto-detection of ALSA audio capture devices using `arecord`
  - Device selection page added to setup wizard (after welcome screen)
  - Device settings section added to settings screen
  - Configuration now stores selected devices in `config.json`
  
### Changed
- **Wizard Flow**: Now includes device selection as second step
  1. Welcome
  2. **Device Selection** (NEW)
  3. Google Drive Setup
  4. Recording Schedules
  5. Finish

- **Config Schema**: Added `devices` section
  ```json
  "devices": {
    "video_device": "/dev/video5",
    "audio_device": "hw:2,0"
  }
  ```

- **Video Preview**: Now uses configured video device instead of hardcoded `/dev/video5`

### Benefits
- **Flexibility**: Works with different ATEM models or video capture devices
- **Multi-device Support**: Can handle systems with multiple video/audio devices
- **User-Friendly**: Auto-detection makes setup easier
- **Future-Proof**: Easy to switch devices without code changes

---

## Version 1.0 - 2026-01-10

### Initial Release
- First-boot setup wizard
- Live monitoring view with video preview
- Settings screen
- Google Drive sync configuration
- Recording schedule management
- Systemd timer generation
- Video capture from ATEM Mini
- Storage monitoring
- Touchscreen-optimized UI (800×480)

