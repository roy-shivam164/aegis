"""
Behavioral Archetypes — maps observed traits to psychological archetypes.

Archetypes are used by ShadowReader to label person profiles and give
the user quick, intuitive summaries of who they're dealing with.
"""

from __future__ import annotations

from typing import Any

# ── Archetype definitions ─────────────────────────────────────────────────────

ARCHETYPES: dict[str, dict[str, Any]] = {
    "The Manipulator": {
        "description": "Uses subtle tactics to control situations and people for personal gain.",
        "keywords": [
            "manipulative", "deceptive", "controlling", "gaslighting", "dishonest",
            "calculating", "scheming", "two-faced", "exploitative",
        ],
        "warning_level": "high",
    },
    "The Supporter": {
        "description": "Genuinely helpful, empathetic, and reliable in difficult situations.",
        "keywords": [
            "helpful", "supportive", "empathetic", "reliable", "kind", "generous",
            "encouraging", "caring", "trustworthy",
        ],
        "warning_level": "low",
    },
    "The Competitor": {
        "description": "Highly driven; sees most interactions as zero-sum competitions.",
        "keywords": [
            "competitive", "ambitious", "driven", "aggressive", "status-seeking",
            "jealous", "territorial", "achievement-focused",
        ],
        "warning_level": "medium",
    },
    "The Avoider": {
        "description": "Conflict-averse; withdraws when challenged or stressed.",
        "keywords": [
            "avoidant", "passive", "dismissive", "withdrawn", "non-committal",
            "indecisive", "fence-sitter", "conflict-averse",
        ],
        "warning_level": "medium",
    },
    "The Visionary": {
        "description": "Creative thinker with strong ideas but sometimes impractical.",
        "keywords": [
            "creative", "visionary", "innovative", "idealistic", "optimistic",
            "big-picture", "inspirational", "unconventional",
        ],
        "warning_level": "low",
    },
    "The Critic": {
        "description": "High standards; frequently points out flaws (sometimes constructively).",
        "keywords": [
            "critical", "judgmental", "perfectionistic", "demanding", "negative",
            "fault-finding", "skeptical", "cynical",
        ],
        "warning_level": "medium",
    },
    "The Diplomat": {
        "description": "Skilled at navigating social situations; builds bridges between people.",
        "keywords": [
            "diplomatic", "tactful", "persuasive", "charming", "politically-savvy",
            "mediating", "consensus-building", "socially-intelligent",
        ],
        "warning_level": "low",
    },
    "Undefined": {
        "description": "Insufficient data to classify this person's behavioral archetype.",
        "keywords": [],
        "warning_level": "unknown",
    },
}


def classify_archetype(interaction_text: str) -> list[str]:
    """Extract archetype-relevant trait keywords from interaction text.

    Parameters
    ----------
    interaction_text:
        Raw description of an interaction with a person.

    Returns
    -------
    list[str]
        Detected trait keywords present in the text.
    """
    lower = interaction_text.lower()
    detected: list[str] = []

    for _archetype, meta in ARCHETYPES.items():
        for keyword in meta["keywords"]:
            if keyword in lower and keyword not in detected:
                detected.append(keyword)

    # Also pick up common behavioural adjectives not in the archetype list
    common_traits = [
        "honest", "funny", "smart", "rude", "aggressive", "kind", "cold",
        "warm", "sarcastic", "passive-aggressive", "direct", "indirect",
        "stubborn", "flexible", "generous", "selfish", "curious", "bored",
    ]
    for trait in common_traits:
        if trait in lower and trait not in detected:
            detected.append(trait)

    return detected[:15]  # cap at 15 traits per interaction


def get_archetype_warning(archetype_name: str) -> str:
    """Return a warning level for a given archetype.

    Parameters
    ----------
    archetype_name:
        Exact archetype name (key from ``ARCHETYPES``).

    Returns
    -------
    str
        ``"low"``, ``"medium"``, ``"high"``, or ``"unknown"``.
    """
    return ARCHETYPES.get(archetype_name, ARCHETYPES["Undefined"])["warning_level"]
