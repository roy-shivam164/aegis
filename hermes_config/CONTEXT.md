# AEGIS Project Context
#
# Place this file at ~/.hermes/CONTEXT.md so Hermes understands the
# AEGIS system architecture and can make intelligent decisions about
# which brain to use for each request.

---

## What AEGIS Is

AEGIS (Adaptive Evolving General Intelligence System) is a personal intelligence
layer running on top of Hermes Agent. It consists of three interconnected brains,
all backed by Qdrant vector memory:

### Brain 1: SkillForge (`/aegis-skillforge`)
- Learns from task failures stored as vectors in Qdrant
- Retrieves similar past failures before retrying
- Evolves skill documents (Hermes playbooks) via LLM rewriting
- Location: `~/aegis/aegis/brains/skillforge.py`

### Brain 2: MirrorSelf (`/aegis-mirror`)
- Logs everything the user shares (mood, entities, deadlines)
- Dual-vector storage: text (1536-dim) + sentiment (384-dim)
- Proactively surfaces 6 trigger types without being asked
- Location: `~/aegis/aegis/brains/mirror_self.py`

### Brain 3: ShadowReader (`/aegis-shadow`)
- Builds behavioral profiles of people the user interacts with
- Classifies into archetypes (The Manipulator, The Supporter, etc.)
- Infers hidden motives via LLM analysis
- Location: `~/aegis/aegis/brains/shadow_reader.py`

### Proactive Heartbeat Engine (`/aegis-heartbeat`)
- Runs every 30 minutes via Hermes cron
- Orchestrates all 6 trigger checks
- Dispatches notifications via Telegram/Discord
- Location: `~/aegis/aegis/proactive/heartbeat.py`

---

## Qdrant Collections

| Collection | Vectors | Purpose |
|---|---|---|
| `failure_traces` | 1536-dim COSINE | Task failure history |
| `skill_documents` | 1536-dim COSINE | Evolved skill playbooks |
| `user_life_log` | text(1536) + sentiment(384) | Life entries |
| `user_patterns` | 1536-dim COSINE | Detected behavioral patterns |
| `person_profiles` | behavior(1536) + comm_style(384) | Person profiles |

---

## Active Services

- **Qdrant**: http://localhost:6333
- **AEGIS API**: http://localhost:8000
- **Dashboard**: http://localhost:5173

---

## How to Use AEGIS Skills

```
/aegis-mirror [text to log]
/aegis-skillforge [task description] [error info]
/aegis-shadow [person name] [interaction description]
/aegis-heartbeat
/aegis-status
```

---

## Directory Structure

```
~/aegis/
├── aegis/          # Python package
│   ├── brains/     # Three AEGIS brains
│   ├── core/       # Qdrant + embedding + Hermes bridge
│   ├── proactive/  # Heartbeat + triggers
│   ├── analysis/   # Clustering + motive inference
│   └── api/        # FastAPI backend
├── hermes_skills/  # Skill documents (already installed here)
└── hermes_config/  # SOUL.md, CONTEXT.md, cron_jobs.yaml
```
