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
        self.signal_file_path = Path("/tmp/filmbot-recording")
        self.video_preview_stopped = False

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
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Video preview (main area - maximize this)
        video_device = self.config.get_video_device()
        self.video_widget = VideoPreviewWidget(device_path=video_device)
        layout.addWidget(self.video_widget, stretch=1)

        # Compact bottom bar with status and settings button
        bottom_bar = self.create_bottom_bar()
        layout.addWidget(bottom_bar)
    
    def create_bottom_bar(self) -> QWidget:
        """Create compact bottom bar with status and settings button."""
        bar = QWidget()
        bar.setMaximumHeight(50)
        bar.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 3px;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(10)

        # Recording status (compact)
        self.recording_label = QLabel("● Idle")
        self.recording_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666;")
        layout.addWidget(self.recording_label)

        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #ccc; font-size: 16px;")
        layout.addWidget(sep1)

        # Next recording (compact)
        self.next_recording_label = QLabel("Next: --")
        self.next_recording_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.next_recording_label)

        # Separator
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #ccc; font-size: 16px;")
        layout.addWidget(sep2)

        # Storage (compact)
        self.storage_label = QLabel("Storage: --")
        self.storage_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.storage_label)

        # Spacer to push settings button to the right
        layout.addStretch()

        # Settings button (compact)
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setFixedHeight(40)
        settings_btn.setMinimumWidth(140)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)

        return bar
    
    def update_status(self):
        """Update all status information."""
        self.check_signal_file()
        self.update_recording_status()
        self.update_next_recording()
        self.update_storage_status()

    def check_signal_file(self):
        """Check for recording signal file and manage video preview."""
        signal_exists = self.signal_file_path.exists()

        if signal_exists and not self.video_preview_stopped:
            # Recording started - stop video preview to release device
            print("Recording signal detected - stopping video preview")
            self.video_widget.stop_preview()
            self.video_preview_stopped = True
        elif not signal_exists and self.video_preview_stopped:
            # Recording finished - restart video preview
            print("Recording signal cleared - restarting video preview")
            self.video_widget.start_preview()
            self.video_preview_stopped = False
    
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
                self.recording_label.setText("🔴 REC")
                self.recording_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f44336;")
                self.video_widget.set_recording(True)
            else:
                self.recording_active = False
                self.recording_label.setText("● Idle")
                self.recording_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666;")
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

