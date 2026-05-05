"""
Notification Sender — dispatches proactive notifications via the
configured Hermes gateway (Telegram or Discord).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aegis.core.hermes_integration import send_notification

logger = logging.getLogger(__name__)


def dispatch_notifications(triggers: list[dict[str, Any]], platform: str = "auto") -> int:
    """Dispatch a list of fired trigger notifications.

    Parameters
    ----------
    triggers:
        List of trigger dicts from ``check_proactive_triggers()``.
    platform:
        ``"telegram"``, ``"discord"``, or ``"auto"``.

    Returns
    -------
    int
        Number of successfully dispatched notifications.
    """
    sent = 0
    for trigger in triggers:
        message = trigger.get("message", "")
        if not message:
            continue
        success = asyncio.run(send_notification(message, platform=platform))
        if success:
            sent += 1
            logger.info("Dispatched trigger '%s'", trigger.get("trigger"))
        else:
            logger.warning("Failed to dispatch trigger '%s'", trigger.get("trigger"))
    return sent


async def dispatch_notifications_async(
    triggers: list[dict[str, Any]], platform: str = "auto"
) -> int:
    """Async version of :func:`dispatch_notifications`.

    Parameters
    ----------
    triggers:
        List of trigger dicts from ``check_proactive_triggers()``.
    platform:
        ``"telegram"``, ``"discord"``, or ``"auto"``.

    Returns
    -------
    int
        Number of successfully dispatched notifications.
    """
    sent = 0
    for trigger in triggers:
        message = trigger.get("message", "")
        if not message:
            continue
        success = await send_notification(message, platform=platform)
        if success:
            sent += 1
    return sent
