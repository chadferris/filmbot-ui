# Filmbot Health Monitoring Setup Guide

## Overview

The health monitoring system sends email alerts when issues are detected:
- 🔴 **Critical alerts** - Recording failures, disk full, device disconnected
- 🟡 **Warning alerts** - Low disk space, high CPU/temp, network issues  
- 🟢 **Daily reports** - System health summary at 8 AM

## Prerequisites

1. **Gmail App Password** - Generate one for the Gmail account already used for Drive sync
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it: "Filmbot Alerts"
   - Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

2. **Email Recipients** - Email addresses that should receive alerts

---

## Installation on Raspberry Pi

### Step 1: Pull Latest Code

```bash
cd ~/Filmbot
git pull
```

### Step 2: Install Health Monitoring

```bash
sudo ./setup-health-monitoring.sh
```

This will:
- Copy health check scripts to `/opt/filmbot-appliance/`
- Install Python dependencies (psutil)
- Set up systemd timers for automated checks
- Enable health checks every 5 minutes
- Enable daily reports at 8 AM

### Step 3: Configure Email Settings

**Option A: Edit config.json directly**

```bash
nano /opt/filmbot-appliance/config.json
```

Add/update the `alerts` section:

```json
{
  "alerts": {
    "enabled": true,
    "email_from": "your-filmbot-gmail@gmail.com",
    "email_to": ["it-team@campus.edu", "admin@campus.edu"],
    "smtp_password": "xxxx xxxx xxxx xxxx",
    "daily_report_time": "08:00",
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00"
  }
}
```

**Option B: Use Python to configure** (if UI not ready)

```bash
cd /opt/filmbot-appliance
source venv/bin/activate
python3
```

```python
from config_manager import ConfigManager

config = ConfigManager()
config.set_alerts_config(
    enabled=True,
    email_from="your-filmbot-gmail@gmail.com",
    email_to=["it-team@campus.edu"],
    smtp_password="xxxx xxxx xxxx xxxx"
)
print("Email alerts configured!")
```

---

## Testing

### Test 1: Health Check (No Email)

```bash
/opt/filmbot-appliance/venv/bin/python3 /opt/filmbot-appliance/health_check.py --test
```

This will print health status without sending emails. You should see:
```
============================================================
FILMBOT HEALTH CHECK - YourDeviceName
Time: 2026-01-13 10:30:00
Overall Status: OK
============================================================

✅ DISK_SPACE: ok
   Disk Space: 234.5 GB free (45.2%)

✅ VIDEO_DEVICE: ok
   Video Device: /dev/video5 ✅

✅ ATEM: ok
   ATEM: Connected ✅

✅ NETWORK: ok
   Network: Online ✅

✅ SYSTEM_RESOURCES: ok
   CPU Usage: 12.3%
   Memory Usage: 34.5%
   Temperature: 45.2°C

✅ UPTIME: ok
   Uptime: 7 days, 14 hours
```

### Test 2: Send Test Email (Daily Report)

```bash
/opt/filmbot-appliance/venv/bin/python3 /opt/filmbot-appliance/health_check.py --daily-report
```

This will send a test daily report email. Check your inbox!

### Test 3: Verify Timers are Running

```bash
# Check health check timer (every 5 min)
systemctl status filmbot-health.timer

# Check daily report timer (8 AM)
systemctl status filmbot-daily-report.timer

# View recent logs
journalctl -u filmbot-health.service -n 20
```

---

## What Gets Monitored

| Check | Critical Alert | Warning Alert |
|-------|---------------|---------------|
| **Disk Space** | < 10% free | < 20% free |
| **Video Device** | Not found | - |
| **ATEM** | - | Not responding |
| **Network** | - | No internet |
| **CPU** | - | > 80% usage |
| **Memory** | - | > 85% usage |
| **Temperature** | > 80°C | > 70°C |

---

## Example Alerts

### Critical Alert Email
```
From: filmbot-location1@gmail.com
To: it-team@campus.edu
Subject: 🔴 CRITICAL: Recording Failed - HeadlessHorseman

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILMBOT CRITICAL ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Device: HeadlessHorseman
Time: 2026-01-13 14:30:00
Issue: Video device not found

DETAILS:
• Device: /dev/video5
• Action: Check USB connections and ATEM power

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION REQUIRED: Please check the device.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Daily Report Email
```
From: filmbot-location1@gmail.com
To: it-team@campus.edu
Subject: 🟢 Daily Report - HeadlessHorseman

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILMBOT DAILY HEALTH REPORT
Date: 2026-01-13
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEVICE: HeadlessHorseman
Status: ✅ Healthy

Disk Space: 234.5 GB free (45.2%)
Video Device: /dev/video5 ✅
ATEM: Connected ✅
Network: Online ✅
CPU Usage: 12.3%
Memory Usage: 34.5%
Temperature: 45.2°C
Uptime: 7 days, 14 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Troubleshooting

### Emails Not Sending

1. **Check configuration:**
   ```bash
   cat /opt/filmbot-appliance/config.json | grep -A 8 "alerts"
   ```

2. **Verify app password is correct** (16 characters, no spaces in config)

3. **Test SMTP manually:**
   ```bash
   /opt/filmbot-appliance/venv/bin/python3 -c "
   from email_notify import EmailNotifier
   notifier = EmailNotifier()
   print('Enabled:', notifier.is_enabled())
   print('Config:', notifier.alerts_config)
   "
   ```

4. **Check logs:**
   ```bash
   journalctl -u filmbot-health.service -f
   ```

### Disable Alerts Temporarily

```bash
# Stop timers
sudo systemctl stop filmbot-health.timer
sudo systemctl stop filmbot-daily-report.timer

# Re-enable later
sudo systemctl start filmbot-health.timer
sudo systemctl start filmbot-daily-report.timer
```

---

## Uninstall

```bash
sudo systemctl stop filmbot-health.timer filmbot-daily-report.timer
sudo systemctl disable filmbot-health.timer filmbot-daily-report.timer
sudo rm /etc/systemd/system/filmbot-health.*
sudo rm /etc/systemd/system/filmbot-daily-report.*
sudo systemctl daemon-reload
```

