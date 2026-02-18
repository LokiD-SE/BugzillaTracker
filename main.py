#!/usr/bin/env python3
"""
Entry point for Bugzilla Tracker.
Main loop that continuously monitors Bugzilla for updates and sends notifications.
"""
import sys
from notifier import check_bugzilla, send_to_google_chat, send_initial_list_to_google_chat, STATE_FILE, save_bug_state, organize_bugs_by_product, fetch_all_bugs
from config import BUGZILLA_BASE_URL, get_query_params


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
        # Get all param sets for each email role
        param_sets = get_query_params()
        segment_names = ["QA Contact", "Creator", "Assigned To"]
        all_segment_bugs = []

        for idx, params in enumerate(param_sets):
            print(f"\nQuerying Bugzilla with params: {params}")
            bugs = fetch_all_bugs_with_params(params)
            # Filter out Internal Tools bugs with RESOLVED status
            filtered_bugs = [
                bug for bug in bugs
                if not (bug.get('product', 'Unknown') == "Internal Tools" and bug.get('status', 'Unknown') == "RESOLVED")
            ]
            all_segment_bugs.append(filtered_bugs)

        # Print each segment separately, skip empty segments
        for idx, bugs in enumerate(all_segment_bugs):
            if not bugs:
                continue
            print(f"\n{'='*60}")
            print(f"{segment_names[idx]} Segment - {len(bugs)} bug(s):")
            print(f"{'='*60}\n")
            # Organize and print bugs by product
            bugs_info = [(bug.get('id'), bug.get('status', 'Unknown'), bug.get('product', 'Unknown')) for bug in bugs]
            bugs_by_product = organize_bugs_by_product(bugs_info)
            product_order = ["Bizom Web", "Mobile App", "Internal Tools"]
            other_products = [p for p in bugs_by_product.keys() if p not in product_order]
            product_order.extend(sorted(other_products))
            for product in product_order:
                if product in bugs_by_product:
                    product_bugs = bugs_by_product[product]
                    print(f"{product} - {len(product_bugs)} bug(s) (sorted by status):")
                    print("-" * 60)
                    for bug_id, status, _ in product_bugs:
                        bug_url = f"{BUGZILLA_BASE_URL}/show_bug.cgi?id={bug_id}"
                        print(f'  • "{bug_url}" - {status}')
                    print()
            print(f"{'='*60}\n")

        # Send segmented bug lists to Google Chat
        segment_bugs_info = [
            [(bug.get('id'), bug.get('status', 'Unknown'), bug.get('product', 'Unknown')) for bug in bugs]
            for bugs in all_segment_bugs
        ]
        send_initial_list_to_google_chat(segment_bugs_info)

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

    # Patch: Add fetch_all_bugs_with_params to notifier.py if not present
    def fetch_all_bugs_with_params(params):
        from notifier import BUGZILLA_URL
        import requests
        import urllib.parse
        # Print the full Bugzilla API URL
        full_url = BUGZILLA_URL + "?" + urllib.parse.urlencode(params, doseq=True)
        print(f"Bugzilla API URL: {full_url}")
        try:
            response = requests.get(BUGZILLA_URL, params=params)
            response.raise_for_status()
            bugs = response.json().get('bugs', [])
            print(f"Found {len(bugs)} bug(s)")
            return bugs
        except Exception as e:
            print(f"Error fetching bugs: {e}")
            return []

    main(single_run=single_run, daily_initial=daily_initial)
