"""
Pattern Distiller — clusters user_life_log entries and extracts
recurring patterns, storing them in ``user_patterns``.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)

_MIN_EVIDENCE_FOR_PATTERN = 2
_MAX_PATTERNS_PER_RUN = 20


def distill_patterns_from_log(qdrant: QdrantManager) -> list[dict[str, Any]]:
    """Cluster life log entries and upsert derived patterns.

    Algorithm:
    1. Fetch all recent life log entries.
    2. Group by ``category`` + ``mood`` combination.
    3. If a combination appears ``>= _MIN_EVIDENCE_FOR_PATTERN`` times,
       synthesise a pattern description and store it.

    Parameters
    ----------
    qdrant:
        Active QdrantManager instance.

    Returns
    -------
    list[dict]
        Newly created / updated pattern records.
    """
    from aegis.core.embedding_engine import embed_text

    entries = qdrant.get_recent_life_log(limit=200)
    if not entries:
        logger.info("No life log entries to distill patterns from")
        return []

    # ── Habit / routine patterns from (category, mood) pairs ─────────────────
    combo_counter: Counter = Counter()
    combo_examples: dict[tuple, list[str]] = {}
    for e in entries:
        key = (e.get("category", "general"), e.get("mood", "neutral"))
        combo_counter[key] += 1
        combo_examples.setdefault(key, []).append(e.get("raw_text", "")[:80])

    new_patterns: list[dict[str, Any]] = []
    count = 0

    for (category, mood), evidence_count in combo_counter.most_common(_MAX_PATTERNS_PER_RUN):
        if evidence_count < _MIN_EVIDENCE_FOR_PATTERN:
            continue
        if count >= _MAX_PATTERNS_PER_RUN:
            break

        # Derive pattern type
        if mood in ("stressed", "sad"):
            pattern_type = "weakness"
        elif mood in ("motivated", "happy"):
            pattern_type = "strength"
        else:
            pattern_type = "routine"

        description = (
            f"When it comes to {category}, you frequently feel {mood} "
            f"(observed {evidence_count} times)."
        )
        confidence = min(0.5 + (evidence_count / 20.0), 0.95)

        vector = embed_text(description)
        pid = qdrant.store_pattern(
            vector=vector,
            pattern_type=pattern_type,
            description=description,
            confidence=round(confidence, 3),
            evidence_count=evidence_count,
            category=category,
        )
        new_patterns.append(
            {
                "id": pid,
                "pattern_type": pattern_type,
                "description": description,
                "confidence": round(confidence, 3),
                "evidence_count": evidence_count,
                "category": category,
                "mood": mood,
            }
        )
        count += 1

    # ── Entity-level habit patterns ───────────────────────────────────────────
    entity_counter: Counter = Counter()
    for e in entries:
        for ent in e.get("entities", []):
            entity_counter[ent] += 1

    for entity, freq in entity_counter.most_common(5):
        if freq >= _MIN_EVIDENCE_FOR_PATTERN + 1:
            description = (
                f"You frequently mention *{entity}* in your logs "
                f"({freq} times) — this appears to be a recurring theme."
            )
            vector = embed_text(description)
            pid = qdrant.store_pattern(
                vector=vector,
                pattern_type="habit",
                description=description,
                confidence=round(min(0.4 + freq / 15.0, 0.9), 3),
                evidence_count=freq,
                category="general",
            )
            new_patterns.append(
                {
                    "id": pid,
                    "pattern_type": "habit",
                    "description": description,
                    "entity": entity,
                    "frequency": freq,
                }
            )

    logger.info("Distilled %d patterns from life log", len(new_patterns))
    return new_patterns
