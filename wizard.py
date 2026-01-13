"""
First-boot setup wizard for Filmbot appliance.
Guides user through initial configuration.
"""

import subprocess
from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QTimeEdit, QListWidget,
    QListWidgetItem, QMessageBox, QTextEdit, QStackedWidget, QCheckBox
)
from PySide6.QtGui import QFont

from config_manager import ConfigManager
from systemd_manager import SystemdManager
from device_detector import detect_video_devices, detect_audio_devices


class WizardPage(QWidget):
    """Base class for wizard pages."""
    
    next_requested = Signal()
    back_requested = Signal()
    
    def __init__(self, title: str, parent=None):
        """Initialize wizard page.
        
        Args:
            title: Page title
            parent: Parent widget
        """
        super().__init__(parent)
        self.title = title
        self.setup_base_ui()
    
    def setup_base_ui(self):
        """Setup base UI structure."""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)
    
    def add_navigation_buttons(self, show_back: bool = True, next_text: str = "Next"):
        """Add navigation buttons to the page.
        
        Args:
            show_back: Whether to show back button
            next_text: Text for next button
        """
        button_layout = QHBoxLayout()
        
        if show_back:
            back_btn = QPushButton("← Back")
            back_btn.setMinimumHeight(50)
            back_btn.setStyleSheet(self._button_style("#757575"))
            back_btn.clicked.connect(self.back_requested.emit)
            button_layout.addWidget(back_btn)
        
        next_btn = QPushButton(next_text)
        next_btn.setMinimumHeight(50)
        next_btn.setStyleSheet(self._button_style("#4CAF50"))
        next_btn.clicked.connect(self.next_requested.emit)
        button_layout.addWidget(next_btn)
        
        self.layout.addLayout(button_layout)
    
    def _button_style(self, color: str) -> str:
        """Get button stylesheet.
        
        Args:
            color: Button color
            
        Returns:
            CSS stylesheet string
        """
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:pressed {{
                background-color: {color}dd;
            }}
        """
    
    def validate(self) -> bool:
        """Validate page input.
        
        Returns:
            True if valid, False otherwise
        """
        return True


class WelcomePage(WizardPage):
    """Welcome screen."""
    
    def __init__(self, parent=None):
        super().__init__("Welcome to Filmbot", parent)
        
        # Description
        desc = QLabel(
            "This wizard will help you set up your Filmbot recording appliance.\n\n"
            "You will configure:\n"
            "• Device settings\n"
            "• Google Drive sync destination\n"
            "• Recording schedules\n"
            "• Email alerts (optional)"
        )
        desc.setStyleSheet("font-size: 16px; padding: 20px;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(desc)
        
        self.layout.addStretch()
        self.add_navigation_buttons(show_back=False, next_text="Start Setup")


class DevicePage(WizardPage):
    """Device selection page."""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__("Select Devices", parent)

        self.config = config

        # Instructions
        instructions = QLabel(
            "Select the video and audio devices for recording.\n"
            "These are typically auto-detected from your ATEM Mini."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 14px; padding: 10px;")
        self.layout.addWidget(instructions)

        # Video device selection
        video_label = QLabel("Video Device:")
        video_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.layout.addWidget(video_label)

        self.video_combo = QComboBox()
        self.video_combo.setMinimumHeight(40)
        self.video_combo.setStyleSheet("font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.video_combo)

        # Audio device selection
        audio_label = QLabel("Audio Device:")
        audio_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.layout.addWidget(audio_label)

        self.audio_combo = QComboBox()
        self.audio_combo.setMinimumHeight(40)
        self.audio_combo.setStyleSheet("font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.audio_combo)

        # Detect button
        detect_btn = QPushButton("🔍 Detect Devices")
        detect_btn.setMinimumHeight(40)
        detect_btn.setStyleSheet(self._button_style("#2196F3"))
        detect_btn.clicked.connect(self.detect_devices)
        self.layout.addWidget(detect_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        self.status_label.setWordWrap(True)
        self.layout.addWidget(self.status_label)

        self.layout.addStretch()
        self.add_navigation_buttons()

        # Initial device detection
        self.detect_devices()

    def detect_devices(self):
        """Detect available devices."""
        self.status_label.setText("Detecting devices...")

        # Detect video devices
        video_devices = detect_video_devices()
        self.video_combo.clear()
        for device_path, device_name in video_devices:
            self.video_combo.addItem(f"{device_name}", device_path)

        # Detect audio devices
        audio_devices = detect_audio_devices()
        self.audio_combo.clear()
        for device_id, device_name in audio_devices:
            self.audio_combo.addItem(f"{device_name}", device_id)

        # Update status
        self.status_label.setText(
            f"Found {len(video_devices)} video device(s) and {len(audio_devices)} audio device(s)"
        )

        # Try to select defaults
        current_devices = self.config.get_devices()

        # Select current video device if it exists
        for i in range(self.video_combo.count()):
            if self.video_combo.itemData(i) == current_devices['video_device']:
                self.video_combo.setCurrentIndex(i)
                break

        # Select current audio device if it exists
        for i in range(self.audio_combo.count()):
            if self.audio_combo.itemData(i) == current_devices['audio_device']:
                self.audio_combo.setCurrentIndex(i)
                break

    def validate(self) -> bool:
        """Validate device selection."""
        if self.video_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No video devices detected")
            return False

        if self.audio_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No audio devices detected")
            return False

        # Save device configuration
        video_device = self.video_combo.currentData()
        audio_device = self.audio_combo.currentData()

        self.config.set_devices(video_device, audio_device)

        return True


class DrivePage(WizardPage):
    """Google Drive configuration page."""
    
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__("Google Drive Setup", parent)
        
        self.config = config
        
        # Instructions
        instructions = QLabel(
            "Configure Google Drive sync for your recordings.\n"
            "Make sure you have already run 'rclone config' to authenticate."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 16px; padding: 10px;")
        self.layout.addWidget(instructions)

        # Remote name
        remote_label = QLabel("rclone Remote Name:")
        remote_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(remote_label)

        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("filmbot-drive:")
        self.remote_input.setText("filmbot-drive:")
        self.remote_input.setMinimumHeight(50)
        self.remote_input.setStyleSheet("font-size: 16px; padding: 8px; font-weight: bold;")
        self.layout.addWidget(self.remote_input)

        # Folder path
        folder_label = QLabel("Destination Folder:")
        folder_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(folder_label)

        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("OrgName/BoxID")
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
        browse_btn.clicked.connect(self.browse_folders)
        folder_row.addWidget(browse_btn)

        self.layout.addLayout(folder_row)

        # Test button
        test_btn = QPushButton("Test Connection")
        test_btn.setMinimumHeight(40)
        test_btn.setStyleSheet(self._button_style("#2196F3"))
        test_btn.clicked.connect(self.test_connection)
        self.layout.addWidget(test_btn)
        
        self.layout.addStretch()
        self.add_navigation_buttons()
    
    def browse_folders(self):
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

    def test_connection(self):
        """Test rclone connection."""
        remote = self.remote_input.text().strip()
        folder = self.folder_input.text().strip()

        if not remote:
            QMessageBox.warning(self, "Error", "Please enter a remote name")
            return

        try:
            # Test with rclone lsd
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
    
    def validate(self) -> bool:
        """Validate drive configuration."""
        if not self.remote_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a remote name")
            return False
        
        if not self.folder_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a folder path")
            return False
        
        # Save configuration
        self.config.set_drive_config(
            self.remote_input.text().strip(),
            self.folder_input.text().strip()
        )
        
        return True


class SchedulePage(WizardPage):
    """Recording schedule configuration page."""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__("Recording Schedules", parent)

        self.config = config

        # Instructions
        instructions = QLabel("Add recording schedules for your services:")
        instructions.setStyleSheet("font-size: 14px; padding: 10px;")
        self.layout.addWidget(instructions)

        # Schedule list
        self.schedule_list = QListWidget()
        self.schedule_list.setMinimumHeight(150)
        self.schedule_list.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.schedule_list)

        # Add schedule form
        form_layout = QVBoxLayout()

        # Day selector
        day_layout = QHBoxLayout()
        day_layout.addWidget(QLabel("Day:"))
        self.day_combo = QComboBox()
        self.day_combo.addItems([
            "Sunday", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday"
        ])
        self.day_combo.setMinimumHeight(40)
        day_layout.addWidget(self.day_combo)
        form_layout.addLayout(day_layout)

        # Time selector
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Start Time:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setMinimumHeight(40)
        time_layout.addWidget(self.time_edit)
        form_layout.addLayout(time_layout)

        # Duration selector
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (minutes):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 240)
        self.duration_spin.setValue(60)
        self.duration_spin.setMinimumHeight(40)
        duration_layout.addWidget(self.duration_spin)
        form_layout.addLayout(duration_layout)

        self.layout.addLayout(form_layout)

        # Add/Remove buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("+ Add Schedule")
        add_btn.setMinimumHeight(40)
        add_btn.setStyleSheet(self._button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_schedule)
        button_layout.addWidget(add_btn)

        remove_btn = QPushButton("- Remove Selected")
        remove_btn.setMinimumHeight(40)
        remove_btn.setStyleSheet(self._button_style("#f44336"))
        remove_btn.clicked.connect(self.remove_schedule)
        button_layout.addWidget(remove_btn)

        self.layout.addLayout(button_layout)

        self.layout.addStretch()
        self.add_navigation_buttons()

        # Load existing schedules
        self.load_schedules()

    def load_schedules(self):
        """Load schedules from config."""
        self.schedule_list.clear()
        for schedule in self.config.get_schedules():
            self.add_schedule_to_list(schedule)

    def add_schedule_to_list(self, schedule: dict):
        """Add a schedule to the list widget."""
        day = schedule['day_of_week'].capitalize()
        time = schedule['start_time']
        duration = schedule['duration_minutes']
        text = f"{day} {time} - {duration} minutes"

        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, schedule['id'])
        self.schedule_list.addItem(item)

    def add_schedule(self):
        """Add a new schedule."""
        day = self.day_combo.currentText().lower()
        time = self.time_edit.time().toString("HH:mm")
        duration = self.duration_spin.value()

        schedule_id = self.config.add_schedule(day, time, duration)

        # Add to list
        schedule = {
            'id': schedule_id,
            'day_of_week': day,
            'start_time': time,
            'duration_minutes': duration
        }
        self.add_schedule_to_list(schedule)

    def remove_schedule(self):
        """Remove selected schedule."""
        current_item = self.schedule_list.currentItem()
        if not current_item:
            return

        schedule_id = current_item.data(Qt.UserRole)
        self.config.remove_schedule(schedule_id)

        row = self.schedule_list.row(current_item)
        self.schedule_list.takeItem(row)

    def validate(self) -> bool:
        """Validate schedules."""
        if self.schedule_list.count() == 0:
            reply = QMessageBox.question(
                self,
                "No Schedules",
                "You haven't added any schedules. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            return reply == QMessageBox.Yes

        return True


class EmailAlertsPage(WizardPage):
    """Email alerts configuration page."""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__("Email Alerts (Optional)", parent)

        self.config = config

        # Description
        desc = QLabel(
            "Configure email alerts to be notified of system issues.\n"
            "This is optional - you can skip this step and configure it later in Settings."
        )
        desc.setStyleSheet("font-size: 14px; padding: 10px;")
        desc.setWordWrap(True)
        self.layout.addWidget(desc)

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Email Alerts")
        self.enable_checkbox.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.enable_checkbox.toggled.connect(self.toggle_fields)
        self.layout.addWidget(self.enable_checkbox)

        # Email from
        from_label = QLabel("Gmail Address (for sending alerts):")
        from_label.setStyleSheet("font-size: 13px; margin-top: 10px;")
        self.layout.addWidget(from_label)

        self.email_from_input = QLineEdit()
        self.email_from_input.setPlaceholderText("filmbot-alerts@gmail.com")
        self.email_from_input.setMinimumHeight(40)
        self.email_from_input.setStyleSheet("font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.email_from_input)

        # Email to
        to_label = QLabel("Email Address (to receive alerts):")
        to_label.setStyleSheet("font-size: 13px; margin-top: 10px;")
        self.layout.addWidget(to_label)

        self.email_to_input = QLineEdit()
        self.email_to_input.setPlaceholderText("admin@example.com")
        self.email_to_input.setMinimumHeight(40)
        self.email_to_input.setStyleSheet("font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.email_to_input)

        # App password
        password_label = QLabel("Gmail App Password:")
        password_label.setStyleSheet("font-size: 13px; margin-top: 10px;")
        self.layout.addWidget(password_label)

        password_help = QLabel(
            "Generate at: myaccount.google.com/apppasswords\n"
            "(Requires 2-Step Verification enabled)"
        )
        password_help.setStyleSheet("font-size: 11px; color: #666; margin-bottom: 5px;")
        self.layout.addWidget(password_help)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("xxxx xxxx xxxx xxxx")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.password_input)

        # Test button
        test_btn = QPushButton("Test Email Configuration")
        test_btn.setMinimumHeight(45)
        test_btn.setStyleSheet(self._button_style("#2196F3"))
        test_btn.clicked.connect(self.test_email)
        self.layout.addWidget(test_btn)

        self.layout.addStretch()
        self.add_navigation_buttons(show_back=True, next_text="Next")

        # Initially disable fields
        self.toggle_fields(False)

    def toggle_fields(self, enabled: bool):
        """Enable/disable input fields based on checkbox."""
        self.email_from_input.setEnabled(enabled)
        self.email_to_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)

    def test_email(self):
        """Test email configuration."""
        if not self.enable_checkbox.isChecked():
            QMessageBox.warning(self, "Error", "Please enable email alerts first")
            return

        email_from = self.email_from_input.text().strip()
        email_to = self.email_to_input.text().strip()
        password = self.password_input.text().strip()

        if not email_from or not email_to or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        # Save temporarily and test
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
                QMessageBox.information(
                    self,
                    "Success",
                    f"Test email sent to {email_to}!\n\nCheck your inbox (and spam folder)."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Failed",
                    "Failed to send test email. Check your credentials and try again."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error testing email: {str(e)}")

    def validate(self) -> bool:
        """Validate and save email configuration."""
        if not self.enable_checkbox.isChecked():
            # Disable alerts if not enabled
            self.config.set_alerts_config(
                enabled=False,
                email_from="",
                email_to=[],
                smtp_password=""
            )
            return True

        email_from = self.email_from_input.text().strip()
        email_to = self.email_to_input.text().strip()
        password = self.password_input.text().strip()

        if not email_from or not email_to or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields or uncheck 'Enable Email Alerts'")
            return False

        # Save configuration
        self.config.set_alerts_config(
            enabled=True,
            email_from=email_from,
            email_to=[email_to],
            smtp_password=password
        )

        return True


class FinishPage(WizardPage):
    """Finish page - apply configuration."""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__("Setup Complete", parent)

        self.config = config

        # Summary
        summary = QLabel(
            "Your Filmbot appliance is now configured!\n\n"
            "Click 'Finish' to apply settings and start monitoring."
        )
        summary.setStyleSheet("font-size: 16px; padding: 20px;")
        summary.setWordWrap(True)
        summary.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(summary)

        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(200)
        self.status_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        self.layout.addWidget(self.status_text)

        self.layout.addStretch()
        self.add_navigation_buttons(show_back=True, next_text="Finish")

    def apply_configuration(self) -> bool:
        """Apply configuration and create systemd services.

        Returns:
            True if successful, False otherwise
        """
        self.status_text.clear()
        self.log("Applying configuration...")

        # Update sync script with new Drive path
        drive_config = self.config.get_drive_config()
        self.log(f"Drive: {drive_config['remote']}{drive_config['folder']}")

        # Create systemd services for schedules
        systemd_mgr = SystemdManager(dry_run=True)  # Use dry_run for safety

        schedules = self.config.get_schedules()
        self.log(f"\nCreating {len(schedules)} recording schedule(s)...")

        for schedule in schedules:
            self.log(f"  - {schedule['day_of_week']} {schedule['start_time']} ({schedule['duration_minutes']} min)")
            # In production, remove dry_run
            # systemd_mgr.create_schedule_services(schedule)

        # Mark as initialized
        self.config.set_initialized(True)
        self.log("\n✓ Configuration saved!")
        self.log("\nNote: Systemd services will be created on the Raspberry Pi.")

        return True

    def log(self, message: str):
        """Add message to status log."""
        self.status_text.append(message)

    def validate(self) -> bool:
        """Apply configuration before finishing."""
        return self.apply_configuration()


class SetupWizard(QWidget):
    """Main setup wizard container."""

    setup_complete = Signal()

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)

        self.config = config

        # Create pages
        self.pages = QStackedWidget()

        self.welcome_page = WelcomePage()
        self.device_page = DevicePage(config)
        self.drive_page = DrivePage(config)
        self.schedule_page = SchedulePage(config)
        self.email_alerts_page = EmailAlertsPage(config)
        self.finish_page = FinishPage(config)

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.device_page)
        self.pages.addWidget(self.drive_page)
        self.pages.addWidget(self.schedule_page)
        self.pages.addWidget(self.email_alerts_page)
        self.pages.addWidget(self.finish_page)

        # Connect signals
        self.welcome_page.next_requested.connect(lambda: self.next_page())

        self.device_page.next_requested.connect(lambda: self.next_page())
        self.device_page.back_requested.connect(lambda: self.prev_page())

        self.drive_page.next_requested.connect(lambda: self.next_page())
        self.drive_page.back_requested.connect(lambda: self.prev_page())

        self.schedule_page.next_requested.connect(lambda: self.next_page())
        self.schedule_page.back_requested.connect(lambda: self.prev_page())

        self.email_alerts_page.next_requested.connect(lambda: self.next_page())
        self.email_alerts_page.back_requested.connect(lambda: self.prev_page())

        self.finish_page.next_requested.connect(self.finish)
        self.finish_page.back_requested.connect(lambda: self.prev_page())

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pages)

    def next_page(self):
        """Go to next page."""
        current_widget = self.pages.currentWidget()

        # Validate current page
        if hasattr(current_widget, 'validate') and not current_widget.validate():
            return

        # Move to next page
        current_index = self.pages.currentIndex()
        if current_index < self.pages.count() - 1:
            self.pages.setCurrentIndex(current_index + 1)

    def prev_page(self):
        """Go to previous page."""
        current_index = self.pages.currentIndex()
        if current_index > 0:
            self.pages.setCurrentIndex(current_index - 1)

    def finish(self):
        """Finish wizard."""
        if self.finish_page.validate():
            self.setup_complete.emit()

