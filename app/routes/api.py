"""
Flask API routes and webhook handler.
Provides REST endpoints for monitoring and GitHub webhook integration.
"""
from flask import Blueprint, jsonify, request
from typing import Dict, Any

from app.db.database import Database
from app.config import Config
from app.services.repository_service import RepositoryService
from app.services.gemini_service import GeminiService
from app.services.email_service import EmailService
from app.services.slack_service import SlackService


# Create blueprint
api_bp = Blueprint("api", __name__)

# Initialize services (will be injected by main app)
db: Database = None
repo_service: RepositoryService = None
gemini_service: GeminiService = None
email_service: EmailService = None
slack_service: SlackService = None


def init_routes(database: Database, repo: RepositoryService, 
               gemini: GeminiService, email: EmailService, slack: SlackService):
    """
    Initialize routes with service dependencies.
    
    Args:
        database: Database instance.
        github: GitHub service instance.
        gemini: Gemini service instance.
        email: Email service instance.
        slack: Slack service instance.
    """
    global db, repo_service, gemini_service, email_service, slack_service
    db = database
    repo_service = repo
    gemini_service = gemini
    email_service = email
    slack_service = slack


@api_bp.route("/health", methods=["GET"])
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status.
    """
    return jsonify({
        "status": "healthy",
        "service": "blockchain-release-monitor",
        "version": "1.0.0"
    })


@api_bp.route("/repos", methods=["GET"])
def get_repositories() -> Dict[str, Any]:
    """
    Get all monitored repositories.
    
    Returns:
        List of repositories with their status.
    """
    try:
        repos = db.get_all_repositories()
        
        repo_list = [
            {
                "repo_name": repo.repo_name,
                "repo_url": repo.repo_url,
                "last_checked": repo.last_checked,
                "last_version_or_tag": repo.last_version_or_tag,
                "last_alerted_version": repo.last_alerted_version,
                "severity": repo.severity,
                "mandatory_upgrade": repo.mandatory_upgrade
            }
            for repo in repos
        ]
        
        return jsonify({
            "success": True,
            "count": len(repo_list),
            "repositories": repo_list
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/repos/<path:repo_name>", methods=["GET"])
def get_repository(repo_name: str) -> Dict[str, Any]:
    """
    Get specific repository details.
    
    Args:
        repo_name: Repository name (owner/repo).
        
    Returns:
        Repository details.
    """
    try:
        repo = db.get_repository(repo_name)
        
        if not repo:
            return jsonify({
                "success": False,
                "error": "Repository not found"
            }), 404
        
        return jsonify({
            "success": True,
            "repository": {
                "repo_name": repo.repo_name,
                "repo_url": repo.repo_url,
                "last_checked": repo.last_checked,
                "last_version_or_tag": repo.last_version_or_tag,
                "last_alerted_version": repo.last_alerted_version,
                "severity": repo.severity,
                "mandatory_upgrade": repo.mandatory_upgrade,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/repos/<path:repo_name>/check", methods=["POST"])
def check_repository(repo_name: str) -> Dict[str, Any]:
    """
    Manually trigger check for specific repository.
    
    Args:
        repo_name: Repository name (owner/repo).
        
    Returns:
        Check result.
    """
    try:
        from app.monitor import check_repository_updates
        
        result = check_repository_updates(
            repo_name, db, repo_service, gemini_service, email_service, slack_service
        )
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/alerts", methods=["GET"])
def get_alerts() -> Dict[str, Any]:
    """
    Get alert history.
    
    Returns:
        List of recent alerts.
    """
    try:
        repo_name = request.args.get("repo_name")
        limit = int(request.args.get("limit", 50))
        
        alerts = db.get_alert_history(repo_name, limit)
        
        alert_list = [
            {
                "id": alert.id,
                "repo_name": alert.repo_name,
                "version": alert.version,
                "severity": alert.severity,
                "mandatory_upgrade": alert.mandatory_upgrade,
                "summary": alert.summary,
                "alerted_at": alert.alerted_at
            }
            for alert in alerts
        ]
        
        return jsonify({
            "success": True,
            "count": len(alert_list),
            "alerts": alert_list
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/webhook/github", methods=["POST"])
def github_webhook() -> Dict[str, Any]:
    """
    Handle GitHub webhook events for releases and tags.
    
    Supports:
    - release (published)
    - create (tag)
    
    Returns:
        Webhook processing result.
    """
    try:
        # Get webhook event type
        event_type = request.headers.get("X-GitHub-Event")
        payload = request.json
        
        if not payload:
            return jsonify({
                "success": False,
                "error": "No payload received"
            }), 400
        
        # Extract repository information
        repository = payload.get("repository", {})
        repo_full_name = repository.get("full_name")
        
        if not repo_full_name:
            return jsonify({
                "success": False,
                "error": "Repository name not found in payload"
            }), 400
        
        # Check if we're monitoring this repository
        if repo_full_name not in Config.MONITORED_REPOS:
            return jsonify({
                "success": False,
                "message": f"Repository {repo_full_name} is not monitored"
            }), 200
        
        # Process based on event type
        if event_type == "release":
            action = payload.get("action")
            if action == "published":
                release = payload.get("release", {})
                if not release.get("prerelease"):
                    # Trigger check for this repository
                    from app.monitor import check_repository_updates
                    
                    result = check_repository_updates(
                        repo_full_name, db, repo_service, 
                        gemini_service, email_service, slack_service
                    )
                    
                    return jsonify({
                        "success": True,
                        "event": "release_published",
                        "repo": repo_full_name,
                        "result": result
                    })
        
        elif event_type == "create":
            ref_type = payload.get("ref_type")
            if ref_type == "tag":
                # Trigger check for this repository
                from app.monitor import check_repository_updates
                
                result = check_repository_updates(
                    repo_full_name, db, repo_service, 
                    gemini_service, email_service, slack_service
                )
                
                return jsonify({
                    "success": True,
                    "event": "tag_created",
                    "repo": repo_full_name,
                    "result": result
                })
        
        # Event not processed
        return jsonify({
            "success": True,
            "message": f"Event {event_type} received but not processed"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/test/email", methods=["POST"])
def test_email() -> Dict[str, Any]:
    """
    Send test email to verify configuration.
    
    Returns:
        Test result.
    """
    try:
        success = email_service.send_test_email()
        
        return jsonify({
            "success": success,
            "message": "Test email sent" if success else "Failed to send test email"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/test/slack", methods=["POST"])
def test_slack() -> Dict[str, Any]:
    """
    Send test Slack message to verify configuration.
    
    Returns:
        Test result.
    """
    try:
        success = slack_service.send_test_message()
        
        return jsonify({
            "success": success,
            "message": "Test Slack message sent" if success else "Failed to send test Slack message",
            "enabled": slack_service.enabled
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
