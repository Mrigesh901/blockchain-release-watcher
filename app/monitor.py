"""
Monitoring logic for checking repository updates.
"""
from typing import Dict, Any

from app.db.database import Database
from app.services.repository_service import RepositoryService
from app.services.gemini_service import GeminiService
from app.services.email_service import EmailService
from app.services.slack_service import SlackService
from app.config import Config


def check_repository_updates(repo_name: str, db: Database, 
                            repo_service: RepositoryService,
                            gemini_service: GeminiService,
                            email_service: EmailService,
                            slack_service: SlackService) -> Dict[str, Any]:
    """
    Check for updates in a single repository.
    
    Args:
        repo_name: Repository name (owner/repo).
        db: Database instance.
        github_service: Repository service instance.
        gemini_service: Gemini service instance.
        email_service: Email service instance.
        
    Returns:
        Result dictionary with update information.
    """
    print(f"\nChecking {repo_name}...")
    
    try:
        # Get repository from database
        repo = db.get_repository(repo_name)
        last_version = repo.last_version_or_tag if repo else None
        
        # Get repo URL
        repo_url = repo_service.get_repo_url(repo_name)
        
        # Check for updates
        update_info = repo_service.check_for_updates(repo_name, last_version)
        
        if "error" in update_info:
            print(f"  Error: {update_info['error']}")
            return {
                "repo_name": repo_name,
                "status": "error",
                "message": update_info["error"]
            }
        
        if not update_info.get("has_update"):
            print(f"  No updates. Current version: {update_info.get('current_version')}")
            
            # Update last checked time
            db.upsert_repository(repo_name, repo_url)
            
            return {
                "repo_name": repo_name,
                "status": "no_update",
                "current_version": update_info.get("current_version")
            }
        
        # New version detected
        new_version = update_info["new_version"]
        old_version = update_info["old_version"] or "N/A"
        is_first_check = update_info.get("is_first_check", False)
        
        print(f"  New version detected: {old_version} → {new_version}")
        
        # Update database with new version
        db.upsert_repository(
            repo_name, 
            repo_url, 
            last_version_or_tag=new_version
        )
        
        # Skip AI analysis and alerts for first check
        if is_first_check:
            print(f"  First check - no alert sent")
            return {
                "repo_name": repo_name,
                "status": "first_check",
                "new_version": new_version,
                "message": "Repository initialized. Will alert on next update."
            }
        
        # Perform AI analysis
        print(f"  Analyzing changes with AI...")
        
        analysis = gemini_service.analyze_version_change(
            repo_name=repo_name,
            old_version=old_version,
            new_version=new_version,
            release_notes=update_info.get("release_notes", ""),
            commit_messages=update_info.get("commit_messages", [])
        )
        
        severity = analysis.get("severity", "MEDIUM")
        mandatory = analysis.get("mandatory_upgrade", False)
        
        print(f"  Severity: {severity}, Mandatory: {mandatory}")
        print(f"  Summary: {analysis.get('summary', '')[:100]}...")
        
        # Update database with analysis
        db.upsert_repository(
            repo_name,
            repo_url,
            severity=severity,
            mandatory_upgrade=mandatory
        )
        
        # Decide if alert should be sent
        should_alert = gemini_service.should_send_alert(analysis)
        
        if should_alert:
            print(f"  Sending alerts...")
            
            alerts_sent = {"email": False, "slack": False}
            
            # Send email alert if enabled
            if Config.EMAIL_ALERTS_ENABLED:
                print(f"    Sending email alert...")
                email_sent = email_service.send_alert(
                    repo_name=repo_name,
                    old_version=old_version,
                    new_version=new_version,
                    analysis=analysis,
                    repo_url=repo_url
                )
                alerts_sent["email"] = email_sent
            else:
                print(f"    Email alerts disabled")
            
            # Send Slack alert if enabled
            if Config.SLACK_ALERTS_ENABLED and slack_service.enabled:
                print(f"    Sending Slack alert...")
                slack_sent = slack_service.send_alert(
                    repo_name=repo_name,
                    old_version=old_version,
                    new_version=new_version,
                    analysis=analysis,
                    repo_url=repo_url
                )
                alerts_sent["slack"] = slack_sent
            elif not Config.SLACK_ALERTS_ENABLED:
                print(f"    Slack alerts disabled")
            
            # Update last alerted version if at least one alert was sent
            if alerts_sent["email"] or alerts_sent["slack"]:
                db.upsert_repository(
                    repo_name,
                    repo_url,
                    last_alerted_version=new_version
                )
                
                # Add to alert history
                db.add_alert_history(
                    repo_name=repo_name,
                    version=new_version,
                    severity=severity,
                    mandatory_upgrade=mandatory,
                    summary=analysis.get("summary", "")
                )
                
                print(f"  ✓ Alert sent successfully")
                
                return {
                    "repo_name": repo_name,
                    "status": "alert_sent",
                    "old_version": old_version,
                    "new_version": new_version,
                    "severity": severity,
                    "mandatory_upgrade": mandatory,
                    "email_sent": alerts_sent["email"],
                    "slack_sent": alerts_sent["slack"],
                    "summary": analysis.get("summary")
                }
            else:
                print(f"  ✗ All notification methods failed")
                return {
                    "repo_name": repo_name,
                    "status": "alert_failed",
                    "old_version": old_version,
                    "new_version": new_version,
                    "message": "All notification methods failed"
                }
        else:
            print(f"  No alert needed (severity too low)")
            return {
                "repo_name": repo_name,
                "status": "update_detected_no_alert",
                "old_version": old_version,
                "new_version": new_version,
                "severity": severity,
                "message": "Update detected but alert criteria not met"
            }
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {
            "repo_name": repo_name,
            "status": "error",
            "message": str(e)
        }


def check_all_repositories(db: Database, repo_service: RepositoryService,
                          gemini_service: GeminiService, 
                          email_service: EmailService,
                          slack_service: SlackService,
                          repo_list: list) -> None:
    """
    Check all monitored repositories for updates.
    
    Args:
        db: Database instance.
        github_service: Repository service instance.
        gemini_service: Gemini service instance.
        email_service: Email service instance.
        slack_service: Slack service instance.
        repo_list: List of repository names to check.
    """
    print(f"\n{'='*60}")
    print(f"Starting repository check for {len(repo_list)} repositories")
    print(f"{'='*60}")
    
    results = []
    
    for repo_name in repo_list:
        result = check_repository_updates(
            repo_name, db, repo_service, gemini_service, email_service, slack_service
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("Check Summary:")
    print(f"{'='*60}")
    
    alerts_sent = sum(1 for r in results if r.get("status") == "alert_sent")
    errors = sum(1 for r in results if r.get("status") == "error")
    no_updates = sum(1 for r in results if r.get("status") == "no_update")
    
    print(f"  Total repositories: {len(results)}")
    print(f"  Alerts sent: {alerts_sent}")
    print(f"  No updates: {no_updates}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")
