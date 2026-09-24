#!/bin/bash
# Filmbot ATEM Recording Script
# Records video from ATEM Mini and saves to NVMe storage

# Don't use set -e so we can clean up signal file even on failure
set +e

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

# Create signal file to tell UI to stop video preview
SIGNAL_FILE="/tmp/filmbot-recording"
echo "$(date): Creating signal file for UI..." >> "$LOG_FILE"
echo "$OUTPUT_FILE" > "$SIGNAL_FILE"

# PID file so the UI can send stop signals to this exact ffmpeg process
# instead of matching every process named "ffmpeg" on the system.
PID_FILE="/tmp/filmbot-recording.pid"

# Wait 3 seconds for UI to release the video device
sleep 3

# Record using ffmpeg. Run in the background so we can capture its PID for
# the PID file, then `wait` on it so this script still blocks until ffmpeg
# has fully exited (and finished writing the moov atom) before continuing.
ffmpeg -f v4l2 -input_format mjpeg -video_size 1920x1080 -framerate 60 -i "$VIDEO_DEVICE" \
       -f alsa -ac 2 -ar 48000 -i "$AUDIO_DEVICE" \
       -t "$DURATION" \
       -c:v libx264 -preset ultrafast -crf 23 \
       -c:a aac -b:a 192k \
       -movflags +faststart \
       "$OUTPUT_FILE" \
       >> "$LOG_FILE" 2>&1 &
FFMPEG_PID=$!
echo "$FFMPEG_PID" > "$PID_FILE"

wait "$FFMPEG_PID"
FFMPEG_EXIT=$?

# ALWAYS remove signal/pid files to tell UI recording is done
echo "$(date): Removing signal file..." >> "$LOG_FILE"
rm -f "$SIGNAL_FILE" "$PID_FILE"

# Check if recording was successful
if [ $FFMPEG_EXIT -eq 0 ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "$(date): Recording completed successfully - Size: $FILE_SIZE" >> "$LOG_FILE"

    # Validate the file is actually playable (has a moov atom / readable
    # stream info) before handing it off to sync-drive.sh. sync-drive.sh
    # uses `rclone move`, which deletes the local file after upload, so we
    # must not let a corrupt/truncated file get uploaded-then-deleted.
    if ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUTPUT_FILE" >> "$LOG_FILE" 2>&1; then
        echo "$(date): File validation passed - $OUTPUT_FILE is playable" >> "$LOG_FILE"

        # Trigger sync (if sync script exists)
        if [ -f "/opt/filmbot-appliance/sync-drive.sh" ]; then
            echo "$(date): Triggering Google Drive sync..." >> "$LOG_FILE"
            /opt/filmbot-appliance/sync-drive.sh >> "$LOG_FILE" 2>&1 &
        fi
    else
        FAILED_DIR="$RECORDINGS_DIR/failed"
        mkdir -p "$FAILED_DIR"
        mv "$OUTPUT_FILE" "$FAILED_DIR/"
        echo "$(date): WARNING - File validation FAILED. $OUTPUT_FILE appears corrupt (missing/invalid moov atom)." >> "$LOG_FILE"
        echo "$(date): Moved to $FAILED_DIR for inspection instead of syncing to Drive." >> "$LOG_FILE"
        exit 1
    fi
else
    echo "$(date): Recording failed with error code $FFMPEG_EXIT" >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

