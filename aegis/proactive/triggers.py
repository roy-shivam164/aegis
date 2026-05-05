"""
Proactive Triggers — 6 trigger types that fire without user prompting.

Each trigger function accepts a ``QdrantManager`` and returns either
a notification dict or ``None`` if the trigger condition is not met.

Trigger types:
1. check_forgotten_pattern   — "You always forget X before Y"
2. check_deadline_proximity  — "Your report is due tomorrow"
3. check_mood_drift          — "You've sounded stressed 4 of last 5 entries"
4. check_recurring_topic     — "You've mentioned switching jobs 6 times"
5. check_appreciation        — "3 tasks nailed today, zero retries"
6. check_connection_reminder — "Haven't mentioned Mom in 3 weeks"
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)

# ── Tunable thresholds ────────────────────────────────────────────────────────

MOOD_DRIFT_WINDOW = 5        # entries to check for mood drift
MOOD_DRIFT_THRESHOLD = 3     # how many must match the negative mood
RECURRING_TOPIC_MIN = 3      # minimum mentions to surface a topic
DEADLINE_WARN_DAYS = 2       # warn N days before a deadline date
CONNECTION_SILENCE_DAYS = 14  # days of silence before connection reminder
APPRECIATION_MIN_TASKS = 3   # successful skill uses in a day to trigger


def check_forgotten_pattern(qdrant: QdrantManager) -> dict[str, Any] | None:
    """Detect patterns where the user frequently forgets something.

    Looks for life log entries containing ``"forgot"`` or ``"forgot to"``
    followed by a recurring subject. If the same forgotten thing appears
    2+ times, fire a reminder.

    Parameters
    ----------
    qdrant:
        Active QdrantManager.

    Returns
    -------
    dict | None
        Notification dict if triggered, else ``None``.
    """
    entries = qdrant.get_recent_life_log(limit=50)
    forget_subjects: list[str] = []
    for entry in entries:
        text = entry.get("raw_text", "").lower()
        if "forgot" in text or "forget" in text:
            # Extract the word(s) after "forgot (to)"
            words = text.split()
            for i, w in enumerate(words):
                if w in ("forgot", "forget") and i + 2 < len(words):
                    phrase = " ".join(words[i + 1 : i + 4])
                    forget_subjects.append(phrase)

    if not forget_subjects:
        return None

    counts = Counter(forget_subjects)
    most_common, count = counts.most_common(1)[0]
    if count >= 2:
        return {
            "trigger": "forgotten_pattern",
            "message": (
                f"🔔 Heads-up: You've mentioned forgetting *{most_common}* "
                f"{count} times recently. Want to set a reminder?"
            ),
            "data": {"subject": most_common, "occurrences": count},
        }
    return None


def check_deadline_proximity(qdrant: QdrantManager) -> dict[str, Any] | None:
    """Warn about upcoming deadlines mentioned in the life log.

    Parameters
    ----------
    qdrant:
        Active QdrantManager.

    Returns
    -------
    dict | None
        Notification dict if triggered, else ``None``.
    """
    entries = qdrant.get_recent_life_log(limit=30)
    deadline_entries = [e for e in entries if e.get("deadline_mentioned")]
    if not deadline_entries:
        return None

    # Pick the most recent deadline-tagged entry
    entry = deadline_entries[0]
    deadline_text = entry.get("deadline_mentioned", "")
    task_preview = entry.get("raw_text", "")[:60]

    # Heuristic: "tomorrow" is always urgent
    if "tomorrow" in deadline_text.lower():
        return {
            "trigger": "deadline_proximity",
            "message": (
                f"⏰ Reminder: You mentioned a deadline **tomorrow** — "
                f"*\"{task_preview}\"*. Don't let it sneak up on you."
            ),
            "data": {"deadline": deadline_text, "task_preview": task_preview},
        }

    if "today" in deadline_text.lower() or "tonight" in deadline_text.lower():
        return {
            "trigger": "deadline_proximity",
            "message": (
                f"🚨 Today's deadline: *\"{task_preview}\"* — "
                f"make sure it's on your radar."
            ),
            "data": {"deadline": deadline_text, "task_preview": task_preview},
        }

    return None


def check_mood_drift(qdrant: QdrantManager) -> dict[str, Any] | None:
    """Detect a negative mood drift over recent entries.

    Fires if ``MOOD_DRIFT_THRESHOLD`` of the last ``MOOD_DRIFT_WINDOW``
    entries share the same negative mood.

    Parameters
    ----------
    qdrant:
        Active QdrantManager.

    Returns
    -------
    dict | None
        Notification dict if triggered, else ``None``.
    """
    entries = qdrant.get_recent_life_log(limit=MOOD_DRIFT_WINDOW)
    if len(entries) < MOOD_DRIFT_WINDOW:
        return None

    moods = [e.get("mood", "neutral") for e in entries]
    negative_moods = {"stressed", "sad"}
    neg_count = sum(1 for m in moods if m in negative_moods)

    if neg_count >= MOOD_DRIFT_THRESHOLD:
        dominant_mood = Counter(m for m in moods if m in negative_moods).most_common(1)[0][0]
        return {
            "trigger": "mood_drift",
            "message": (
                f"💙 I've noticed you've seemed *{dominant_mood}* in {neg_count} of your last "
                f"{MOOD_DRIFT_WINDOW} entries. Everything okay? Sometimes talking it out helps."
            ),
            "data": {"dominant_mood": dominant_mood, "count": neg_count, "window": MOOD_DRIFT_WINDOW},
        }
    return None


def check_recurring_topic(qdrant: QdrantManager) -> dict[str, Any] | None:
    """Surface a topic the user keeps returning to but hasn't acted on.

    Parameters
    ----------
    qdrant:
        Active QdrantManager.

    Returns
    -------
    dict | None
        Notification dict if triggered, else ``None``.
    """
    entries = qdrant.get_recent_life_log(limit=50)
    if not entries:
        return None

    # Count entity mentions
    entity_counter: Counter = Counter()
    for e in entries:
        for ent in e.get("entities", []):
            entity_counter[ent] += 1

    # Also check for keyword themes
    theme_counter: Counter = Counter()
    goal_phrases = ["switch jobs", "quit", "start business", "move to", "learn", "lose weight"]
    for e in entries:
        text = e.get("raw_text", "").lower()
        for phrase in goal_phrases:
            if phrase in text:
                theme_counter[phrase] += 1

    # Check themes first (higher signal)
    for theme, count in theme_counter.most_common(1):
        if count >= RECURRING_TOPIC_MIN:
            return {
                "trigger": "recurring_topic",
                "message": (
                    f"🔁 You've mentioned *\"{theme}\"* {count} times recently. "
                    "Is this something you'd like to make a concrete plan for?"
                ),
                "data": {"topic": theme, "count": count},
            }

    # Then check entities
    for entity, count in entity_counter.most_common(1):
        if count >= RECURRING_TOPIC_MIN + 1:
            return {
                "trigger": "recurring_topic",
                "message": (
                    f"🔁 You've mentioned *{entity}* {count} times recently. "
                    "This seems important to you — want to talk it through?"
                ),
                "data": {"topic": entity, "count": count},
            }

    return None


def check_appreciation(qdrant: QdrantManager) -> dict[str, Any] | None:
    """Celebrate when the user has had a productive day with multiple successes.

    Checks failure_traces for today's successful traces.

    Parameters
    ----------
    qdrant:
        Active QdrantManager.

    Returns
    -------
    dict | None
        Notification dict if triggered, else ``None``.
    """
    today_str = datetime.now(timezone.utc).date().isoformat()
    traces, _ = qdrant.client.scroll(
        collection_name=qdrant.client._DEFAULT_COLLECTION_NAME  # type: ignore[attr-defined]
        if False
        else "failure_traces",
        scroll_filter=None,
        with_payload=True,
        limit=100,
    )
    today_successes = [
        t for t in traces
        if t.payload
        and t.payload.get("success") is True
        and (t.payload.get("timestamp", "")[:10] == today_str)
    ]

    if len(today_successes) >= APPRECIATION_MIN_TASKS:
        return {
            "trigger": "appreciation",
            "message": (
                f"🏆 Impressive work today — {len(today_successes)} tasks completed "
                "successfully. You're on a roll. Keep the momentum going."
            ),
            "data": {"successes_today": len(today_successes)},
        }
    return None


def check_connection_reminder(qdrant: QdrantManager) -> dict[str, Any] | None:
    """Remind the user to reconnect with someone they haven't mentioned recently.

    Looks for people in person_profiles who haven't appeared in life log
    entries for ``CONNECTION_SILENCE_DAYS`` days.

    Parameters
    ----------
    qdrant:
        Active QdrantManager.

    Returns
    -------
    dict | None
        Notification dict if triggered, else ``None``.
    """
    profiles = qdrant.get_all_profiles()
    if not profiles:
        return None

    entries = qdrant.get_recent_life_log(limit=100)
    all_text = " ".join(e.get("raw_text", "").lower() for e in entries)

    cutoff = datetime.now(timezone.utc) - timedelta(days=CONNECTION_SILENCE_DAYS)

    for profile in profiles:
        name = profile.get("person_name", "")
        last_updated = profile.get("last_updated", "")

        # Check if name hasn't been mentioned in recent logs
        if name.lower() not in all_text:
            try:
                last_dt = datetime.fromisoformat(last_updated)
                if last_dt < cutoff:
                    return {
                        "trigger": "connection_reminder",
                        "message": (
                            f"👋 You haven't mentioned **{name}** in over "
                            f"{CONNECTION_SILENCE_DAYS} days. "
                            "Might be worth checking in."
                        ),
                        "data": {
                            "person": name,
                            "last_interaction": last_updated,
                            "days_silent": (datetime.now(timezone.utc) - last_dt).days,
                        },
                    }
            except (ValueError, TypeError):
                pass

    return None
