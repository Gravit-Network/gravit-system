import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from services.consensus.main import app, ConsensusRequest


client = TestClient(app)


class TestConsensusAPI:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "gtc_available" in data

    def test_consensus_endpoint_valid_request(self):
        request_data = {
            "hypothesis_id": "test-123",
            "hypotheses": [
                {"hypothesis": "Test hypothesis 1", "confidence": 0.8},
                {"hypothesis": "Test hypothesis 2", "confidence": 0.6}
            ],
            "n_agents": 50,
            "n_hypotheses": 2,
            "max_iterations": 100,
            "tolerance": 1e-6,
            "byzantine_fraction": 0.1
        }

        response = client.post("/api/v1/consensus", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["hypothesis_id"] == "test-123"
        assert "fixed_point" in data
        assert "iterations" in data


class TestConsensusEngine:
    @pytest.mark.asyncio
    async def test_hypotheses_to_signals(self):
        from services.consensus.main import _hypotheses_to_signals

        hypotheses = [
            {"hypothesis": "H1", "confidence": 0.9},
            {"hypothesis": "H2", "confidence": 0.5}
        ]

        signals = _hypotheses_to_signals(hypotheses, n_agents=10, n_hypotheses=2)

        assert signals.shape == (10, 2)
        assert signals[0, 0] > 0
        assert signals[0, 1] == 0
