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
        "calendar_export": {
            "enabled": True,
            "delivery": "user_initiated_ics_download",
            "server_side_schedule": False,
            "description": (
                "A dated application workspace can export local calendar reminders; "
                "this is not a subscription or background notification."
            ),
        },
        "identity": {
            "anonymous_read_access": True,
            "authenticated_owner": False,
            "server_side_profile": False,
            "cross_device_sync": False,
            "local_browser_storage_only": True,
        },
        "consent": {
            "collection_enabled": False,
            "version": None,
            "purpose": None,
            "frequency": None,
            "withdrawal_path": "not_available_until_activation",
        },
        "storage": {
            "server_side_subscriptions": False,
            "server_side_saved_views": False,
            "personal_data_retention": "not_applicable",
        },
        "public_behavior": {
            "subscription_ui": False,
            "background_delivery": False,
            "browser_local_saves_are_subscriptions": False,
            "calendar_export_is_subscription": False,
            "account_ui": False,
            "sync_ui": False,
        },
        "required_before_activation": [
            "authenticated_owner",
            "identity_provider_and_account_recovery",
            "explicit_opt_in_with_purpose_and_frequency",
            "versioned_consent_record_and_withdrawal",
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
