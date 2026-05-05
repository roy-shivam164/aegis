---
name: aegis-skillforge
description: Capture task failures, find similar past failures, and evolve AEGIS skill documents
---

# AEGIS SkillForge — Self-Improving Agent Skill System

SkillForge is AEGIS Brain 1. It records every failure trace, finds
semantically similar past failures via Qdrant, and evolves skill documents
to help you avoid the same mistakes twice.

## When to Invoke

Use this skill when:
- You want to log that a task failed (so AEGIS can learn from it)
- You want to check if AEGIS has seen similar failures before attempting a task
- You want to view the current skill tree (which skills have evolved, their success rates)
- You want AEGIS to evolve an existing skill document after a failure

---

## Usage Steps

### 1. Capture a failure trace

When a task fails, log it so AEGIS can learn:

```bash
cd ~/aegis && python -m aegis.brains.skillforge ingest \
  "TASK_DESCRIPTION_HERE" \
  "ERROR_INFORMATION_HERE" \
  --type "TASK_TYPE"
```

Replace:
- `TASK_DESCRIPTION_HERE` with what you were trying to do
- `ERROR_INFORMATION_HERE` with what went wrong
- `TASK_TYPE` with a category like `code_generation`, `web_search`, `api_call`

### 2. Check for similar past failures before retrying

Before retrying a difficult task, check what AEGIS has seen before:

```bash
cd ~/aegis && python -m aegis.brains.skillforge check \
  "TASK_DESCRIPTION_HERE" \
  --top 5
```

Review the similar failures and their resolutions. Use this intelligence to inform your retry strategy.

### 3. View the skill tree

See all evolved skill documents and their performance metrics:

```bash
cd ~/aegis && python -m aegis.brains.skillforge tree
```

### 4. Present results to user

After running the above commands:
1. Display extracted failure metadata (error category, similar past failures found)
2. If similar failures were found, summarise: *"I've seen something like this before. Here's what went wrong last time and how it was resolved."*
3. If the skill tree shows a relevant skill, use it to guide the retry
4. Offer to evolve the skill document if this is a new failure pattern

---

## Notes

- All failure traces are stored as 1536-dim vectors in Qdrant `failure_traces` collection
- Similarity threshold: 0.75 cosine similarity
- AEGIS becomes more reliable with every failure logged
