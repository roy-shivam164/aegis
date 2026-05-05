#!/usr/bin/env python3
"""
seed_demo.py — Pre-populate all 5 AEGIS Qdrant collections with
realistic demo data for the hackathon 3-minute video.

Populates:
  • 12 failure traces (with 3 skill evolution chains)
  •  6 skill documents
  • 35 life log entries over 2 weeks
  •  8 user patterns
  •  4 person profiles

Run:
    python scripts/seed_demo.py
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegis.core.qdrant_manager import QdrantManager
from aegis.core.embedding_engine import embed_text, embed_sentiment

qdrant = QdrantManager()


def _ts(days_ago: int = 0, hours_ago: int = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)
    return dt.isoformat()


# ─────────────────────────────────────────────────────────────────────────────
#  1. Initialize collections
# ─────────────────────────────────────────────────────────────────────────────
print("Initializing Qdrant collections...")
qdrant.initialize_collections()
print("✓ Collections ready")


# ─────────────────────────────────────────────────────────────────────────────
#  2. Skill documents (6)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSeeding skill documents...")

SKILLS = [
    {
        "name": "web_search",
        "content": "# Web Search\n\n1. Use DuckDuckGo as primary.\n2. Fallback to Bing.\n3. Summarise top 3 results.",
        "success_rate": 0.82,
        "uses": 47,
    },
    {
        "name": "code_generation",
        "content": "# Code Generation\n\n1. Parse requirements carefully.\n2. Write tests first.\n3. Iterate on failures.",
        "success_rate": 0.71,
        "uses": 33,
    },
    {
        "name": "api_call",
        "content": "# API Call\n\n1. Validate endpoint.\n2. Handle rate limits with exponential backoff.\n3. Parse response schema.",
        "success_rate": 0.90,
        "uses": 120,
    },
    {
        "name": "data_analysis",
        "content": "# Data Analysis\n\n1. Check data types.\n2. Handle nulls.\n3. Visualise distributions first.",
        "success_rate": 0.65,
        "uses": 18,
    },
    {
        "name": "email_draft",
        "content": "# Email Draft\n\n1. Identify tone (formal/casual).\n2. Keep under 150 words.\n3. Clear CTA at end.",
        "success_rate": 0.94,
        "uses": 62,
    },
    {
        "name": "file_operations",
        "content": "# File Operations\n\n1. Always check path exists.\n2. Use atomic writes.\n3. Handle permissions errors.",
        "success_rate": 0.88,
        "uses": 29,
    },
]

skill_ids: dict[str, str] = {}
for skill in SKILLS:
    vec = embed_text(skill["content"])
    sid = qdrant.store_skill_document(
        vector=vec,
        skill_name=skill["name"],
        version=1,
        success_rate=skill["success_rate"],
        total_uses=skill["uses"],
        markdown_content=skill["content"],
    )
    skill_ids[skill["name"]] = sid
    print(f"  ✓ Skill: {skill['name']} [{sid[:8]}]")


# ─────────────────────────────────────────────────────────────────────────────
#  3. Failure traces (12)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSeeding failure traces...")

FAILURES = [
    {
        "task": "Search for recent Python 3.13 release notes",
        "error": "Timeout: DuckDuckGo rate limit exceeded after 3 retries",
        "type": "web_search",
        "steps": ["Query DuckDuckGo", "Got 429", "Retry 1", "Retry 2", "Timeout"],
        "success": False,
        "days_ago": 14,
    },
    {
        "task": "Search for recent Python 3.13 release notes",
        "error": "Switched to Bing, got results successfully",
        "type": "web_search",
        "steps": ["Query DuckDuckGo", "Got 429", "Switch to Bing", "Success"],
        "success": True,
        "days_ago": 13,
    },
    {
        "task": "Generate FastAPI endpoint with authentication",
        "error": "Generated code had JWT import error — wrong library version",
        "type": "code_generation",
        "steps": ["Parse requirements", "Generate code", "Run tests", "Import error"],
        "success": False,
        "days_ago": 10,
    },
    {
        "task": "Generate FastAPI endpoint with authentication",
        "error": "Specified exact library versions in prompt, code ran correctly",
        "type": "code_generation",
        "steps": ["Parse requirements", "Check lib versions", "Generate code", "Tests pass"],
        "success": True,
        "days_ago": 9,
    },
    {
        "task": "Call OpenWeather API for 5-day forecast",
        "error": "API key missing from environment — KeyError: OPENWEATHER_API_KEY",
        "type": "api_call",
        "steps": ["Build URL", "Load API key", "KeyError", "Failed"],
        "success": False,
        "days_ago": 7,
    },
    {
        "task": "Analyse CSV sales data for Q3 trends",
        "error": "NaN values in revenue column caused division by zero in trend calc",
        "type": "data_analysis",
        "steps": ["Load CSV", "Compute trends", "ZeroDivisionError", "Crash"],
        "success": False,
        "days_ago": 5,
    },
    {
        "task": "Analyse CSV sales data for Q4 trends",
        "error": "Added null handling, analysis completed successfully",
        "type": "data_analysis",
        "steps": ["Load CSV", "Drop nulls", "Compute trends", "Success"],
        "success": True,
        "days_ago": 4,
    },
    {
        "task": "Draft formal email to client about project delay",
        "error": "Email too long (320 words), client complained",
        "type": "email_draft",
        "steps": ["Identify tone", "Draft", "Review length", "Sent 320 words"],
        "success": False,
        "days_ago": 3,
    },
    {
        "task": "Draft formal email to client about scope change",
        "error": "Kept under 150 words with clear CTA, positive response",
        "type": "email_draft",
        "steps": ["Identify tone", "Draft 140 words", "Clear CTA", "Sent"],
        "success": True,
        "days_ago": 2,
    },
    {
        "task": "Write output to /tmp/report.csv",
        "error": "PermissionError: /tmp/report.csv: Read-only file system",
        "type": "file_operations",
        "steps": ["Open file", "PermissionError", "Failed"],
        "success": False,
        "days_ago": 1,
    },
    {
        "task": "Generate unit tests for database module",
        "error": "Missing fixture setup — pytest raises fixture not found",
        "type": "code_generation",
        "steps": ["Parse module", "Generate tests", "Run pytest", "Fixture error"],
        "success": False,
        "days_ago": 1,
    },
    {
        "task": "Search for Qdrant Python SDK examples",
        "error": "Found comprehensive examples in official docs",
        "type": "web_search",
        "steps": ["Query Qdrant docs", "Found examples", "Extracted code"],
        "success": True,
        "days_ago": 0,
    },
]

for trace in FAILURES:
    embed_input = f"Task: {trace['task']}\nError: {trace['error']}"
    vec = embed_text(embed_input)
    pid = qdrant.store_failure_trace(
        vector=vec,
        task_type=trace["type"],
        error_category="timeout" if "timeout" in trace["error"].lower() else "unknown",
        execution_steps=trace["steps"],
        root_cause=trace["error"],
        resolution="resolved" if trace["success"] else "pending",
        skill_doc_id=skill_ids.get(trace["type"], ""),
        attempt_number=1,
        success=trace["success"],
    )
    status = "✓" if trace["success"] else "✗"
    print(f"  {status} Failure trace: {trace['task'][:50]} [{pid[:8]}]")


# ─────────────────────────────────────────────────────────────────────────────
#  4. Life log entries (35)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSeeding life log entries...")

LIFE_LOG = [
    # Week 2 ago
    ("Crushed my morning workout today, feeling amazing and energized!", "happy", "health", 14),
    ("Had a rough meeting with my boss, felt completely dismissed", "stressed", "work", 14),
    ("Need to finish the Q3 report by next Friday or there'll be trouble", "stressed", "work", 13),
    ("Mom called, we talked for an hour. Miss spending time with her.", "happy", "relationship", 13),
    ("Forgot to submit my expense report again — third time this month!", "stressed", "finance", 12),
    ("Going to start learning Rust this weekend, been wanting to for ages", "motivated", "goal", 12),
    ("The team project is going well, working great with Sarah", "happy", "work", 11),
    ("Couldn't sleep again, kept thinking about the job switch idea", "stressed", "goal", 11),
    ("Had a nice dinner with Alex, feels like things are improving", "happy", "relationship", 10),
    ("Salary review coming up next month, need to prepare my case", "stressed", "finance", 10),
    # Week 1 ago
    ("Actually started Rust! Completed the first two chapters. Due date: ship project in 3 months", "motivated", "goal", 9),
    ("Long day, exhausted. Three back-to-back meetings with John", "stressed", "work", 9),
    ("Forgot to call back the dentist for my appointment. Need to tomorrow.", "neutral", "health", 8),
    ("Thinking about switching jobs again. Maybe startup culture suits me better.", "neutral", "goal", 8),
    ("John dismissed my API redesign proposal in front of the whole team", "sad", "work", 7),
    ("Had a great run — 5km personal best! 24:30.", "happy", "health", 7),
    ("Expense report STILL not submitted. Must do it today no excuses", "stressed", "finance", 6),
    ("Sarah gave really thoughtful feedback on my design doc", "happy", "work", 6),
    ("Can't stop thinking about the startup idea from last week", "motivated", "goal", 5),
    ("John interrupted me again during standup. Pattern forming.", "stressed", "work", 5),
    # Last 4 days
    ("Finally submitted expense report. Only 3 weeks late…", "neutral", "finance", 4),
    ("Switching jobs topic came up again — researched 3 companies", "motivated", "goal", 4),
    ("Good workout but right knee is sore. Need to see physio.", "neutral", "health", 3),
    ("Had coffee with former colleague Mike. Interesting startup opportunity.", "motivated", "work", 3),
    ("Deadline for client presentation is tomorrow morning. Not fully ready.", "stressed", "work", 2),
    ("John actually agreed with my suggestion today. First time.", "happy", "work", 2),
    ("Rust project going well. Completed 5 chapters this week.", "motivated", "goal", 1),
    ("Thinking about the startup again — maybe it's time to actually do it", "motivated", "goal", 1),
    ("Tired but productive day. Finished three things off my list.", "neutral", "work", 1),
    ("Sarah mentioned Mom's been asking about me. Should call her soon.", "neutral", "relationship", 1),
    # Today
    ("Crushed the client presentation — they loved it! Zero questions.", "happy", "work", 0),
    ("Physio confirmed knee is fine, just tight IT band. Need stretching.", "neutral", "health", 0),
    ("Job switch: Applied to two companies today. Exciting and terrifying.", "motivated", "goal", 0),
    ("Great day overall. Thinking tomorrow I should start the Rust side project properly.", "happy", "goal", 0),
    ("Alex texted, want to meet this weekend. Looking forward to it.", "happy", "relationship", 0),
]

from aegis.brains.mirror_self import (
    _detect_mood, _detect_category, _extract_entities,
    _score_importance, _is_actionable, _extract_deadline
)

for text, mood, category, days_ago in LIFE_LOG:
    tv = embed_text(text)
    sv = embed_sentiment(text)
    entities = _extract_entities(text)
    importance = _score_importance(text, mood)
    actionable = _is_actionable(text)
    deadline = _extract_deadline(text)

    pid = qdrant.store_life_log_entry(
        text_vector=tv,
        sentiment_vector=sv,
        raw_text=text,
        category=category,
        mood=mood,
        entities=entities,
        importance=importance,
        actionable=actionable,
        deadline_mentioned=deadline,
    )
    print(f"  ✓ Life log: {text[:55]}... [{pid[:8]}]")


# ─────────────────────────────────────────────────────────────────────────────
#  5. User patterns (8)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSeeding user patterns...")

PATTERNS = [
    ("habit", "You frequently forget financial admin tasks (expenses, invoices)", "finance", 0.88, 7),
    ("weakness", "Work-related stress peaks around meetings with John", "work", 0.80, 5),
    ("strength", "You consistently feel motivated and positive after physical exercise", "health", 0.92, 8),
    ("routine", "You tend to log goals and ideas in the evening", "goal", 0.70, 6),
    ("habit", "The topic of switching jobs recurs regularly — you mention it every 1-2 weeks", "goal", 0.85, 6),
    ("strength", "Your code quality improves significantly when you write tests first", "work", 0.78, 4),
    ("weakness", "You tend to underestimate how long reports take to prepare", "work", 0.72, 3),
    ("preference", "You perform best when working with collaborative, honest colleagues like Sarah", "work", 0.75, 5),
]

for ptype, desc, cat, conf, evidence in PATTERNS:
    vec = embed_text(desc)
    pid = qdrant.store_pattern(
        vector=vec,
        pattern_type=ptype,
        description=desc,
        confidence=conf,
        evidence_count=evidence,
        category=cat,
    )
    print(f"  ✓ Pattern [{ptype}]: {desc[:55]}... [{pid[:8]}]")


# ─────────────────────────────────────────────────────────────────────────────
#  6. Person profiles (4)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSeeding person profiles...")

PROFILES = [
    {
        "name": "John",
        "relationship": "colleague",
        "traits": ["dismissive", "competitive", "territorial", "status-seeking"],
        "motives": ["Power Seeking", "Territorial Behaviour", "Social Advancement"],
        "trust": 0.28,
        "interactions": 8,
        "behavior_text": "John frequently dismisses ideas, interrupts in meetings, and deflects credit",
        "comm_text": "formal but passive-aggressive, uses indirect put-downs",
    },
    {
        "name": "Sarah",
        "relationship": "colleague",
        "traits": ["collaborative", "honest", "constructive", "reliable"],
        "motives": ["Genuine Helpfulness", "Quality-Focused"],
        "trust": 0.91,
        "interactions": 12,
        "behavior_text": "Sarah gives thoughtful feedback, acknowledges others' contributions, reliable",
        "comm_text": "direct, warm, evidence-based, always constructive",
    },
    {
        "name": "Alex",
        "relationship": "friend",
        "traits": ["supportive", "empathetic", "consistent", "caring"],
        "motives": ["Genuine Connection", "Mutual Support"],
        "trust": 0.87,
        "interactions": 6,
        "behavior_text": "Alex consistently checks in, remembers important events, supportive during stress",
        "comm_text": "casual, warm, attentive, remembers details",
    },
    {
        "name": "Mike",
        "relationship": "professional acquaintance",
        "traits": ["entrepreneurial", "visionary", "persuasive", "ambitious"],
        "motives": ["Network Building", "Opportunity Seeking"],
        "trust": 0.55,
        "interactions": 2,
        "behavior_text": "Mike seems enthusiastic about opportunities, presented startup idea quickly",
        "comm_text": "energetic, pitchy, uses persuasive framing",
    },
]

for p in PROFILES:
    bv = embed_text(p["behavior_text"])
    cv = embed_sentiment(p["comm_text"])
    pid = qdrant.store_person_profile(
        behavior_vector=bv,
        communication_style_vector=cv,
        person_name=p["name"],
        relationship=p["relationship"],
        traits=p["traits"],
        motive_signals=p["motives"],
        trust_score=p["trust"],
        interaction_count=p["interactions"],
    )
    print(f"  ✓ Profile: {p['name']} (trust={p['trust']}) [{pid[:8]}]")


print("\n" + "=" * 60)
print("✅ Demo seed complete!")
print("=" * 60)
print("\nData seeded:")
print(f"  • {len(SKILLS)} skill documents")
print(f"  • {len(FAILURES)} failure/success traces")
print(f"  • {len(LIFE_LOG)} life log entries (2 weeks)")
print(f"  • {len(PATTERNS)} user patterns")
print(f"  • {len(PROFILES)} person profiles")
print("\nReady for your 3-minute demo! 🚀")
print("\nStart the API:   uvicorn aegis.api.server:app --reload")
print("Start dashboard: cd dashboard && npm run dev")
