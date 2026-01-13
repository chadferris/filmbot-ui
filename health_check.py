#!/usr/bin/env python3
"""
Health check monitoring for Filmbot system.
Monitors system health and sends alerts when issues are detected.
"""

import os
import sys
import shutil
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
from config_manager import ConfigManager
from email_notify import EmailNotifier


class HealthChecker:
    """Monitors Filmbot system health."""
    
    # Thresholds
    DISK_WARNING_PERCENT = 20  # Warn if less than 20% free
    DISK_CRITICAL_PERCENT = 10  # Critical if less than 10% free
    CPU_WARNING_PERCENT = 80   # Warn if CPU > 80%
    MEMORY_WARNING_PERCENT = 85  # Warn if memory > 85%
    TEMP_WARNING_C = 70  # Warn if temp > 70°C
    TEMP_CRITICAL_C = 80  # Critical if temp > 80°C
    
    def __init__(self, config_path: Path = None):
        """Initialize health checker.
        
        Args:
            config_path: Optional custom config path
        """
        self.config_manager = ConfigManager(config_path)
        self.notifier = EmailNotifier(config_path)
        self.state_file = Path("/var/tmp/filmbot-health-state.json")
        
    def check_disk_space(self) -> Tuple[str, Dict]:
        """Check disk space on NVMe drive.
        
        Returns:
            Tuple of (status, details)
            status: 'ok', 'warning', or 'critical'
        """
        nvme_path = Path("/mnt/nvme")
        
        if not nvme_path.exists():
            return 'critical', {
                'Issue': 'NVMe drive not mounted',
                'Path': str(nvme_path),
                'Action': 'Check if drive is connected and mounted'
            }
        
        try:
            usage = shutil.disk_usage(nvme_path)
            percent_free = (usage.free / usage.total) * 100
            gb_free = usage.free / (1024**3)
            gb_total = usage.total / (1024**3)
            
            if percent_free < self.DISK_CRITICAL_PERCENT:
                return 'critical', {
                    'Issue': 'Disk space critically low',
                    'Free Space': f'{gb_free:.1f} GB ({percent_free:.1f}%)',
                    'Total Space': f'{gb_total:.1f} GB',
                    'Action': 'Delete old recordings or expand storage'
                }
            elif percent_free < self.DISK_WARNING_PERCENT:
                return 'warning', {
                    'Issue': 'Disk space running low',
                    'Free Space': f'{gb_free:.1f} GB ({percent_free:.1f}%)',
                    'Total Space': f'{gb_total:.1f} GB'
                }
            else:
                return 'ok', {
                    'Disk Space': f'{gb_free:.1f} GB free ({percent_free:.1f}%)'
                }
                
        except Exception as e:
            return 'critical', {
                'Issue': 'Failed to check disk space',
                'Error': str(e)
            }
    
    def check_video_device(self) -> Tuple[str, Dict]:
        """Check if video device is available.
        
        Returns:
            Tuple of (status, details)
        """
        video_device = self.config_manager.get_video_device()
        
        if not Path(video_device).exists():
            return 'critical', {
                'Issue': 'Video device not found',
                'Device': video_device,
                'Action': 'Check USB connections and ATEM power'
            }
        
        return 'ok', {'Video Device': f'{video_device} ✅'}
    
    def check_atem_connection(self) -> Tuple[str, Dict]:
        """Check ATEM connection via ping.
        
        Returns:
            Tuple of (status, details)
        """
        atem_ip = "192.168.100.2"
        
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', atem_ip],
                capture_output=True,
                timeout=3
            )
            
            if result.returncode == 0:
                return 'ok', {'ATEM': 'Connected ✅'}
            else:
                return 'warning', {
                    'Issue': 'ATEM not responding',
                    'IP': atem_ip,
                    'Action': 'Check ATEM power and ethernet connection'
                }
                
        except Exception as e:
            return 'warning', {
                'Issue': 'Failed to check ATEM',
                'Error': str(e)
            }
    
    def check_network(self) -> Tuple[str, Dict]:
        """Check network connectivity.
        
        Returns:
            Tuple of (status, details)
        """
        try:
            # Check internet connectivity
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                capture_output=True,
                timeout=3
            )
            
            if result.returncode == 0:
                return 'ok', {'Network': 'Online ✅'}
            else:
                return 'warning', {
                    'Issue': 'No internet connectivity',
                    'Action': 'Check WiFi connection'
                }
                
        except Exception as e:
            return 'warning', {
                'Issue': 'Failed to check network',
                'Error': str(e)
            }
    
    def check_system_resources(self) -> Tuple[str, Dict]:
        """Check CPU, memory, and temperature.
        
        Returns:
            Tuple of (status, details)
        """
        details = {}
        status = 'ok'
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.CPU_WARNING_PERCENT:
            status = 'warning'
            details['CPU Usage'] = f'{cpu_percent:.1f}% (HIGH)'
        else:
            details['CPU Usage'] = f'{cpu_percent:.1f}%'
        
        # Memory usage
        memory = psutil.virtual_memory()
        if memory.percent > self.MEMORY_WARNING_PERCENT:
            status = 'warning'
            details['Memory Usage'] = f'{memory.percent:.1f}% (HIGH)'
        else:
            details['Memory Usage'] = f'{memory.percent:.1f}%'
        
        # Temperature (Raspberry Pi specific)
        try:
            temp_file = Path('/sys/class/thermal/thermal_zone0/temp')
            if temp_file.exists():
                temp_c = int(temp_file.read_text().strip()) / 1000
                if temp_c > self.TEMP_CRITICAL_C:
                    status = 'critical'
                    details['Temperature'] = f'{temp_c:.1f}°C (CRITICAL)'
                elif temp_c > self.TEMP_WARNING_C:
                    status = 'warning'
                    details['Temperature'] = f'{temp_c:.1f}°C (HIGH)'
                else:
                    details['Temperature'] = f'{temp_c:.1f}°C'
        except:
            pass
        
        return status, details

    def check_uptime(self) -> Dict:
        """Get system uptime.

        Returns:
            Dictionary with uptime info
        """
        try:
            uptime_seconds = int(Path('/proc/uptime').read_text().split()[0].split('.')[0])
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600

            if days > 0:
                uptime_str = f"{days} days, {hours} hours"
            else:
                uptime_str = f"{hours} hours"

            return {'Uptime': uptime_str}
        except:
            return {'Uptime': 'Unknown'}

    def run_health_check(self) -> Dict:
        """Run complete health check.

        Returns:
            Dictionary with all health check results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'device_name': self.config_manager.get_device_name(),
            'checks': {},
            'overall_status': 'ok'
        }

        # Run all checks
        checks = [
            ('disk_space', self.check_disk_space),
            ('video_device', self.check_video_device),
            ('atem', self.check_atem_connection),
            ('network', self.check_network),
            ('system_resources', self.check_system_resources),
        ]

        for check_name, check_func in checks:
            status, details = check_func()
            results['checks'][check_name] = {
                'status': status,
                'details': details
            }

            # Update overall status (critical > warning > ok)
            if status == 'critical':
                results['overall_status'] = 'critical'
            elif status == 'warning' and results['overall_status'] != 'critical':
                results['overall_status'] = 'warning'

        # Add uptime
        results['checks']['uptime'] = {
            'status': 'ok',
            'details': self.check_uptime()
        }

        return results

    def send_alerts(self, results: Dict):
        """Send alerts based on health check results.

        Args:
            results: Health check results dictionary
        """
        if not self.notifier.is_enabled():
            return

        # Send critical alerts immediately
        for check_name, check_data in results['checks'].items():
            if check_data['status'] == 'critical':
                title = check_data['details'].get('Issue', f'{check_name} check failed')
                self.notifier.send_critical_alert(title, check_data['details'])

        # Send warning alerts (batched)
        warnings = []
        for check_name, check_data in results['checks'].items():
            if check_data['status'] == 'warning':
                warnings.append((check_name, check_data['details']))

        if warnings:
            warning_details = {}
            for check_name, details in warnings:
                for key, value in details.items():
                    warning_details[f"{check_name} - {key}"] = value

            self.notifier.send_warning_alert("System Warnings", warning_details)

    def send_daily_report(self):
        """Send daily health report."""
        if not self.notifier.is_enabled():
            return

        results = self.run_health_check()

        # Build report data
        report_data = {
            'status': 'Healthy' if results['overall_status'] == 'ok' else 'Issues Detected'
        }

        # Add all check details
        for check_name, check_data in results['checks'].items():
            for key, value in check_data['details'].items():
                report_data[key] = value

        self.notifier.send_daily_report(report_data)


def main():
    """Main entry point for health check script."""
    import argparse

    parser = argparse.ArgumentParser(description='Filmbot Health Check')
    parser.add_argument('--daily-report', action='store_true',
                       help='Send daily health report')
    parser.add_argument('--test', action='store_true',
                       help='Run health check and print results (no alerts)')
    args = parser.parse_args()

    checker = HealthChecker()

    if args.test:
        # Test mode - just print results
        results = checker.run_health_check()
        print(f"\n{'='*60}")
        print(f"FILMBOT HEALTH CHECK - {results['device_name']}")
        print(f"Time: {results['timestamp']}")
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"{'='*60}\n")

        for check_name, check_data in results['checks'].items():
            status_emoji = {'ok': '✅', 'warning': '🟡', 'critical': '🔴'}.get(check_data['status'], '❓')
            print(f"{status_emoji} {check_name.upper()}: {check_data['status']}")
            for key, value in check_data['details'].items():
                print(f"   {key}: {value}")
            print()

    elif args.daily_report:
        # Send daily report
        checker.send_daily_report()
        print("Daily report sent")

    else:
        # Normal health check with alerts
        results = checker.run_health_check()
        checker.send_alerts(results)

        # Print summary
        if results['overall_status'] != 'ok':
            print(f"Health check completed: {results['overall_status'].upper()}")
        else:
            print("Health check completed: All systems OK")


if __name__ == '__main__':
    main()

