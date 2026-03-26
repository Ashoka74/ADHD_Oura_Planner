"""
Wellbeing MCP Server — Oura Ring API + Session Effectiveness Log

Wraps Oura Ring API v2 endpoints needed for the wellbeing-calendar plugin.
Adds a local session effectiveness log for tracking technique outcomes.

Environment variables:
  OURA_ACCESS_TOKEN  — Personal access token from https://cloud.ouraring.com/personal-access-tokens
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from fastmcp import FastMCP

mcp = FastMCP("wellbeing-oura")

OURA_BASE = "https://api.ouraring.com/v2/usercollection"
SESSION_LOG_PATH = Path(os.environ.get("SESSION_LOG_PATH", "/tmp/wellbeing-sessions.json"))


def _token() -> str:
    token = os.environ.get("OURA_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("OURA_ACCESS_TOKEN environment variable is required")
    return token


def _headers() -> dict:
    return {"Authorization": f"Bearer {_token()}"}


async def _oura_get(endpoint: str, params: dict) -> dict:
    params = {k: v for k, v in params.items() if v is not None}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{OURA_BASE}/{endpoint}", headers=_headers(), params=params)
        resp.raise_for_status()
        return resp.json()


# ─── Session Log Helpers ───


def _load_sessions() -> list[dict]:
    if SESSION_LOG_PATH.exists():
        return json.loads(SESSION_LOG_PATH.read_text())
    return []


def _save_sessions(sessions: list[dict]):
    SESSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSION_LOG_PATH.write_text(json.dumps(sessions, indent=2))


# ─── Oura Data Tools ───


@mcp.tool()
async def oura_get_daily_sleep(start_date: str, end_date: str) -> dict:
    """Get daily sleep score summaries from Oura including sleep score contributors for a date range.
    Dates in YYYY-MM-DD format."""
    return await _oura_get("daily_sleep", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_sleep(start_date: str, end_date: str) -> dict:
    """Get detailed sleep period data from Oura including sleep stages (deep, REM, light),
    heart rate, HRV, movement, and timing for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("sleep", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_readiness(start_date: str, end_date: str) -> dict:
    """Get daily readiness scores from Oura including HRV balance, body temperature,
    and recovery index for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("daily_readiness", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_stress(start_date: str, end_date: str) -> dict:
    """Get daily stress data from Oura including stress high, recovery, and rest minutes
    for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("daily_stress", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_activity(start_date: str, end_date: str) -> dict:
    """Get daily activity summaries from Oura including steps, calories, MET minutes,
    and movement data for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("daily_activity", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_heart_rate(start_datetime: str, end_datetime: str) -> dict:
    """Get heart rate time-series data from Oura (5-minute intervals) for a datetime range.
    Uses ISO 8601 datetime parameters. Example: 2024-01-01T00:00:00+00:00"""
    return await _oura_get("heartrate", {"start_datetime": start_datetime, "end_datetime": end_datetime})


@mcp.tool()
async def oura_get_daily_spo2(start_date: str, end_date: str) -> dict:
    """Get daily SpO2 (blood oxygen) data from Oura for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("daily_spo2", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_resilience(start_date: str, end_date: str) -> dict:
    """Get daily resilience data from Oura for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("daily_resilience", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_workouts(start_date: str, end_date: str) -> dict:
    """Get workout data from Oura for a date range. Dates in YYYY-MM-DD format."""
    return await _oura_get("workout", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_personal_info() -> dict:
    """Get personal info from Oura including age, weight, height, and biological sex."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{OURA_BASE}/personal_info", headers=_headers())
        resp.raise_for_status()
        return resp.json()


# ─── Session Effectiveness Log ───


@mcp.tool()
async def oura_log_session(
    technique: str,
    trigger: str,
    duration_min: int,
    hr_before: Optional[float] = None,
    hr_after: Optional[float] = None,
    completed: Optional[str] = None,
    user_rating: Optional[int] = None,
    calendar_event_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Log a wellbeing session for effectiveness tracking.

    Args:
        technique: Technique ID (e.g., BOX-BREATH, BREATH-RESONANT, WALK-MINDFUL)
        trigger: What triggered this session (e.g., "daily-plan", "anomaly-stress-spike", "manual")
        duration_min: Session duration in minutes
        hr_before: Average heart rate 10 min before session (optional, fill in later)
        hr_after: Average heart rate 10 min after session (optional, fill in later)
        completed: yes / partially / skipped (optional, fill in at follow-up)
        user_rating: 1-5 rating from user (optional, fill in at follow-up)
        calendar_event_id: Google Calendar event ID (optional)
        notes: Free text notes (optional)
    """
    sessions = _load_sessions()
    entry = {
        "id": len(sessions) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "technique": technique,
        "trigger": trigger,
        "duration_min": duration_min,
        "hr_before": hr_before,
        "hr_after": hr_after,
        "hr_delta": round(hr_after - hr_before, 1) if hr_before and hr_after else None,
        "completed": completed,
        "user_rating": user_rating,
        "calendar_event_id": calendar_event_id,
        "notes": notes,
    }
    sessions.append(entry)
    _save_sessions(sessions)
    return {"message": "Session logged", "entry": entry}


@mcp.tool()
async def oura_update_session(
    session_id: int,
    hr_before: Optional[float] = None,
    hr_after: Optional[float] = None,
    completed: Optional[str] = None,
    user_rating: Optional[int] = None,
    notes: Optional[str] = None,
) -> dict:
    """Update an existing session log entry (e.g., to add follow-up data).

    Args:
        session_id: The session ID to update
        hr_before: Average HR before session
        hr_after: Average HR after session
        completed: yes / partially / skipped
        user_rating: 1-5 rating
        notes: Additional notes
    """
    sessions = _load_sessions()
    for entry in sessions:
        if entry["id"] == session_id:
            if hr_before is not None:
                entry["hr_before"] = hr_before
            if hr_after is not None:
                entry["hr_after"] = hr_after
            if completed is not None:
                entry["completed"] = completed
            if user_rating is not None:
                entry["user_rating"] = user_rating
            if notes is not None:
                entry["notes"] = notes
            if entry.get("hr_before") and entry.get("hr_after"):
                entry["hr_delta"] = round(entry["hr_after"] - entry["hr_before"], 1)
            _save_sessions(sessions)
            return {"message": "Session updated", "entry": entry}
    return {"error": f"Session {session_id} not found"}


@mcp.tool()
async def oura_get_session_log(
    last_n: Optional[int] = None,
    technique: Optional[str] = None,
) -> dict:
    """Retrieve the effectiveness log of past wellbeing sessions.
    Shows technique, HR delta, completion rate, and ratings.
    Use this to analyze which techniques work best and inform future recommendations.

    Args:
        last_n: Return only the last N entries (default: all)
        technique: Filter by technique ID (e.g., BOX-BREATH)
    """
    sessions = _load_sessions()

    if technique:
        sessions = [s for s in sessions if s["technique"] == technique]
    if last_n:
        sessions = sessions[-last_n:]

    completed_sessions = [s for s in sessions if s.get("completed") == "yes"]
    hr_deltas = [s["hr_delta"] for s in completed_sessions if s.get("hr_delta") is not None]
    ratings = [s["user_rating"] for s in completed_sessions if s.get("user_rating") is not None]

    by_technique: dict[str, dict] = {}
    for s in sessions:
        t = s["technique"]
        if t not in by_technique:
            by_technique[t] = {"count": 0, "completed": 0, "hr_deltas": [], "ratings": []}
        by_technique[t]["count"] += 1
        if s.get("completed") == "yes":
            by_technique[t]["completed"] += 1
        if s.get("hr_delta") is not None:
            by_technique[t]["hr_deltas"].append(s["hr_delta"])
        if s.get("user_rating") is not None:
            by_technique[t]["ratings"].append(s["user_rating"])

    summary = {}
    for t, data in by_technique.items():
        summary[t] = {
            "sessions": data["count"],
            "completed": data["completed"],
            "avg_hr_delta": round(sum(data["hr_deltas"]) / len(data["hr_deltas"]), 1) if data["hr_deltas"] else None,
            "avg_rating": round(sum(data["ratings"]) / len(data["ratings"]), 1) if data["ratings"] else None,
        }

    return {
        "total_sessions": len(sessions),
        "completion_rate": round(len(completed_sessions) / len(sessions) * 100) if sessions else 0,
        "avg_hr_delta": round(sum(hr_deltas) / len(hr_deltas), 1) if hr_deltas else None,
        "avg_user_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "by_technique": summary,
        "entries": sessions,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
