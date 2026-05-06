"""
GQRVP Consensus Service

Implements the Gravit Quantum Resilient Verification Protocol.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

try:
    from gravit_truth_consensus.consensus import run_consensus, kl_divergence
    from gravit_truth_consensus.graph import create_erdos_renyi_graph
    GTC_AVAILABLE = True
except ImportError:
    GTC_AVAILABLE = False
    print("Warning: gravit-truth-consensus not installed. Using fallback.")


app = FastAPI(title="Consensus Service", version="1.0.0")


class ConsensusRequest(BaseModel):
    hypothesis_id: str
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    n_agents: int = Field(default=100, ge=1, le=10000)
    n_hypotheses: int = Field(default=3, ge=2, le=100)
    max_iterations: int = Field(default=1000, ge=1, le=100000)
    tolerance: float = Field(default=1e-6, ge=1e-10, le=1e-3)
    byzantine_fraction: float = Field(default=0.0, ge=0.0, le=0.49)
    learning_rate: float = Field(default=0.1, ge=0.01, le=1.0)
    mixing_rate: float = Field(default=0.3, ge=0.01, le=1.0)


class ConsensusResponse(BaseModel):
    hypothesis_id: str
    fixed_point: List[float]
    iterations: int
    converged: bool
    final_divergence: float
    byzantine_fraction: float
    contamination_bound: Optional[float] = None
    consensus_time_ms: float
    timestamp: str


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gtc_available": GTC_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }


def _hypotheses_to_signals(hypotheses: List[Dict[str, Any]], n_agents: int, n_hypotheses: int) -> np.ndarray:
    signals = np.zeros((n_agents, n_hypotheses))
    for i, hyp in enumerate(hypotheses[:n_hypotheses]):
        confidence = hyp.get('confidence', 0.5)
        signals[:, i] = np.log(confidence / (1 - confidence))
    return signals


async def _run_fallback(
    graph: np.ndarray,
    signals: np.ndarray,
    max_iterations: int,
    tolerance: float,
    byzantine_fraction: float,
    learning_rate: float,
    mixing_rate: float
) -> Dict[str, Any]:
    n_agents, n_hypotheses = signals.shape

    beliefs = np.ones((n_agents, n_hypotheses)) / n_hypotheses

    n_byzantine = int(n_agents * byzantine_fraction)
    byzantine_indices = np.random.choice(n_agents, n_byzantine, replace=False) if n_byzantine > 0 else []

    prev_beliefs = beliefs.copy()

    for i in range(max_iterations):
        beliefs = beliefs * np.exp(learning_rate * signals)
        beliefs = beliefs / beliefs.sum(axis=1, keepdims=True)
        beliefs = (1 - mixing_rate) * beliefs + mixing_rate * (graph @ beliefs)

        for idx in byzantine_indices:
            beliefs[idx] = np.random.dirichlet(np.ones(n_hypotheses))

        if i > 0:
            divergence = float(np.mean([
                np.sum(beliefs[j] * np.log(beliefs[j] / (prev_beliefs[j] + 1e-12)))
                for j in range(n_agents)
            ]))
            if divergence < tolerance:
                return {
                    "fixed_point": beliefs[0],
                    "iterations": i,
                    "converged": True,
                    "final_divergence": divergence,
                    "contamination_bound": None
                }
        prev_beliefs = beliefs.copy()

    divergence = float(np.mean([
        np.sum(beliefs[j] * np.log(beliefs[j] / (prev_beliefs[j] + 1e-12)))
        for j in range(n_agents)
    ]))

    return {
        "fixed_point": beliefs[0],
        "iterations": max_iterations,
        "converged": False,
        "final_divergence": divergence,
        "contamination_bound": None
    }


@app.post("/api/v1/consensus", response_model=ConsensusResponse)
async def run_consensus_endpoint(request: ConsensusRequest):
    start_time = time.time()

    try:
        signals = _hypotheses_to_signals(request.hypotheses, request.n_agents, request.n_hypotheses)
        graph = create_erdos_renyi_graph(request.n_agents, p=0.3)

        if GTC_AVAILABLE:
            result = run_consensus(
                graph=graph,
                signals=signals,
                max_iter=request.max_iterations,
                tol=request.tolerance,
                beta=request.byzantine_fraction,
                eta=request.learning_rate,
                gamma=request.mixing_rate
            )
        else:
            result = await _run_fallback(
                graph=graph,
                signals=signals,
                max_iterations=request.max_iterations,
                tolerance=request.tolerance,
                byzantine_fraction=request.byzantine_fraction,
                learning_rate=request.learning_rate,
                mixing_rate=request.mixing_rate
            )

        elapsed_ms = (time.time() - start_time) * 1000

        return ConsensusResponse(
            hypothesis_id=request.hypothesis_id,
            fixed_point=result["fixed_point"].tolist(),
            iterations=result["iterations"],
            converged=result["converged"],
            final_divergence=result["final_divergence"],
            byzantine_fraction=request.byzantine_fraction,
            contamination_bound=result.get("contamination_bound"),
            consensus_time_ms=elapsed_ms,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
