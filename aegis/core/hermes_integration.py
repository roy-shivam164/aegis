"""
Hermes Integration Bridge.

Provides helpers for:
- Reading / writing Hermes skill documents from ``~/.hermes/skills/aegis/``
- Sending notifications through the active Hermes Gateway (Telegram / Discord)
- Parsing Hermes cron job definitions

These utilities abstract the file-system and HTTP details so that AEGIS
brain modules do not need to know the Hermes internals directly.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import httpx

from aegis.config import settings

logger = logging.getLogger(__name__)

# ── Path helpers ──────────────────────────────────────────────────────────────


def _skills_dir() -> Path:
    """Resolve and return the Hermes AEGIS skills directory."""
    return Path(os.path.expanduser(settings.hermes_skills_dir))


def _hermes_home() -> Path:
    """Resolve and return the Hermes home directory."""
    return Path(os.path.expanduser(settings.hermes_home))


# ── Skill document I/O ────────────────────────────────────────────────────────


def read_skill(skill_name: str) -> str | None:
    """Read a Hermes skill document by name.

    Parameters
    ----------
    skill_name:
        Filename without ``.md`` extension (e.g. ``"aegis-mirror"``).

    Returns
    -------
    str | None
        Markdown content of the skill, or ``None`` if not found.
    """
    path = _skills_dir() / f"{skill_name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning("Skill document not found: %s", path)
    return None


def write_skill(skill_name: str, markdown_content: str) -> Path:
    """Write (or overwrite) a Hermes skill document.

    Parameters
    ----------
    skill_name:
        Filename without ``.md`` extension.
    markdown_content:
        The full markdown content to write.

    Returns
    -------
    Path
        Absolute path of the written file.
    """
    skills_dir = _skills_dir()
    skills_dir.mkdir(parents=True, exist_ok=True)
    path = skills_dir / f"{skill_name}.md"
    path.write_text(markdown_content, encoding="utf-8")
    logger.info("Skill document written: %s", path)
    return path


def list_installed_skills() -> list[str]:
    """Return the names of all installed AEGIS skill documents."""
    skills_dir = _skills_dir()
    if not skills_dir.exists():
        return []
    return [p.stem for p in skills_dir.glob("*.md")]


# ── Gateway notifications ─────────────────────────────────────────────────────


async def send_notification(message: str, platform: str = "auto") -> bool:
    """Send *message* via the configured Hermes gateway platform.

    Parameters
    ----------
    message:
        The notification text to send.
    platform:
        ``"telegram"``, ``"discord"``, or ``"auto"`` (picks first configured).

    Returns
    -------
    bool
        ``True`` if the notification was dispatched successfully.
    """
    if platform == "auto":
        if settings.telegram_bot_token and settings.telegram_chat_id:
            platform = "telegram"
        elif settings.discord_webhook_url:
            platform = "discord"
        else:
            logger.warning("No notification gateway configured — message dropped: %s", message)
            return False

    if platform == "telegram":
        return await _send_telegram(message)
    if platform == "discord":
        return await _send_discord(message)

    logger.error("Unknown platform: %s", platform)
    return False


async def _send_telegram(message: str) -> bool:
    """Send a message via the Telegram Bot API."""
    url = (
        f"https://api.telegram.org/bot{settings.telegram_bot_token}"
        f"/sendMessage"
    )
    payload = {"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.debug("Telegram notification sent")
            return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Telegram send failed: %s", exc)
        return False


async def _send_discord(message: str) -> bool:
    """Send a message via a Discord Incoming Webhook."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                settings.discord_webhook_url,
                json={"content": message},
            )
            resp.raise_for_status()
            logger.debug("Discord notification sent")
            return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Discord send failed: %s", exc)
        return False


# ── Status helpers ────────────────────────────────────────────────────────────


def get_hermes_status() -> dict[str, Any]:
    """Return a quick health-check dictionary for the Hermes integration."""
    home = _hermes_home()
    skills_dir = _skills_dir()
    return {
        "hermes_home_exists": home.exists(),
        "aegis_skills_dir_exists": skills_dir.exists(),
        "installed_skills": list_installed_skills(),
        "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "discord_configured": bool(settings.discord_webhook_url),
    }
