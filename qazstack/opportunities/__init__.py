"""Reusable opportunity-radar contracts for QAZ.FUND."""

from .geofit import GeoFitResult, evaluate_geo_fit
from .models import OpportunityRecord, SourceContract

__all__ = [
    "GeoFitResult",
    "OpportunityRecord",
    "SourceContract",
    "evaluate_geo_fit",
]
