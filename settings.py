"""
Settings screen for Filmbot appliance.
Allows configuration changes after initial setup.
"""

import socket
import subprocess
import sys
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QTime, QTimer
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
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Title - smaller for compact display
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(6)
        content_layout.setContentsMargins(3, 3, 3, 3)

        # Use 2-column layout for top sections to save vertical space
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # Left column: Devices + System
        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        left_col.addWidget(self.create_device_section())
        left_col.addWidget(self.create_system_section())
        top_row.addLayout(left_col)

        # Right column: Google Drive + Schedules
        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_col.addWidget(self.create_drive_section())
        right_col.addWidget(self.create_schedules_section())
        top_row.addLayout(right_col)

        content_layout.addLayout(top_row)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Back button - taller for touch
        back_btn = QPushButton("← Back")
        back_btn.setMinimumHeight(45)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
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
        group = QGroupBox("Devices")
        group.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; padding-top: 8px; }")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 10, 4, 4)

        # Video device - inline label
        video_row = QHBoxLayout()
        video_row.setSpacing(3)
        video_label = QLabel("Video:")
        video_label.setStyleSheet("font-size: 11px;")
        video_label.setFixedWidth(45)
        video_row.addWidget(video_label)
        self.video_device_combo = QComboBox()
        self.video_device_combo.setMinimumHeight(38)
        self.video_device_combo.setStyleSheet("font-size: 10px;")
        video_row.addWidget(self.video_device_combo)
        layout.addLayout(video_row)

        # Audio device - inline label
        audio_row = QHBoxLayout()
        audio_row.setSpacing(3)
        audio_label = QLabel("Audio:")
        audio_label.setStyleSheet("font-size: 11px;")
        audio_label.setFixedWidth(45)
        audio_row.addWidget(audio_label)
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.setMinimumHeight(38)
        self.audio_device_combo.setStyleSheet("font-size: 10px;")
        audio_row.addWidget(self.audio_device_combo)
        layout.addLayout(audio_row)

        # Buttons - taller, stacked vertically
        detect_btn = QPushButton("🔍 Detect")
        detect_btn.setMinimumHeight(40)
        detect_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        detect_btn.clicked.connect(self.detect_devices)
        layout.addWidget(detect_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        save_btn.clicked.connect(self.save_device_settings)
        layout.addWidget(save_btn)

        return group

    def create_drive_section(self) -> QGroupBox:
        """Create Google Drive settings section."""
        group = QGroupBox("Google Drive")
        group.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; padding-top: 8px; }")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 10, 4, 4)

        # Remote - inline label
        remote_row = QHBoxLayout()
        remote_row.setSpacing(3)
        remote_label = QLabel("Remote:")
        remote_label.setStyleSheet("font-size: 11px;")
        remote_label.setFixedWidth(55)
        remote_row.addWidget(remote_label)
        self.remote_input = QLineEdit()
        self.remote_input.setMinimumHeight(38)
        self.remote_input.setStyleSheet("font-size: 10px; padding: 4px;")
        remote_row.addWidget(self.remote_input)
        layout.addLayout(remote_row)

        # Folder - inline label with browse button
        folder_row = QHBoxLayout()
        folder_row.setSpacing(3)
        folder_label = QLabel("Folder:")
        folder_label.setStyleSheet("font-size: 11px;")
        folder_label.setFixedWidth(55)
        folder_row.addWidget(folder_label)

        self.folder_input = QLineEdit()
        self.folder_input.setMinimumHeight(38)
        self.folder_input.setStyleSheet("font-size: 10px; padding: 4px;")
        folder_row.addWidget(self.folder_input)

        browse_btn = QPushButton("📁")
        browse_btn.setMinimumHeight(38)
        browse_btn.setFixedWidth(45)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
            }
            QPushButton:pressed {
                background-color: #F57C00;
            }
        """)
        browse_btn.clicked.connect(self.browse_drive_folders)
        folder_row.addWidget(browse_btn)

        layout.addLayout(folder_row)

        # Buttons - taller, stacked
        test_btn = QPushButton("🔗 Test")
        test_btn.setMinimumHeight(40)
        test_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        test_btn.clicked.connect(self.test_drive_connection)
        layout.addWidget(test_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        save_btn.clicked.connect(self.save_drive_settings)
        layout.addWidget(save_btn)

        return group
    
    def create_schedules_section(self) -> QGroupBox:
        """Create recording schedules section."""
        group = QGroupBox("Schedules")
        group.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; padding-top: 8px; }")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 10, 4, 4)

        # Schedule list with buttons on the right
        list_row = QHBoxLayout()
        list_row.setSpacing(3)

        self.schedule_list = QListWidget()
        self.schedule_list.setMinimumHeight(70)
        self.schedule_list.setStyleSheet("font-size: 10px;")
        list_row.addWidget(self.schedule_list)

        # Buttons on the right side of list
        btn_col = QVBoxLayout()
        btn_col.setSpacing(3)

        add_btn = QPushButton("➕")
        add_btn.setMinimumHeight(32)
        add_btn.setFixedWidth(40)
        add_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        add_btn.clicked.connect(self.add_schedule)
        btn_col.addWidget(add_btn)

        remove_btn = QPushButton("➖")
        remove_btn.setMinimumHeight(32)
        remove_btn.setFixedWidth(40)
        remove_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        remove_btn.clicked.connect(self.remove_schedule)
        btn_col.addWidget(remove_btn)

        list_row.addLayout(btn_col)
        layout.addLayout(list_row)

        # Add schedule form - vertical stack for touch
        self.day_combo = QComboBox()
        self.day_combo.addItems([
            "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
        ])
        self.day_combo.setMinimumHeight(38)
        self.day_combo.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.day_combo)

        time_dur_layout = QHBoxLayout()
        time_dur_layout.setSpacing(3)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setMinimumHeight(38)
        self.time_edit.setStyleSheet("font-size: 11px;")
        time_dur_layout.addWidget(self.time_edit)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 240)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix("m")
        self.duration_spin.setMinimumHeight(38)
        self.duration_spin.setStyleSheet("font-size: 11px;")
        time_dur_layout.addWidget(self.duration_spin)

        layout.addLayout(time_dur_layout)

        return group

    def create_system_section(self) -> QGroupBox:
        """Create system information section."""
        group = QGroupBox("System")
        group.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; padding-top: 8px; }")
        layout = QVBoxLayout(group)
        layout.setSpacing(3)
        layout.setContentsMargins(4, 10, 4, 4)

        # Device name - inline
        name_row = QHBoxLayout()
        name_row.setSpacing(3)
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-size: 11px;")
        name_label.setFixedWidth(45)
        name_row.addWidget(name_label)

        self.device_name_input = QLineEdit()
        self.device_name_input.setMinimumHeight(38)
        self.device_name_input.setStyleSheet("font-size: 10px;")
        name_row.addWidget(self.device_name_input)

        save_name_btn = QPushButton("💾")
        save_name_btn.setMinimumHeight(38)
        save_name_btn.setFixedWidth(45)
        save_name_btn.setStyleSheet("font-size: 14px;")
        save_name_btn.clicked.connect(self.save_device_name)
        name_row.addWidget(save_name_btn)
        layout.addLayout(name_row)

        # Info labels - hostname and IP on same line
        info_row = QHBoxLayout()
        self.hostname_label = QLabel("Host: --")
        self.hostname_label.setStyleSheet("font-size: 9px;")
        info_row.addWidget(self.hostname_label)

        self.ip_label = QLabel("IP: --")
        self.ip_label.setStyleSheet("font-size: 9px;")
        info_row.addWidget(self.ip_label)
        layout.addLayout(info_row)

        self.storage_info_label = QLabel("Storage: --")
        self.storage_info_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(self.storage_info_label)

        # Kiosk mode - checkbox and button on same line
        kiosk_row = QHBoxLayout()
        kiosk_row.setSpacing(3)
        self.hide_taskbar_checkbox = QCheckBox("Kiosk")
        self.hide_taskbar_checkbox.setMinimumHeight(40)
        self.hide_taskbar_checkbox.setStyleSheet("font-size: 11px;")
        kiosk_row.addWidget(self.hide_taskbar_checkbox)

        save_ui_btn = QPushButton("🔄 Apply")
        save_ui_btn.setMinimumHeight(40)
        save_ui_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        save_ui_btn.clicked.connect(self.save_ui_settings)
        kiosk_row.addWidget(save_ui_btn)
        layout.addLayout(kiosk_row)

        # Email alerts button
        email_btn = QPushButton("📧 Email Alerts")
        email_btn.setMinimumHeight(40)
        email_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        email_btn.clicked.connect(self.open_email_alerts_dialog)
        layout.addWidget(email_btn)

        return group

    def open_email_alerts_dialog(self):
        """Open email alerts configuration dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QGridLayout
        from PySide6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowTitle("Email Alerts Settings")
        dialog.setMinimumWidth(700)
        dialog.setMaximumHeight(400)

        # Set window flags to allow positioning on Wayland
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title bar (since we removed window frame)
        title_bar = QHBoxLayout()
        title_label = QLabel("📧 Email Alerts Settings")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        title_bar.addWidget(title_label)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("font-size: 16px; background: #f44336; color: white; border-radius: 4px;")
        close_btn.clicked.connect(dialog.reject)
        title_bar.addWidget(close_btn)
        layout.addLayout(title_bar)

        # Enable checkbox
        enable_checkbox = QCheckBox("Enable Email Alerts")
        enable_checkbox.setMinimumHeight(35)
        enable_checkbox.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(enable_checkbox)

        # Grid layout for compact form
        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 5, 0, 5)

        # Email from - label and input on same row
        from_label = QLabel("Gmail:")
        from_label.setStyleSheet("font-size: 11px;")
        from_label.setFixedWidth(80)
        grid.addWidget(from_label, 0, 0)

        from_input = QLineEdit()
        from_input.setPlaceholderText("filmbot-alerts@gmail.com")
        from_input.setMinimumHeight(38)
        from_input.setStyleSheet("font-size: 11px; padding: 3px;")
        grid.addWidget(from_input, 0, 1)

        # Email to - label and input on same row
        to_label = QLabel("Send To:")
        to_label.setStyleSheet("font-size: 11px;")
        to_label.setFixedWidth(80)
        grid.addWidget(to_label, 1, 0)

        to_input = QLineEdit()
        to_input.setPlaceholderText("admin@example.com")
        to_input.setMinimumHeight(38)
        to_input.setStyleSheet("font-size: 11px; padding: 3px;")
        grid.addWidget(to_input, 1, 1)

        # Password - label and input on same row
        pass_label = QLabel("App Password:")
        pass_label.setStyleSheet("font-size: 11px;")
        pass_label.setFixedWidth(80)
        grid.addWidget(pass_label, 2, 0)

        pass_input = QLineEdit()
        pass_input.setPlaceholderText("xxxx xxxx xxxx xxxx")
        pass_input.setEchoMode(QLineEdit.Password)
        pass_input.setMinimumHeight(38)
        pass_input.setStyleSheet("font-size: 11px; padding: 3px;")
        grid.addWidget(pass_input, 2, 1)

        # Help text below password
        pass_help = QLabel("Generate at: myaccount.google.com/apppasswords")
        pass_help.setStyleSheet("font-size: 9px; color: #666;")
        grid.addWidget(pass_help, 3, 1)

        layout.addLayout(grid)

        # Load current settings
        alerts_config = self.config.get_alerts_config()
        enable_checkbox.setChecked(alerts_config.get('enabled', False))
        from_input.setText(alerts_config.get('email_from', ''))
        email_to = alerts_config.get('email_to', [])
        to_input.setText(email_to[0] if email_to else '')
        pass_input.setText(alerts_config.get('smtp_password', ''))

        # Toggle fields
        def toggle_fields(enabled):
            from_input.setEnabled(enabled)
            to_input.setEnabled(enabled)
            pass_input.setEnabled(enabled)

        enable_checkbox.toggled.connect(toggle_fields)
        toggle_fields(enable_checkbox.isChecked())

        # Buttons - compact
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        test_btn = QPushButton("📧 Test")
        test_btn.setMinimumHeight(42)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)

        def test_email():
            if not enable_checkbox.isChecked():
                QMessageBox.warning(dialog, "Error", "Please enable email alerts first")
                return

            email_from = from_input.text().strip()
            email_to = to_input.text().strip()
            password = pass_input.text().strip()

            if not email_from or not email_to or not password:
                QMessageBox.warning(dialog, "Error", "Please fill in all fields")
                return

            # Save temporarily
            self.config.set_alerts_config(
                enabled=True,
                email_from=email_from,
                email_to=[email_to],
                smtp_password=password
            )

            # Test sending
            try:
                from email_notify import EmailNotifier
                notifier = EmailNotifier()
                success = notifier.send_email(
                    subject="Test Email from Filmbot",
                    body="This is a test email. If you receive this, email alerts are working!",
                    priority="info"
                )

                if success:
                    QMessageBox.information(dialog, "Success", f"Test email sent to {email_to}!")
                else:
                    QMessageBox.warning(dialog, "Failed", "Failed to send test email. Check credentials.")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error: {str(e)}")

        test_btn.clicked.connect(test_email)
        btn_layout.addWidget(test_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setMinimumHeight(42)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)

        def save_settings():
            enabled = enable_checkbox.isChecked()

            if enabled:
                email_from = from_input.text().strip()
                email_to = to_input.text().strip()
                password = pass_input.text().strip()

                if not email_from or not email_to or not password:
                    QMessageBox.warning(dialog, "Error", "Please fill in all fields")
                    return

                self.config.set_alerts_config(
                    enabled=True,
                    email_from=email_from,
                    email_to=[email_to],
                    smtp_password=password
                )
            else:
                self.config.set_alerts_config(
                    enabled=False,
                    email_from="",
                    email_to=[],
                    smtp_password=""
                )

            QMessageBox.information(dialog, "Success", "Email alerts settings saved!")
            dialog.accept()

        save_btn.clicked.connect(save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # Show and position at top of screen
        dialog.show()
        # Get screen geometry
        screen = dialog.screen()
        if screen:
            screen_geometry = screen.geometry()
            # Position at top center
            dialog_width = dialog.width()
            x = (screen_geometry.width() - dialog_width) // 2
            y = 20  # 20 pixels from top
            dialog.move(x, y)

        dialog.exec()

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
            self.ip_label.setText(f"IP: {ip}")
        except:
            self.ip_label.setText("IP: Not connected")

        # Storage info
        self.update_storage_info()

        # UI settings
        self.hide_taskbar_checkbox.setChecked(self.config.get_hide_taskbar())

    def load_schedules(self):
        """Load schedules into list."""
        self.schedule_list.clear()
        # Map full day names to abbreviations
        day_abbrev = {
            'sunday': 'Sun', 'monday': 'Mon', 'tuesday': 'Tue',
            'wednesday': 'Wed', 'thursday': 'Thu', 'friday': 'Fri', 'saturday': 'Sat'
        }
        for schedule in self.config.get_schedules():
            day = day_abbrev.get(schedule['day_of_week'].lower(), schedule['day_of_week'][:3])
            time = schedule['start_time']
            duration = schedule['duration_minutes']
            text = f"{day} {time} ({duration}m)"

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

        # Show message and restart app
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Success")
        msg.setText("UI settings saved!\n\nThe app will restart now.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

        # Restart the application
        QTimer.singleShot(100, self.restart_application)

    def restart_application(self):
        """Restart the application."""
        # Get the main window
        main_window = self.window()
        main_window.close()

        # Restart using the same executable and arguments
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

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
