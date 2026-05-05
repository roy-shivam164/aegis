# AEGIS Architecture Deep-Dive

## Overview

AEGIS is structured as an **extension layer** over [Hermes Agent](https://github.com/NousResearch/hermes-agent). It adds three connected "brains" backed by Qdrant vector memory, orchestrated by a proactive heartbeat engine.

```
User (Telegram / Discord / CLI)
         │
         ▼
┌─────────────────────────────┐
│      Hermes Agent           │  ← Conversation layer, skill routing, cron
│   (NousResearch/hermes)     │
└────────────┬────────────────┘
             │  invokes
             ▼
┌─────────────────────────────────────────────────────────┐
│                    AEGIS Extension Layer                 │
│                                                         │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ SkillForge │  │ MirrorSelf  │  │  ShadowReader    │  │
│  │ (Brain 1)  │  │  (Brain 2)  │  │   (Brain 3)      │  │
│  └─────┬──────┘  └──────┬──────┘  └────────┬─────────┘  │
│        │                │                  │             │
│        └────────────────┴──────────────────┘             │
│                         │                                │
│          ┌──────────────▼──────────────┐                 │
│          │   Proactive Heartbeat Engine │                 │
│          │   (6 trigger types)          │                 │
│          └──────────────┬──────────────┘                 │
│                         │                                │
│          ┌──────────────▼──────────────┐                 │
│          │    Core Services            │                 │
│          │  QdrantManager              │                 │
│          │  EmbeddingEngine            │                 │
│          │  HermesIntegration          │                 │
│          └──────────────┬──────────────┘                 │
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
             ┌────────────────────────┐
             │     Qdrant v1.9+       │
             │  5 vector collections  │
             └────────────────────────┘
```

---

## Hermes Agent Integration Points

### 1. Skills System (`~/.hermes/skills/aegis/`)

Hermes reads skill documents from `~/.hermes/skills/` and makes them
invocable via `/skillname`. AEGIS provides 5 skill documents:

| Skill | Description |
|---|---|
| `aegis-skillforge.md` | Failure capture, similar failure retrieval, skill evolution |
| `aegis-mirror.md` | Life entry logging, NLU extraction, proactive triggers |
| `aegis-shadow.md` | Person profiling, archetype classification, motive inference |
| `aegis-heartbeat.md` | Manual heartbeat trigger |
| `aegis-status.md` | System health overview |

### 2. SOUL.md Personality

`hermes_config/SOUL.md` defines the JARVIS-like persona that Hermes uses to shape all responses. Key characteristics:
- Proactive (surfaces insights without being asked)
- Warm but direct
- Slight wit
- References past patterns

### 3. Cron Scheduler

`hermes_config/cron_jobs.yaml` registers recurring jobs:
- **Every 30 min**: Full heartbeat cycle
- **Daily 8am**: Pattern distillation
- **Monday 9am**: Skill tree report

---

## Vector Collections Design

### `failure_traces` (1536-dim COSINE)

Stores every task attempt (success or failure). The embedding captures the combined task description + error information for rich semantic similarity matching.

**Key insight**: By embedding `"Task: {desc}\nError: {error}"` together, we capture the semantic relationship between *what was attempted* and *what went wrong* in a single vector. This enables Qdrant to find failures that are similar in both task type AND failure mode.

### `skill_documents` (1536-dim COSINE)

Stores the markdown content of skill documents as vectors. When searching for a relevant skill, we embed the current task and find the most semantically similar skill document.

**Evolution**: Each time a skill is evolved (rewritten by LLM), the new vector is upserted at the same ID, keeping the point count stable while the semantic content drifts toward more reliable playbooks.

### `user_life_log` (named vectors: text 1536, sentiment 384)

Dual-vector design serves two distinct search modes:
- **`text` vector (1536)**: Semantic search over content ("find entries about job switching")
- **`sentiment` vector (384)**: Fast mood-space search ("find entries with similar emotional tone")

The 384-dim sentiment vector uses `all-MiniLM-L6-v2` which is faster and captures emotional nuance well in lower dimensions.

### `user_patterns` (1536-dim COSINE)

Distilled from life log clusters. Patterns are updated incrementally — a running distillation process groups entries by (category, mood) and entity frequency to surface recurring themes.

### `person_profiles` (named vectors: behavior 1536, communication_style 384)

- **`behavior` vector**: Captures *what this person does* (actions, patterns, strategies)
- **`communication_style` vector**: Captures *how they communicate* (tone, directness, register)

Profiles use a running vector average blend: when a new interaction arrives, the new vector is blended with the existing one weighted by interaction count, so early interactions don't permanently dominate the profile.

---

## Brain Architecture Details

### Brain 1: SkillForge — Learning Loop

```
Task attempt ──→ Failure? ──→ embed(task + error) ──→ store in failure_traces
                                      │
                              On next similar task:
                                      │
                              search failure_traces
                                      │
                              retrieve similar past failures
                                      │
                              use failure context to inform retry
                                      │
                              success? ──→ LLM rewrite skill doc
                                      │
                              store evolved skill in skill_documents
```

**GEPA (Gradient-free Evolutionary Prompt Adaptation)**: The skill evolution step uses GPT-4o-mini to rewrite the skill markdown, guided by:
1. What the current skill doc says
2. What went wrong (failure trace)
3. What worked in similar successful attempts

### Brain 2: MirrorSelf — NLU Pipeline

```
raw_text
   │
   ├── _detect_mood()       → "stressed", "happy", "motivated"...
   ├── _detect_category()   → "health", "work", "finance"...
   ├── _extract_entities()  → ["John", "Sarah", "Rust"]...
   ├── _score_importance()  → 0.0–1.0
   ├── _is_actionable()     → True/False
   └── _extract_deadline()  → "tomorrow", "next Friday"...
   │
   ├── embed_text() → 1536-dim OpenAI embedding
   └── embed_sentiment() → 384-dim MiniLM embedding
   │
   └── store_life_log_entry() → Qdrant user_life_log
```

**6 Proactive Trigger Types**:

| Trigger | Logic |
|---|---|
| `forgotten_pattern` | Count "forgot" in recent 50 entries; fire if same subject ≥2 times |
| `deadline_proximity` | Check for "tomorrow/today" in deadline fields of recent entries |
| `mood_drift` | If ≥3 of last 5 entries are negative mood, fire |
| `recurring_topic` | Count entity/phrase frequency; fire if ≥3 occurrences of goal phrase |
| `appreciation` | Count today's successful failure traces; fire if ≥3 |
| `connection_reminder` | Check person_profiles not mentioned in life log for ≥14 days |

### Brain 3: ShadowReader — Profile Architecture

```
interaction_text
   │
   ├── embed_text() → behavior_vector (1536-dim)
   ├── embed_sentiment() → communication_style_vector (384-dim)
   ├── classify_archetype() → trait keywords → archetype label
   └── infer_motives() → GPT-4o-mini or keyword fallback
   │
   └── store / blend with existing profile in person_profiles
```

**Running Vector Average**: 
```
blended = old_vector * (n-1)/n + new_vector * 1/n
```
where `n` is the interaction count. This gives recent interactions slightly more weight while preventing single interactions from dominating old profiles.

---

## FastAPI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/api/status` | System-wide status |
| GET | `/api/skill-tree` | SkillForge skill tree |
| GET | `/api/life-log?limit=N` | Recent life log entries |
| GET | `/api/patterns` | User patterns |
| GET | `/api/profiles` | Person profile summaries |
| GET | `/api/profiles/{name}` | Full profile analysis |
| POST | `/api/ingest` | Ingest new life log entry |
| POST | `/api/heartbeat` | Manual heartbeat trigger |
| POST | `/api/capture-failure` | Record failure trace |

---

## Scalability Notes

- All 5 Qdrant collections use COSINE distance — appropriate for normalized OpenAI embeddings
- Collections with named vectors (`user_life_log`, `person_profiles`) support independent search over each named vector without retrieving both
- The running vector average for person profiles scales to thousands of interactions without storage growth
- Pattern distillation is an incremental process — runs in O(n) over recent entries
- The daily notification cap prevents notification fatigue while still being proactive
