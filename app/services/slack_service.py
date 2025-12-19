"""
Slack notification service.
Sends alerts to Slack channels using webhooks.
"""
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import Config


class SlackService:
    """Service for sending Slack notifications."""
    
    def __init__(self):
        """Initialize Slack service with webhook URL."""
        self.webhook_url = Config.SLACK_WEBHOOK_URL
        self.enabled = bool(self.webhook_url)
    
    def _create_alert_blocks(self, repo_name: str, old_version: str,
                            new_version: str, analysis: Dict[str, Any],
                            repo_url: str = "") -> list:
        """
        Create Slack blocks for version alert.
        
        Args:
            repo_name: Repository name.
            old_version: Previous version.
            new_version: New version.
            analysis: AI analysis results.
            repo_url: Repository URL.
            
        Returns:
            List of Slack block elements.
        """
        severity = analysis.get("severity", "MEDIUM")
        mandatory = analysis.get("mandatory_upgrade", False)
        
        # Emoji and color based on severity
        emoji_map = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "ℹ️",
            "LOW": "📝"
        }
        
        color_map = {
            "CRITICAL": "#d93f0b",  # Red
            "HIGH": "#f2c744",      # Orange/Yellow
            "MEDIUM": "#2eb886",    # Green
            "LOW": "#6b7280"        # Gray
        }
        
        emoji = emoji_map.get(severity, "📢")
        color = color_map.get(severity, "#2eb886")
        
        # Build header
        mandatory_text = " *[MANDATORY]*" if mandatory else ""
        header = f"{emoji} *{severity}*{mandatory_text} Update: {repo_name}"
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {repo_name} Update Available",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{repo_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Version Change:*\n`{old_version}` → `{new_version}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{emoji} {severity}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Mandatory:*\n{'✅ YES' if mandatory else '❌ NO'}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary*\n{analysis.get('summary', 'No summary available.')}"
                }
            }
        ]
        
        # Add reasoning section
        reasoning = analysis.get('reasoning', '')
        if reasoning:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reasoning*\n{reasoning}"
                }
            })
        
        # Add recommendation based on severity/mandatory
        blocks.append({"type": "divider"})
        
        if mandatory:
            recommendation = "⚠️ *MANDATORY UPGRADE REQUIRED*\n• Review changes immediately\n• Plan upgrade timeline\n• Test in staging environment\n• Deploy to production ASAP"
        elif severity == "CRITICAL":
            recommendation = "🚨 *CRITICAL UPDATE*\n• Review security implications\n• Upgrade as soon as possible\n• Monitor for network consensus changes"
        elif severity == "HIGH":
            recommendation = "⚠️ *HIGH PRIORITY*\n• Review changes at earliest convenience\n• Plan upgrade within next maintenance window"
        else:
            recommendation = "ℹ️ *INFORMATIONAL*\n• Review changes when convenient\n• No urgent action required"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": recommendation
            }
        })
        
        # Add action buttons
        if repo_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View on GitHub",
                            "emoji": True
                        },
                        "url": repo_url,
                        "style": "primary"
                    }
                ]
            })
        
        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Blockchain Release Monitor | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })
        
        return blocks
    
    def send_alert(self, repo_name: str, old_version: str,
                  new_version: str, analysis: Dict[str, Any],
                  repo_url: str = "") -> bool:
        """
        Send Slack alert for version update.
        
        Args:
            repo_name: Repository name.
            old_version: Previous version.
            new_version: New version.
            analysis: AI analysis results.
            repo_url: Repository URL.
            
        Returns:
            True if message sent successfully, False otherwise.
        """
        if not self.enabled:
            print("  Slack notifications disabled (no webhook URL)")
            return False
        
        try:
            blocks = self._create_alert_blocks(
                repo_name, old_version, new_version, analysis, repo_url
            )
            
            # Prepare message
            severity = analysis.get("severity", "MEDIUM")
            mandatory = analysis.get("mandatory_upgrade", False)
            mandatory_text = " [MANDATORY]" if mandatory else ""
            
            payload = {
                "blocks": blocks,
                "text": f"{severity}{mandatory_text} Update: {repo_name} {old_version} → {new_version}"  # Fallback text
            }
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✓ Slack alert sent successfully")
                return True
            else:
                print(f"  ✗ Failed to send Slack alert: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error sending Slack alert: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify Slack configuration.
        
        Returns:
            True if test message sent successfully, False otherwise.
        """
        if not self.enabled:
            print("Slack notifications disabled (no webhook URL configured)")
            return False
        
        try:
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🧪 Test Message",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Blockchain Release Monitor* is configured correctly!\n\nYou will receive alerts here for blockchain repository updates."
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Test sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                            }
                        ]
                    }
                ],
                "text": "Test message from Blockchain Release Monitor"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✓ Slack test message sent successfully")
                return True
            else:
                print(f"✗ Failed to send Slack test message: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error sending Slack test message: {e}")
            return False
