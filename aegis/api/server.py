"""
AEGIS FastAPI Dashboard Backend.

Endpoints
---------
GET  /health                    — health check
GET  /api/status                — system-wide status
GET  /api/skill-tree            — SkillForge skill tree
GET  /api/life-log              — recent life log entries
GET  /api/patterns              — user patterns
GET  /api/profiles              — person profiles
GET  /api/profiles/{name}       — single profile with full analysis
POST /api/ingest                — ingest a new life log entry
POST /api/heartbeat             — trigger a manual heartbeat cycle
POST /api/capture-failure       — record a failure trace
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegis.config import settings
from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AEGIS API",
    description="Adaptive Evolving General Intelligence System — Dashboard Backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Qdrant client (created once on startup)
_qdrant: QdrantManager | None = None


def get_qdrant() -> QdrantManager:
    """Return (or lazily create) the shared QdrantManager."""
    global _qdrant  # noqa: PLW0603
    if _qdrant is None:
        _qdrant = QdrantManager()
    return _qdrant


# ── Request / response models ─────────────────────────────────────────────────


class IngestRequest(BaseModel):
    """Body for POST /api/ingest."""

    text: str
    source: str = "api"


class CaptureFailureRequest(BaseModel):
    """Body for POST /api/capture-failure."""

    task_description: str
    execution_steps: list[str] = []
    error_info: str
    task_type: str = "generic"
    success: bool = False


# ── Endpoints ─────────────────────────────────────────────────────────────────


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return a simple liveness probe."""
    return {"status": "ok", "service": "aegis-api"}


@app.get("/api/status", tags=["system"])
def get_status() -> dict[str, Any]:
    """Return overall AEGIS system status.

    Includes Qdrant collection stats and Hermes integration status.
    """
    from aegis.core.hermes_integration import get_hermes_status

    qdrant = get_qdrant()
    collection_names = [
        settings.collection_failure_traces,
        settings.collection_skill_documents,
        settings.collection_user_life_log,
        settings.collection_user_patterns,
        settings.collection_person_profiles,
    ]
    collections: dict[str, Any] = {}
    for name in collection_names:
        try:
            collections[name] = qdrant.collection_info(name)
        except Exception as exc:  # noqa: BLE001
            collections[name] = {"error": str(exc)}

    return {
        "aegis_version": "0.1.0",
        "qdrant_url": settings.qdrant_url,
        "collections": collections,
        "hermes": get_hermes_status(),
    }


@app.get("/api/skill-tree", tags=["skillforge"])
def get_skill_tree() -> dict[str, Any]:
    """Return the full SkillForge skill tree."""
    from aegis.brains.skillforge import SkillForge

    sf = SkillForge(qdrant=get_qdrant())
    return sf.get_skill_tree()


@app.get("/api/life-log", tags=["mirror"])
def get_life_log(limit: int = 20) -> dict[str, Any]:
    """Return recent life log entries."""
    qdrant = get_qdrant()
    entries = qdrant.get_recent_life_log(limit=min(limit, 100))
    return {"entries": entries, "count": len(entries)}


@app.get("/api/patterns", tags=["mirror"])
def get_patterns() -> dict[str, Any]:
    """Return all user patterns."""
    qdrant = get_qdrant()
    patterns = qdrant.get_all_patterns()
    return {"patterns": patterns, "count": len(patterns)}


@app.get("/api/profiles", tags=["shadow"])
def get_profiles() -> dict[str, Any]:
    """Return all person profiles (summary)."""
    from aegis.brains.shadow_reader import ShadowReader

    sr = ShadowReader(qdrant=get_qdrant())
    return {"profiles": sr.list_profiles(), "count": len(sr.list_profiles())}


@app.get("/api/profiles/{person_name}", tags=["shadow"])
def get_profile(person_name: str) -> dict[str, Any]:
    """Return full analysis for a specific person."""
    from aegis.brains.shadow_reader import ShadowReader

    sr = ShadowReader(qdrant=get_qdrant())
    result = sr.analyze_person(person_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/ingest", tags=["mirror"])
def ingest_entry(body: IngestRequest) -> dict[str, Any]:
    """Ingest a new life log entry and return extracted metadata."""
    from aegis.brains.mirror_self import MirrorSelf

    ms = MirrorSelf(qdrant=get_qdrant())
    result = ms.ingest_entry(body.text, source=body.source)
    return result


@app.post("/api/heartbeat", tags=["proactive"])
def run_heartbeat() -> dict[str, Any]:
    """Manually trigger a heartbeat cycle."""
    from aegis.proactive.heartbeat import HeartbeatEngine

    engine = HeartbeatEngine(qdrant=get_qdrant())
    return engine.run_cycle()


@app.post("/api/capture-failure", tags=["skillforge"])
def capture_failure(body: CaptureFailureRequest) -> dict[str, Any]:
    """Record a task failure (or success) trace."""
    from aegis.brains.skillforge import SkillForge

    sf = SkillForge(qdrant=get_qdrant())
    point_id = sf.capture_failure(
        task_description=body.task_description,
        execution_steps=body.execution_steps,
        error_info=body.error_info,
        task_type=body.task_type,
        success=body.success,
    )
    return {"stored_id": point_id, "success": body.success}


# ── Main entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "aegis.api.server:app",
        host=settings.aegis_api_host,
        port=settings.aegis_api_port,
        reload=True,
    )
