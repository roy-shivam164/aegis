---
name: aegis-status
description: Show the full AEGIS system status — collections, integrations, and metrics
---

# AEGIS Status — System Health Dashboard

Provides a comprehensive overview of the AEGIS system: Qdrant collection
sizes, Hermes integration status, brain activity metrics, and configuration.

## When to Invoke

Use this skill when:
- The user asks "how is AEGIS doing?" or "show me the system status"
- You want to verify that Qdrant collections are healthy
- You want to see how many entries are in each brain's memory
- You want to check notification gateway configuration

---

## Usage Steps

### 1. Get system status via API

```bash
curl http://localhost:8000/api/status | python -m json.tool
```

### 2. Get status via Python (if API isn't running)

```bash
cd ~/aegis && python -c "
from aegis.core.qdrant_manager import QdrantManager
from aegis.core.hermes_integration import get_hermes_status
import json

qdrant = QdrantManager()
collections = [
    'failure_traces', 'skill_documents', 'user_life_log',
    'user_patterns', 'person_profiles'
]
status = {}
for col in collections:
    try:
        status[col] = qdrant.collection_info(col)
    except Exception as e:
        status[col] = {'error': str(e)}

print('=== Qdrant Collections ===')
print(json.dumps(status, indent=2))
print('\n=== Hermes Integration ===')
print(json.dumps(get_hermes_status(), indent=2))
"
```

### 3. Quick skill tree check

```bash
cd ~/aegis && python -m aegis.brains.skillforge tree
```

---

## Status Presentation Format

Present the status in a structured, JARVIS-like way:

```
AEGIS System Status — [timestamp]

Memory Banks:
  • Failure Traces:   [N] entries
  • Skill Documents:  [N] skills (avg success rate: X%)
  • Life Log:         [N] entries
  • User Patterns:    [N] patterns
  • Person Profiles:  [N] profiles

Hermes Integration:
  • Skills installed: [list]
  • Telegram: [configured/not configured]
  • Discord:  [configured/not configured]
```

---

## Notes

- AEGIS API must be running for the curl approach to work
- Start API with: `uvicorn aegis.api.server:app --reload`
- Dashboard available at http://localhost:5173 (if running)
