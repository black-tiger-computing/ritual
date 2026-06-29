"""
RITUAL Authentication - GitHub OAuth
Simple session-based auth with GitHub OAuth
"""

import secrets
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

# Simple in-memory session store (use Redis/DB in production)
_sessions: Dict[str, Dict[str, Any]] = {}


@dataclass
class User:
    """Authenticated user."""
    id: str
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    github_token: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def get_github_config() -> tuple[str, str]:
    """Get GitHub OAuth config from env."""
    client_id = "Iv1.placeholder"  # Replace with actual GitHub OAuth App client ID
    client_secret = ""  # Set via GITHUB_CLIENT_SECRET env var
    return client_id, client_secret


def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)


def create_session(user: User) -> str:
    """Create a new session for user."""
    token = generate_session_token()
    _sessions[token] = {
        "user": user.__dict__,
        "expires_at": time.time() + (7 * 24 * 60 * 60)  # 7 days
    }
    return token


def get_session(token: str) -> Optional[User]:
    """Get user from session token."""
    session = _sessions.get(token)
    if not session:
        return None
    
    if time.time() > session["expires_at"]:
        del _sessions[token]
        return None
    
    return User(**session["user"])


def delete_session(token: str):
    """Delete a session."""
    _sessions.pop(token, None)


def get_current_user(request: Request) -> Optional[User]:
    """Get current user from request."""
    token = request.cookies.get("session_token")
    if not token:
        # Also check Authorization header
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    
    if token:
        return get_session(token)
    return None


def require_auth(request: Request) -> User:
    """Require authentication or raise 401."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


# GitHub OAuth
def get_github_auth_url(state: str) -> str:
    """Get GitHub OAuth authorization URL."""
    client_id, _ = get_github_config()
    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&scope=read:user,user:email"
        f"&state={state}"
    )


def exchange_code_for_token(code: str) -> Optional[str]:
    """Exchange OAuth code for access token."""
    client_id, client_secret = get_github_config()
    
    if not client_secret:
        logger.warning("GitHub OAuth not configured - client_secret not set")
        return None
    
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        },
        headers={"Accept": "application/json"},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None


def get_github_user(token: str) -> Optional[Dict[str, Any]]:
    """Get GitHub user info."""
    response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    return None


def get_github_emails(token: str) -> list:
    """Get GitHub user emails."""
    response = requests.get(
        "https://api.github.com/user/emails",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        return [e for e in response.json() if e.get("primary")]
    return []
