#!/usr/bin/env python3
"""
Fetch all bugs from Bugzilla segmented by QA Contact, Creator, and Assigned To.
Prints the bug list in segments and saves to a file.
"""
from config import get_query_params, BUGZILLA_URL
import requests
import urllib.parse

segment_names = ["QA Contact", "Creator", "Assigned To"]


def fetch_all_bugs_with_params(params):
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


def organize_bugs_by_product(bugs_info):
    status_priority = {
        'IN_PROGRESS': 1,
        'IN_PROGRESS_DEV': 2,
        'CONFIRMED': 3,
        'NEEDS_INFO': 4,
        'UNCONFIRMED': 5,
        'REOPENED': 6,
        'RESOLVED': 7,
    }
    bugs_by_product = {}
    for bug_info in bugs_info:
        product = bug_info[2]
        if product not in bugs_by_product:
            bugs_by_product[product] = []
        bugs_by_product[product].append(bug_info)
    for product in bugs_by_product:
        bugs_by_product[product].sort(
            key=lambda x: (
                status_priority.get(x[1], 999),
                x[0]
            )
        )
    return bugs_by_product


def print_segmented_bugs():
    param_sets = get_query_params()
    all_segment_bugs = []
    for idx, params in enumerate(param_sets):
        print(f"\nQuerying Bugzilla with params: {params}")
        bugs = fetch_all_bugs_with_params(params)
        bugs_info = [(bug.get('id'), bug.get('status', 'Unknown'), bug.get('product', 'Unknown')) for bug in bugs]
        all_segment_bugs.append(bugs_info)

    for idx, bugs_info in enumerate(all_segment_bugs):
        if not bugs_info:
            continue
        print(f"\n{'='*60}")
        print(f"{segment_names[idx]} Segment - {len(bugs_info)} bug(s):")
        print(f"{'='*60}\n")
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
                    bug_url = f"https://bugzilla.bizom.in/show_bug.cgi?id={bug_id}"
                    print(f'  • "{bug_url}" - {status}')
                print()
        print(f"{'='*60}\n")

if __name__ == "__main__":
    print_segmented_bugs()
