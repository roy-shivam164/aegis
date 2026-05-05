"""
Brain 1: SkillForge — Self-Improving Agent Memory

SkillForge captures every task failure as a vector in Qdrant, retrieves
semantically similar past failures before retrying, and uses LLM-assisted
rewriting to evolve Hermes skill documents over time.

Standalone usage
----------------
    python -m aegis.brains.skillforge ingest <task> <error>
    python -m aegis.brains.skillforge check <task_description>
    python -m aegis.brains.skillforge tree
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from aegis.config import settings
from aegis.core.embedding_engine import embed_text
from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)


class SkillForge:
    """Brain 1 — learns from failures and evolves skill documents."""

    def __init__(self, qdrant: QdrantManager | None = None) -> None:
        """Initialise SkillForge.

        Parameters
        ----------
        qdrant:
            Optional pre-constructed ``QdrantManager``.  A new one is created
            if not provided.
        """
        self.qdrant = qdrant or QdrantManager()

    # ── Core operations ───────────────────────────────────────────────────────

    def capture_failure(
        self,
        task_description: str,
        execution_steps: list[str],
        error_info: str,
        task_type: str = "generic",
        skill_doc_id: str = "",
        attempt_number: int = 1,
        success: bool = False,
    ) -> str:
        """Store a failure (or success) trace in Qdrant.

        Parameters
        ----------
        task_description:
            Human-readable description of the task that was attempted.
        execution_steps:
            Ordered list of steps taken during execution.
        error_info:
            Error message, traceback, or description of what went wrong.
        task_type:
            Broad category (e.g. ``"code_generation"``, ``"web_search"``).
        skill_doc_id:
            ID of the skill document used (if any).
        attempt_number:
            Retry count (1 = first attempt).
        success:
            ``True`` for success traces (used for skill performance tracking).

        Returns
        -------
        str
            The Qdrant point ID of the stored trace.
        """
        # Embed task description + error info together for richer similarity matching
        embed_input = f"Task: {task_description}\nError: {error_info}"
        vector = embed_text(embed_input)

        # Categorise the error
        error_category = _categorise_error(error_info)

        point_id = self.qdrant.store_failure_trace(
            vector=vector,
            task_type=task_type,
            error_category=error_category,
            execution_steps=execution_steps,
            root_cause=error_info,
            resolution="pending" if not success else "resolved",
            skill_doc_id=skill_doc_id,
            attempt_number=attempt_number,
            success=success,
        )
        status = "success" if success else "failure"
        logger.info("Captured %s trace [%s] for task: %s", status, point_id, task_description[:60])
        return point_id

    def find_similar_failures(
        self, task_description: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Find past failures semantically similar to *task_description*.

        Parameters
        ----------
        task_description:
            Description of the current task.
        top_k:
            Maximum number of similar failures to return.

        Returns
        -------
        list[dict]
            List of failure trace records with similarity scores.
        """
        vector = embed_text(task_description)
        results = self.qdrant.search_similar_failures(vector, top_k=top_k, only_failures=True)
        logger.info("Found %d similar failures for: %s", len(results), task_description[:60])
        return results

    def evolve_skill(
        self,
        skill_doc_id: str,
        failure_trace: dict[str, Any],
        success_trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evolve a skill document based on a failure (and optionally a success) trace.

        This method:
        1. Retrieves the current skill document.
        2. Builds a prompt summarising what went wrong.
        3. Uses the OpenAI API to rewrite the skill document.
        4. Stores the new version back in Qdrant.

        Parameters
        ----------
        skill_doc_id:
            The Qdrant point ID of the skill document to evolve.
        failure_trace:
            A failure trace dictionary (as returned by ``find_similar_failures``).
        success_trace:
            Optional success trace to use as a "what works" reference.

        Returns
        -------
        dict
            The updated skill document record.
        """
        # Retrieve existing skill records
        skills = self.qdrant.get_all_skills()
        existing = next((s for s in skills if s["id"] == skill_doc_id), None)

        if existing is None:
            logger.warning("Skill doc %s not found — creating initial document", skill_doc_id)
            existing = {
                "skill_name": f"skill_{skill_doc_id[:8]}",
                "version": 0,
                "success_rate": 0.0,
                "total_uses": 0,
                "markdown_content": "# Skill Document\n\nNo content yet.",
            }

        new_version = existing.get("version", 0) + 1
        evolved_content = _llm_evolve_skill(
            current_content=existing.get("markdown_content", ""),
            failure_trace=failure_trace,
            success_trace=success_trace,
        )

        new_vector = embed_text(evolved_content)
        new_id = self.qdrant.store_skill_document(
            vector=new_vector,
            skill_name=existing.get("skill_name", "unknown"),
            version=new_version,
            success_rate=existing.get("success_rate", 0.0),
            total_uses=existing.get("total_uses", 0),
            markdown_content=evolved_content,
            doc_id=skill_doc_id,  # overwrite in place
        )
        logger.info(
            "Evolved skill '%s' to v%d [%s]", existing.get("skill_name"), new_version, new_id
        )
        return {
            "id": new_id,
            "skill_name": existing.get("skill_name"),
            "version": new_version,
            "markdown_content": evolved_content,
        }

    def get_skill_tree(self) -> dict[str, Any]:
        """Return a structured overview of all skill documents.

        Returns
        -------
        dict
            ``{"skills": [...], "total_skills": int, "avg_success_rate": float}``
        """
        skills = self.qdrant.get_all_skills()
        if not skills:
            return {"skills": [], "total_skills": 0, "avg_success_rate": 0.0}

        avg_sr = sum(s.get("success_rate", 0.0) for s in skills) / len(skills)
        return {
            "skills": skills,
            "total_skills": len(skills),
            "avg_success_rate": round(avg_sr, 3),
        }

    def register_skill(
        self, skill_name: str, markdown_content: str
    ) -> str:
        """Register a brand-new skill document in Qdrant.

        Parameters
        ----------
        skill_name:
            Short identifier (e.g. ``"web_search"``).
        markdown_content:
            Initial markdown playbook content.

        Returns
        -------
        str
            The new point ID.
        """
        vector = embed_text(markdown_content)
        point_id = self.qdrant.store_skill_document(
            vector=vector,
            skill_name=skill_name,
            version=1,
            success_rate=0.0,
            total_uses=0,
            markdown_content=markdown_content,
        )
        logger.info("Registered new skill '%s' [%s]", skill_name, point_id)
        return point_id

    def update_skill_stats(
        self, skill_doc_id: str, success: bool
    ) -> None:
        """Update success_rate and total_uses after a task attempt.

        Parameters
        ----------
        skill_doc_id:
            The Qdrant point ID of the skill document.
        success:
            Whether the latest attempt succeeded.
        """
        skills = self.qdrant.get_all_skills()
        doc = next((s for s in skills if s["id"] == skill_doc_id), None)
        if doc is None:
            logger.warning("Skill doc %s not found for stat update", skill_doc_id)
            return

        total = doc.get("total_uses", 0) + 1
        successes = round(doc.get("success_rate", 0.0) * doc.get("total_uses", 0))
        if success:
            successes += 1
        new_rate = successes / total

        vector = embed_text(doc.get("markdown_content", ""))
        self.qdrant.store_skill_document(
            vector=vector,
            skill_name=doc.get("skill_name", "unknown"),
            version=doc.get("version", 1),
            success_rate=round(new_rate, 4),
            total_uses=total,
            markdown_content=doc.get("markdown_content", ""),
            doc_id=skill_doc_id,
        )


# ── Private helpers ───────────────────────────────────────────────────────────


def _categorise_error(error_info: str) -> str:
    """Heuristically categorise an error string into a broad category."""
    lower = error_info.lower()
    if any(k in lower for k in ("timeout", "timed out", "deadline")):
        return "timeout"
    if any(k in lower for k in ("rate limit", "quota", "429")):
        return "rate_limit"
    if any(k in lower for k in ("auth", "permission", "403", "401", "forbidden")):
        return "auth_error"
    if any(k in lower for k in ("not found", "404", "missing")):
        return "not_found"
    if any(k in lower for k in ("network", "connection", "unreachable")):
        return "network_error"
    if any(k in lower for k in ("syntax", "parse", "invalid json")):
        return "parse_error"
    return "unknown"


def _llm_evolve_skill(
    current_content: str,
    failure_trace: dict[str, Any],
    success_trace: dict[str, Any] | None,
) -> str:
    """Call the LLM to rewrite a skill document based on failure evidence.

    Falls back to appending a lessons-learned section if the API is not
    configured.
    """
    from aegis.config import settings as cfg  # local import to avoid circulars

    if not cfg.openai_api_key:
        # Offline fallback — append a lessons-learned block
        lessons = (
            f"\n\n## Lessons Learned (auto-appended {datetime.now(timezone.utc).date()})\n\n"
            f"**Root cause**: {failure_trace.get('root_cause', 'unknown')}\n"
            f"**Error category**: {failure_trace.get('error_category', 'unknown')}\n"
            f"**Steps that failed**: {failure_trace.get('execution_steps', [])}\n"
        )
        return current_content + lessons

    from openai import OpenAI

    client = OpenAI(api_key=cfg.openai_api_key)
    prompt = (
        "You are an expert technical writer for AI agent playbooks.\n\n"
        "## Current Skill Document\n"
        f"{current_content}\n\n"
        "## Failure Trace\n"
        f"Root cause: {failure_trace.get('root_cause', 'unknown')}\n"
        f"Error category: {failure_trace.get('error_category', 'unknown')}\n"
        f"Steps: {failure_trace.get('execution_steps', [])}\n"
    )
    if success_trace:
        prompt += (
            "\n## Success Trace (for reference)\n"
            f"Steps: {success_trace.get('execution_steps', [])}\n"
        )
    prompt += (
        "\n\nRewrite the skill document to avoid this failure in the future. "
        "Keep the same markdown format. Output ONLY the new markdown content."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()


# ── CLI entry-point ───────────────────────────────────────────────────────────

def _cli() -> None:
    """Minimal CLI for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(description="SkillForge CLI")
    sub = parser.add_subparsers(dest="cmd")

    ingest = sub.add_parser("ingest", help="Record a failure trace")
    ingest.add_argument("task", help="Task description")
    ingest.add_argument("error", help="Error information")
    ingest.add_argument("--type", default="generic", dest="task_type")

    check = sub.add_parser("check", help="Find similar past failures")
    check.add_argument("task", help="Task description")
    check.add_argument("--top", type=int, default=5)

    sub.add_parser("tree", help="Print skill tree")

    args = parser.parse_args()
    sf = SkillForge()

    if args.cmd == "ingest":
        pid = sf.capture_failure(args.task, [], args.error, task_type=args.task_type)
        print(json.dumps({"stored_id": pid}))
    elif args.cmd == "check":
        results = sf.find_similar_failures(args.task, top_k=args.top)
        print(json.dumps(results, indent=2))
    elif args.cmd == "tree":
        tree = sf.get_skill_tree()
        print(json.dumps(tree, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _cli()
