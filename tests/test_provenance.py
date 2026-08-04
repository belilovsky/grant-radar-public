from __future__ import annotations

from datetime import date, datetime, timezone

from core.models import Opportunity, OpportunityType
from core.provenance import provenance_profile


def _item(**kwargs) -> Opportunity:
    values = {
        "source": "official_source",
        "source_url": "https://example.org/program",
        "type": OpportunityType.GRANT,
        "title": "Kazakhstan support programme",
        "deadline": date(2027, 4, 1),
        "amount_min": 1000,
        "languages": ["en"],
        "discovered_at": datetime(2026, 8, 4, 1, 2, tzinfo=timezone.utc),
    }
    values.update(kwargs)
    return Opportunity(**values)


def test_provenance_distinguishes_observation_from_explicit_verification() -> None:
    profile = provenance_profile(
        _item(
            opportunity_status="open",
            raw={
                "source_language": "en",
                "last_verified_at": "2026-08-04T00:30:00Z",
                "deadline_raw": "1 April 2027",
                "amount_raw": "USD 1,000–5,000",
            },
        )
    )

    assert profile == {
        "schema_version": "provenance.v1",
        "source": "official_source",
        "source_url": "https://example.org/program",
        "evidence_state": "sourced",
        "evidence_basis": ["direct_source_url"],
        "observed_at": "2026-08-04T01:02:00+00:00",
        "last_verified_at": "2026-08-04T00:30:00Z",
        "source_language": "en",
        "source_language_basis": "explicit",
        "status": "open",
        "deadline_confidence": "supported",
        "amount_confidence": "supported",
        "missing_metadata": [],
    }


def test_provenance_does_not_promote_discovered_at_to_verified_at() -> None:
    profile = provenance_profile(_item(raw={}, languages=["ru"]))

    assert profile["observed_at"] == "2026-08-04T01:02:00+00:00"
    assert profile["last_verified_at"] is None
    assert profile["source_language"] == "ru"
    assert profile["source_language_basis"] == "record_languages"
    assert "last_verified_at" in profile["missing_metadata"]
