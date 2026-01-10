"""
Systemd manager for Filmbot appliance.
Generates and manages recording timer services.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List


class SystemdManager:
    """Manages systemd timer services for scheduled recordings."""
    
    SERVICE_TEMPLATE = """[Unit]
Description=Filmbot Recording {schedule_id}
After=network.target

[Service]
Type=oneshot
User=filmbot
ExecStart=/opt/filmbot-appliance/record-atem.sh {duration}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    TIMER_TEMPLATE = """[Unit]
Description=Filmbot Recording Timer {schedule_id}

[Timer]
OnCalendar={on_calendar}
Persistent=true

[Install]
WantedBy=timers.target
"""
    
    SYSTEMD_PATH = Path("/etc/systemd/system")
    
    def __init__(self, dry_run: bool = False):
        """Initialize systemd manager.
        
        Args:
            dry_run: If True, don't actually write files or run systemctl commands
        """
        self.dry_run = dry_run
    
    def _run_command(self, cmd: List[str]) -> bool:
        """Run a shell command.
        
        Args:
            cmd: Command and arguments as list
            
        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            print(f"stderr: {e.stderr}")
            return False
    
    def _write_file(self, path: Path, content: str) -> bool:
        """Write content to file.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"[DRY RUN] Would write to {path}:")
            print(content)
            return True
        
        try:
            with open(path, 'w') as f:
                f.write(content)
            return True
        except IOError as e:
            print(f"Error writing file {path}: {e}")
            return False
    
    def _day_to_calendar(self, day_of_week: str, start_time: str) -> str:
        """Convert day and time to systemd OnCalendar format.
        
        Args:
            day_of_week: Day name (e.g., 'sunday', 'monday')
            start_time: Time in HH:MM format
            
        Returns:
            OnCalendar string (e.g., 'Sun 09:20')
        """
        day_map = {
            'monday': 'Mon',
            'tuesday': 'Tue',
            'wednesday': 'Wed',
            'thursday': 'Thu',
            'friday': 'Fri',
            'saturday': 'Sat',
            'sunday': 'Sun'
        }
        
        day_abbr = day_map.get(day_of_week.lower(), 'Sun')
        return f"{day_abbr} {start_time}"
    
    def create_schedule_services(self, schedule: Dict[str, Any]) -> bool:
        """Create systemd service and timer files for a schedule.
        
        Args:
            schedule: Schedule dictionary with id, day_of_week, start_time, duration_minutes
            
        Returns:
            True if successful, False otherwise
        """
        schedule_id = schedule['id']
        duration_seconds = schedule['duration_minutes'] * 60
        on_calendar = self._day_to_calendar(schedule['day_of_week'], schedule['start_time'])
        
        # Generate service file
        service_content = self.SERVICE_TEMPLATE.format(
            schedule_id=schedule_id,
            duration=duration_seconds
        )
        
        # Generate timer file
        timer_content = self.TIMER_TEMPLATE.format(
            schedule_id=schedule_id,
            on_calendar=on_calendar
        )
        
        # Write files
        service_path = self.SYSTEMD_PATH / f"filmbot-record-{schedule_id}.service"
        timer_path = self.SYSTEMD_PATH / f"filmbot-record-{schedule_id}.timer"
        
        if not self._write_file(service_path, service_content):
            return False
        
        if not self._write_file(timer_path, timer_content):
            return False
        
        # Reload systemd
        if not self._run_command(['sudo', 'systemctl', 'daemon-reload']):
            return False
        
        # Enable and start timer if schedule is enabled
        if schedule.get('enabled', True):
            if not self._run_command(['sudo', 'systemctl', 'enable', f"filmbot-record-{schedule_id}.timer"]):
                return False
            if not self._run_command(['sudo', 'systemctl', 'start', f"filmbot-record-{schedule_id}.timer"]):
                return False
        
        return True
    
    def remove_schedule_services(self, schedule_id: str) -> bool:
        """Remove systemd service and timer files for a schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            True if successful, False otherwise
        """
        # Stop and disable timer
        self._run_command(['sudo', 'systemctl', 'stop', f"filmbot-record-{schedule_id}.timer"])
        self._run_command(['sudo', 'systemctl', 'disable', f"filmbot-record-{schedule_id}.timer"])
        
        # Remove files
        service_path = self.SYSTEMD_PATH / f"filmbot-record-{schedule_id}.service"
        timer_path = self.SYSTEMD_PATH / f"filmbot-record-{schedule_id}.timer"
        
        if service_path.exists():
            service_path.unlink()
        if timer_path.exists():
            timer_path.unlink()
        
        # Reload systemd
        return self._run_command(['sudo', 'systemctl', 'daemon-reload'])

