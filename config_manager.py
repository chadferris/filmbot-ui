"""
Configuration manager for Filmbot appliance.
Handles reading/writing config.json with validation.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

CONFIG_PATH = Path("/opt/filmbot-appliance/config.json")
# For development/testing, fall back to local path
if not CONFIG_PATH.parent.exists():
    CONFIG_PATH = Path.home() / ".filmbot" / "config.json"
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Manages Filmbot configuration file."""
    
    DEFAULT_CONFIG = {
        "initialized": False,
        "google_drive": {
            "remote": "filmbot-drive:",
            "folder": ""
        },
        "devices": {
            "video_device": "/dev/video5",
            "audio_device": "hw:2,0"
        },
        "schedules": [],
        "device_name": "Filmbot",
        "ui": {
            "hide_taskbar": False
        },
        "alerts": {
            "enabled": False,
            "email_from": "",
            "email_to": [],
            "smtp_password": "",
            "daily_report_time": "08:00",
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00"
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_path: Optional custom config path (for testing)
        """
        self.config_path = config_path or CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._config = self.load()

    def _deep_merge_defaults(self, config: dict, defaults: dict):
        """Deep merge defaults into config, preserving existing values.

        Args:
            config: Existing configuration dictionary (modified in place)
            defaults: Default configuration dictionary
        """
        for key, default_value in defaults.items():
            if key not in config:
                # Key doesn't exist, add the default
                config[key] = default_value
            elif isinstance(default_value, dict) and isinstance(config[key], dict):
                # Both are dicts, recurse
                self._deep_merge_defaults(config[key], default_value)
            # else: key exists and is not a dict, keep existing value

    def load(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config
        
        try:
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
            # Ensure all required keys exist with deep merge
            self._deep_merge_defaults(self._config, self.DEFAULT_CONFIG)
            return self._config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config
    
    def save(self) -> bool:
        """Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if appliance has been initialized."""
        return self._config.get("initialized", False)
    
    def set_initialized(self, value: bool = True):
        """Set initialization status."""
        self._config["initialized"] = value
        self.save()
    
    def get_drive_config(self) -> Dict[str, str]:
        """Get Google Drive configuration."""
        return self._config.get("google_drive", self.DEFAULT_CONFIG["google_drive"])
    
    def set_drive_config(self, remote: str, folder: str):
        """Set Google Drive configuration."""
        self._config["google_drive"] = {
            "remote": remote,
            "folder": folder
        }
        self.save()
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get recording schedules."""
        return self._config.get("schedules", [])
    
    def add_schedule(self, day_of_week: str, start_time: str, duration_minutes: int) -> str:
        """Add a new recording schedule.
        
        Args:
            day_of_week: Day name (e.g., 'sunday', 'monday')
            start_time: Start time in HH:MM format
            duration_minutes: Duration in minutes
            
        Returns:
            Schedule ID
        """
        schedules = self.get_schedules()
        # Generate unique ID
        schedule_id = f"service-{len(schedules) + 1}"
        
        schedule = {
            "id": schedule_id,
            "day_of_week": day_of_week.lower(),
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "enabled": True
        }
        
        schedules.append(schedule)
        self._config["schedules"] = schedules
        self.save()
        return schedule_id
    
    def update_schedule(self, schedule_id: str, **kwargs):
        """Update an existing schedule."""
        schedules = self.get_schedules()
        for schedule in schedules:
            if schedule["id"] == schedule_id:
                schedule.update(kwargs)
                break
        self._config["schedules"] = schedules
        self.save()
    
    def remove_schedule(self, schedule_id: str):
        """Remove a schedule by ID."""
        schedules = self.get_schedules()
        self._config["schedules"] = [s for s in schedules if s["id"] != schedule_id]
        self.save()
    
    def get_device_name(self) -> str:
        """Get device name."""
        return self._config.get("device_name", "Filmbot")
    
    def set_device_name(self, name: str):
        """Set device name."""
        self._config["device_name"] = name
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return self._config.copy()

    def get_devices(self) -> Dict[str, str]:
        """Get device configuration."""
        return self._config.get("devices", self.DEFAULT_CONFIG["devices"])

    def set_devices(self, video_device: str, audio_device: str):
        """Set device configuration."""
        self._config["devices"] = {
            "video_device": video_device,
            "audio_device": audio_device
        }
        self.save()

    def get_video_device(self) -> str:
        """Get video device path."""
        devices = self.get_devices()
        return devices.get("video_device", "/dev/video5")

    def get_audio_device(self) -> str:
        """Get audio device identifier."""
        devices = self.get_devices()
        return devices.get("audio_device", "hw:2,0")

    def get_hide_taskbar(self) -> bool:
        """Get hide taskbar setting."""
        ui_config = self._config.get("ui", {})
        return ui_config.get("hide_taskbar", False)

    def get_alerts_config(self) -> Dict[str, any]:
        """Get alerts configuration."""
        return self._config.get("alerts", self.DEFAULT_CONFIG["alerts"])

    def set_alerts_config(self, enabled: bool, email_from: str, email_to: list,
                         smtp_password: str, daily_report_time: str = "08:00",
                         quiet_hours_start: str = "22:00", quiet_hours_end: str = "07:00"):
        """Set alerts configuration.

        Args:
            enabled: Whether alerts are enabled
            email_from: Gmail address to send from (e.g., filmbot@gmail.com)
            email_to: List of email addresses to send alerts to
            smtp_password: Gmail app password (16 characters)
            daily_report_time: Time for daily report (HH:MM format)
            quiet_hours_start: Start of quiet hours (HH:MM format)
            quiet_hours_end: End of quiet hours (HH:MM format)
        """
        self._config["alerts"] = {
            "enabled": enabled,
            "email_from": email_from,
            "email_to": email_to if isinstance(email_to, list) else [email_to],
            "smtp_password": smtp_password,
            "daily_report_time": daily_report_time,
            "quiet_hours_start": quiet_hours_start,
            "quiet_hours_end": quiet_hours_end
        }
        self.save()

    def is_alerts_enabled(self) -> bool:
        """Check if alerts are enabled."""
        alerts = self.get_alerts_config()
        return alerts.get("enabled", False)

    def set_hide_taskbar(self, hide: bool):
        """Set hide taskbar setting."""
        if "ui" not in self._config:
            self._config["ui"] = {}
        self._config["ui"]["hide_taskbar"] = hide
        self.save()

