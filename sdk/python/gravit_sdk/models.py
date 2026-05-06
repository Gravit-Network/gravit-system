"""Data models for Gravit Python SDK."""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from datetime import datetime


@dataclass
class Hypothesis:
    hypothesis_id: str
    hypothesis: str
    confidence: float
    provenance: str
    timestamp: str


@dataclass
class ConsensusResult:
    fixed_point: List[float]
    iterations: int
    converged: bool
    final_divergence: float
    consensus_time_ms: float


@dataclass
class ValidationResult:
    hypothesis_id: str
    validated: bool
    score: float
    reasoning: str
    timestamp: str


@dataclass
class EQLResult:
    results: List[Dict[str, Any]]
    query_type: str
    count: int
    timestamp: str
