"""
Logic for querying Bugzilla and formatting Chat messages.
"""
import json
from pathlib import Path
import requests
from datetime import datetime, timedelta, timezone
from config import BUGZILLA_URL, GOOGLE_CHAT_WEBHOOK, CHECK_INTERVAL_MINUTES, get_query_params, BUGZILLA_BASE_URL

# State file to track bug statuses
STATE_FILE = Path(__file__).parent / 'bug_state.json'


def load_bug_state():
    """
    Load the previous bug states from the state file.
    Returns a dictionary mapping bug_id to status.
    """
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load bug state file: {e}")
            return {}
    return {}


def save_bug_state(bug_states):
    """
    Save the current bug states to the state file.
    
    Args:
        bug_states: Dictionary mapping bug_id to status
    """
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(bug_states, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save bug state file: {e}")


def fetch_initial_bugs(months_ago=1):
    """
    Fetch bugs from the last N months for initial run.
    Uses last_change_time in YYYY-MM-DD format (e.g., 2025-11-01).
    
    Args:
        months_ago: Number of months to look back (default: 1)
    
    Returns:
        List of bugs
    """
    query_params = get_query_params()
    
    # Calculate date N months ago
    target_date = datetime.now(timezone.utc) - timedelta(days=months_ago * 30)
    last_change_date = target_date.strftime('%Y-%m-%d')
    
    # Add last_change_time in YYYY-MM-DD format (not full datetime)
    query_params["last_change_time"] = last_change_date
    
    print(f"Fetching bugs changed since {last_change_date} (last {months_ago} months)...")
    
    try:
        response = requests.get(BUGZILLA_URL, params=query_params)
        response.raise_for_status()
        bugs = response.json().get('bugs', [])
        print(f"Found {len(bugs)} bug(s) from the last {months_ago} months")
        return bugs
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bugs from Bugzilla: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching bugs: {e}")
        return []


def check_bugzilla(is_initial_run=False):
    """
    Check Bugzilla for bugs modified in the last CHECK_INTERVAL_MINUTES.
    Returns a tuple: (status_changed_bugs, all_bugs_info)
    - status_changed_bugs: List of bugs that have changed status
    - all_bugs_info: List of tuples (bug_id, status) for all current bugs (only on initial run)
    """
    # Load previous states to check if this is an initial run
    previous_states = load_bug_state()
    is_initial = is_initial_run or len(previous_states) == 0
    
    if is_initial:
        # On initial run, fetch bugs from last 1 month
        print("Initial run detected. Fetching bugs from last 1 month...")
        bugs = fetch_initial_bugs(months_ago=1)
        all_bugs_info = []
    else:
        # Only look for bugs changed since the last check
        since_time = (datetime.now(timezone.utc) - timedelta(minutes=CHECK_INTERVAL_MINUTES)).strftime('%Y-%m-%dT%H:%M:%SZ')
        query_params = get_query_params()
        query_params["last_change_time"] = since_time
        
        try:
            response = requests.get(BUGZILLA_URL, params=query_params)
            response.raise_for_status()
            bugs = response.json().get('bugs', [])
        except requests.exceptions.RequestException as e:
            print(f"Error checking Bugzilla: {e}")
            return [], []
        except Exception as e:
            print(f"Unexpected error checking Bugzilla: {e}")
            return [], []
        
        all_bugs_info = None
    
    # Track current states and find status changes
    current_states = previous_states.copy()
    status_changed_bugs = []
    
    for bug in bugs:
        bug_id = bug.get('id')
        current_status = bug.get('status', 'Unknown')
        
        if bug_id:
            bug_id_str = str(bug_id)
            # Update current state
            current_states[bug_id_str] = current_status
            
            if is_initial:
                # On initial run, collect all bugs info
                all_bugs_info.append((bug_id, current_status))
            else:
                # Check if status has changed
                previous_status = previous_states.get(bug_id_str)
                if previous_status and previous_status != current_status:
                    # Store previous status in bug dict for notification
                    bug['_previous_status'] = previous_status
                    status_changed_bugs.append(bug)
                    print(f"Status change detected for bug #{bug_id}: {previous_status} -> {current_status}")
                elif not previous_status:
                    # New bug we haven't seen before - treat as status change
                    status_changed_bugs.append(bug)
                    print(f"New bug detected: #{bug_id} with status {current_status}")
    
    # Save current states for next check (includes all tracked bugs)
    save_bug_state(current_states)
    
    return status_changed_bugs, all_bugs_info


def send_initial_list_to_google_chat(all_bugs_info):
    """
    Send the initial list of bugs to Google Chat.
    
    Args:
        all_bugs_info: List of tuples (bug_id, status) for all bugs
    """
    if not GOOGLE_CHAT_WEBHOOK:
        print("Warning: GOOGLE_CHAT_WEBHOOK not configured. Skipping notification.")
        return
    
    if not all_bugs_info or len(all_bugs_info) == 0:
        return
    
    # Sort bugs by ID
    sorted_bugs = sorted(all_bugs_info, key=lambda x: x[0])
    
    # Format the message
    header = f"📋 *Initial Bug List - {len(sorted_bugs)} bug(s) found*\n\n"
    
    # Build the list
    bug_list = []
    for index, (bug_id, status) in enumerate(sorted_bugs, start=1):
        bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
        bug_list.append(f"{index}. \"{bug_url}\" - {status}")
    
    text = header + "\n".join(bug_list)
    
    payload = {"text": text}
    
    try:
        response = requests.post(GOOGLE_CHAT_WEBHOOK, json=payload)
        response.raise_for_status()
        print(f"Successfully sent initial bug list to Google Chat ({len(sorted_bugs)} bugs)")
        print(f"Starting to monitor bugs...")
    except requests.exceptions.RequestException as e:
        print(f"Error sending initial list to Google Chat: {e}")
    except Exception as e:
        print(f"Unexpected error sending initial list to Google Chat: {e}")


def send_to_google_chat(bug, previous_status=None):
    """
    Send a formatted bug notification to Google Chat.
    
    Args:
        bug: A dictionary containing bug information from Bugzilla API
        previous_status: The previous status of the bug (if available)
    """
    if not GOOGLE_CHAT_WEBHOOK:
        print("Warning: GOOGLE_CHAT_WEBHOOK not configured. Skipping notification.")
        return
    
    # Format the bug information
    bug_id = bug.get('id', 'N/A')
    summary = bug.get('summary', 'No summary')
    status = bug.get('status', 'Unknown')
    component = bug.get('component', 'Unknown')
    
    # Include status change information if available
    status_info = f"*Status:* {status}"
    if previous_status:
        status_info = f"*Status:* {previous_status} → {status}"
    
    text = (
        f"🐞 *Bug Status Changed: #{bug_id}*\n"
        f"*Summary:* {summary}\n"
        f"{status_info} | *Component:* {component}\n"
        f"🔗 {BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
    )
    
    payload = {"text": text}
    
    try:
        response = requests.post(GOOGLE_CHAT_WEBHOOK, json=payload)
        response.raise_for_status()
        print(f"Successfully sent notification for bug #{bug_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification to Google Chat for bug #{bug_id}: {e}")
    except Exception as e:
        print(f"Unexpected error sending notification for bug #{bug_id}: {e}")

