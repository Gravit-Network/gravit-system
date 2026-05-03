# Gravit Open Network — Full System

**Gravit** is a reasoning verification and computation system for autonomous agents. It combines Proof of Reasoning (PoR), mathematical hypothesis validation, and a trust/reputation system for agent networks.

## System Architecture

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

## Repository Structure

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

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Gravit-Network/gravit-system
cd gravit-system
docker-compose up --build
curl http://localhost:8000/health

