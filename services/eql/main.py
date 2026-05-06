"""
EQL Service for Gravit Open Network

Provides query interface for reasoning history using EQL.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from parser import EQLParser, EQLExecutor, EQLSyntaxError


app = FastAPI(title="EQL Service", version="1.0.0")

_history_store: List[Dict[str, Any]] = []


class EQLQueryRequest(BaseModel):
    eql: str


class StoreRequest(BaseModel):
    hypothesis_id: str
    agent: str
    hypothesis: str
    confidence: float
    consensus: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/v1/query")
async def execute_query(request: EQLQueryRequest):
    try:
        parser = EQLParser()
        query = parser.parse(request.eql)

        executor = EQLExecutor(_history_store)
        results = executor.execute(query)

        return {
            "results": results,
            "query_type": query.type,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except EQLSyntaxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/store")
async def store_trace(request: StoreRequest):
    trace = request.dict()
    trace["timestamp"] = datetime.utcnow().isoformat()
    _history_store.append(trace)

    return {"status": "stored", "id": len(_history_store) - 1}


@app.get("/api/v1/history")
async def get_history(limit: int = 100, offset: int = 0):
    return {
        "total": len(_history_store),
        "results": _history_store[offset:offset + limit]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
