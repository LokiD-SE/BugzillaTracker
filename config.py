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
EMAIL = os.getenv("EMAIL", "")

# Build query parameters dictionary
def get_query_params():
    """
    Returns the query parameters dictionary for Bugzilla API.
    Note: last_change_time will be added dynamically in notifier.py
    """
    params = {
        "status": BUG_STATUS,  # Use 'status' instead of 'bug_status'
    }
    
    # Add qa_contact and creator if email is provided
    if EMAIL:
        params["qa_contact"] = EMAIL
        params["creator"] = EMAIL
    
    # Add product filter only if specified
    if PRODUCT and any(PRODUCT):  # Check if PRODUCT list is not empty
        params["product"] = PRODUCT
    
    # Add API key if provided
    if BUGZILLA_API_KEY:
        params["api_key"] = BUGZILLA_API_KEY
    
    return params

