"""
Behavior Clustering — groups person interaction vectors into clusters
to surface recurring behavioral patterns across interactions.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)


def cluster_person_interactions(
    qdrant: QdrantManager,
    person_name: str,
    n_clusters: int = 3,
) -> list[dict[str, Any]]:
    """Cluster behavioral vectors for a specific person.

    Retrieves all life log entries mentioning *person_name*, groups them
    by semantic similarity using K-Means, and returns cluster summaries.

    Parameters
    ----------
    qdrant:
        Active QdrantManager instance.
    person_name:
        The name of the person whose interactions should be clustered.
    n_clusters:
        Target number of clusters (auto-reduced if insufficient data).

    Returns
    -------
    list[dict]
        A list of cluster summaries: ``{"cluster_id": int, "size": int,
        "representative_text": str}``.
    """
    from aegis.core.embedding_engine import embed_text

    # Search life log for entries mentioning this person
    query_vec = embed_text(f"interaction with {person_name}")
    entries = qdrant.search_life_log(query_vec, vector_name="text", top_k=50)

    if len(entries) < 2:
        logger.info("Insufficient interaction data for %s — skipping clustering", person_name)
        return []

    # Extract embedding proxies via numpy random (actual vectors not returned by search)
    # We use the payload text to re-embed for clustering
    texts = [e.get("raw_text", "") for e in entries]
    vectors = np.array([embed_text(t) for t in texts])

    actual_k = min(n_clusters, len(texts))
    if actual_k < 2:
        return [{"cluster_id": 0, "size": len(texts), "representative_text": texts[0]}]

    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=actual_k, random_state=42, n_init="auto")
    labels = km.fit_predict(vectors)

    clusters: list[dict[str, Any]] = []
    for cid in range(actual_k):
        indices = [i for i, lbl in enumerate(labels) if lbl == cid]
        if not indices:
            continue
        # Pick the entry closest to the centroid
        centroid = km.cluster_centers_[cid]
        closest_idx = min(indices, key=lambda i: float(np.linalg.norm(vectors[i] - centroid)))
        clusters.append(
            {
                "cluster_id": cid,
                "size": len(indices),
                "representative_text": texts[closest_idx][:150],
            }
        )

    return clusters
