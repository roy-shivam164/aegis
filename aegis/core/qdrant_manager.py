"""
Qdrant Manager — initialises all 5 AEGIS collections and exposes
typed helper methods for every upsert / search operation.

Collections
-----------
1. failure_traces    — 1536-dim COSINE
2. skill_documents   — 1536-dim COSINE
3. user_life_log     — named vectors: text (1536), sentiment (384)
4. user_patterns     — 1536-dim COSINE
5. person_profiles   — named vectors: behavior (1536), communication_style (384)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from aegis.config import settings

logger = logging.getLogger(__name__)

# ── Collection metadata constants ────────────────────────────────────────────

_COLLECTIONS: dict[str, dict] = {
    settings.collection_failure_traces: {
        "type": "single",
        "size": settings.dim_large,
        "distance": models.Distance.COSINE,
    },
    settings.collection_skill_documents: {
        "type": "single",
        "size": settings.dim_large,
        "distance": models.Distance.COSINE,
    },
    settings.collection_user_life_log: {
        "type": "named",
        "vectors": {
            "text": models.VectorParams(size=settings.dim_large, distance=models.Distance.COSINE),
            "sentiment": models.VectorParams(
                size=settings.dim_small, distance=models.Distance.COSINE
            ),
        },
    },
    settings.collection_user_patterns: {
        "type": "single",
        "size": settings.dim_large,
        "distance": models.Distance.COSINE,
    },
    settings.collection_person_profiles: {
        "type": "named",
        "vectors": {
            "behavior": models.VectorParams(
                size=settings.dim_large, distance=models.Distance.COSINE
            ),
            "communication_style": models.VectorParams(
                size=settings.dim_small, distance=models.Distance.COSINE
            ),
        },
    },
}


class QdrantManager:
    """Thin wrapper around QdrantClient that manages AEGIS collections."""

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        """Initialise the Qdrant client.

        Parameters
        ----------
        url:
            Qdrant service URL.  Defaults to ``settings.qdrant_url``.
        api_key:
            Qdrant API key for managed clusters.  Defaults to ``settings.qdrant_api_key``.
        """
        self.client = QdrantClient(
            url=url or settings.qdrant_url,
            api_key=api_key or settings.qdrant_api_key or None,
        )
        logger.info("QdrantManager connected to %s", url or settings.qdrant_url)

    # ── Collection lifecycle ──────────────────────────────────────────────────

    def initialize_collections(self) -> None:
        """Create all 5 AEGIS collections if they do not already exist."""
        existing = {c.name for c in self.client.get_collections().collections}

        for name, cfg in _COLLECTIONS.items():
            if name in existing:
                logger.debug("Collection '%s' already exists — skipping", name)
                continue

            if cfg["type"] == "single":
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=cfg["size"],
                        distance=cfg["distance"],
                    ),
                )
            else:  # named vectors
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=cfg["vectors"],
                )
            logger.info("Created collection '%s'", name)

    def collection_info(self, name: str) -> dict[str, Any]:
        """Return a JSON-serialisable summary for a collection."""
        info = self.client.get_collection(name)
        return {
            "name": name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status,
        }

    # ── failure_traces helpers ────────────────────────────────────────────────

    def store_failure_trace(
        self,
        vector: list[float],
        task_type: str,
        error_category: str,
        execution_steps: list[str],
        root_cause: str,
        resolution: str,
        skill_doc_id: str,
        attempt_number: int,
        success: bool,
    ) -> str:
        """Embed and store a failure (or success) trace. Returns the point ID."""
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=settings.collection_failure_traces,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "task_type": task_type,
                        "error_category": error_category,
                        "execution_steps": execution_steps,
                        "root_cause": root_cause,
                        "resolution": resolution,
                        "skill_doc_id": skill_doc_id,
                        "attempt_number": attempt_number,
                        "success": success,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
            ],
        )
        return point_id

    def search_similar_failures(
        self,
        query_vector: list[float],
        top_k: int = 5,
        only_failures: bool = True,
    ) -> list[dict[str, Any]]:
        """Semantic search over failure_traces.

        Parameters
        ----------
        query_vector:
            Embedding of the current task description.
        top_k:
            Maximum number of results to return.
        only_failures:
            When ``True``, filter to traces where ``success=False``.
        """
        query_filter = None
        if only_failures:
            query_filter = models.Filter(
                must=[models.FieldCondition(key="success", match=models.MatchValue(value=False))]
            )
        results = self.client.search(
            collection_name=settings.collection_failure_traces,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, **r.payload} for r in results]

    # ── skill_documents helpers ───────────────────────────────────────────────

    def store_skill_document(
        self,
        vector: list[float],
        skill_name: str,
        version: int,
        success_rate: float,
        total_uses: int,
        markdown_content: str,
        doc_id: str | None = None,
    ) -> str:
        """Upsert a skill document. Returns the point ID."""
        point_id = doc_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self.client.upsert(
            collection_name=settings.collection_skill_documents,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "skill_name": skill_name,
                        "version": version,
                        "success_rate": success_rate,
                        "total_uses": total_uses,
                        "created_at": now,
                        "last_evolved": now,
                        "markdown_content": markdown_content,
                    },
                )
            ],
        )
        return point_id

    def search_skill_documents(
        self, query_vector: list[float], top_k: int = 3
    ) -> list[dict[str, Any]]:
        """Search skill_documents by semantic similarity."""
        results = self.client.search(
            collection_name=settings.collection_skill_documents,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, **r.payload} for r in results]

    def get_all_skills(self) -> list[dict[str, Any]]:
        """Return all skill documents (scroll through collection)."""
        records, _ = self.client.scroll(
            collection_name=settings.collection_skill_documents,
            with_payload=True,
            limit=1000,
        )
        return [{"id": r.id, **r.payload} for r in records]

    # ── user_life_log helpers ─────────────────────────────────────────────────

    def store_life_log_entry(
        self,
        text_vector: list[float],
        sentiment_vector: list[float],
        raw_text: str,
        category: str,
        mood: str,
        entities: list[str],
        importance: float,
        actionable: bool,
        deadline_mentioned: str | None = None,
    ) -> str:
        """Store a life log entry with dual named vectors. Returns point ID."""
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=settings.collection_user_life_log,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector={"text": text_vector, "sentiment": sentiment_vector},
                    payload={
                        "category": category,
                        "mood": mood,
                        "entities": entities,
                        "importance": importance,
                        "actionable": actionable,
                        "deadline_mentioned": deadline_mentioned,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "raw_text": raw_text,
                    },
                )
            ],
        )
        return point_id

    def search_life_log(
        self,
        query_vector: list[float],
        vector_name: str = "text",
        top_k: int = 10,
        category_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over user_life_log."""
        query_filter = None
        if category_filter:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="category", match=models.MatchValue(value=category_filter)
                    )
                ]
            )
        results = self.client.search(
            collection_name=settings.collection_user_life_log,
            query_vector=models.NamedVector(name=vector_name, vector=query_vector),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, **r.payload} for r in results]

    def get_recent_life_log(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent life log entries (by scroll, sorted post-fetch)."""
        records, _ = self.client.scroll(
            collection_name=settings.collection_user_life_log,
            with_payload=True,
            limit=limit,
        )
        entries = [{"id": r.id, **r.payload} for r in records]
        return sorted(entries, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    # ── user_patterns helpers ─────────────────────────────────────────────────

    def store_pattern(
        self,
        vector: list[float],
        pattern_type: str,
        description: str,
        confidence: float,
        evidence_count: int,
        category: str,
        pattern_id: str | None = None,
    ) -> str:
        """Upsert a user pattern. Returns the point ID."""
        point_id = pattern_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self.client.upsert(
            collection_name=settings.collection_user_patterns,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "pattern_type": pattern_type,
                        "description": description,
                        "confidence": confidence,
                        "evidence_count": evidence_count,
                        "first_observed": now,
                        "last_confirmed": now,
                        "category": category,
                    },
                )
            ],
        )
        return point_id

    def get_all_patterns(self) -> list[dict[str, Any]]:
        """Return all user patterns."""
        records, _ = self.client.scroll(
            collection_name=settings.collection_user_patterns,
            with_payload=True,
            limit=500,
        )
        return [{"id": r.id, **r.payload} for r in records]

    # ── person_profiles helpers ───────────────────────────────────────────────

    def store_person_profile(
        self,
        behavior_vector: list[float],
        communication_style_vector: list[float],
        person_name: str,
        relationship: str,
        traits: list[str],
        motive_signals: list[str],
        trust_score: float,
        interaction_count: int,
        profile_id: str | None = None,
    ) -> str:
        """Upsert a person profile. Returns the point ID."""
        point_id = profile_id or str(uuid.uuid4())
        self.client.upsert(
            collection_name=settings.collection_person_profiles,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector={
                        "behavior": behavior_vector,
                        "communication_style": communication_style_vector,
                    },
                    payload={
                        "person_name": person_name,
                        "relationship": relationship,
                        "traits": traits,
                        "motive_signals": motive_signals,
                        "trust_score": trust_score,
                        "interaction_count": interaction_count,
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                    },
                )
            ],
        )
        return point_id

    def get_person_profile(self, person_name: str) -> dict[str, Any] | None:
        """Fetch a person's profile by exact name match."""
        results, _ = self.client.scroll(
            collection_name=settings.collection_person_profiles,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="person_name", match=models.MatchValue(value=person_name)
                    )
                ]
            ),
            with_payload=True,
            limit=1,
        )
        if results:
            return {"id": results[0].id, **results[0].payload}
        return None

    def search_similar_profiles(
        self, query_vector: list[float], vector_name: str = "behavior", top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Find profiles with similar behavioral vectors."""
        results = self.client.search(
            collection_name=settings.collection_person_profiles,
            query_vector=models.NamedVector(name=vector_name, vector=query_vector),
            limit=top_k,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, **r.payload} for r in results]

    def get_all_profiles(self) -> list[dict[str, Any]]:
        """Return all person profiles."""
        records, _ = self.client.scroll(
            collection_name=settings.collection_person_profiles,
            with_payload=True,
            limit=500,
        )
        return [{"id": r.id, **r.payload} for r in records]
