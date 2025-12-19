"""
Main application entry point.
Runs Flask API server and scheduled monitoring tasks.
"""
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from app.config import Config
from app.db.database import Database
from app.services.repository_service import RepositoryService
from app.services.gemini_service import GeminiService
from app.services.email_service import EmailService
from app.services.slack_service import SlackService
from app.routes.api import api_bp, init_routes
from app.monitor import check_all_repositories


def create_app() -> Flask:
    """
    Create and configure Flask application.
    
    Returns:
        Configured Flask app.
    """
    # Validate configuration
    missing = Config.validate()
    if missing:
        print("ERROR: Missing required configuration:")
        for item in missing:
            print(f"  - {item}")
        print("\nPlease check your .env file.")
        exit(1)
    
    # Initialize services
    print("Initializing services...")
    
    db = Database(Config.DATABASE_PATH)
    tag_filters = Config.get_repo_tag_filters()
    repo_service = RepositoryService(tag_filters=tag_filters)
    gemini_service = GeminiService()
    email_service = EmailService()
    slack_service = SlackService()
    
    print("✓ Database initialized")
    print("✓ Repository service initialized (GitHub + GitLab)")
    if tag_filters:
        print(f"  Tag filters configured for: {', '.join(tag_filters.keys())}")
    print("✓ Gemini service initialized")
    
    # Log notification methods status
    if Config.EMAIL_ALERTS_ENABLED:
        print("✓ Email service initialized (enabled)")
    else:
        print("✓ Email service initialized (disabled)")
    
    if slack_service.enabled and Config.SLACK_ALERTS_ENABLED:
        print("✓ Slack service initialized (enabled)")
    elif Config.SLACK_ALERTS_ENABLED:
        print("⚠ Slack alerts enabled but webhook URL not configured")
    else:
        print("✓ Slack service initialized (disabled)")
    
    # Initialize monitored repositories in database
    print("\nInitializing monitored repositories:")
    for repo_name in Config.MONITORED_REPOS:
        repo_url = repo_service.get_repo_url(repo_name)
        platform = repo_service.get_platform(repo_name)
        db.upsert_repository(repo_name, repo_url)
        print(f"  - {repo_name} [{platform}]")
    
    # Create Flask app
    app = Flask(__name__)
    
    # Initialize routes with services
    init_routes(db, repo_service, gemini_service, email_service, slack_service)
    app.register_blueprint(api_bp)
    
    # Setup scheduler for periodic checks
    scheduler = BackgroundScheduler()
    
    def scheduled_check():
        """Scheduled repository check task."""
        with app.app_context():
            check_all_repositories(
                db, repo_service, gemini_service, 
                email_service, slack_service, Config.MONITORED_REPOS
            )
    
    # Schedule periodic checks
    scheduler.add_job(
        func=scheduled_check,
        trigger="interval",
        minutes=Config.CHECK_INTERVAL_MINUTES,
        id="repository_check",
        name="Check repositories for updates"
    )
    
    # Start scheduler
    scheduler.start()
    print(f"\n✓ Scheduler started (checking every {Config.CHECK_INTERVAL_MINUTES} minutes)")
    
    # Shutdown scheduler on exit
    atexit.register(lambda: scheduler.shutdown())
    
    # Run initial check
    print("\nRunning initial repository check...")
    with app.app_context():
        scheduled_check()
    
    return app


def main():
    """Main application entry point."""
    print("="*60)
    print("Blockchain Release Monitor")
    print("="*60)
    
    app = create_app()
    
    print("\n" + "="*60)
    print("Starting Flask server...")
    print("="*60)
    print(f"API available at: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print("\nAvailable endpoints:")
    print(f"  GET  /health")
    print(f"  GET  /repos")
    print(f"  GET  /repos/<repo_name>")
    print(f"  POST /repos/<repo_name>/check")
    print(f"  GET  /alerts")
    print(f"  POST /webhook/github")
    print(f"  POST /test/email")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=False
    )


if __name__ == "__main__":
    main()
