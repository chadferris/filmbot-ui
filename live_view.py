"""
Live monitoring view for Filmbot appliance.
Main screen showing video preview and status information.
"""

import os
import subprocess
import struct
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QProcess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget, QProgressBar
)
from PySide6.QtGui import QFont

from video_preview import VideoPreviewWidget
from recording_screen import RecordingScreen
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
        self.signal_file = Path("/tmp/filmbot-recording")

        # Audio monitoring
        self.audio_process = None
        self.audio_buffer = bytearray()

        self.setup_ui()

        # Update timer - refresh status every 1 second (faster to detect recording)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)

        # Audio level timer - update every 100ms for smooth meter
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self.update_audio_level)
        self.audio_timer.start(100)

        # Initial status update
        self.update_status()

        # Start audio monitoring
        self.start_audio_monitoring()
    
    def setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Stacked widget to switch between live view and recording screen
        self.stack = QStackedWidget()

        # Live view with video preview
        live_widget = QWidget()
        live_layout = QVBoxLayout(live_widget)
        live_layout.setContentsMargins(0, 0, 0, 0)
        live_layout.setSpacing(5)

        video_device = self.config.get_video_device()
        self.video_widget = VideoPreviewWidget(device_path=video_device)
        live_layout.addWidget(self.video_widget, stretch=1)

        # Audio level meter
        audio_bar = self.create_audio_meter()
        live_layout.addWidget(audio_bar)

        # Compact bottom bar with status and settings button
        bottom_bar = self.create_bottom_bar()
        live_layout.addWidget(bottom_bar)

        # Recording screen
        self.recording_widget = RecordingScreen()

        # Add both to stack
        self.stack.addWidget(live_widget)
        self.stack.addWidget(self.recording_widget)

        layout.addWidget(self.stack)

    def create_audio_meter(self) -> QWidget:
        """Create audio level meter widget."""
        bar = QWidget()
        bar.setMaximumHeight(40)
        bar.setStyleSheet("""
            QWidget {
                background-color: #2c2c2c;
                border-radius: 3px;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Audio icon/label
        audio_label = QLabel("🎤 Audio:")
        audio_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        layout.addWidget(audio_label)

        # Progress bar for audio level
        self.audio_meter = QProgressBar()
        self.audio_meter.setRange(0, 100)
        self.audio_meter.setValue(0)
        self.audio_meter.setTextVisible(False)
        self.audio_meter.setMaximumHeight(20)
        self.audio_meter.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.7 #4CAF50,
                    stop:0.7 #FFC107, stop:0.9 #FFC107,
                    stop:0.9 #F44336);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.audio_meter, stretch=1)

        # dB label
        self.audio_db_label = QLabel("-- dB")
        self.audio_db_label.setStyleSheet("font-size: 12px; color: #aaa; min-width: 60px;")
        layout.addWidget(self.audio_db_label)

        return bar

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
        self.check_recording_signal()
        self.update_recording_status()
        self.update_next_recording()
        self.update_storage_status()

    def check_recording_signal(self):
        """Check if recording signal file exists and switch screens accordingly."""
        if self.signal_file.exists():
            # Recording is active - switch to recording screen
            if self.stack.currentIndex() != 1:
                print("Recording signal detected - stopping video preview and audio monitoring")
                self.video_widget.stop_preview()
                self.stop_audio_monitoring()
                self.stack.setCurrentIndex(1)

                # Try to read filename from signal file
                try:
                    with open(self.signal_file, 'r') as f:
                        filename = Path(f.read().strip()).name
                        self.recording_widget.set_filename(filename)
                except:
                    pass
        else:
            # Recording is not active - switch to live view
            if self.stack.currentIndex() != 0:
                print("Recording signal cleared - restarting video preview and audio monitoring")
                self.stack.setCurrentIndex(0)
                self.video_widget.start_preview()
                self.start_audio_monitoring()
    
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
    
    def start_audio_monitoring(self):
        """Start background audio monitoring process."""
        if self.audio_process is not None:
            return  # Already running

        audio_device = self.config.get_audio_device()

        # Start arecord process to continuously capture audio
        self.audio_process = QProcess(self)
        self.audio_process.readyReadStandardOutput.connect(self.on_audio_data)

        # Capture 0.1 second chunks continuously (4800 samples at 48kHz)
        # Format: S16_LE (16-bit signed little endian), 2 channels, 48kHz
        self.audio_process.start('arecord', [
            '-D', audio_device,
            '-f', 'S16_LE',
            '-r', '48000',
            '-c', '2',
            '-t', 'raw'  # Raw PCM output
        ])

    def stop_audio_monitoring(self):
        """Stop background audio monitoring process."""
        if self.audio_process is not None:
            self.audio_process.kill()
            self.audio_process.waitForFinished(1000)
            self.audio_process = None
            self.audio_buffer.clear()

            # Reset meter
            self.audio_meter.setValue(0)
            self.audio_db_label.setText("-- dB")

    def on_audio_data(self):
        """Handle incoming audio data from arecord process."""
        if self.audio_process is None:
            return

        # Read available data
        data = self.audio_process.readAllStandardOutput().data()
        self.audio_buffer.extend(data)

        # Keep buffer size reasonable (last 0.5 seconds = 96000 samples * 2 bytes * 2 channels)
        max_buffer_size = 96000 * 2 * 2
        if len(self.audio_buffer) > max_buffer_size:
            self.audio_buffer = self.audio_buffer[-max_buffer_size:]

    def update_audio_level(self):
        """Calculate and update audio level meter from buffer."""
        if len(self.audio_buffer) < 4:
            return

        # Calculate RMS from buffer (16-bit signed samples)
        samples = []
        for i in range(0, len(self.audio_buffer) - 1, 2):
            # Unpack 16-bit signed integer
            sample = struct.unpack('<h', self.audio_buffer[i:i+2])[0]
            samples.append(sample)

        if not samples:
            return

        # Calculate RMS (Root Mean Square)
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5

        # Convert to dB (reference: 32768 = 0 dB for 16-bit audio)
        if rms > 0:
            db = 20 * (rms / 32768.0) ** 0.5 * 100  # Scale to 0-100 for progress bar
            db_value = 20 * ((rms / 32768.0) ** 0.5) - 60  # Actual dB value (-60 to 0 range)

            # Clamp to 0-100 for progress bar
            db = max(0, min(100, db))

            self.audio_meter.setValue(int(db))
            self.audio_db_label.setText(f"{db_value:.1f} dB")
        else:
            self.audio_meter.setValue(0)
            self.audio_db_label.setText("-- dB")

    def closeEvent(self, event):
        """Handle widget close event."""
        self.update_timer.stop()
        self.audio_timer.stop()
        self.stop_audio_monitoring()
        super().closeEvent(event)

