"""
Settings screen for Filmbot appliance.
Allows configuration changes after initial setup.
"""

import socket
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QComboBox, QSpinBox, QTimeEdit, QGroupBox, QScrollArea, QCheckBox
)
from PySide6.QtGui import QFont

from config_manager import ConfigManager
from systemd_manager import SystemdManager
from device_detector import detect_video_devices, detect_audio_devices


class SettingsScreen(QWidget):
    """Settings and configuration screen."""
    
    back_requested = Signal()
    
    def __init__(self, config: ConfigManager, parent=None):
        """Initialize settings screen.
        
        Args:
            config: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config = config
        self.systemd_mgr = SystemdManager(dry_run=True)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the UI layout."""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2196F3;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Device settings
        content_layout.addWidget(self.create_device_section())

        # Google Drive settings
        content_layout.addWidget(self.create_drive_section())

        # Recording schedules
        content_layout.addWidget(self.create_schedules_section())

        # System info
        content_layout.addWidget(self.create_system_section())
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Back button
        back_btn = QPushButton("← Back to Live View")
        back_btn.setMinimumHeight(50)
        back_btn.setStyleSheet("""
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
        back_btn.clicked.connect(self.back_requested.emit)
        main_layout.addWidget(back_btn)

    def create_device_section(self) -> QGroupBox:
        """Create device settings section."""
        group = QGroupBox("Recording Devices")
        group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        layout = QVBoxLayout(group)

        # Video device
        layout.addWidget(QLabel("Video Device:"))
        self.video_device_combo = QComboBox()
        self.video_device_combo.setMinimumHeight(40)
        layout.addWidget(self.video_device_combo)

        # Audio device
        layout.addWidget(QLabel("Audio Device:"))
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.setMinimumHeight(40)
        layout.addWidget(self.audio_device_combo)

        # Buttons
        btn_layout = QHBoxLayout()

        detect_btn = QPushButton("🔍 Detect Devices")
        detect_btn.setMinimumHeight(40)
        detect_btn.clicked.connect(self.detect_devices)
        btn_layout.addWidget(detect_btn)

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_device_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        return group

    def create_drive_section(self) -> QGroupBox:
        """Create Google Drive settings section."""
        group = QGroupBox("Google Drive")
        group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        layout = QVBoxLayout(group)
        
        # Remote
        remote_label = QLabel("Remote:")
        remote_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(remote_label)
        self.remote_input = QLineEdit()
        self.remote_input.setMinimumHeight(50)
        self.remote_input.setStyleSheet("font-size: 16px; padding: 8px; font-weight: bold;")
        layout.addWidget(self.remote_input)
        
        # Folder
        folder_label = QLabel("Folder:")
        folder_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(folder_label)

        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setMinimumHeight(50)
        self.folder_input.setStyleSheet("font-size: 16px; padding: 8px; font-weight: bold;")
        folder_row.addWidget(self.folder_input)

        browse_btn = QPushButton("📁 Browse")
        browse_btn.setMinimumHeight(50)
        browse_btn.setFixedWidth(140)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #F57C00;
            }
        """)
        browse_btn.clicked.connect(self.browse_drive_folders)
        folder_row.addWidget(browse_btn)

        layout.addLayout(folder_row)

        # Buttons
        btn_layout = QHBoxLayout()

        test_btn = QPushButton("Test Connection")
        test_btn.setMinimumHeight(40)
        test_btn.clicked.connect(self.test_drive_connection)
        btn_layout.addWidget(test_btn)

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_drive_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def create_schedules_section(self) -> QGroupBox:
        """Create recording schedules section."""
        group = QGroupBox("Recording Schedules")
        group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        layout = QVBoxLayout(group)
        
        # Schedule list
        self.schedule_list = QListWidget()
        self.schedule_list.setMinimumHeight(150)
        layout.addWidget(self.schedule_list)
        
        # Add schedule form
        form_layout = QHBoxLayout()
        
        self.day_combo = QComboBox()
        self.day_combo.addItems([
            "Sunday", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday"
        ])
        form_layout.addWidget(self.day_combo)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(9, 0))
        form_layout.addWidget(self.time_edit)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 240)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" min")
        form_layout.addWidget(self.duration_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self.add_schedule)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("- Remove")
        remove_btn.clicked.connect(self.remove_schedule)
        btn_layout.addWidget(remove_btn)
        
        layout.addLayout(btn_layout)
        
        return group

    def create_system_section(self) -> QGroupBox:
        """Create system information section."""
        group = QGroupBox("System Information")
        group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        layout = QVBoxLayout(group)

        # Device name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Device Name:"))
        self.device_name_input = QLineEdit()
        self.device_name_input.setMinimumHeight(40)
        name_layout.addWidget(self.device_name_input)
        layout.addLayout(name_layout)

        # Hostname
        self.hostname_label = QLabel("Hostname: --")
        layout.addWidget(self.hostname_label)

        # IP address
        self.ip_label = QLabel("IP Address: --")
        layout.addWidget(self.ip_label)

        # Storage
        self.storage_info_label = QLabel("Storage: --")
        layout.addWidget(self.storage_info_label)

        # Kiosk mode (hide taskbar)
        self.hide_taskbar_checkbox = QCheckBox("Hide taskbar (Kiosk Mode)")
        self.hide_taskbar_checkbox.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.hide_taskbar_checkbox)

        help_label = QLabel("⚠️ Restart app to apply kiosk mode changes")
        help_label.setStyleSheet("font-size: 12px; color: #666; font-style: italic;")
        layout.addWidget(help_label)

        # Save buttons
        btn_layout = QHBoxLayout()

        save_name_btn = QPushButton("Save Device Name")
        save_name_btn.setMinimumHeight(40)
        save_name_btn.clicked.connect(self.save_device_name)
        btn_layout.addWidget(save_name_btn)

        save_ui_btn = QPushButton("Save UI Settings")
        save_ui_btn.setMinimumHeight(40)
        save_ui_btn.clicked.connect(self.save_ui_settings)
        btn_layout.addWidget(save_ui_btn)

        layout.addLayout(btn_layout)

        return group

    def load_settings(self):
        """Load current settings from config."""
        # Device settings
        self.load_devices()

        # Drive settings
        drive_config = self.config.get_drive_config()
        self.remote_input.setText(drive_config['remote'])
        self.folder_input.setText(drive_config['folder'])

        # Schedules
        self.load_schedules()

        # System info
        self.device_name_input.setText(self.config.get_device_name())
        self.hostname_label.setText(f"Hostname: {socket.gethostname()}")

        # Get IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"IP Address: {ip}")
        except:
            self.ip_label.setText("IP Address: Not connected")

        # Storage info
        self.update_storage_info()

        # UI settings
        self.hide_taskbar_checkbox.setChecked(self.config.get_hide_taskbar())

    def load_schedules(self):
        """Load schedules into list."""
        self.schedule_list.clear()
        for schedule in self.config.get_schedules():
            day = schedule['day_of_week'].capitalize()
            time = schedule['start_time']
            duration = schedule['duration_minutes']
            text = f"{day} {time} - {duration} min"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, schedule['id'])
            self.schedule_list.addItem(item)

    def update_storage_info(self):
        """Update storage information."""
        import os
        recordings_path = Path("/mnt/nvme/recordings")

        if not recordings_path.exists():
            recordings_path = Path.home() / "filmbot-recordings"
            recordings_path.mkdir(exist_ok=True)

        try:
            stat = os.statvfs(recordings_path)
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            used_gb = ((stat.f_blocks - stat.f_bfree) * stat.f_frsize) / (1024**3)
            self.storage_info_label.setText(f"Storage: {used_gb:.1f} GB / {total_gb:.1f} GB")
        except:
            self.storage_info_label.setText("Storage: --")

    def browse_drive_folders(self):
        """Browse Google Drive folders using rclone."""
        remote = self.remote_input.text().strip()

        if not remote:
            QMessageBox.warning(self, "Error", "Please enter a remote name first")
            return

        try:
            # Get current folder or root
            current_folder = self.folder_input.text().strip()

            # List directories
            result = subprocess.run(
                ['rclone', 'lsd', f"{remote}{current_folder}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                QMessageBox.warning(self, "Error", f"Failed to list folders:\n{result.stderr}")
                return

            # Parse folder list
            folders = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # rclone lsd format: "          -1 2024-01-01 12:00:00        -1 FolderName"
                    parts = line.split()
                    if len(parts) >= 5:
                        folder_name = ' '.join(parts[4:])
                        folders.append(folder_name)

            if not folders:
                QMessageBox.information(self, "Browse", "No folders found in this location")
                return

            # Show folder selection dialog
            from PySide6.QtWidgets import QInputDialog
            folder, ok = QInputDialog.getItem(
                self,
                "Select Folder",
                "Choose a folder:",
                folders,
                0,
                False
            )

            if ok and folder:
                # Append to current path
                if current_folder:
                    new_path = f"{current_folder}/{folder}"
                else:
                    new_path = folder
                self.folder_input.setText(new_path)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Browse failed: {str(e)}")

    def test_drive_connection(self):
        """Test Google Drive connection."""
        remote = self.remote_input.text().strip()
        folder = self.folder_input.text().strip()

        if not remote:
            QMessageBox.warning(self, "Error", "Please enter a remote name")
            return

        try:
            result = subprocess.run(
                ['rclone', 'lsd', f"{remote}{folder}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                QMessageBox.information(self, "Success", "Connection test successful!")
            else:
                QMessageBox.warning(self, "Error", f"Connection failed:\n{result.stderr}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Test failed: {str(e)}")

    def save_drive_settings(self):
        """Save Google Drive settings."""
        remote = self.remote_input.text().strip()
        folder = self.folder_input.text().strip()

        if not remote or not folder:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        self.config.set_drive_config(remote, folder)
        QMessageBox.information(self, "Success", "Drive settings saved!")

    def add_schedule(self):
        """Add a new recording schedule."""
        day = self.day_combo.currentText().lower()
        time = self.time_edit.time().toString("HH:mm")
        duration = self.duration_spin.value()

        schedule_id = self.config.add_schedule(day, time, duration)

        # Create systemd service
        schedule = {
            'id': schedule_id,
            'day_of_week': day,
            'start_time': time,
            'duration_minutes': duration,
            'enabled': True
        }

        # Note: In production, remove dry_run
        # self.systemd_mgr.create_schedule_services(schedule)

        self.load_schedules()
        QMessageBox.information(self, "Success", "Schedule added!")

    def remove_schedule(self):
        """Remove selected schedule."""
        current_item = self.schedule_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a schedule to remove")
            return

        schedule_id = current_item.data(Qt.UserRole)

        # Remove systemd service
        # Note: In production, remove dry_run
        # self.systemd_mgr.remove_schedule_services(schedule_id)

        self.config.remove_schedule(schedule_id)
        self.load_schedules()
        QMessageBox.information(self, "Success", "Schedule removed!")

    def save_device_name(self):
        """Save device name."""
        name = self.device_name_input.text().strip()
        if name:
            self.config.set_device_name(name)
            QMessageBox.information(self, "Success", "Device name saved!")
        else:
            QMessageBox.warning(self, "Error", "Please enter a device name")

    def save_ui_settings(self):
        """Save UI settings."""
        hide_taskbar = self.hide_taskbar_checkbox.isChecked()
        self.config.set_hide_taskbar(hide_taskbar)
        QMessageBox.information(
            self,
            "Success",
            "UI settings saved!\n\nRestart the app for changes to take effect."
        )

    def load_devices(self):
        """Load device settings into combos."""
        self.detect_devices()

        # Select current devices
        devices = self.config.get_devices()

        # Select current video device
        for i in range(self.video_device_combo.count()):
            if self.video_device_combo.itemData(i) == devices['video_device']:
                self.video_device_combo.setCurrentIndex(i)
                break

        # Select current audio device
        for i in range(self.audio_device_combo.count()):
            if self.audio_device_combo.itemData(i) == devices['audio_device']:
                self.audio_device_combo.setCurrentIndex(i)
                break

    def detect_devices(self):
        """Detect available devices."""
        # Detect video devices
        video_devices = detect_video_devices()
        self.video_device_combo.clear()
        for device_path, device_name in video_devices:
            self.video_device_combo.addItem(f"{device_name}", device_path)

        # Detect audio devices
        audio_devices = detect_audio_devices()
        self.audio_device_combo.clear()
        for device_id, device_name in audio_devices:
            self.audio_device_combo.addItem(f"{device_name}", device_id)

    def save_device_settings(self):
        """Save device settings."""
        if self.video_device_combo.count() == 0 or self.audio_device_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No devices detected")
            return

        video_device = self.video_device_combo.currentData()
        audio_device = self.audio_device_combo.currentData()

        self.config.set_devices(video_device, audio_device)
        QMessageBox.information(
            self,
            "Success",
            "Device settings saved!\n\nRestart the UI for changes to take effect."
        )

