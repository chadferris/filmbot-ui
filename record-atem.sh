#!/bin/bash
# Filmbot ATEM Recording Script
# Records video from ATEM Mini and saves to NVMe storage

set -e

# Configuration
DURATION=${1:-3600}  # Duration in seconds (default 1 hour)
RECORDINGS_DIR="/mnt/nvme/recordings"
VIDEO_DEVICE="/dev/video5"
AUDIO_DEVICE="hw:2,0"
LOG_FILE="/var/log/filmbot-record.log"

# Load device configuration if available
CONFIG_FILE="/opt/filmbot-appliance/config.json"
if [ -f "$CONFIG_FILE" ]; then
    # Extract video and audio devices from config using Python
    VIDEO_DEVICE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('devices', {}).get('video_device', '$VIDEO_DEVICE'))" 2>/dev/null || echo "$VIDEO_DEVICE")
    AUDIO_DEVICE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('devices', {}).get('audio_device', '$AUDIO_DEVICE'))" 2>/dev/null || echo "$AUDIO_DEVICE")
fi

# Ensure recordings directory exists
mkdir -p "$RECORDINGS_DIR"

# Generate filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEVICE_NAME=$(hostname)
OUTPUT_FILE="$RECORDINGS_DIR/${DEVICE_NAME}_${TIMESTAMP}.mp4"

# Log start
echo "$(date): Starting recording - Duration: ${DURATION}s, Output: $OUTPUT_FILE" >> "$LOG_FILE"
echo "$(date): Video: $VIDEO_DEVICE, Audio: $AUDIO_DEVICE" >> "$LOG_FILE"

# Stop the UI to release the video device
echo "$(date): Stopping filmbot-ui to release video device..." >> "$LOG_FILE"
systemctl stop filmbot-ui.service

# Record using ffmpeg
ffmpeg -f v4l2 -input_format mjpeg -video_size 1920x1080 -framerate 60 -i "$VIDEO_DEVICE" \
       -f alsa -ac 2 -ar 48000 -i "$AUDIO_DEVICE" \
       -t "$DURATION" \
       -c:v libx264 -preset ultrafast -crf 23 \
       -c:a aac -b:a 192k \
       -movflags +faststart \
       "$OUTPUT_FILE" \
       >> "$LOG_FILE" 2>&1

# Check if recording was successful
if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "$(date): Recording completed successfully - Size: $FILE_SIZE" >> "$LOG_FILE"

    # Trigger sync (if sync script exists)
    if [ -f "/opt/filmbot-appliance/sync-drive.sh" ]; then
        echo "$(date): Triggering Google Drive sync..." >> "$LOG_FILE"
        /opt/filmbot-appliance/sync-drive.sh >> "$LOG_FILE" 2>&1 &
    fi

    # Restart the UI
    echo "$(date): Restarting filmbot-ui..." >> "$LOG_FILE"
    systemctl start filmbot-ui.service
else
    echo "$(date): Recording failed with error code $?" >> "$LOG_FILE"

    # Restart the UI even if recording failed
    echo "$(date): Restarting filmbot-ui after failure..." >> "$LOG_FILE"
    systemctl start filmbot-ui.service

    exit 1
fi

