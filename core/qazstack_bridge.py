"""Optional QazStack integration points for shared opportunity primitives."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Protocol


class SharedSourceContract(Protocol):
    def validate(self) -> None: ...


@lru_cache(maxsize=1)
def _shared_source_contract_cls():
    from qazstack.opportunities import SourceContract

    return SourceContract


def validate_shared_source_contract(parser: Any) -> bool:
    """Validate parser metadata against the packaged QazStack contract."""

    source_contract_cls = _shared_source_contract_cls()
    contract: SharedSourceContract = source_contract_cls(
        slug=str(getattr(parser, "slug", "") or getattr(parser, "name", "")),
        name=str(getattr(parser, "name", "")),
        base_url=str(getattr(parser, "base_url", "")),
        request_delay=float(getattr(parser, "request_delay", 0.0)),
        default_tags=tuple(getattr(parser, "default_tags", ()) or ()),
    )
    contract.validate()
    return True
