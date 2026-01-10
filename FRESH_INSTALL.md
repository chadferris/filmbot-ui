# Filmbot Recording Appliance - Fresh Installation Guide

This guide walks you through setting up the Filmbot Recording Appliance on a **brand new Raspberry Pi** with a fresh Raspberry Pi OS installation.

## Hardware Requirements

- **Raspberry Pi 5** (4GB or 8GB recommended)
- **4.3" Touchscreen Display** (800×480)
- **Blackmagic ATEM Mini** (or compatible video capture device)
- **MicroSD card** (32GB or larger)
- **Power supply** for Raspberry Pi 5
- **Internet connection** (for initial setup)

## Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi Imager**
   - Get it from: https://www.raspberrypi.com/software/

2. **Flash Raspberry Pi OS**
   - Insert microSD card into your computer
   - Open Raspberry Pi Imager
   - Choose OS: **Raspberry Pi OS (64-bit)** with desktop
   - Choose Storage: Your microSD card
   - Click the gear icon (⚙️) for advanced options:
     - Set hostname: `filmbot` (or your choice)
     - Enable SSH (optional, for remote access)
     - Set username: `filmbot`
     - Set password: (your choice)
     - Configure WiFi (if needed)
   - Click **Write** and wait for completion

3. **Boot the Raspberry Pi**
   - Insert the microSD card into the Raspberry Pi
   - Connect the touchscreen display
   - Connect the ATEM Mini via USB
   - Power on the Raspberry Pi
   - Complete the initial setup wizard if prompted

## Step 2: Install Filmbot Software

1. **Open Terminal** on the Raspberry Pi

2. **Clone the Filmbot repository**
   ```bash
   cd ~
   git clone https://github.com/chadferris/filmbot-ui.git
   cd filmbot-ui
   ```

3. **Run the installer**
   ```bash
   chmod +x install.sh setup-nvme.sh
   ./install.sh
   ```

   The installer will:
   - Install all system dependencies (ffmpeg, rclone, v4l-utils, alsa-utils)
   - Create a Python virtual environment
   - Install PySide6 and other Python packages
   - Set up the Filmbot UI application
   - Install recording and sync scripts
   - Configure auto-login
   - Enable auto-start on boot
   - Check for video capture devices (ATEM works as UVC device)

4. **Set up NVMe storage**
   ```bash
   sudo ./setup-nvme.sh
   ```

   This will:
   - Format the NVMe drive (⚠️ ERASES ALL DATA)
   - Create ext4 filesystem
   - Mount at `/mnt/nvme`
   - Add to `/etc/fstab` for auto-mount on boot
   - Create `/mnt/nvme/recordings` directory

5. **Configure Google Drive (rclone)**
   ```bash
   rclone config
   ```

   Follow these steps:
   - Choose `n` for new remote
   - Name: `filmbot-drive` (or your choice)
   - Storage: Choose `drive` (Google Drive)
   - Client ID/Secret: Press Enter to skip (use defaults)
   - Scope: Choose `drive` (full access)
   - Root folder: Press Enter to skip
   - Service account: Press Enter to skip
   - Advanced config: `n`
   - Auto config: `n` (we'll use remote auth)
   - Follow the URL and paste the verification code
   - Configure as Shared Drive: `n` (unless using Shared Drive)
   - Confirm and quit

6. **Reboot**
   ```bash
   sudo reboot
   ```

## Step 3: Initial Configuration (Setup Wizard)

After reboot, the Filmbot UI will start automatically and show the setup wizard:

### Page 1: Welcome
- Click **Next** to begin setup

### Page 2: Device Selection
- **Video Device**: Select your ATEM Mini (e.g., "Blackmagic Design")
- **Audio Device**: Select the audio input (e.g., "USB Audio")
- Click **Detect Devices** if devices don't appear
- Click **Next**

### Page 3: Google Drive Setup
- **Remote**: Enter your rclone remote name (e.g., `filmbot-drive:`)
- **Folder**: Enter the folder path (e.g., `Church-Recordings`)
- Click **Test Connection** to verify
- Click **Next**

### Page 4: Recording Schedules
- Click **Add Schedule** to create recording times
- Set day of week, start time, and duration
- Add multiple schedules as needed
- Click **Next**

### Page 5: Finish
- Review your settings
- Enter a device name (e.g., `HeadlessHorseman`)
- Click **Finish**

## Step 4: You're Done!

The Filmbot appliance is now ready to use:

- **Live View**: Shows video preview and system status
- **Settings**: Access via the settings button to modify configuration
- **Automatic Recording**: Recordings will start based on your schedules
- **Auto-Upload**: Videos are automatically uploaded to Google Drive

## Troubleshooting

### Video preview not working
```bash
# Check if ATEM is detected
lsusb | grep -i blackmagic
v4l2-ctl --list-devices

# Restart the UI
sudo systemctl restart filmbot-ui.service
```

### Check logs
```bash
sudo journalctl -u filmbot-ui.service -f
```

### Manual start/stop
```bash
sudo systemctl start filmbot-ui.service
sudo systemctl stop filmbot-ui.service
sudo systemctl status filmbot-ui.service
```

## Next Steps

- Configure Google Drive sync (see DEPLOYMENT.md)
- Set up remote access via SSH or VNC
- Mount the Pi in your recording location
- Test a recording schedule

---

**Need help?** Check the other documentation files:
- `README.md` - Overview and features
- `DEPLOYMENT.md` - Detailed deployment guide
- `QUICK_START.md` - Quick reference guide

