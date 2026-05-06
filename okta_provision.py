#!/usr/bin/env python3
"""
Okta Lab Provisioning Script
Creates groups and assigns users to them via the Okta API.

Idempotent: safe to re-run. Will not double-create groups or duplicate assignments.

Setup:
    1. Set environment variables:
        export OKTA_DOMAIN="https://trial-8474009.okta.com"
        export OKTA_API_TOKEN="your-token-here"

    2. Install dependencies:
        pip install requests

    3. Run:
        python3 okta_provision.py

Usage notes:
    - API token must have admin permissions to create groups and manage memberships
    - Users must already exist in the tenant before running this script
    - Re-running is safe; existing groups and assignments will be detected and skipped
"""

import os
import sys
import requests
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN")
OKTA_API_TOKEN = os.environ.get("OKTA_API_TOKEN")

if not OKTA_DOMAIN or not OKTA_API_TOKEN:
    print("ERROR: OKTA_DOMAIN and OKTA_API_TOKEN environment variables must be set.")
    print("Example:")
    print("  export OKTA_DOMAIN='https://trial-8474009.okta.com'")
    print("  export OKTA_API_TOKEN='your-token-here'")
    sys.exit(1)

HEADERS = {
    "Authorization": f"SSWS {OKTA_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Groups to create
GROUPS = [
    {"name": "Engineering", "description": "Engineering team — dev tools and infrastructure"},
    {"name": "Marketing", "description": "Marketing team — content and analytics tools"},
    {"name": "Sales", "description": "Sales team — CRM and sales enablement"},
    {"name": "IT", "description": "IT team — admin access to systems and security"},
    {"name": "Executive", "description": "Executive team — broad access with stricter MFA"},
    {"name": "All Employees", "description": "Universal group — baseline apps for all employees"},
]

# User-to-group mapping (by login / username)
USER_GROUP_ASSIGNMENTS = {
    "benfranklin@cloud9-consulting.com": ["Executive", "All Employees"],
    "thomas@cloud9-consulting.com":      ["Engineering", "All Employees"],
    "alex@cloud9-consulting.com":        ["Executive", "All Employees"],
    "john@cloud9-consulting.com":        ["Executive", "All Employees"],
    "abigail@cloud9-consulting.com":     ["Marketing", "All Employees"],
    "paul@cloud9-consulting.com":        ["IT", "All Employees"],
    "betsy@cloud9-consulting.com":       ["Marketing", "All Employees"],
    "nigeld@cloud9-consulting.com":      ["IT", "Executive", "All Employees"],
}


# ============================================================
# API HELPERS
# ============================================================

def find_group_by_name(name: str) -> Optional[dict]:
    """Look up a group by name. Returns the group object or None."""
    response = requests.get(
        f"{OKTA_DOMAIN}/api/v1/groups",
        headers=HEADERS,
        params={"q": name},
    )
    response.raise_for_status()
    for group in response.json():
        if group["profile"]["name"] == name:
            return group
    return None


def create_group(name: str, description: str) -> dict:
    """Create a new group. Returns the created group object."""
    payload = {
        "profile": {
            "name": name,
            "description": description,
        }
    }
    response = requests.post(
        f"{OKTA_DOMAIN}/api/v1/groups",
        headers=HEADERS,
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def find_user_by_login(login: str) -> Optional[dict]:
    """Look up a user by login (username/email). Returns the user object or None."""
    response = requests.get(
        f"{OKTA_DOMAIN}/api/v1/users/{login}",
        headers=HEADERS,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_user_groups(user_id: str) -> list:
    """Return the list of groups a user is currently a member of."""
    response = requests.get(
        f"{OKTA_DOMAIN}/api/v1/users/{user_id}/groups",
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


def add_user_to_group(user_id: str, group_id: str) -> None:
    """Add a user to a group. Idempotent — Okta returns 204 either way."""
    response = requests.put(
        f"{OKTA_DOMAIN}/api/v1/groups/{group_id}/users/{user_id}",
        headers=HEADERS,
    )
    response.raise_for_status()


# ============================================================
# MAIN PROVISIONING LOGIC
# ============================================================

def ensure_groups_exist() -> dict:
    """
    Make sure all configured groups exist.
    Returns a dict mapping group name -> group ID.
    """
    print("\n=== Ensuring groups exist ===")
    name_to_id = {}

    for group_config in GROUPS:
        name = group_config["name"]
        existing = find_group_by_name(name)

        if existing:
            print(f"  [skip] '{name}' already exists (id={existing['id']})")
            name_to_id[name] = existing["id"]
        else:
            created = create_group(name, group_config["description"])
            print(f"  [created] '{name}' (id={created['id']})")
            name_to_id[name] = created["id"]

    return name_to_id


def assign_users_to_groups(group_name_to_id: dict) -> None:
    """Walk the user-to-group mapping and ensure each user is in their target groups."""
    print("\n=== Assigning users to groups ===")

    for login, target_groups in USER_GROUP_ASSIGNMENTS.items():
        user = find_user_by_login(login)
        if not user:
            print(f"  [warn] User '{login}' not found in tenant — skipping")
            continue

        user_id = user["id"]
        current_group_ids = {g["id"] for g in get_user_groups(user_id)}

        for group_name in target_groups:
            group_id = group_name_to_id.get(group_name)
            if not group_id:
                print(f"  [error] Group '{group_name}' not found — skipping for {login}")
                continue

            if group_id in current_group_ids:
                print(f"  [skip] {login} already in '{group_name}'")
            else:
                add_user_to_group(user_id, group_id)
                print(f"  [added] {login} -> '{group_name}'")


def main():
    print(f"Connecting to {OKTA_DOMAIN}")
    try:
        group_name_to_id = ensure_groups_exist()
        assign_users_to_groups(group_name_to_id)
        print("\n✓ Provisioning complete.\n")
    except requests.HTTPError as e:
        print(f"\n✗ HTTP error: {e}")
        print(f"  Response: {e.response.text}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"\n✗ Request error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
