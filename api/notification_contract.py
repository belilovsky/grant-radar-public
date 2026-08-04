"""Explicit boundary for future QAZ.FUND notifications.

The public catalog is read-only and currently has no identity, subscription
store, or notification worker. Keeping that state machine explicit prevents a
future UI or AI consumer from treating local browser saves as an active
subscription.
"""

from __future__ import annotations

from typing import Any


def notification_contract(origin: str) -> dict[str, Any]:
    """Return the versioned, non-operational notification boundary."""

    base = origin.rstrip("/")
    return {
        "schema_version": "notification-v1",
        "product": "qaz-fund",
        "status": "not_enabled",
        "delivery": {
            "enabled": False,
            "worker_running": False,
            "channels": {
                "email": {"enabled": False, "provider": None},
                "telegram": {"enabled": False, "provider": None},
            },
        },
        "storage": {
            "server_side_subscriptions": False,
            "personal_data_retention": "not_applicable",
        },
        "public_behavior": {
            "subscription_ui": False,
            "background_delivery": False,
            "browser_local_saves_are_subscriptions": False,
        },
        "required_before_activation": [
            "authenticated_owner",
            "explicit_opt_in_with_purpose_and_frequency",
            "verified_delivery_channel",
            "delivery_attempt_and_receipt_log",
            "unsubscribe_and_delete_path",
            "retry_and_idempotency_policy",
            "retention_and_access_policy",
        ],
        "links": {
            "terms": f"{base}/terms?lang=ru",
            "data_policy": f"{base}/data-policy?lang=ru",
            "insights": f"{base}/insights.json?lang=ru",
        },
    }
