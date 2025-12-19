"""
Email notification service.
Sends email alerts using SMTP.
"""
import smtplib
from email.message import EmailMessage
from typing import Dict, Any
from datetime import datetime

from app.config import Config


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.email_from = Config.EMAIL_FROM
        self.email_to = Config.EMAIL_TO
    
    def _create_alert_email(self, repo_name: str, old_version: str,
                           new_version: str, analysis: Dict[str, Any],
                           repo_url: str = "") -> EmailMessage:
        """
        Create email message for version alert.
        
        Args:
            repo_name: Repository name.
            old_version: Previous version.
            new_version: New version.
            analysis: AI analysis results.
            repo_url: Repository URL.
            
        Returns:
            EmailMessage object.
        """
        msg = EmailMessage()
        
        severity = analysis.get("severity", "MEDIUM")
        mandatory = analysis.get("mandatory_upgrade", False)
        
        # Subject line
        subject_prefix = "🚨 CRITICAL" if severity == "CRITICAL" else \
                        "⚠️ HIGH" if severity == "HIGH" else \
                        "ℹ️ MEDIUM" if severity == "MEDIUM" else \
                        "📝 LOW"
        
        mandatory_flag = " [MANDATORY]" if mandatory else ""
        
        msg["Subject"] = f"{subject_prefix}{mandatory_flag} {repo_name} Update: {new_version}"
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        
        # Email body
        body = f"""Blockchain Release Monitor Alert
{'=' * 60}

Repository: {repo_name}
Version Change: {old_version} → {new_version}
Severity: {severity}
Mandatory Upgrade: {'YES' if mandatory else 'NO'}

{'=' * 60}
SUMMARY
{'=' * 60}

{analysis.get('summary', 'No summary available.')}

{'=' * 60}
REASONING
{'=' * 60}

{analysis.get('reasoning', 'No detailed reasoning provided.')}

{'=' * 60}
RECOMMENDATION
{'=' * 60}

"""
        
        if mandatory:
            body += """⚠️  This is a MANDATORY upgrade. Action required:
   - Review the changes immediately
   - Plan upgrade timeline
   - Test in staging environment
   - Deploy to production ASAP
"""
        elif severity == "CRITICAL":
            body += """🚨 CRITICAL update detected:
   - Review security implications
   - Upgrade as soon as possible
   - Monitor for network consensus changes
"""
        elif severity == "HIGH":
            body += """⚠️  HIGH priority update:
   - Review changes at your earliest convenience
   - Plan upgrade within reasonable timeframe
   - Consider impact on your infrastructure
"""
        else:
            body += """ℹ️  Update available:
   - Review when convenient
   - No immediate action required
   - Plan upgrade during regular maintenance
"""
        
        body += f"""

{'=' * 60}
LINKS
{'=' * 60}

Repository: {repo_url or f'https://github.com/{repo_name}'}
New Version: {repo_url}/releases/tag/{new_version}

{'=' * 60}

Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Blockchain Release Monitor
"""
        
        msg.set_content(body)
        
        return msg
    
    def send_alert(self, repo_name: str, old_version: str, new_version: str,
                  analysis: Dict[str, Any], repo_url: str = "") -> bool:
        """
        Send email alert for version update.
        
        Args:
            repo_name: Repository name.
            old_version: Previous version.
            new_version: New version.
            analysis: AI analysis results.
            repo_url: Repository URL.
            
        Returns:
            True if email sent successfully, False otherwise.
        """
        try:
            # Create email message
            msg = self._create_alert_email(
                repo_name, old_version, new_version, analysis, repo_url
            )
            
            # Send email via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"Alert email sent for {repo_name} {new_version}")
            return True
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        Send test email to verify configuration.
        
        Returns:
            True if test email sent successfully.
        """
        try:
            msg = EmailMessage()
            msg["Subject"] = "Blockchain Release Monitor - Test Email"
            msg["From"] = self.email_from
            msg["To"] = self.email_to
            
            body = """This is a test email from Blockchain Release Monitor.

If you received this email, your email configuration is working correctly.

Configuration:
- SMTP Host: {smtp_host}
- SMTP Port: {smtp_port}
- From: {email_from}
- To: {email_to}

Generated at: {timestamp} UTC
""".format(
                smtp_host=self.smtp_host,
                smtp_port=self.smtp_port,
                email_from=self.email_from,
                email_to=self.email_to,
                timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            msg.set_content(body)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print("Test email sent successfully")
            return True
            
        except Exception as e:
            print(f"Failed to send test email: {e}")
            return False
