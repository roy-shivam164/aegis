# 🧠 AEGIS — Adaptive Evolving General Intelligence System

> *"The AI that learns you, improves itself, and thinks ahead — so you don't have to."*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-red?logo=qdrant)](https://qdrant.tech)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-purple)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AEGIS** is a JARVIS-like personal intelligence system built on top of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research, with **Qdrant** as the semantic memory backbone. Built for the **Qdrant "Think Outside the Bot" Hackathon 2026**.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AEGIS SYSTEM                                  │
│                                                                      │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────────────┐   │
│  │  Brain 1    │   │   Brain 2    │   │       Brain 3           │   │
│  │ SkillForge  │   │  MirrorSelf  │   │    ShadowReader         │   │
│  │             │   │              │   │                         │   │
│  │ Learn from  │   │ Learn YOU —  │   │ Analyze others —        │   │
│  │ failures,   │   │ habits, mood,│   │ build personality       │   │
│  │ self-evolve │   │ proactive    │   │ profiles, infer motives │   │
│  │ skill docs  │   │ reminders    │   │                         │   │
│  └──────┬──────┘   └──────┬───────┘   └────────────┬────────────┘   │
│         │                 │                         │                │
│         └─────────────────┴─────────────────────────┘                │
│                           │                                          │
│              ┌────────────▼────────────┐                             │
│              │  Proactive Heartbeat    │                             │
│              │  Engine (Hermes Cron)   │                             │
│              │  6 trigger types        │                             │
│              └────────────┬────────────┘                             │
│                           │                                          │
│              ┌────────────▼────────────┐                             │
│              │  Hermes Gateway Layer   │                             │
│              │  Telegram / Discord     │                             │
│              └─────────────────────────┘                             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    QDRANT VECTOR DB                          │    │
│  │  failure_traces │ skill_documents │ user_life_log            │    │
│  │  user_patterns  │ person_profiles                            │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 What AEGIS Does

### Brain 1: SkillForge 🔨
Self-improving agent that:
- Captures every task failure as a structured vector in Qdrant (`failure_traces`)
- Retrieves semantically similar past failures before retrying
- Evolves skill documents (Hermes markdown playbooks) via LLM-based rewrites
- Tracks skill performance (`success_rate`, `total_uses`) over time

### Brain 2: MirrorSelf 🪞
JARVIS-like personal intelligence that:
- Embeds everything you say into `user_life_log` (dual vectors: text + sentiment)
- Extracts entities, mood, deadlines, category, importance via NLU pipeline
- Distills reusable patterns into `user_patterns` (habits, weaknesses, routines)
- Proactively fires 6 types of reminders/suggestions **without being asked**

### Brain 3: ShadowReader 🕵️
Behavioral analyst that:
- Builds deep personality profiles of people you interact with
- Clusters behavioral vectors into archetypes
- Infers hidden motives from interaction patterns
- Maintains trust scores and motive signal timelines

### Proactive Heartbeat Engine ⚡
Runs on Hermes's cron scheduler every 30 minutes:
1. **Forgotten Pattern** — "You always forget X before Y"
2. **Deadline Proximity** — "Your report is due tomorrow"
3. **Mood Drift** — "You've sounded stressed 4 of last 5 entries"
4. **Recurring Topic** — "You've mentioned switching jobs 6 times"
5. **Appreciation** — "3 tasks nailed today, zero retries — impressive"
6. **Connection Reminder** — "Haven't mentioned Mom in 3 weeks"

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research) |
| Vector Database | [Qdrant](https://qdrant.tech) v1.9+ |
| LLM / Embeddings | OpenAI `text-embedding-3-small` (1536-dim) |
| Sentiment Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| API Backend | FastAPI + Uvicorn |
| Dashboard | React 18 + TypeScript + Vite + Recharts |
| Scheduling | Hermes built-in cron scheduler |
| Notifications | Telegram / Discord via Hermes Gateway |
| Runtime | Python 3.11+ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed
- OpenAI API key

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/aegis.git
cd aegis
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run the automated setup

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Start Qdrant in Docker
- Install Python dependencies
- Initialize all 5 Qdrant collections
- Install Hermes skill documents

### 3. Seed demo data (for hackathon demo)

```bash
python scripts/seed_demo.py
```

### 4. Start the dashboard

```bash
cd dashboard && npm install && npm run dev
# Open http://localhost:5173
```

### 5. Start the API backend

```bash
uvicorn aegis.api.server:app --reload --host 0.0.0.0 --port 8000
```

---

## 🤖 Hermes Integration

### Installing Skills

```bash
chmod +x scripts/install_skills.sh
./scripts/install_skills.sh
```

Then in Hermes chat:
```
/aegis-mirror Log an entry: Had a great workout, feeling energized
/aegis-skillforge Check what tasks I've been failing at
/aegis-shadow Analyze John from work
/aegis-heartbeat Run proactive check now
/aegis-status Show AEGIS system status
```

### SOUL.md Personality

Copy `hermes_config/SOUL.md` to your Hermes config directory to give AEGIS its JARVIS-like personality:

```bash
cp hermes_config/SOUL.md ~/.hermes/SOUL.md
cp hermes_config/CONTEXT.md ~/.hermes/CONTEXT.md
```

### Cron Jobs

Register the heartbeat cron in Hermes:

```bash
cp hermes_config/cron_jobs.yaml ~/.hermes/cron_jobs.yaml
```

---

## 📁 Project Structure

```
aegis/
├── aegis/                   # Core Python package
│   ├── core/
│   │   ├── qdrant_manager.py    # 5 collections, upsert/search helpers
│   │   ├── embedding_engine.py  # OpenAI + sentence-transformers
│   │   └── hermes_integration.py
│   ├── brains/
│   │   ├── skillforge.py        # Brain 1: failure → skill evolution
│   │   ├── mirror_self.py       # Brain 2: life log → proactive JARVIS
│   │   └── shadow_reader.py     # Brain 3: person profiling
│   ├── proactive/
│   │   ├── heartbeat.py         # Main heartbeat loop
│   │   ├── triggers.py          # 6 trigger types
│   │   ├── pattern_distiller.py # Cluster life_log → patterns
│   │   └── notification_sender.py
│   ├── analysis/
│   │   ├── behavior_cluster.py
│   │   ├── motive_inference.py
│   │   └── archetypes.py
│   └── api/
│       └── server.py            # FastAPI dashboard backend
├── hermes_skills/           # Copy to ~/.hermes/skills/aegis/
├── hermes_config/           # SOUL.md, CONTEXT.md, cron_jobs.yaml
├── dashboard/               # React+TS JARVIS dashboard
├── scripts/                 # Setup, seed, install helpers
└── docs/
    └── architecture.md
```

---

## 🎬 Demo

> 📹 **[Demo Video Placeholder]** — 3-minute walkthrough showing:
> 1. Agent failing a task → failure stored in Qdrant
> 2. Agent retrieving similar past failure → retrying with evolved skill
> 3. Life log entry → immediate proactive reminder fires
> 4. Person analysis → motive profile visualized in dashboard

### Screenshots

<!-- Add screenshots here -->

---

## 🏆 Hackathon Info

- **Event**: Qdrant "Think Outside the Bot" Hackathon 2026
- **Track**: Agent + Vector Memory
- **Key Innovation**: First system to combine Hermes GEPA skill evolution + Qdrant semantic failure matching + proactive JARVIS-like life intelligence in a single unified architecture

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for the Qdrant Hackathon 2026*
