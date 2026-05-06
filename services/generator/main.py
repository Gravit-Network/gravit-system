"""
PoR Validator Service for Gravit Open Network

Validates hypotheses using Proof of Reasoning.
"""

from typing import List, Dict, Any
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Validator Service", version="1.0.0")


class ValidateRequest(BaseModel):
    hypothesis_id: str
    evidence: List[Dict[str, Any]]


class ValidateResponse(BaseModel):
    hypothesis_id: str
    validated: bool
    score: float
    reasoning: str
    timestamp: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/validate", response_model=ValidateResponse)
async def validate_hypothesis(request: ValidateRequest):
    evidence_score = min(1.0, len(request.evidence) * 0.2) if request.evidence else 0.3
    validated = evidence_score > 0.5

    return ValidateResponse(
        hypothesis_id=request.hypothesis_id,
        validated=validated,
        score=evidence_score,
        reasoning=f"Validation based on {len(request.evidence)} evidence items. Score: {evidence_score:.2f}",
        timestamp=datetime.utcnow().isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
