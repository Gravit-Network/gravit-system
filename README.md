# Gravit Open Network — Full System

**Gravit** is a reasoning verification and computation system for autonomous agents. It combines Proof of Reasoning (PoR), mathematical hypothesis validation, and a trust/reputation system for agent networks.

## Quick Start

```bash
git clone https://github.com/Gravit-Network/gravit-system
cd gravit-system
docker-compose -f infra/docker-compose.yml up --build
curl http://localhost:8000/health
```

## API Examples

### Generate a hypothesis

```bash
POST /v1/generate
{
  "prompt": "Will AI surpass human intelligence by 2030?",
  "llm": "grok"
}
```

### Run consensus

```bash
POST /v1/consensus
{
  "hypothesis_id": "hyp-123",
  "rounds": 100
}
```

### Query with EQL

```bash
POST /v1/query
{
  "eql": "FIND traces WHERE agent = \"grok\" AND consensus > 0.7"
}
```

## License

Apache 2.0 with Commons Clause
