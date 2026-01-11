#!/usr/bin/env python3
"""
Filmbot Recording Appliance - Main Application
Touchscreen UI for Raspberry Pi 5 with 4.3" display.
"""

import sys
from PySide6.QtWidgets import QApplication, QStackedWidget, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen

from config_manager import ConfigManager
from wizard import SetupWizard
from live_view import LiveView
from settings import SettingsScreen


class FilmbotApp(QMainWindow):
    """Main Filmbot application window."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        self.config = ConfigManager()
        
        # Setup window
        self.setWindowTitle("Filmbot Recording Appliance")

        # Apply kiosk mode if enabled
        if self.config.get_hide_taskbar():
            # Frameless window to remove decorations
            self.setWindowFlags(Qt.FramelessWindowHint)

        # Set window size for 800x480 touchscreen
        self.resize(800, 480)
        self.setMinimumSize(800, 480)
        self.setMaximumSize(800, 480)
        
        # Create stacked widget for different screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Create screens
        self.wizard = SetupWizard(self.config)
        self.live_view = LiveView(self.config)
        self.settings = SettingsScreen(self.config)
        
        # Add to stack
        self.stack.addWidget(self.wizard)
        self.stack.addWidget(self.live_view)
        self.stack.addWidget(self.settings)
        
        # Connect signals
        self.wizard.setup_complete.connect(self.show_live_view)
        self.live_view.settings_requested.connect(self.show_settings)
        self.settings.back_requested.connect(self.show_live_view)
        
        # Show appropriate screen
        if self.config.is_initialized():
            self.show_live_view()
        else:
            self.show_wizard()
    
    def show_wizard(self):
        """Show the setup wizard."""
        self.stack.setCurrentWidget(self.wizard)
    
    def show_live_view(self):
        """Show the live monitoring view."""
        self.stack.setCurrentWidget(self.live_view)
    
    def show_settings(self):
        """Show the settings screen."""
        # Reload settings when showing
        self.settings.load_settings()
        self.stack.setCurrentWidget(self.settings)


def main():
    """Main entry point."""
    # Create application
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # For touchscreen, enable touch events
    # app.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, True)

    # Create and show main window
    window = FilmbotApp()

    # If kiosk mode is enabled, position at top-left
    if window.config.get_hide_taskbar():
        window.setGeometry(0, 0, 800, 480)
        window.showNormal()
    else:
        window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

