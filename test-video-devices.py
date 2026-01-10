#!/usr/bin/env python3
"""
Test video devices to find which one actually works.
Helps diagnose ATEM Mini capture issues.
"""

import cv2
import sys
from pathlib import Path

def test_device(device_path):
    """Test if a video device can capture frames."""
    print(f"\n{'='*60}")
    print(f"Testing: {device_path}")
    print('='*60)
    
    # Try to open device
    cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"❌ Cannot open device")
        return False
    
    print(f"✓ Device opened successfully")
    
    # Get device properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    
    print(f"  Resolution: {int(width)}x{int(height)}")
    print(f"  FPS: {fps}")
    print(f"  Format: {fourcc_str}")
    
    # Try to read a frame
    print(f"\nAttempting to read frame...")
    ret, frame = cap.read()
    
    if ret:
        print(f"✓ Successfully read frame: {frame.shape}")
        cap.release()
        return True
    else:
        print(f"❌ Failed to read frame")
        
        # Try with MJPEG
        print(f"\nRetrying with MJPEG format...")
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        ret, frame = cap.read()
        if ret:
            print(f"✓ MJPEG worked! Frame: {frame.shape}")
            cap.release()
            return True
        
        # Try with YUYV
        print(f"\nRetrying with YUYV format...")
        cap.release()
        cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('Y', 'U', 'Y', 'V'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        ret, frame = cap.read()
        if ret:
            print(f"✓ YUYV worked! Frame: {frame.shape}")
            cap.release()
            return True
        
        print(f"❌ All formats failed")
        cap.release()
        return False

def main():
    """Test all video devices."""
    print("Filmbot Video Device Tester")
    print("="*60)
    
    # Find all video devices
    video_devices = list(Path("/dev").glob("video*"))
    video_devices.sort()
    
    if not video_devices:
        print("No video devices found!")
        return
    
    print(f"Found {len(video_devices)} video device(s):")
    for dev in video_devices:
        print(f"  - {dev}")
    
    # Test each device
    working_devices = []
    for device in video_devices:
        if test_device(str(device)):
            working_devices.append(device)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    if working_devices:
        print(f"✓ Working devices ({len(working_devices)}):")
        for dev in working_devices:
            print(f"  - {dev}")
        print(f"\nRecommendation: Use {working_devices[0]} in your config")
    else:
        print("❌ No working video devices found!")
        print("\nTroubleshooting:")
        print("  1. Check if ATEM Mini is connected via USB")
        print("  2. Run: lsusb | grep -i blackmagic")
        print("  3. Check dmesg for USB errors: dmesg | tail -50")
        print("  4. Verify device permissions: ls -l /dev/video*")

if __name__ == "__main__":
    main()

