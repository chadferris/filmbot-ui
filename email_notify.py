#!/usr/bin/env python3
"""
Email notification system for Filmbot alerts.
Sends alerts via Gmail SMTP using app password.
"""

import smtplib
import socket
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from config_manager import ConfigManager


class EmailNotifier:
    """Handles email notifications for Filmbot alerts."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize email notifier.
        
        Args:
            config_path: Optional custom config path
        """
        self.config_manager = ConfigManager(config_path)
        self.alerts_config = self.config_manager.get_alerts_config()
        
    def is_enabled(self) -> bool:
        """Check if email alerts are enabled."""
        return self.alerts_config.get("enabled", False)
    
    def send_email(self, subject: str, body: str, priority: str = "normal") -> bool:
        """Send an email alert.
        
        Args:
            subject: Email subject
            body: Email body (plain text)
            priority: Alert priority ('critical', 'warning', 'info')
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_enabled():
            print("Email alerts are disabled")
            return False
        
        email_from = self.alerts_config.get("email_from", "")
        email_to = self.alerts_config.get("email_to", [])
        smtp_password = self.alerts_config.get("smtp_password", "")
        
        if not email_from or not email_to or not smtp_password:
            print("Email configuration incomplete")
            return False
        
        # Add emoji prefix based on priority
        emoji_map = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🟢"
        }
        emoji = emoji_map.get(priority, "📧")
        subject = f"{emoji} {subject}"
        
        # Create email message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = email_from
        msg['To'] = ', '.join(email_to) if isinstance(email_to, list) else email_to
        msg.set_content(body)
        
        try:
            # Connect to Gmail SMTP
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(email_from, smtp_password)
                smtp.send_message(msg)
            
            print(f"Email sent successfully: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("SMTP authentication failed. Check email and app password.")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP error: {e}")
            return False
        except socket.timeout:
            print("SMTP connection timed out")
            return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_critical_alert(self, title: str, details: dict) -> bool:
        """Send a critical alert email.
        
        Args:
            title: Alert title (e.g., "Recording Failed")
            details: Dictionary of alert details
            
        Returns:
            True if sent successfully
        """
        device_name = self.config_manager.get_device_name()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = f"CRITICAL: {title} - {device_name}"
        
        body = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILMBOT CRITICAL ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Device: {device_name}
Time: {timestamp}
Issue: {title}

DETAILS:
"""
        for key, value in details.items():
            body += f"• {key}: {value}\n"
        
        body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION REQUIRED: Please check the device.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return self.send_email(subject, body, priority="critical")
    
    def send_warning_alert(self, title: str, details: dict) -> bool:
        """Send a warning alert email.
        
        Args:
            title: Alert title
            details: Dictionary of alert details
            
        Returns:
            True if sent successfully
        """
        device_name = self.config_manager.get_device_name()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = f"WARNING: {title} - {device_name}"
        
        body = f"""Device: {device_name}
Time: {timestamp}
Warning: {title}

Details:
"""
        for key, value in details.items():
            body += f"• {key}: {value}\n"
        
        return self.send_email(subject, body, priority="warning")
    
    def send_daily_report(self, report_data: dict) -> bool:
        """Send daily health report.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            True if sent successfully
        """
        device_name = self.config_manager.get_device_name()
        date = datetime.now().strftime("%Y-%m-%d")
        
        subject = f"Daily Report - {device_name}"
        
        # Determine overall status
        status = report_data.get("status", "Unknown")
        status_emoji = "✅" if status == "Healthy" else "⚠️"
        
        body = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILMBOT DAILY HEALTH REPORT
Date: {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEVICE: {device_name}
Status: {status_emoji} {status}

"""
        
        for key, value in report_data.items():
            if key != "status":
                body += f"{key}: {value}\n"
        
        body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return self.send_email(subject, body, priority="info")

