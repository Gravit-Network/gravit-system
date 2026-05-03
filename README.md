# Gravit Open Network — Full System

**Gravit** is a reasoning verification and computation system for autonomous agents. It combines Proof of Reasoning (PoR), mathematical hypothesis validation, and a trust/reputation system for agent networks.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ UI Layer │
│ (React / TypeScript) │
└─────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────┐
│ API Gateway │
│ (FastAPI / gRPC) │
└─────────────────────────────────────────────────────────────┘
│
┌──────────────┬──────────────┬──────────────┬────────────────┐
│ Generator │ Validator │ Consensus │ History │
│ (LLM Int.) │ (PoR Check) │ (GQRVP) │ Keeper │
└──────────────┴──────────────┴──────────────┴────────────────┘
│
┌─────────────────────────────────────────────────────────────┐
│ EQL Query Engine │
└─────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
gravit-system/
├── services/ # Microservices
│ ├── generator/ # LLM integration (Grok, GPT, Claude)
│ ├── validator/ # PoR validation
│ ├── consensus/ # GQRVP consensus engine
│ ├── history/ # Temporal trace storage
│ ├── api/ # API Gateway
│ └── eql/ # EQL query language
├── sdk/ # SDK for external services
│ ├── python/
│ └── typescript/
├── ui/ # Frontend application
├── infra/ # Docker configuration
│ ├── docker/
│ └── docker-compose.yml
├── tests/ # Unit and integration tests
├── scripts/ # Deployment scripts
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Gravit-Network/gravit-system
cd gravit-system
docker-compose up --build
curl http://localhost:8000/health
```

### 2. Start all services with Docker Compose

```bash
docker-compose up --build
```

### 3. Verify the system is running

```bash
curl http://localhost:8000/health
```

## API Examples

### Generate a hypothesis

```bash
POST /v1/generate
Content-Type: application/json

{
  "prompt": "Will AI surpass human intelligence by 2030?",
  "llm": "grok"
}
```
Response:
```json
{
  "hypothesis_id": "hyp-123",
  "hypothesis": "AI will surpass human intelligence by 2030...",
  "confidence": 0.85,
  "provenance": "grok-3"
}
```

### Submit hypothesis for validation

```bash
POST /v1/validate
Content-Type: application/json

{
  "hypothesis_id": "hyp-123",
  "evidence": [...]
}
```

### Request consensus

```bash
POST /v1/consensus
Content-Type: application/json

{
  "hypothesis_id": "hyp-123",
  "rounds": 100
}
```
Response:
```json
{
  "consensus": {
    "true_probability": 0.78,
    "byzantine_fraction": 0.12,
    "iterations": 47,
    "fixed_point_reached": true
  }
}
```

### Query history with EQL

```bash
POST /v1/query
Content-Type: application/json

{
  "eql": "FIND traces WHERE agent = \"grok\" AND consensus > 0.7"
}
```

## EQL (Epistemic Query Language)

EQL allows you to query the reasoning history:

```sql
-- Find all hypotheses from Grok with consensus > 0.8
FIND traces WHERE agent = "grok" AND consensus > 0.8

-- Get the evolution of a specific hypothesis
TRACE hyp-123 OVER TIME

-- Find contradicting hypotheses
FIND traces WHERE contradicts(hyp-123) = true
```

## Trust and Reputation System

Trust scoring: Evaluates hypotheses based on consistency, evidence strength, and structure

Staking: Agents stake GRAVIT tokens to participate

Slashing: Malicious behavior results in stake reduction

Reputation: Long-term agent reputation influences consensus weight

## Dependencies

This system depends on:

gravit-truth-consensus — Mathematical consensus core

gravitnet — Protocol specification

## Development

### Run tests

```bash
pytest tests/
```

### Run a single service

```bash
cd services/consensus
python -m gravit.consensus
```

### Build SDK

```bash
cd sdk/python
python setup.py build
```

## License

Apache 2.0 with Commons Clause — see LICENSE
