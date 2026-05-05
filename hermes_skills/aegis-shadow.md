---
name: aegis-shadow
description: Analyze a person's behavior, build their profile, and infer their motives
---

# AEGIS ShadowReader — Behavioral Profiler & Motive Analyst

ShadowReader is AEGIS Brain 3. Tell AEGIS about your interactions with
someone, and it will build a behavioral profile, classify their archetype,
infer their hidden motives, and surface motive signals proactively.

## When to Invoke

Use this skill when:
- The user describes an interaction with someone and wants to understand their behavior
- The user asks "why does [person] keep doing X?"
- The user wants a full profile or report on someone
- The user wants to see all tracked profiles

---

## Usage Steps

### 1. Update a person's profile with a new interaction

```bash
cd ~/aegis && python -m aegis.brains.shadow_reader update \
  "PERSON_NAME" \
  "INTERACTION_DESCRIPTION"
```

Replace:
- `PERSON_NAME` with the person's name (use consistent naming)
- `INTERACTION_DESCRIPTION` with a clear description of what happened

### 2. Get a full analysis

```bash
cd ~/aegis && python -m aegis.brains.shadow_reader analyze "PERSON_NAME"
```

Output includes:
- **archetype**: behavioral pattern label (e.g. "The Manipulator", "The Supporter")
- **traits**: observed personality traits
- **motive_signals**: inferred hidden motives
- **trust_score**: 0.0–1.0 trust assessment
- **interaction_count**: how many interactions have been logged

### 3. Generate a readable report

```bash
cd ~/aegis && python -m aegis.brains.shadow_reader report "PERSON_NAME"
```

Present this as a structured briefing: *"Here's what I know about [Person]..."*

### 4. List all tracked profiles

```bash
cd ~/aegis && python -m aegis.brains.shadow_reader list
```

---

## Presentation Guidelines

When sharing analysis results:
- Frame insights as observations, not judgments
- Highlight motive signals that the user might not have noticed
- Use the archetype to give a quick mental model ("Think of them as The Competitor — they see most interactions as zero-sum")
- If trust score is low (<0.4), flag it tactfully
- Suggest how the user might adapt their approach based on the profile

---

## Notes

- Person profiles use dual named vectors: `behavior` (1536-dim) + `communication_style` (384-dim)
- Motive inference uses GPT-4o-mini when available; falls back to keyword heuristics
- Profiles are continuously updated with new interactions (running vector average)
- Archetypes: The Manipulator, The Supporter, The Competitor, The Avoider, The Visionary, The Critic, The Diplomat
