#!/bin/bash
# NVMe Drive Setup Script for Filmbot
# Formats and mounts NVMe drive for recording storage

set -e

echo "=== Filmbot NVMe Drive Setup ==="
echo ""
echo "WARNING: This will FORMAT the NVMe drive and erase all data!"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    echo "Usage: sudo ./setup-nvme.sh"
    exit 1
fi

# Detect NVMe drive
NVME_DEVICE=$(lsblk -d -n -o NAME,TYPE | grep nvme | head -n 1 | awk '{print $1}')

if [ -z "$NVME_DEVICE" ]; then
    echo "Error: No NVMe drive detected"
    echo ""
    echo "Available drives:"
    lsblk
    exit 1
fi

NVME_PATH="/dev/${NVME_DEVICE}"
echo "Detected NVMe drive: $NVME_PATH"
echo ""

# Show drive info
lsblk "$NVME_PATH"
echo ""

# Confirm
read -p "Format $NVME_PATH and mount at /mnt/nvme? (yes/no) " -r
echo
if [ "$REPLY" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Unmount if already mounted
if mount | grep -q "$NVME_PATH"; then
    echo "Unmounting existing mount..."
    umount "${NVME_PATH}"* 2>/dev/null || true
fi

# Create partition table
echo "Creating partition table..."
parted -s "$NVME_PATH" mklabel gpt
parted -s "$NVME_PATH" mkpart primary ext4 0% 100%

# Wait for partition to be created
sleep 2

# Determine partition name
if [ -e "${NVME_PATH}p1" ]; then
    PARTITION="${NVME_PATH}p1"
elif [ -e "${NVME_PATH}1" ]; then
    PARTITION="${NVME_PATH}1"
else
    echo "Error: Could not find partition"
    exit 1
fi

# Format partition
echo "Formatting $PARTITION as ext4..."
mkfs.ext4 -F "$PARTITION"

# Create mount point
echo "Creating mount point /mnt/nvme..."
mkdir -p /mnt/nvme

# Get UUID
UUID=$(blkid -s UUID -o value "$PARTITION")
echo "Partition UUID: $UUID"

# Add to fstab
echo "Adding to /etc/fstab..."
if ! grep -q "/mnt/nvme" /etc/fstab; then
    echo "UUID=$UUID /mnt/nvme ext4 defaults,nofail 0 2" >> /etc/fstab
    echo "Added to /etc/fstab"
else
    echo "Entry already exists in /etc/fstab"
fi

# Mount
echo "Mounting..."
mount /mnt/nvme

# Create recordings directory
echo "Creating recordings directory..."
mkdir -p /mnt/nvme/recordings
chown -R filmbot:filmbot /mnt/nvme/recordings
chmod 755 /mnt/nvme/recordings

# Verify
echo ""
echo "=== Setup Complete ==="
echo ""
df -h /mnt/nvme
echo ""
ls -ld /mnt/nvme/recordings
echo ""
echo "NVMe drive is ready for use!"
echo "Recordings will be saved to: /mnt/nvme/recordings"

