"""
Logic for querying Bugzilla and formatting Chat messages.
"""
import json
from pathlib import Path
import requests
from datetime import datetime, timedelta, timezone
from config import BUGZILLA_URL, GOOGLE_CHAT_WEBHOOK, get_query_params, BUGZILLA_BASE_URL

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


def fetch_all_bugs():
    """
    Fetch bugs matching the configured filters from the last 2 months.
    
    Returns:
        List of bugs
    """
    query_params = get_query_params()
    # Add last_change_time filter for 2 months of data
    two_months_ago = (datetime.now(timezone.utc) - timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')
    query_params['last_change_time'] = two_months_ago
    
    print(f"Fetching bugs changed in the last 2 months (since {two_months_ago})...")
    
    try:
        response = requests.get(BUGZILLA_URL, params=query_params)
        response.raise_for_status()
        bugs = response.json().get('bugs', [])
        print(f"Found {len(bugs)} bug(s)")
        return bugs
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bugs from Bugzilla: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching bugs: {e}")
        return []


def check_bugzilla():
    """
    Fetch all bugs matching filters and track status changes.
    Returns a tuple: (status_changed_bugs, all_bugs_info)
    - status_changed_bugs: List of bugs that have changed status
    - all_bugs_info: List of tuples (bug_id, status, product) for all current bugs
    """
    # Load previous states
    previous_states = load_bug_state()
    
    # Fetch all bugs (no time filter)
    bugs = fetch_all_bugs()
    all_bugs_info = []
    status_changed_bugs = []
    
    # Track current states
    current_states = previous_states.copy()
    
    for bug in bugs:
        bug_id = bug.get('id')
        current_status = bug.get('status', 'Unknown')
        product = bug.get('product', 'Unknown')
        
        if bug_id:
            bug_id_str = str(bug_id)
            # Update current state
            current_states[bug_id_str] = current_status
            
            # Collect all bugs info with product
            all_bugs_info.append((bug_id, current_status, product))
            
            # Check if status has changed
            previous_status = previous_states.get(bug_id_str)
            if previous_status and previous_status != current_status:
                # Store previous status in bug dict for notification
                bug['_previous_status'] = previous_status
                status_changed_bugs.append(bug)
                print(f"Status change detected for bug #{bug_id}: {previous_status} -> {current_status}")
            elif not previous_status:
                # New bug we haven't seen before
                status_changed_bugs.append(bug)
                print(f"New bug detected: #{bug_id} with status {current_status}")
    
    # Save current states for next check
    save_bug_state(current_states)
    
    return status_changed_bugs, all_bugs_info


def send_initial_list_to_google_chat(all_bugs_info):
    """
    Send the initial list of bugs to Google Chat.
    
    Args:
        all_bugs_info: List of tuples (bug_id, status, product) for all bugs
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
    for index, (bug_id, status, product) in enumerate(sorted_bugs, start=1):
        bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
        bug_list.append(f"{index}. \"{bug_url}\" - {status} - {product}")
    
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

