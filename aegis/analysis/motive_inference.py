"""
Motive Inference — uses LLM analysis to infer a person's hidden motives
from interaction descriptions.

Falls back to keyword heuristics when no OpenAI API key is configured.
"""

from __future__ import annotations

import logging
from typing import Any

from aegis.config import settings

logger = logging.getLogger(__name__)

# ── Keyword-based fallback motive signals ────────────────────────────────────

_MOTIVE_KEYWORDS: dict[str, list[str]] = {
    "seeking_validation": ["praise", "compliment", "approval", "recognition", "acknowledge"],
    "power_seeking": ["control", "authority", "dominate", "overrule", "decision", "boss"],
    "financial_interest": ["money", "salary", "pay", "profit", "invest", "budget", "cost"],
    "social_advancement": ["network", "impress", "status", "reputation", "visibility", "brand"],
    "conflict_avoidance": ["avoid", "passive", "silent", "ignore", "withdraw", "escape"],
    "genuine_helpfulness": ["help", "support", "assist", "care", "give", "share", "volunteer"],
    "information_gathering": ["ask", "probe", "question", "curious", "data", "research", "find out"],
    "territorial_behaviour": ["mine", "protect", "ownership", "boundary", "territory", "keep out"],
}


def infer_motives(person_name: str, interaction_text: str) -> list[str]:
    """Infer likely motives for a person based on an interaction description.

    Uses OpenAI GPT if available; otherwise falls back to keyword matching.

    Parameters
    ----------
    person_name:
        The name of the person being analysed.
    interaction_text:
        Description of the interaction from the user's perspective.

    Returns
    -------
    list[str]
        List of inferred motive signal strings (short, human-readable).
    """
    if settings.openai_api_key:
        return _llm_infer_motives(person_name, interaction_text)
    return _keyword_infer_motives(interaction_text)


def _keyword_infer_motives(text: str) -> list[str]:
    """Keyword-based motive inference fallback."""
    lower = text.lower()
    signals: list[str] = []
    for motive, keywords in _MOTIVE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            signals.append(motive.replace("_", " ").title())
    return signals or ["Motive unclear — insufficient data"]


def _llm_infer_motives(person_name: str, interaction_text: str) -> list[str]:
    """LLM-based motive inference via OpenAI."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            f"Analyse the following interaction with {person_name} and list up to 5 "
            "likely hidden motives or psychological drivers behind their behaviour. "
            "Be concise — each motive should be a short phrase (3–8 words). "
            "Return ONLY a JSON array of strings.\n\n"
            f"Interaction: {interaction_text}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        import json

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        # Handle both {"motives": [...]} and direct list responses
        if isinstance(data, list):
            return data[:5]
        for key in ("motives", "signals", "results"):
            if key in data and isinstance(data[key], list):
                return data[key][:5]
        return list(data.values())[0][:5] if data else ["Motive unclear"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM motive inference failed: %s — using keyword fallback", exc)
        return _keyword_infer_motives(interaction_text)


def build_motive_summary(motive_signals: list[str], trust_score: float) -> dict[str, Any]:
    """Build a structured motive summary dict.

    Parameters
    ----------
    motive_signals:
        List of detected motive strings.
    trust_score:
        Current trust score (0.0–1.0).

    Returns
    -------
    dict
        ``{"top_motives": [...], "trust_level": str, "caution_flag": bool}``
    """
    if trust_score >= 0.7:
        trust_level = "high"
    elif trust_score >= 0.4:
        trust_level = "moderate"
    else:
        trust_level = "low"

    caution_flag = any(
        "manipulat" in s.lower() or "power" in s.lower() or "territorial" in s.lower()
        for s in motive_signals
    ) or trust_score < 0.3

    return {
        "top_motives": motive_signals[:3],
        "trust_level": trust_level,
        "caution_flag": caution_flag,
    }
