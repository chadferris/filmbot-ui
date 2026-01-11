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

        # Set window size for 800x480 touchscreen
        self.resize(800, 480)
        
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
    app.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, True)

    # Create and show main window
    window = FilmbotApp()

    # Always use Screen 0 (DSI-2 - the physical touchscreen)
    # This ensures the app appears on the actual display, not Pi Connect virtual display
    screens = app.screens()
    if screens:
        # Use the first screen (DSI-2 800x480 touchscreen)
        primary_screen = screens[0]
        print(f"Filmbot: Using screen: {primary_screen.name()} ({primary_screen.geometry().width()}x{primary_screen.geometry().height()})")

        # Set the window to use this screen explicitly
        window.setScreen(primary_screen)

    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

