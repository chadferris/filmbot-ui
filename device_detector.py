"""
Device detection utilities for Filmbot appliance.
Detects available video and audio devices.
"""

import subprocess
import re
from pathlib import Path
from typing import List, Tuple


def detect_video_devices() -> List[Tuple[str, str]]:
    """Detect available V4L2 video devices.
    
    Returns:
        List of (device_path, device_name) tuples
    """
    devices = []
    
    # Check /dev/video* devices
    video_devices = sorted(Path("/dev").glob("video*"))
    
    for device_path in video_devices:
        try:
            # Use v4l2-ctl to get device info
            result = subprocess.run(
                ['v4l2-ctl', '--device', str(device_path), '--info'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Parse device name from output
                name_match = re.search(r'Card type\s*:\s*(.+)', result.stdout)
                if name_match:
                    device_name = name_match.group(1).strip()
                else:
                    device_name = f"Video Device {device_path.name}"
                
                devices.append((str(device_path), device_name))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # v4l2-ctl not available or timeout
            devices.append((str(device_path), f"Video Device {device_path.name}"))
    
    # Fallback if no devices found
    if not devices:
        devices.append(("/dev/video5", "Default Video Device (not detected)"))
    
    return devices


def detect_audio_devices() -> List[Tuple[str, str]]:
    """Detect available ALSA audio capture devices.
    
    Returns:
        List of (device_id, device_name) tuples
    """
    devices = []
    
    try:
        # Use arecord to list capture devices
        result = subprocess.run(
            ['arecord', '-l'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # Parse output for card and device numbers
            # Format: "card 2: Design [Blackmagic Design], device 0: USB Audio [USB Audio]"
            pattern = r'card (\d+):.*?\[(.+?)\].*?device (\d+):'
            
            for match in re.finditer(pattern, result.stdout):
                card_num = match.group(1)
                card_name = match.group(2)
                device_num = match.group(3)
                
                device_id = f"hw:{card_num},{device_num}"
                device_name = f"{card_name} (card {card_num}, device {device_num})"
                
                devices.append((device_id, device_name))
    
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback if no devices found
    if not devices:
        devices.append(("hw:2,0", "Default Audio Device (not detected)"))
    
    return devices


def get_device_info(video_device: str, audio_device: str) -> str:
    """Get formatted device information string.
    
    Args:
        video_device: Video device path
        audio_device: Audio device identifier
        
    Returns:
        Formatted info string
    """
    info_lines = []
    
    # Video device info
    try:
        result = subprocess.run(
            ['v4l2-ctl', '--device', video_device, '--list-formats-ext'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # Look for MJPEG format
            if 'MJPEG' in result.stdout or 'Motion-JPEG' in result.stdout:
                info_lines.append(f"Video: {video_device} (MJPEG supported)")
            else:
                info_lines.append(f"Video: {video_device}")
        else:
            info_lines.append(f"Video: {video_device}")
    except:
        info_lines.append(f"Video: {video_device}")
    
    # Audio device info
    info_lines.append(f"Audio: {audio_device}")
    
    return "\n".join(info_lines)


if __name__ == "__main__":
    """Test device detection."""
    print("=== Video Devices ===")
    for device_path, device_name in detect_video_devices():
        print(f"  {device_path}: {device_name}")
    
    print("\n=== Audio Devices ===")
    for device_id, device_name in detect_audio_devices():
        print(f"  {device_id}: {device_name}")

