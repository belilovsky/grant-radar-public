from __future__ import annotations

from semantic_service.catalog import public_search_documents


def test_semantic_catalog_keeps_only_public_normalized_fields():
    documents = public_search_documents(
        [
            {
                "id": "opportunity-1",
                "title": "  AI   support ",
                "summary": "For  Kazakhstan teams",
                "funder": "Example Foundation",
                "type": "grant",
                "tags": ["ai", "kazakhstan"],
                "eligibility": ["startups"],
                "source": "example",
                "raw": {"private_note": "must not enter index"},
                "source_url": "https://example.org/private-not-needed",
            }
        ]
    )

    assert documents == [
        {
            "id": "opportunity-1",
            "text": (
                "AI support\nFor Kazakhstan teams\nExample Foundation\ngrant\n"
                "ai kazakhstan\nstartups\nexample"
            ),
        }
    ]
