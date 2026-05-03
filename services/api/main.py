"""
API Gateway for Gravit System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import uuid
from datetime import datetime

app = FastAPI(title="Gravit Open Network API", version="1.0.0")

# CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (from environment or defaults)
GENERATOR_URL = "http://generator:8001"
VALIDATOR_URL = "http://validator:8002"
CONSENSUS_URL = "http://consensus:8003"
HISTORY_URL = "http://history:8004"
EQL_URL = "http://eql:8005"


class GenerateRequest(BaseModel):
    prompt: str
    llm: str = "grok"
    max_tokens: int = 500


class GenerateResponse(BaseModel):
    hypothesis_id: str
    hypothesis: str
    confidence: float
    provenance: str
    timestamp: datetime


class ValidateRequest(BaseModel):
    hypothesis_id: str
    evidence: List[Dict[str, Any]]


class ConsensusRequest(BaseModel):
    hypothesis_id: str
    rounds: int = 100


class EQLQuery(BaseModel):
    eql: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate_hypothesis(request: GenerateRequest):
    """Generate a hypothesis using an LLM."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GENERATOR_URL}/generate",
            json=request.dict()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Generator failed")

        result = response.json()

    return GenerateResponse(
        hypothesis_id=str(uuid.uuid4()),
        hypothesis=result["hypothesis"],
        confidence=result["confidence"],
        provenance=request.llm,
        timestamp=datetime.now()
    )


@app.post("/v1/validate")
async def validate_hypothesis(request: ValidateRequest):
    """Validate a hypothesis with PoR."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VALIDATOR_URL}/validate",
            json=request.dict()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Validation failed")

        result = response.json()

    # Store in history
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{HISTORY_URL}/store",
            json={
                "hypothesis_id": request.hypothesis_id,
                "validation": result,
                "timestamp": datetime.now().isoformat()
            }
        )

    return result


@app.post("/v1/consensus")
async def run_consensus(request: ConsensusRequest):
    """Run GQRVP consensus on a hypothesis."""
    # Retrieve hypothesis from history
    async with httpx.AsyncClient() as client:
        history_response = await client.get(f"{HISTORY_URL}/get/{request.hypothesis_id}")
        if history_response.status_code != 200:
            raise HTTPException(status_code=404, detail="Hypothesis not found")

        hypothesis_data = history_response.json()

    # Run consensus
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONSENSUS_URL}/run",
            json={
                "hypothesis": hypothesis_data,
                "rounds": request.rounds
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Consensus failed")

        result = response.json()

    # Update history with consensus result
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{HISTORY_URL}/update",
            json={
                "hypothesis_id": request.hypothesis_id,
                "consensus": result,
                "timestamp": datetime.now().isoformat()
            }
        )

    return result


@app.post("/v1/query")
async def eql_query(query: EQLQuery):
    """Execute an EQL query."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EQL_URL}/query",
            json=query.dict()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Query failed")

        return response.json()
