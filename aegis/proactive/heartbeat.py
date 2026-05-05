"""
Proactive Heartbeat Engine.

Runs on the Hermes cron scheduler at the configured interval.  Each
heartbeat cycle:

1. Runs all 6 proactive trigger checks (MirrorSelf)
2. Dispatches fired notifications via the Hermes gateway
3. Distils new user patterns from recent life log entries
4. Logs cycle metrics

Can also be triggered manually or via Hermes ``/aegis-heartbeat``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

from aegis.config import settings
from aegis.core.qdrant_manager import QdrantManager

logger = logging.getLogger(__name__)

# Track daily notification count to respect the cap
_daily_notification_count: int = 0
_daily_reset_date: str = ""


class HeartbeatEngine:
    """Orchestrates all proactive AEGIS behaviours on a timed cycle."""

    def __init__(self, qdrant: QdrantManager | None = None) -> None:
        """Initialise the heartbeat engine.

        Parameters
        ----------
        qdrant:
            Optional pre-constructed ``QdrantManager``.
        """
        self.qdrant = qdrant or QdrantManager()
        self._last_run: datetime | None = None

    # ── Single heartbeat cycle ────────────────────────────────────────────────

    def run_cycle(self) -> dict[str, Any]:
        """Execute one full heartbeat cycle synchronously.

        Returns
        -------
        dict
            Cycle summary with keys: ``triggered``, ``dispatched``,
            ``patterns_distilled``, ``timestamp``.
        """
        return asyncio.run(self.run_cycle_async())

    async def run_cycle_async(self) -> dict[str, Any]:
        """Execute one full heartbeat cycle asynchronously.

        Returns
        -------
        dict
            Cycle summary.
        """
        global _daily_notification_count, _daily_reset_date  # noqa: PLW0603

        start = time.monotonic()
        now = datetime.now(timezone.utc)

        # Reset daily counter on new day
        today_str = now.date().isoformat()
        if today_str != _daily_reset_date:
            _daily_notification_count = 0
            _daily_reset_date = today_str

        logger.info("Heartbeat cycle starting at %s", now.isoformat())

        # ── 1. Check triggers ──────────────────────────────────────────────
        from aegis.brains.mirror_self import MirrorSelf

        ms = MirrorSelf(qdrant=self.qdrant)
        triggers = ms.check_proactive_triggers()

        # ── 2. Dispatch notifications (respect daily cap) ──────────────────
        from aegis.proactive.notification_sender import dispatch_notifications_async

        remaining_budget = (
            settings.aegis_max_proactive_notifications_per_day - _daily_notification_count
        )
        triggers_to_send = triggers[:max(0, remaining_budget)]
        dispatched = await dispatch_notifications_async(triggers_to_send)
        _daily_notification_count += dispatched

        # ── 3. Distil patterns ─────────────────────────────────────────────
        from aegis.proactive.pattern_distiller import distill_patterns_from_log

        patterns = distill_patterns_from_log(self.qdrant)

        self._last_run = now
        elapsed = time.monotonic() - start

        summary = {
            "timestamp": now.isoformat(),
            "triggered": len(triggers),
            "dispatched": dispatched,
            "patterns_distilled": len(patterns),
            "elapsed_seconds": round(elapsed, 3),
            "daily_notifications_used": _daily_notification_count,
        }
        logger.info("Heartbeat cycle complete: %s", summary)
        return summary

    # ── Continuous loop (for background scheduling) ───────────────────────────

    def start_loop(self) -> None:
        """Run the heartbeat engine in a blocking loop.

        Sleeps for ``settings.aegis_heartbeat_interval_minutes`` between
        each cycle.  Designed to be run as a background thread / process.
        """
        interval_secs = settings.aegis_heartbeat_interval_minutes * 60
        logger.info(
            "Heartbeat engine started — interval: %d min",
            settings.aegis_heartbeat_interval_minutes,
        )
        while True:
            try:
                self.run_cycle()
            except Exception as exc:  # noqa: BLE001
                logger.error("Heartbeat cycle error: %s", exc)
            time.sleep(interval_secs)
