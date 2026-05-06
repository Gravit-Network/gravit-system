import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@pytest.fixture
def sample_hypothesis():
    return {
        "hypothesis_id": "sample-123",
        "hypothesis": "Test hypothesis for unit tests",
        "confidence": 0.85,
        "provenance": "test-agent",
        "evidence": ["evidence-1", "evidence-2"],
        "timestamp": "2026-05-04T00:00:00Z"
    }


@pytest.fixture
def sample_consensus_result():
    return {
        "fixed_point": [0.7, 0.3],
        "iterations": 42,
        "converged": True,
        "final_divergence": 1e-7,
        "byzantine_fraction": 0.1
    }
