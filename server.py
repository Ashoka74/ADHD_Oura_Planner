"""
Wellbeing MCP Server — Oura Ring OAuth2 + API + Session Log

Full Oura Ring MCP with OAuth2 authorization code flow.
Deployed on Railway, connects to Claude as a remote MCP.

Environment variables:
  OURA_CLIENT_ID       — From https://cloud.ouraring.com/oauth/applications
  OURA_CLIENT_SECRET   — From Oura developer portal
  SESSION_LOG_PATH     — Path to session log JSON (default: /tmp/wellbeing-sessions.json)
  TOKEN_PATH           — Path to OAuth token JSON (default: /tmp/oura-token.json)
  BASE_URL             — Public URL of this server (e.g., https://oura-toolkit-production.up.railway.app)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from fastmcp import FastMCP

mcp = FastMCP("wellbeing-oura")

OURA_BASE = "https://api.ouraring.com/v2/usercollection"
OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"

CLIENT_ID = os.environ.get("OURA_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OURA_CLIENT_SECRET", "")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001")

TOKEN_PATH = Path(os.environ.get("TOKEN_PATH", "/tmp/oura-token.json"))
SESSION_LOG_PATH = Path(os.environ.get("SESSION_LOG_PATH", "/tmp/wellbeing-sessions.json"))

SCOPES = "email personal daily heartrate tag workout session spo2 ring_configuration stress heart_health"


# ─── Token Management ───


def _load_token() -> dict:
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text())
    return {}


def _save_token(token_data: dict):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))


def _get_access_token() -> str:
    token_data = _load_token()
    access_token = token_data.get("access_token", "")
    if not access_token:
        raise ValueError(
            f"Not authenticated. Visit {BASE_URL}/authorize to connect your Oura account."
        )
    return access_token


async def _refresh_token() -> str:
    """Refresh the access token using the refresh token."""
    token_data = _load_token()
    refresh = token_data.get("refresh_token")
    if not refresh:
        raise ValueError(
            f"No refresh token. Visit {BASE_URL}/authorize to re-connect your Oura account."
        )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            OURA_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        new_token = resp.json()
        new_token["refreshed_at"] = datetime.utcnow().isoformat() + "Z"
        _save_token(new_token)
        return new_token["access_token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_access_token()}"}


async def _oura_get(endpoint: str, params: dict) -> dict:
    params = {k: v for k, v in params.items() if v is not None}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{OURA_BASE}/{endpoint}", headers=_headers(), params=params
        )
        if resp.status_code == 401:
            # Token expired, try refresh
            new_token = await _refresh_token()
            headers = {"Authorization": f"Bearer {new_token}"}
            resp = await client.get(
                f"{OURA_BASE}/{endpoint}", headers=headers, params=params
            )
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


# ─── Auth Tools ───


@mcp.tool()
async def oura_auth_status() -> dict:
    """Check if the Oura account is connected and the token is valid."""
    token_data = _load_token()
    if not token_data.get("access_token"):
        return {
            "connected": False,
            "message": f"Not connected. Visit {BASE_URL}/authorize to connect your Oura account.",
        }
    # Test the token
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{OURA_BASE}/personal_info",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            if resp.status_code == 401:
                # Try refresh
                await _refresh_token()
                return {"connected": True, "message": "Token refreshed successfully."}
            resp.raise_for_status()
            return {"connected": True, "message": "Oura account connected and token valid."}
    except Exception as e:
        return {"connected": False, "message": f"Error: {str(e)}"}


@mcp.tool()
async def oura_get_auth_url() -> dict:
    """Get the URL to authorize this app with your Oura account."""
    redirect_uri = f"{BASE_URL}/callback"
    url = (
        f"{OURA_AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={SCOPES.replace(' ', '+')}"
    )
    return {"auth_url": url, "message": f"Visit this URL to connect your Oura account: {url}"}


# ─── Oura Data Tools ───


@mcp.tool()
async def oura_get_daily_sleep(start_date: str, end_date: str) -> dict:
    """Get daily sleep score summaries including contributors for a date range. YYYY-MM-DD format."""
    return await _oura_get("daily_sleep", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_sleep(start_date: str, end_date: str) -> dict:
    """Get detailed sleep periods with stages, HR, HRV, movement, timing. YYYY-MM-DD format."""
    return await _oura_get("sleep", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_readiness(start_date: str, end_date: str) -> dict:
    """Get daily readiness scores with HRV balance, temperature, recovery index. YYYY-MM-DD format."""
    return await _oura_get("daily_readiness", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_stress(start_date: str, end_date: str) -> dict:
    """Get daily stress data with stress_high, recovery, rest minutes. YYYY-MM-DD format."""
    return await _oura_get("daily_stress", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_activity(start_date: str, end_date: str) -> dict:
    """Get daily activity with steps, calories, MET minutes, movement. YYYY-MM-DD format."""
    return await _oura_get("daily_activity", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_heart_rate(start_datetime: str, end_datetime: str) -> dict:
    """Get heart rate time-series (5-min intervals). ISO 8601 datetime format."""
    return await _oura_get("heartrate", {"start_datetime": start_datetime, "end_datetime": end_datetime})


@mcp.tool()
async def oura_get_daily_spo2(start_date: str, end_date: str) -> dict:
    """Get daily SpO2 (blood oxygen) data. YYYY-MM-DD format."""
    return await _oura_get("daily_spo2", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_daily_resilience(start_date: str, end_date: str) -> dict:
    """Get daily resilience data. YYYY-MM-DD format."""
    return await _oura_get("daily_resilience", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_workouts(start_date: str, end_date: str) -> dict:
    """Get workout data. YYYY-MM-DD format."""
    return await _oura_get("workout", {"start_date": start_date, "end_date": end_date})


@mcp.tool()
async def oura_get_personal_info() -> dict:
    """Get personal info including age, weight, height, biological sex."""
    return await _oura_get("personal_info", {})


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
        trigger: What triggered this (e.g., "daily-plan", "anomaly-stress-spike", "manual")
        duration_min: Session duration in minutes
        hr_before: Average HR 10 min before session
        hr_after: Average HR 10 min after session
        completed: yes / partially / skipped
        user_rating: 1-5 (5 = very helpful)
        calendar_event_id: Google Calendar event ID
        notes: Free text notes
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
    """Update an existing session log entry with follow-up data.

    Args:
        session_id: Session ID to update
        hr_before: Average HR before session
        hr_after: Average HR after session
        completed: yes / partially / skipped
        user_rating: 1-5
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


# ─── HTTP routes for OAuth callback ───

from starlette.applications import Starlette
from starlette.responses import RedirectResponse, JSONResponse
from starlette.routing import Route


async def authorize(request):
    """Redirect user to Oura OAuth authorization page."""
    redirect_uri = f"{BASE_URL}/callback"
    url = (
        f"{OURA_AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={SCOPES.replace(' ', '+')}"
    )
    return RedirectResponse(url)


async def callback(request):
    """Handle OAuth callback — exchange code for token."""
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "No authorization code received"}, status_code=400)

    redirect_uri = f"{BASE_URL}/callback"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            OURA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        if resp.status_code != 200:
            return JSONResponse(
                {"error": "Token exchange failed", "details": resp.text},
                status_code=resp.status_code,
            )
        token_data = resp.json()
        token_data["created_at"] = datetime.utcnow().isoformat() + "Z"
        _save_token(token_data)

    # Redirect back to Claude Desktop
    return RedirectResponse("claude://claude.ai/customize/connectors")


async def health(request):
    """Health check endpoint."""
    token = _load_token()
    return JSONResponse({
        "status": "ok",
        "oura_connected": bool(token.get("access_token")),
    })


# Mount OAuth routes onto the MCP server
from starlette.routing import Mount

mcp._additional_http_routes = [
    Route("/authorize", authorize),
    Route("/callback", callback),
    Route("/health", health),
]


if __name__ == "__main__":
    import sys
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8089)))
    else:
        mcp.run(transport="stdio")
