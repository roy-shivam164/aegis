---
name: aegis-mirror
description: Log a life entry and get proactive insights from AEGIS MirrorSelf brain
---

# AEGIS MirrorSelf — Life Logger & Proactive JARVIS Intelligence

MirrorSelf is AEGIS Brain 2. It learns your life patterns, moods, habits,
and routines from everything you share. It then proactively surfaces reminders,
suggestions, and appreciation — without being asked. Just like JARVIS.

## When to Invoke

Use this skill when:
- You want to log something from your day (a thought, an event, a feeling)
- You want to see what proactive suggestions AEGIS has for you right now
- You want a snapshot of your current context (mood, topics, deadlines)
- You want to see the patterns AEGIS has detected in your life

---

## Usage Steps

### 1. Log a life entry

```bash
cd ~/aegis && python -m aegis.brains.mirror_self ingest "USER_TEXT_HERE"
```

Replace `USER_TEXT_HERE` with exactly what the user said they want to log.

The output will include:
- **mood**: detected emotional state
- **category**: life domain (health/work/relationship/finance/goal)
- **entities**: people, places, things mentioned
- **importance**: 0.0–1.0 importance score
- **actionable**: whether this implies something to do
- **deadline_mentioned**: any deadline detected in the text

### 2. Run proactive trigger checks

After logging, always run the trigger checks:

```bash
cd ~/aegis && python -m aegis.brains.mirror_self check-triggers
```

If any triggers fire, present them as proactive suggestions with a JARVIS-like tone.
Example: *"By the way — you've mentioned feeling stressed 4 times this week. Everything alright?"*

### 3. Get current context (optional)

```bash
cd ~/aegis && python -m aegis.brains.mirror_self context
```

Use this to personalise responses with the user's current state.

### 4. Distil patterns (weekly)

```bash
cd ~/aegis && python -m aegis.brains.mirror_self patterns
```

Present newly detected patterns with insight: *"I've noticed that when it comes to work, you often feel stressed — this is the 7th time. Might be worth addressing."*

---

## JARVIS Tone Guidelines

When presenting proactive insights:
- Be warm but concise
- Lead with the observation, not a question
- Occasionally express appreciation for accomplishments
- Reference past patterns to show you remember
- Never be preachy or repetitive about the same insight

---

## Notes

- Life log uses dual named vectors: `text` (1536-dim) + `sentiment` (384-dim)
- Up to 10 proactive notifications per day (configurable)
- Patterns are stored in `user_patterns` Qdrant collection
