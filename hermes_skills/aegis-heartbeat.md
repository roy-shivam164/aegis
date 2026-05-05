---
name: aegis-heartbeat
description: Manually trigger the AEGIS proactive heartbeat cycle
---

# AEGIS Heartbeat — Proactive Intelligence Engine

The Heartbeat Engine is the proactive core of AEGIS. It normally runs
automatically on Hermes's cron scheduler every 30 minutes, but you can
also trigger it manually at any time.

## When to Invoke

Use this skill when:
- The user explicitly asks AEGIS to "check in" or "give me updates"
- You want to run all 6 proactive trigger checks right now
- You want to know if any patterns or deadlines are firing

---

## Trigger Types Checked

Each heartbeat run checks all 6 trigger types:

1. **Forgotten Pattern** — Have you been forgetting the same thing repeatedly?
2. **Deadline Proximity** — Any upcoming deadlines from your life log?
3. **Mood Drift** — Have you been consistently stressed or sad recently?
4. **Recurring Topic** — Is there something you keep bringing up but not acting on?
5. **Appreciation** — Have you had a great run of successful tasks today?
6. **Connection Reminder** — Is there someone you haven't checked in with lately?

---

## Usage Steps

### Run a manual heartbeat cycle via API

```bash
curl -X POST http://localhost:8000/api/heartbeat
```

Or via Python:

```bash
cd ~/aegis && python -c "
from aegis.proactive.heartbeat import HeartbeatEngine
engine = HeartbeatEngine()
result = engine.run_cycle()
import json; print(json.dumps(result, indent=2))
"
```

### Start the continuous heartbeat loop

```bash
cd ~/aegis && python -c "
from aegis.proactive.heartbeat import HeartbeatEngine
HeartbeatEngine().start_loop()
"
```

---

## Interpreting Results

After running:
1. Show the count of triggers that fired
2. Present each fired notification with JARVIS-like delivery
3. Report how many patterns were distilled
4. Note if the daily notification budget is nearly exhausted

---

## Notes

- Heartbeat interval: 30 minutes (configurable via `AEGIS_HEARTBEAT_INTERVAL_MINUTES`)
- Daily notification cap: 10 (configurable via `AEGIS_MAX_PROACTIVE_NOTIFICATIONS_PER_DAY`)
- Notifications are sent via Telegram or Discord (whichever is configured)
