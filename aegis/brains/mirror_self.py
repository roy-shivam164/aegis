"""
Brain 2: MirrorSelf — Proactive JARVIS-Like Personal Intelligence

MirrorSelf ingests everything the user says, extracts structured metadata
(mood, entities, deadlines, category, importance) via an NLU pipeline,
stores dual-vector entries in Qdrant, distils recurring patterns, and
fires proactive notifications without being asked — just like JARVIS.

Standalone usage
----------------
    python -m aegis.brains.mirror_self ingest "Had a great workout today"
    python -m aegis.brains.mirror_self check-triggers
    python -m aegis.brains.mirror_self context
    python -m aegis.brains.mirror_self patterns
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

from aegis.config import settings
from aegis.core.embedding_engine import embed_sentiment, embed_text
from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)

# ── Mood / sentiment constants ────────────────────────────────────────────────

_MOOD_KEYWORDS: dict[str, list[str]] = {
    "happy": ["great", "awesome", "excited", "happy", "love", "fantastic", "amazing", "joy"],
    "stressed": ["stressed", "overwhelmed", "anxious", "worried", "tired", "exhausted", "burned"],
    "sad": ["sad", "depressed", "lonely", "upset", "down", "miserable", "unhappy"],
    "motivated": ["motivated", "energized", "focused", "productive", "determined", "pumped"],
    "neutral": [],
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "health": ["workout", "gym", "run", "diet", "sleep", "doctor", "sick", "exercise", "calories"],
    "work": ["meeting", "project", "deadline", "boss", "colleague", "office", "client", "report"],
    "relationship": ["friend", "family", "mom", "dad", "partner", "date", "colleague", "dinner"],
    "finance": ["money", "salary", "invest", "expense", "bill", "budget", "savings", "rent"],
    "goal": ["goal", "dream", "plan", "want to", "going to", "next year", "someday"],
}

_DEADLINE_PATTERNS = [
    r"(?:due|deadline|submit|finish|complete)\s+(?:by\s+)?([A-Za-z0-9,\s]+)",
    r"(?:tomorrow|next week|next month|on [A-Za-z]+day)",
    r"in (\d+) (?:days?|weeks?|months?)",
]


class MirrorSelf:
    """Brain 2 — learns the user and proactively surfaces insights."""

    def __init__(self, qdrant: QdrantManager | None = None) -> None:
        """Initialise MirrorSelf.

        Parameters
        ----------
        qdrant:
            Optional pre-constructed ``QdrantManager``.
        """
        self.qdrant = qdrant or QdrantManager()

    # ── Ingestion pipeline ────────────────────────────────────────────────────

    def ingest_entry(self, raw_text: str, source: str = "manual") -> dict[str, Any]:
        """NLU pipeline: extract metadata, embed, and store in Qdrant.

        Parameters
        ----------
        raw_text:
            The user's raw text entry.
        source:
            Origin of the entry (``"manual"``, ``"telegram"``, ``"discord"``).

        Returns
        -------
        dict
            Extracted metadata + Qdrant point ID.
        """
        # ── NLU extraction ─────────────────────────────────────────────────
        mood = _detect_mood(raw_text)
        category = _detect_category(raw_text)
        entities = _extract_entities(raw_text)
        importance = _score_importance(raw_text, mood)
        actionable = _is_actionable(raw_text)
        deadline = _extract_deadline(raw_text)

        # ── Embedding ──────────────────────────────────────────────────────
        text_vector = embed_text(raw_text)
        sentiment_vector = embed_sentiment(raw_text)

        # ── Storage ────────────────────────────────────────────────────────
        point_id = self.qdrant.store_life_log_entry(
            text_vector=text_vector,
            sentiment_vector=sentiment_vector,
            raw_text=raw_text,
            category=category,
            mood=mood,
            entities=entities,
            importance=importance,
            actionable=actionable,
            deadline_mentioned=deadline,
        )

        result = {
            "id": point_id,
            "raw_text": raw_text,
            "source": source,
            "mood": mood,
            "category": category,
            "entities": entities,
            "importance": importance,
            "actionable": actionable,
            "deadline_mentioned": deadline,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(
            "Ingested life log entry [%s] mood=%s category=%s", point_id[:8], mood, category
        )
        return result

    # ── Pattern distillation ──────────────────────────────────────────────────

    def distill_patterns(self) -> list[dict[str, Any]]:
        """Cluster life_log entries and extract recurring user patterns.

        Patterns are stored (or refreshed) in Qdrant ``user_patterns``.

        Returns
        -------
        list[dict]
            List of newly identified / updated pattern records.
        """
        from aegis.proactive.pattern_distiller import distill_patterns_from_log

        return distill_patterns_from_log(self.qdrant)

    # ── Context snapshot ──────────────────────────────────────────────────────

    def get_current_context(self) -> dict[str, Any]:
        """Return a snapshot of the user's current context.

        Returns
        -------
        dict
            Keys: ``recent_mood``, ``dominant_topics``, ``upcoming_deadlines``,
            ``recent_entities``.
        """
        recent = self.qdrant.get_recent_life_log(limit=10)
        if not recent:
            return {"recent_mood": "unknown", "dominant_topics": [], "upcoming_deadlines": []}

        moods = [e.get("mood", "neutral") for e in recent]
        recent_mood = max(set(moods), key=moods.count)

        # Aggregate entities
        all_entities: list[str] = []
        for e in recent:
            all_entities.extend(e.get("entities", []))
        entity_counts: dict[str, int] = {}
        for ent in all_entities:
            entity_counts[ent] = entity_counts.get(ent, 0) + 1
        top_entities = sorted(entity_counts, key=entity_counts.get, reverse=True)[:5]  # type: ignore[arg-type]

        # Deadlines
        deadlines = [
            {"text": e.get("raw_text", "")[:80], "deadline": e.get("deadline_mentioned")}
            for e in recent
            if e.get("deadline_mentioned")
        ]

        categories = [e.get("category", "general") for e in recent]
        dominant_topics = list({c for c in categories if c != "general"})

        return {
            "recent_mood": recent_mood,
            "dominant_topics": dominant_topics,
            "upcoming_deadlines": deadlines,
            "recent_entities": top_entities,
            "entry_count": len(recent),
        }

    # ── Proactive trigger check ───────────────────────────────────────────────

    def check_proactive_triggers(self) -> list[dict[str, Any]]:
        """Run all 6 proactive trigger checks.

        Returns
        -------
        list[dict]
            List of fired trigger notifications (may be empty).
        """
        from aegis.proactive.triggers import (
            check_appreciation,
            check_connection_reminder,
            check_deadline_proximity,
            check_forgotten_pattern,
            check_mood_drift,
            check_recurring_topic,
        )

        fired: list[dict[str, Any]] = []
        checks = [
            check_forgotten_pattern,
            check_deadline_proximity,
            check_mood_drift,
            check_recurring_topic,
            check_appreciation,
            check_connection_reminder,
        ]
        for fn in checks:
            try:
                result = fn(self.qdrant)
                if result:
                    fired.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Trigger %s failed: %s", fn.__name__, exc)

        logger.info("%d proactive triggers fired", len(fired))
        return fired


# ── NLU helpers ───────────────────────────────────────────────────────────────


def _detect_mood(text: str) -> str:
    """Detect dominant mood from keyword matching."""
    lower = text.lower()
    scores: dict[str, int] = {}
    for mood, keywords in _MOOD_KEYWORDS.items():
        scores[mood] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "neutral"


def _detect_category(text: str) -> str:
    """Detect the life category from keyword matching."""
    lower = text.lower()
    scores: dict[str, int] = {}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "general"


def _extract_entities(text: str) -> list[str]:
    """Heuristic entity extraction: capitalised words, common proper nouns."""
    # Simple heuristic: words that start with a capital letter (not at sentence start)
    words = text.split()
    entities: list[str] = []
    for i, word in enumerate(words):
        clean = re.sub(r"[^A-Za-z]", "", word)
        if clean and clean[0].isupper() and i > 0 and len(clean) > 2:
            entities.append(clean)
    return list(dict.fromkeys(entities))[:10]  # deduplicate, cap at 10


def _score_importance(text: str, mood: str) -> float:
    """Score importance 0.0–1.0 based on emotional weight and content signals."""
    score = 0.3  # baseline
    if mood in ("stressed", "sad"):
        score += 0.3
    if mood in ("motivated", "happy"):
        score += 0.15
    important_signals = ["important", "critical", "urgent", "deadline", "must", "need to", "goal"]
    for sig in important_signals:
        if sig in text.lower():
            score += 0.1
            break
    return min(round(score, 2), 1.0)


def _is_actionable(text: str) -> bool:
    """Return True if the text contains action-oriented language."""
    actionable_patterns = [
        r"\b(?:need to|must|should|will|going to|plan to|have to|want to)\b",
        r"\b(?:todo|task|remind|remember|don't forget)\b",
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in actionable_patterns)


def _extract_deadline(text: str) -> str | None:
    """Extract deadline mentions from text."""
    for pattern in _DEADLINE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


# ── CLI entry-point ───────────────────────────────────────────────────────────


def _cli() -> None:
    """Minimal CLI for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(description="MirrorSelf CLI")
    sub = parser.add_subparsers(dest="cmd")

    ingest = sub.add_parser("ingest", help="Ingest a life log entry")
    ingest.add_argument("text", help="Raw text to log")
    ingest.add_argument("--source", default="manual")

    sub.add_parser("check-triggers", help="Run proactive trigger checks")
    sub.add_parser("context", help="Show current context snapshot")
    sub.add_parser("patterns", help="Distil and show user patterns")

    args = parser.parse_args()
    ms = MirrorSelf()

    if args.cmd == "ingest":
        result = ms.ingest_entry(args.text, source=args.source)
        print(json.dumps(result, indent=2))
    elif args.cmd == "check-triggers":
        triggers = ms.check_proactive_triggers()
        print(json.dumps(triggers, indent=2))
    elif args.cmd == "context":
        ctx = ms.get_current_context()
        print(json.dumps(ctx, indent=2))
    elif args.cmd == "patterns":
        patterns = ms.distill_patterns()
        print(json.dumps(patterns, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _cli()
