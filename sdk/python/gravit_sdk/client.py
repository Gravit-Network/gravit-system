"""
Gravit API Client
"""

import httpx
from typing import Optional, List, Dict, Any

from gravit_sdk.models import Hypothesis, ConsensusResult, ValidationResult, EQLQuery, EQLResult


class GravitClient:
    """
    Client for Gravit Open Network API.

    Example:
        client = GravitClient(base_url="https://api.gravitnetwork.org")
        hypothesis = client.generate_hypothesis(
            prompt="Will AI surpass human intelligence?",
            llm="grok"
        )
        consensus = client.run_consensus(hypothesis.hypothesis_id)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers()
        )

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate_hypothesis(
        self,
        prompt: str,
        llm: str = "grok",
        max_tokens: int = 500
    ) -> Hypothesis:
        response = self._client.post(
            "/v1/generate",
            json={
                "prompt": prompt,
                "llm": llm,
                "max_tokens": max_tokens
            }
        )
        response.raise_for_status()
        data = response.json()
        return Hypothesis(**data)

    def validate_hypothesis(
        self,
        hypothesis_id: str,
        evidence: List[Dict[str, Any]]
    ) -> ValidationResult:
        response = self._client.post(
            "/v1/validate",
            json={
                "hypothesis_id": hypothesis_id,
                "evidence": evidence
            }
        )
        response.raise_for_status()
        data = response.json()
        return ValidationResult(**data)

    def run_consensus(
        self,
        hypothesis_id: str,
        rounds: int = 100
    ) -> ConsensusResult:
        response = self._client.post(
            "/v1/consensus",
            json={
                "hypothesis_id": hypothesis_id,
                "rounds": rounds
            }
        )
        response.raise_for_status()
        data = response.json()
        return ConsensusResult(**data.get("consensus", {}))

    def query(self, eql: str) -> EQLResult:
        response = self._client.post(
            "/v1/query",
            json={"eql": eql}
        )
        response.raise_for_status()
        data = response.json()
        return EQLResult(**data)

    def get_health(self) -> Dict[str, Any]:
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
