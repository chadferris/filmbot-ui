#!/bin/bash
# Filmbot Google Drive Sync Script
# Syncs recordings to Google Drive using config from config.json

RECORDINGS_DIR="/mnt/nvme/recordings"
CONFIG_FILE="/opt/filmbot-appliance/config.json"
LOG_FILE="/var/log/filmbot-rclone.log"

# Load configuration from config.json
if [ -f "$CONFIG_FILE" ]; then
    REMOTE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('google_drive', {}).get('remote', 'filmbot-drive:'))" 2>/dev/null || echo "filmbot-drive:")
    FOLDER=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('google_drive', {}).get('folder', 'Recordings'))" 2>/dev/null || echo "Recordings")
    DRIVE_DEST="${REMOTE}${FOLDER}"
else
    # Fallback if config doesn't exist
    DRIVE_DEST="filmbot-drive:Recordings"
fi

# Ensure log file exists
touch "$LOG_FILE"

# Sync recordings to Google Drive
echo "$(date): Starting sync to $DRIVE_DEST" >> "$LOG_FILE"

rclone move "$RECORDINGS_DIR" "$DRIVE_DEST" \
    --log-file="$LOG_FILE" \
    --log-level INFO \
    --transfers 1 \
    --checkers 1 \
    --stats 30s \
    --stats-one-line \
    --delete-empty-src-dirs

if [ $? -eq 0 ]; then
    echo "$(date): Sync completed successfully" >> "$LOG_FILE"
else
    echo "$(date): Sync failed with error code $?" >> "$LOG_FILE"
fi

