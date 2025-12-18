#!/usr/bin/env python3
"""
Entry point for Bugzilla Tracker.
Main loop that continuously monitors Bugzilla for updates and sends notifications.
"""
import sys
from notifier import check_bugzilla, send_to_google_chat, send_initial_list_to_google_chat, STATE_FILE, save_bug_state
from config import BUGZILLA_BASE_URL


def main(single_run=False, daily_initial=False):
    """
    Main function that fetches all bugs and tracks status changes.
    
    Args:
        single_run: If True, run once and exit (for scheduled jobs like GitHub Actions)
        daily_initial: If True, reset state for fresh daily fetch (for daily 10 AM run)
    """
    print("Bugzilla Tracker - Daily Run")
    if daily_initial:
        print("Daily initial run (10 AM) - fetching all bugs and posting initial list\n")
        # Reset state file for fresh daily fetch
        print("Resetting state for fresh bug list fetch...")
        save_bug_state({})
    else:
        print("Fetching all bugs and checking for status changes\n")
    
    try:
        # Fetch all bugs and check for status changes
        status_changed_bugs, all_bugs_info = check_bugzilla()
        
        # Print all bugs with product
        if all_bugs_info and len(all_bugs_info) > 0:
            print(f"\n{'='*60}")
            print(f"Found {len(all_bugs_info)} bug(s):")
            print(f"{'='*60}")
            for index, (bug_id, status, product) in enumerate(sorted(all_bugs_info, key=lambda x: x[0]), start=1):
                bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
                print(f'{index}."{bug_url}" - {status} - {product}')
            print(f"{'='*60}\n")
            
            # Send initial list to Google Chat
            send_initial_list_to_google_chat(all_bugs_info)
        
        # Print and notify status changes
        if status_changed_bugs:
            print(f"\nFound {len(status_changed_bugs)} bug(s) with status changes:")
            for index, bug in enumerate(status_changed_bugs, start=1):
                bug_id = bug.get('id')
                previous_status = bug.get('_previous_status')
                current_status = bug.get('status', 'Unknown')
                product = bug.get('product', 'Unknown')
                bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
                
                if previous_status:
                    print(f'{index}."{bug_url}" - {previous_status} → {current_status} - {product}')
                else:
                    print(f'{index}."{bug_url}" - {current_status} (new) - {product}')
                
                # Send notification
                send_to_google_chat(bug, previous_status)
            print()
        else:
            print("No status changes detected.")
        
        print("Run completed. Exiting.")
            
    except KeyboardInterrupt:
        print("\n\nStopping Bugzilla Tracker...")
        print("Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    # Check for flags (for scheduled jobs)
    single_run = "--single-run" in sys.argv
    daily_initial = "--daily-initial" in sys.argv
    main(single_run=single_run, daily_initial=daily_initial)
