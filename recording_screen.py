"""
Recording in progress screen for Filmbot appliance.
Displays animated recording indicator when recording is active.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont


class RecordingScreen(QWidget):
    """Screen shown during active recording."""
    
    def __init__(self, parent=None):
        """Initialize recording screen."""
        super().__init__(parent)
        
        self.blink_state = False
        self.setup_ui()
        
        # Blink timer for recording indicator
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(500)  # Blink every 500ms
    
    def setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Set black background
        self.setStyleSheet("background-color: black;")
        
        # Recording indicator
        self.rec_label = QLabel("🔴 REC")
        self.rec_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(72)
        font.setBold(True)
        self.rec_label.setFont(font)
        self.rec_label.setStyleSheet("color: #ff0000;")
        layout.addWidget(self.rec_label)
        
        # Status text
        self.status_label = QLabel("Recording in Progress")
        self.status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(32)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: white; margin-top: 20px;")
        layout.addWidget(self.status_label)
        
        # Info text
        self.info_label = QLabel("Do not power off the device")
        self.info_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        self.info_label.setFont(font)
        self.info_label.setStyleSheet("color: #999; margin-top: 40px;")
        layout.addWidget(self.info_label)
    
    def toggle_blink(self):
        """Toggle the blinking recording indicator."""
        self.blink_state = not self.blink_state
        if self.blink_state:
            self.rec_label.setStyleSheet("color: #ff0000;")
        else:
            self.rec_label.setStyleSheet("color: #660000;")
    
    def set_filename(self, filename: str):
        """Update the recording filename display.
        
        Args:
            filename: Name of the file being recorded
        """
        self.info_label.setText(f"Recording: {filename}\nDo not power off the device")
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.blink_timer.stop()
        super().closeEvent(event)

