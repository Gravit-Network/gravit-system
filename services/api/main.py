"""
API Gateway for Gravit Open Network

Routes requests to appropriate microservices.
"""

import httpx
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="Gravit API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_URLS = {
    "generator": "http://generator:8001",
    "validator": "http://validator:8002",
    "consensus": "http://consensus:8003",
    "history": "http://history:8004",
    "eql": "http://eql:8005",
}


class GenerateRequest(BaseModel):
    prompt: str
    llm: str = "grok"
    max_tokens: int = 500


class ValidateRequest(BaseModel):
    hypothesis_id: str
    evidence: list


class ConsensusRequest(BaseModel):
    hypothesis_id: str
    rounds: int = 100


class EQLQueryRequest(BaseModel):
    eql: str


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": SERVICE_URLS
    }


@app.post("/v1/generate")
async def generate_hypothesis(request: GenerateRequest):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['generator']}/generate",
                json=request.dict()
            )
            response.raise_for_status()
            result = response.json()

            await client.post(
                f"{SERVICE_URLS['history']}/api/v1/store",
                json={
                    "hypothesis_id": result.get("hypothesis_id"),
                    "agent": request.llm,
                    "hypothesis": result.get("hypothesis"),
                    "confidence": result.get("confidence"),
                    "metadata": {"prompt": request.prompt}
                }
            )

            return result
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Generator service unavailable: {str(e)}")


@app.post("/v1/validate")
async def validate_hypothesis(request: ValidateRequest):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['validator']}/validate",
                json=request.dict()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Validator service unavailable: {str(e)}")


@app.post("/v1/consensus")
async def run_consensus(request: ConsensusRequest):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            history_response = await client.get(
                f"{SERVICE_URLS['history']}/api/v1/history"
            )
            history_response.raise_for_status()
            history = history_response.json()

            hypothesis_data = None
            for item in history.get("results", []):
                if item.get("hypothesis_id") == request.hypothesis_id:
                    hypothesis_data = item
                    break

            if not hypothesis_data:
                raise HTTPException(status_code=404, detail="Hypothesis not found")

            consensus_response = await client.post(
                f"{SERVICE_URLS['consensus']}/api/v1/consensus",
                json={
                    "hypothesis_id": request.hypothesis_id,
                    "hypotheses": [hypothesis_data],
                    "n_agents": 100,
                    "n_hypotheses": 2,
                    "max_iterations": request.rounds
                }
            )
            consensus_response.raise_for_status()
            consensus_result = consensus_response.json()

            return {
                "hypothesis_id": request.hypothesis_id,
                "consensus": consensus_result
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Consensus service unavailable: {str(e)}")


@app.post("/v1/query")
async def eql_query(request: EQLQueryRequest):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['eql']}/api/v1/query",
                json=request.dict()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"EQL service unavailable: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
