#!/usr/bin/env python3
"""
Test Slack and email alert configuration.
"""
from app.config import Config
from app.services.email_service import EmailService
from app.services.slack_service import SlackService


def main():
    """Test notification services."""
    print("=" * 60)
    print("Notification Services Test")
    print("=" * 60)
    print()
    
    # Check configuration
    print("Configuration Status:")
    print(f"  Email Alerts Enabled: {Config.EMAIL_ALERTS_ENABLED}")
    print(f"  Slack Alerts Enabled: {Config.SLACK_ALERTS_ENABLED}")
    print(f"  Slack Webhook Configured: {bool(Config.SLACK_WEBHOOK_URL)}")
    print()
    
    # Test Email
    if Config.EMAIL_ALERTS_ENABLED:
        print("-" * 60)
        print("Testing Email Service...")
        print("-" * 60)
        
        email_service = EmailService()
        try:
            success = email_service.send_test_email()
            if success:
                print("✓ Email test passed!")
            else:
                print("✗ Email test failed!")
        except Exception as e:
            print(f"✗ Email test error: {e}")
        print()
    else:
        print("Email alerts disabled - skipping email test")
        print()
    
    # Test Slack
    if Config.SLACK_ALERTS_ENABLED:
        print("-" * 60)
        print("Testing Slack Service...")
        print("-" * 60)
        
        slack_service = SlackService()
        
        if slack_service.enabled:
            try:
                success = slack_service.send_test_message()
                if success:
                    print("✓ Slack test passed!")
                else:
                    print("✗ Slack test failed!")
            except Exception as e:
                print(f"✗ Slack test error: {e}")
        else:
            print("⚠ Slack webhook URL not configured")
            print("  Add SLACK_WEBHOOK_URL to .env to enable Slack notifications")
        print()
    else:
        print("Slack alerts disabled - skipping Slack test")
        print()
    
    print("=" * 60)
    print("Configuration Summary:")
    print("=" * 60)
    
    email_configured = Config.EMAIL_ALERTS_ENABLED and Config.SMTP_USERNAME
    slack_configured = Config.SLACK_ALERTS_ENABLED and Config.SLACK_WEBHOOK_URL
    
    if email_configured and slack_configured:
        print("✓ Both email and Slack alerts configured")
    elif email_configured:
        print("✓ Email alerts configured")
        print("ℹ Slack alerts not configured (optional)")
    elif slack_configured:
        print("✓ Slack alerts configured")
        print("ℹ Email alerts not configured (optional)")
    else:
        print("⚠ No notification methods configured!")
        print("  Configure at least one: Email or Slack")
    
    print()
    print("To enable/disable alerts, set in .env:")
    print("  EMAIL_ALERTS_ENABLED=true/false")
    print("  SLACK_ALERTS_ENABLED=true/false")
    print()


if __name__ == "__main__":
    main()
