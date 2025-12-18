#!/usr/bin/env python3
"""
Entry point for Bugzilla Tracker.
Main loop that continuously monitors Bugzilla for updates and sends notifications.
"""
import time
import sys
from datetime import datetime
from notifier import check_bugzilla, send_to_google_chat, send_initial_list_to_google_chat, STATE_FILE, save_bug_state
from config import CHECK_INTERVAL_MINUTES, BUGZILLA_BASE_URL


def main(single_run=False, daily_initial=False):
    """
    Main loop that checks Bugzilla periodically and sends notifications.
    
    Args:
        single_run: If True, run once and exit (for scheduled jobs like GitHub Actions)
        daily_initial: If True, force initial run (for daily 10 AM fetch)
    """
    print("Monitoring Bugzilla...")
    print(f"Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    if single_run:
        if daily_initial:
            print("Daily initial run mode (10 AM) - will fetch and post initial bug list\n")
        else:
            print("Single run mode (hourly check) - will check for status changes\n")
    else:
        print("Press Ctrl+C to stop\n")
    
    # Check if this is the initial run
    # If daily_initial is True, reset state to force initial fetch
    if daily_initial:
        print("Daily initial run: Resetting state for fresh bug list fetch...")
        save_bug_state({})  # Reset state file
        is_initial_run = True
    else:
        is_initial_run = not STATE_FILE.exists() or (STATE_FILE.exists() and STATE_FILE.stat().st_size == 0)
    
    try:
        while True:
            # Use initial run flag only on first iteration
            if is_initial_run:
                status_changed_bugs, all_bugs_info = check_bugzilla(is_initial_run=True)
                is_initial_run = False  # After first run, it's no longer initial
            else:
                status_changed_bugs, all_bugs_info = check_bugzilla(is_initial_run=False)
            
            # On initial run, print all bugs and send to Google Chat
            if all_bugs_info is not None and len(all_bugs_info) > 0:
                print(f"\n{'='*60}")
                print(f"Initial Run - Found {len(all_bugs_info)} bug(s):")
                print(f"{'='*60}")
                for index, (bug_id, status) in enumerate(sorted(all_bugs_info, key=lambda x: x[0]), start=1):
                    bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
                    print(f'{index}."{bug_url}" - {status}')
                print(f"{'='*60}\n")
                
                # Send initial list to Google Chat
                send_initial_list_to_google_chat(all_bugs_info)
            
            # Print status changes
            if status_changed_bugs:
                print(f"\nFound {len(status_changed_bugs)} bug(s) with status changes:")
                for index, bug in enumerate(status_changed_bugs, start=1):
                    bug_id = bug.get('id')
                    previous_status = bug.get('_previous_status')
                    current_status = bug.get('status', 'Unknown')
                    bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
                    
                    if previous_status:
                        print(f'{index}."{bug_url}" - {previous_status} → {current_status}')
                    else:
                        print(f'{index}."{bug_url}" - {current_status} (new)')
                    
                    # Send notification
                    send_to_google_chat(bug, previous_status)
                print()
            elif all_bugs_info is None:
                # Only print "no changes" if it's not the initial run
                print(f"No status changes detected (checked at {time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # If single run mode, exit after one check
            if single_run:
                print("Single run completed. Exiting.")
                break
            
            # Wait for the next check interval
            time.sleep(CHECK_INTERVAL_MINUTES * 60)
            
    except KeyboardInterrupt:
        print("\n\nStopping Bugzilla Tracker...")
        print("Goodbye!")


if __name__ == "__main__":
    # Check for flags (for scheduled jobs)
    single_run = "--single-run" in sys.argv
    daily_initial = "--daily-initial" in sys.argv
    main(single_run=single_run, daily_initial=daily_initial)
