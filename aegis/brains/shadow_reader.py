"""
Brain 3: ShadowReader — Behavioral Profiler & Motive Analyst

ShadowReader builds deep personality profiles of the people the user
interacts with, clusters behavioral patterns into archetypes, infers
hidden motives via LLM analysis, and surfaces motive signals proactively.

Standalone usage
----------------
    python -m aegis.brains.shadow_reader update "Alice" "She dismissed my idea again in the meeting"
    python -m aegis.brains.shadow_reader analyze "Alice"
    python -m aegis.brains.shadow_reader report "Alice"
    python -m aegis.brains.shadow_reader list
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from aegis.config import settings
from aegis.core.embedding_engine import embed_sentiment, embed_text
from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)


class ShadowReader:
    """Brain 3 — builds personality profiles and infers motives."""

    def __init__(self, qdrant: QdrantManager | None = None) -> None:
        """Initialise ShadowReader.

        Parameters
        ----------
        qdrant:
            Optional pre-constructed ``QdrantManager``.
        """
        self.qdrant = qdrant or QdrantManager()

    # ── Profile operations ────────────────────────────────────────────────────

    def update_profile(self, person_name: str, new_interaction_text: str) -> dict[str, Any]:
        """Add a new interaction and update the person's profile.

        Parameters
        ----------
        person_name:
            The name of the person (case-sensitive).
        new_interaction_text:
            Description of the new interaction (from the user's perspective).

        Returns
        -------
        dict
            Updated profile record.
        """
        from aegis.analysis.motive_inference import infer_motives
        from aegis.analysis.archetypes import classify_archetype

        existing = self.qdrant.get_person_profile(person_name)

        # Build new embeddings from the fresh interaction
        behavior_vector = embed_text(new_interaction_text)
        comm_style_vector = embed_sentiment(new_interaction_text)

        if existing:
            # Merge: blend new vector with existing (running average approximation)
            interaction_count = existing.get("interaction_count", 1) + 1
            old_bv = existing.get("_behavior_vector", behavior_vector)
            old_cv = existing.get("_comm_vector", comm_style_vector)
            behavior_vector = _blend_vectors(old_bv, behavior_vector, interaction_count)
            comm_style_vector = _blend_vectors(old_cv, comm_style_vector, interaction_count)

            # Accumulate traits / motive signals
            traits: list[str] = existing.get("traits", [])
            motive_signals: list[str] = existing.get("motive_signals", [])
            trust_score: float = existing.get("trust_score", 0.5)
            relationship: str = existing.get("relationship", "unknown")
            profile_id: str | None = existing["id"]
        else:
            interaction_count = 1
            traits = []
            motive_signals = []
            trust_score = 0.5
            relationship = "unknown"
            profile_id = None

        # LLM-based motive inference
        new_motives = infer_motives(person_name, new_interaction_text)
        motive_signals = list(dict.fromkeys(motive_signals + new_motives))[:10]

        # Archetype classification
        archetype_traits = classify_archetype(new_interaction_text)
        traits = list(dict.fromkeys(traits + archetype_traits))[:15]

        # Trust score heuristic adjustment
        trust_delta = _estimate_trust_delta(new_interaction_text)
        trust_score = max(0.0, min(1.0, trust_score + trust_delta))

        new_id = self.qdrant.store_person_profile(
            behavior_vector=behavior_vector,
            communication_style_vector=comm_style_vector,
            person_name=person_name,
            relationship=relationship,
            traits=traits,
            motive_signals=motive_signals,
            trust_score=round(trust_score, 3),
            interaction_count=interaction_count,
            profile_id=profile_id,
        )
        logger.info(
            "Updated profile for '%s' — %d interactions, trust=%.2f",
            person_name,
            interaction_count,
            trust_score,
        )
        return self.qdrant.get_person_profile(person_name) or {"id": new_id}

    def analyze_person(self, person_name: str) -> dict[str, Any]:
        """Return a full analysis of a person's profile.

        Parameters
        ----------
        person_name:
            The name of the person to analyse.

        Returns
        -------
        dict
            Profile data enriched with archetype label and motive summary.
        """
        from aegis.analysis.behavior_cluster import cluster_person_interactions
        from aegis.analysis.archetypes import ARCHETYPES

        profile = self.qdrant.get_person_profile(person_name)
        if profile is None:
            return {"error": f"No profile found for '{person_name}'"}

        # Cluster interactions from behavior space
        similar = self.qdrant.search_similar_profiles(
            query_vector=embed_text(person_name),
            vector_name="behavior",
            top_k=5,
        )
        archetype_label = _pick_archetype(profile.get("traits", []))

        return {
            **profile,
            "archetype": archetype_label,
            "similar_profiles": [p["person_name"] for p in similar if p["person_name"] != person_name],
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_person_report(self, person_name: str) -> str:
        """Generate a readable text report for a person.

        Parameters
        ----------
        person_name:
            Name of the person.

        Returns
        -------
        str
            Formatted text report.
        """
        analysis = self.analyze_person(person_name)
        if "error" in analysis:
            return analysis["error"]

        lines = [
            f"## ShadowReader Report — {person_name}",
            f"**Relationship**: {analysis.get('relationship', 'unknown')}",
            f"**Archetype**: {analysis.get('archetype', 'unknown')}",
            f"**Trust Score**: {analysis.get('trust_score', 0.5):.2f} / 1.0",
            f"**Interactions logged**: {analysis.get('interaction_count', 0)}",
            "",
            "### Observed Traits",
            ", ".join(analysis.get("traits", ["none detected"])),
            "",
            "### Motive Signals",
        ]
        for signal in analysis.get("motive_signals", ["none detected"]):
            lines.append(f"- {signal}")
        lines += [
            "",
            f"*Report generated: {analysis.get('analysis_timestamp', '')}*",
        ]
        return "\n".join(lines)

    def list_profiles(self) -> list[dict[str, Any]]:
        """Return a summary list of all tracked person profiles."""
        profiles = self.qdrant.get_all_profiles()
        return [
            {
                "person_name": p.get("person_name"),
                "relationship": p.get("relationship"),
                "trust_score": p.get("trust_score"),
                "interaction_count": p.get("interaction_count"),
                "last_updated": p.get("last_updated"),
            }
            for p in profiles
        ]


# ── Private helpers ───────────────────────────────────────────────────────────


def _blend_vectors(
    old: list[float], new: list[float], n: int
) -> list[float]:
    """Compute a running-average blend of two vectors.

    ``blended = old * (n-1)/n + new * 1/n``
    """
    weight_old = (n - 1) / n
    weight_new = 1.0 / n
    return [o * weight_old + nv * weight_new for o, nv in zip(old, new)]


def _estimate_trust_delta(interaction_text: str) -> float:
    """Heuristic: positive interactions increase trust, negative decrease it."""
    lower = interaction_text.lower()
    positive = ["helped", "supported", "agreed", "honest", "kind", "reliable", "generous"]
    negative = ["lied", "betrayed", "dismissed", "ignored", "manipulated", "rude", "aggressive"]
    pos_count = sum(1 for w in positive if w in lower)
    neg_count = sum(1 for w in negative if w in lower)
    return (pos_count - neg_count) * 0.05


def _pick_archetype(traits: list[str]) -> str:
    """Select the most likely archetype based on observed traits."""
    from aegis.analysis.archetypes import ARCHETYPES

    if not traits:
        return "Unknown"

    best_archetype = "Undefined"
    best_count = 0
    for archetype, meta in ARCHETYPES.items():
        overlap = sum(1 for t in traits if t.lower() in [kw.lower() for kw in meta["keywords"]])
        if overlap > best_count:
            best_count = overlap
            best_archetype = archetype
    return best_archetype


# ── CLI entry-point ───────────────────────────────────────────────────────────


def _cli() -> None:
    """Minimal CLI for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(description="ShadowReader CLI")
    sub = parser.add_subparsers(dest="cmd")

    update_p = sub.add_parser("update", help="Add an interaction for a person")
    update_p.add_argument("name", help="Person name")
    update_p.add_argument("interaction", help="Interaction description")

    analyze_p = sub.add_parser("analyze", help="Analyze a person's profile")
    analyze_p.add_argument("name", help="Person name")

    report_p = sub.add_parser("report", help="Generate a readable report")
    report_p.add_argument("name", help="Person name")

    sub.add_parser("list", help="List all tracked profiles")

    args = parser.parse_args()
    sr = ShadowReader()

    if args.cmd == "update":
        result = sr.update_profile(args.name, args.interaction)
        print(json.dumps(result, indent=2, default=str))
    elif args.cmd == "analyze":
        result = sr.analyze_person(args.name)
        print(json.dumps(result, indent=2, default=str))
    elif args.cmd == "report":
        print(sr.get_person_report(args.name))
    elif args.cmd == "list":
        print(json.dumps(sr.list_profiles(), indent=2, default=str))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _cli()
