#!/usr/bin/env python3
"""
Test script for Filmbot UI
Run this on a development machine to test the UI without Raspberry Pi hardware.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from config_manager import ConfigManager
from wizard import SetupWizard
from live_view import LiveView
from settings import SettingsScreen


def test_config_manager():
    """Test configuration manager."""
    print("Testing ConfigManager...")
    
    # Use temporary config
    test_config_path = Path.home() / ".filmbot-test" / "config.json"
    test_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove old test config
    if test_config_path.exists():
        test_config_path.unlink()
    
    config = ConfigManager(test_config_path)
    
    # Test initial state
    assert not config.is_initialized(), "Should not be initialized"
    
    # Test drive config
    config.set_drive_config("test-remote:", "test-folder")
    drive_config = config.get_drive_config()
    assert drive_config['remote'] == "test-remote:"
    assert drive_config['folder'] == "test-folder"
    
    # Test schedules
    schedule_id = config.add_schedule("sunday", "09:20", 60)
    schedules = config.get_schedules()
    assert len(schedules) == 1
    assert schedules[0]['day_of_week'] == "sunday"
    
    # Test device name
    config.set_device_name("TestDevice")
    assert config.get_device_name() == "TestDevice"
    
    # Test initialization
    config.set_initialized(True)
    assert config.is_initialized()
    
    print("✓ ConfigManager tests passed")
    return config


def test_wizard(app):
    """Test setup wizard."""
    print("Testing SetupWizard...")
    
    # Create test config
    test_config_path = Path.home() / ".filmbot-test" / "wizard-config.json"
    test_config_path.parent.mkdir(parents=True, exist_ok=True)
    if test_config_path.exists():
        test_config_path.unlink()
    
    config = ConfigManager(test_config_path)
    wizard = SetupWizard(config)
    
    # Show wizard
    wizard.show()
    wizard.resize(800, 480)
    
    print("✓ SetupWizard created successfully")
    print("  Close the wizard window to continue tests...")
    
    wizard.exec()


def test_live_view(app):
    """Test live view."""
    print("Testing LiveView...")
    
    # Create test config with data
    test_config_path = Path.home() / ".filmbot-test" / "live-config.json"
    test_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = ConfigManager(test_config_path)
    config.set_initialized(True)
    config.set_drive_config("filmbot-drive:", "TestOrg/Box1")
    config.add_schedule("sunday", "09:20", 60)
    config.add_schedule("sunday", "10:55", 60)
    
    live_view = LiveView(config)
    live_view.show()
    live_view.resize(800, 480)
    
    print("✓ LiveView created successfully")
    print("  Note: Video preview will show error (no /dev/video5)")
    print("  Close the window to continue tests...")
    
    live_view.exec()


def test_settings(app):
    """Test settings screen."""
    print("Testing SettingsScreen...")
    
    # Create test config with data
    test_config_path = Path.home() / ".filmbot-test" / "settings-config.json"
    test_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = ConfigManager(test_config_path)
    config.set_initialized(True)
    config.set_drive_config("filmbot-drive:", "TestOrg/Box1")
    config.add_schedule("sunday", "09:20", 60)
    config.set_device_name("TestDevice")
    
    settings = SettingsScreen(config)
    settings.show()
    settings.resize(800, 480)
    
    print("✓ SettingsScreen created successfully")
    print("  Close the window to continue...")
    
    settings.exec()


def main():
    """Run all tests."""
    print("=== Filmbot UI Test Suite ===\n")
    
    # Test config manager (no GUI)
    test_config_manager()
    print()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Test wizard
    reply = QMessageBox.question(
        None,
        "Test Wizard",
        "Test the Setup Wizard?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        test_wizard(app)
    
    # Test live view
    reply = QMessageBox.question(
        None,
        "Test Live View",
        "Test the Live View screen?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        test_live_view(app)
    
    # Test settings
    reply = QMessageBox.question(
        None,
        "Test Settings",
        "Test the Settings screen?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        test_settings(app)
    
    print("\n=== All Tests Complete ===")
    print("Test configurations saved to ~/.filmbot-test/")


if __name__ == "__main__":
    main()

