# Okta Lab Provisioning

A Python script that talks directly to the Okta API to provision groups and assign users. Built as a hands-on lab to deepen IAM fundamentals and demonstrate attribute-driven group management at scale.

## What it does

- Creates Okta groups idempotently (safe to re-run)
- Assigns users to groups based on a configurable mapping
- Pairs with Okta group rules for fully attribute-driven membership
- Reads credentials from environment variables (no secrets in code)

## Why it exists

Manual GUI work doesn't scale. Real IAM operations live in code: provisioning workflows, drift detection, lifecycle automation, integrations with HR systems. This script is the smallest version of that pattern — declarative inputs, idempotent operations, observable output.

## Architecture

```
HRIS attributes (department, title, etc.)
        ↓
   Okta user profiles
        ↓
   Okta group rules
        ↓
   Group memberships
        ↓
   SCIM-provisioned downstream apps
```

User attributes drive group membership through rules. Group membership drives app access through assignments. App access drives provisioning through SCIM. One source of truth, full lifecycle automation.

## Setup

### Prerequisites

- Python 3.8+
- An Okta tenant (a free developer tenant works)
- Okta API token with admin permissions

### Install

```bash
git clone https://github.com/dumont94/okta-lab-provisioning.git
cd okta-lab-provisioning
pip3 install -r requirements.txt
```

### Configure

Set environment variables for your tenant:

```bash
export OKTA_DOMAIN="https://your-tenant.okta.com"
export OKTA_API_TOKEN="your-api-token"
```

Edit `okta_provision.py` to define your groups and user-to-group mappings:

```python
GROUPS = [
    {"name": "Engineering", "description": "Engineering team"},
    {"name": "Marketing", "description": "Marketing team"},
]

USER_GROUP_ASSIGNMENTS = {
    "alice@example.com": ["Engineering", "All Employees"],
    "bob@example.com":   ["Marketing", "All Employees"],
}
```

### Run

```bash
python3 okta_provision.py
```

Re-runs are idempotent — you'll see `[skip]` for everything that already exists.

## Security notes

This is lab code. Production deployments should harden in a few ways:

- **Scoped tokens.** Use Okta API Service Apps with OAuth 2.0 scopes instead of Super Admin tokens. Limit blast radius if a token leaks.
- **Network restrictions.** Lock API tokens to specific network zones (corporate IPs, VPN ranges) so leaked tokens can't be used from arbitrary origins.
- **Secret management.** Move from environment variables to a secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) for production credentials.
- **Token rotation.** Even unused tokens should rotate on a schedule. Compromised credentials are often used months after the leak.
- **Audit logging.** Pipe Okta System Log events into a SIEM (Splunk, Sentinel) so all admin API actions are observable.

## What's next

Future iterations will demonstrate:

- Group rules creation via API (attribute-driven group membership)
- SCIM provisioning to a downstream app (e.g. Slack)
- Drift detection — compare declared state against actual state
- HRIS-driven onboarding pattern (CSV simulating a Workday export)

## Built with

- Python 3
- requests for HTTP
- Okta API for everything else

## Author

Nigel Dumont — Senior Systems & Infrastructure Administrator  
[LinkedIn](https://linkedin.com/in/nigeldumont) · [GitHub](https://github.com/dumont94)
