"""
Live monitoring view for Filmbot appliance.
Main screen showing video preview and status information.
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtGui import QFont

from video_preview import VideoPreviewWidget
from config_manager import ConfigManager


class LiveView(QWidget):
    """Main live monitoring view."""
    
    settings_requested = Signal()
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        """Initialize live view.
        
        Args:
            config_manager: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config = config_manager
        self.recording_active = False
        
        self.setup_ui()
        
        # Update timer - refresh status every 5 seconds
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)
        
        # Initial status update
        self.update_status()
    
    def setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Video preview (main area)
        video_device = self.config.get_video_device()
        self.video_widget = VideoPreviewWidget(device_path=video_device)
        self.video_widget.setMinimumHeight(400)
        layout.addWidget(self.video_widget, stretch=3)
        
        # Status panel
        status_panel = self.create_status_panel()
        layout.addWidget(status_panel, stretch=1)
        
        # Settings button
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setMinimumHeight(50)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)
    
    def create_status_panel(self) -> QFrame:
        """Create the status information panel.
        
        Returns:
            Status panel widget
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        
        # Recording status
        self.recording_label = QLabel("● Idle")
        self.recording_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #666;")
        layout.addWidget(self.recording_label)
        
        # Next recording
        self.next_recording_label = QLabel("Next: --")
        self.next_recording_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.next_recording_label)
        
        # Sync status
        self.sync_label = QLabel("Sync: --")
        self.sync_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.sync_label)
        
        # Storage
        self.storage_label = QLabel("Storage: --")
        self.storage_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.storage_label)
        
        return panel
    
    def update_status(self):
        """Update all status information."""
        self.update_recording_status()
        self.update_next_recording()
        self.update_sync_status()
        self.update_storage_status()
    
    def update_recording_status(self):
        """Update recording status indicator."""
        # Check if any recording service is active
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'filmbot-record-*.service'],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0 and 'active' in result.stdout:
                self.recording_active = True
                self.recording_label.setText("🔴 RECORDING")
                self.recording_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")
                self.video_widget.set_recording(True)
            else:
                self.recording_active = False
                self.recording_label.setText("● Idle")
                self.recording_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #666;")
                self.video_widget.set_recording(False)
        except Exception as e:
            print(f"Error checking recording status: {e}")
    
    def update_next_recording(self):
        """Update next scheduled recording information."""
        schedules = self.config.get_schedules()
        
        if not schedules:
            self.next_recording_label.setText("Next: No schedules configured")
            return
        
        # Find next upcoming recording
        # For now, just show the first enabled schedule
        for schedule in schedules:
            if schedule.get('enabled', True):
                day = schedule['day_of_week'].capitalize()
                time = schedule['start_time']
                duration = schedule['duration_minutes']
                self.next_recording_label.setText(
                    f"Next: {day} {time} ({duration} min)"
                )
                return
        
        self.next_recording_label.setText("Next: No enabled schedules")
    
    def update_sync_status(self):
        """Update Google Drive sync status."""
        log_path = Path("/var/log/filmbot-rclone.log")
        
        if not log_path.exists():
            self.sync_label.setText("Sync: No log file")
            return
        
        try:
            # Read last few lines of log
            result = subprocess.run(
                ['tail', '-n', '20', str(log_path)],
                capture_output=True,
                text=True
            )
            
            if 'Transferred:' in result.stdout:
                # Parse for recent activity
                self.sync_label.setText("Sync: ✓ Active")
                self.sync_label.setStyleSheet("font-size: 14px; color: #4CAF50;")
            else:
                self.sync_label.setText("Sync: Idle")
                self.sync_label.setStyleSheet("font-size: 14px;")
        except Exception as e:
            self.sync_label.setText(f"Sync: Error")
            print(f"Error reading sync log: {e}")
    
    def update_storage_status(self):
        """Update local storage information."""
        recordings_path = Path("/mnt/nvme/recordings")
        
        # Fallback for development
        if not recordings_path.exists():
            recordings_path = Path.home() / "filmbot-recordings"
            recordings_path.mkdir(exist_ok=True)
        
        try:
            # Get disk usage
            stat = os.statvfs(recordings_path)
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            used_gb = ((stat.f_blocks - stat.f_bfree) * stat.f_frsize) / (1024**3)
            
            self.storage_label.setText(f"Storage: {used_gb:.1f} GB / {total_gb:.1f} GB")
        except Exception as e:
            self.storage_label.setText("Storage: --")
            print(f"Error getting storage info: {e}")
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.update_timer.stop()
        super().closeEvent(event)

