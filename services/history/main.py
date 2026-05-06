"""
History Keeper Service for Gravit Open Network

Stores and retrieves temporal traces with Merkle tree integrity.
"""

import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="History Service", version="1.0.0")

_history_store: List[Dict[str, Any]] = []
_merkle_tree: List[str] = []


class StoreRequest(BaseModel):
    hypothesis_id: str
    agent: str
    hypothesis: str
    confidence: float
    consensus: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


def _get_merkle_root() -> str:
    if not _merkle_tree:
        return hashlib.sha256(b"empty").hexdigest()

    nodes = _merkle_tree.copy()
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        nodes = [
            hashlib.sha256((nodes[i] + nodes[i + 1]).encode()).hexdigest()
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0]


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/v1/store")
async def store_trace(request: StoreRequest):
    trace = request.dict()
    trace["timestamp"] = datetime.utcnow().isoformat()

    trace_str = json.dumps(trace, sort_keys=True)
    merkle_hash = hashlib.sha256(trace_str.encode()).hexdigest()
    trace["merkle_hash"] = merkle_hash

    trace_id = len(_history_store)
    _history_store.append(trace)
    _merkle_tree.append(merkle_hash)

    return {
        "status": "stored",
        "id": trace_id,
        "merkle_hash": merkle_hash,
        "merkle_root": _get_merkle_root()
    }


@app.get("/api/v1/history")
async def get_history(limit: int = 100, offset: int = 0, hypothesis_id: Optional[str] = None):
    results = _history_store[offset:offset + limit]

    if hypothesis_id:
        results = [r for r in results if r.get("hypothesis_id") == hypothesis_id]

    return {
        "total": len(_history_store),
        "offset": offset,
        "limit": limit,
        "merkle_root": _get_merkle_root(),
        "results": results
    }


@app.get("/api/v1/history/{trace_id}")
async def get_trace(trace_id: int):
    if trace_id >= len(_history_store):
        raise HTTPException(status_code=404, detail="Trace not found")

    return {
        "trace": _history_store[trace_id],
        "merkle_root": _get_merkle_root()
    }


@app.get("/api/v1/history/verify/{trace_id}")
async def verify_trace(trace_id: int):
    if trace_id >= len(_history_store):
        raise HTTPException(status_code=404, detail="Trace not found")

    trace = _history_store[trace_id]
    stored_hash = trace.get("merkle_hash")

    trace_copy = {k: v for k, v in trace.items() if k != "merkle_hash"}
    computed_hash = hashlib.sha256(json.dumps(trace_copy, sort_keys=True).encode()).hexdigest()

    return {
        "trace_id": trace_id,
        "verified": stored_hash == computed_hash,
        "stored_hash": stored_hash,
        "computed_hash": computed_hash,
        "merkle_root": _get_merkle_root()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
