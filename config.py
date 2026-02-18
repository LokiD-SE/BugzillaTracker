"""
Configuration loader for Bugzilla Tracker.
Reads environment variables from .env file and provides configuration constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Get the directory where this config.py file is located
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Bugzilla API Configuration
BUGZILLA_URL = os.getenv("BUGZILLA_URL", "https://bugzilla.bizom.in/rest/bug")
BUGZILLA_BASE_URL = "https://bugzilla.bizom.in"
BUGZILLA_API_KEY = os.getenv("BUGZILLA_API_KEY", "")

# Google Chat Webhook
GOOGLE_CHAT_WEBHOOK = os.getenv("GOOGLE_CHAT_WEBHOOK", "")

# Check Interval (in minutes)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))

# Query Parameters
# Status values matching the working URL format
BUG_STATUS = os.getenv("BUG_STATUS", "UNCONFIRMED,CONFIRMED,NEEDS_INFO,IN_PROGRESS,IN_PROGRESS_DEV,RESOLVED,REOPENED").split(",")
# Product filter (optional - can be empty)
PRODUCT = os.getenv("PRODUCT", "").split(",") if os.getenv("PRODUCT") else []

# Email for qa_contact and creator filters
def fetch_email_from_google_chat():
    """
    Attempt to fetch the user's email from Google Chat API.
    Returns the email if found, else None.
    """
    # Placeholder: Implement actual Google Chat API call here
    # For now, always return None to fallback to .env
    # Example: Use Google People API or Chat API if available
    return None

# Try to fetch email from Google Chat, fallback to .env value
_fetched_email = fetch_email_from_google_chat()
EMAIL = _fetched_email if _fetched_email else os.getenv("EMAIL", "")

# LAST_CHANGE_TIME from .env (optional)
LAST_CHANGE_TIME = os.getenv("LAST_CHANGE_TIME", None)

# Build query parameters dictionary
def get_query_params():
    """
    Returns the query parameters dictionary for Bugzilla API.
    If LAST_CHANGE_TIME is set in .env, use it. Otherwise, default to 2 months ago.
    """
    from datetime import datetime, timedelta, timezone
    base_params = {
        "status": BUG_STATUS,
    }
    if PRODUCT and any(PRODUCT):
        base_params["product"] = PRODUCT
    if BUGZILLA_API_KEY:
        base_params["api_key"] = BUGZILLA_API_KEY

    # Set last_change_time from .env or default to 2 months ago
    if LAST_CHANGE_TIME:
        last_change_time = LAST_CHANGE_TIME
    else:
        last_change_time = (datetime.now(timezone.utc) - timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')
    base_params["last_change_time"] = last_change_time

    # Build three param sets for each email role
    param_sets = []
    if EMAIL:
        # QA Contact
        qa_params = base_params.copy()
        qa_params["qa_contact"] = EMAIL
        param_sets.append(qa_params)

        # Creator
        creator_params = base_params.copy()
        creator_params["creator"] = EMAIL
        param_sets.append(creator_params)

        # Assigned To
        assigned_params = base_params.copy()
        assigned_params["assigned_to"] = EMAIL
        param_sets.append(assigned_params)
    else:
        # If no email, just return base params
        param_sets.append(base_params)

    return param_sets

