"""
RITUAL Auth Routes
GitHub OAuth login/logout endpoints
"""

import secrets
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from app.auth import (
    get_github_auth_url, exchange_code_for_token, get_github_user,
    get_github_emails, create_session, delete_session, get_current_user, User
)

logger = logging.getLogger(__name__)

auth_router = APIRouter()

# State storage for OAuth (in production use Redis)
_oauth_states = {}


@auth_router.get("/auth/login")
async def github_login(request: Request):
    """Redirect to GitHub OAuth."""
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = {"created_at": __import__("time").time()}
    
    auth_url = get_github_auth_url(state)
    
    return RedirectResponse(url=auth_url, status_code=302)


@auth_router.get("/auth/callback")
async def github_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle GitHub OAuth callback."""
    if error:
        return JSONResponse(
            status_code=400,
            content={"error": f"GitHub denied: {error}"}
        )
    
    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "No code provided"}
        )
    
    # Exchange code for token
    token = exchange_code_for_token(code)
    
    if not token:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get access token - OAuth not configured"}
        )
    
    # Get user info
    gh_user = get_github_user(token)
    if not gh_user:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get user info"}
        )
    
    # Get primary email
    emails = get_github_emails(token)
    primary_email = emails[0].get("email") if emails else None
    
    # Create user
    user = User(
        id=str(gh_user["id"]),
        username=gh_user["login"],
        email=primary_email,
        avatar_url=gh_user.get("avatar_url"),
        github_token=token
    )
    
    # Create session
    session_token = create_session(user)
    
    # Redirect to app with session cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 days
        samesite="lax"
    )
    
    return response


@auth_router.get("/auth/me")
async def get_me(request: Request):
    """Get current user info."""
    user = get_current_user(request)
    
    if not user:
        return JSONResponse(
            status_code=401,
            content={"authenticated": False}
        )
    
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url
        }
    }


@auth_router.post("/auth/logout")
async def logout(request: Request):
    """Logout user."""
    token = request.cookies.get("session_token")
    if token:
        delete_session(token)
    
    response = JSONResponse(content={"success": True})
    response.delete_cookie("session_token")
    return response


@auth_router.get("/auth/status")
async def auth_status(request: Request):
    """Check authentication status."""
    user = get_current_user(request)
    
    return {
        "authenticated": user is not None,
        "username": user.username if user else None,
        "configured": bool(__import__("os").getenv("GITHUB_CLIENT_SECRET"))
    }
