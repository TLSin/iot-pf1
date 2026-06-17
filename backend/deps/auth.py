"""
deps/auth.py — FastAPI dependency for extracting an authenticated Supabase user.

Usage:
    from deps.auth import get_current_user

    @router.get("/whatever")
    def my_route(user = Depends(get_current_user)):
        user_id = user["id"]

The dependency reads the `Authorization: Bearer <token>` header, verifies the
JWT with Supabase (via get_user()), and returns the user dict.  It never trusts
a user_id passed in the request body.
"""

from fastapi import Depends, HTTPException, Header
from supabase_client.supabase import auth_client


def get_current_user(authorization: str = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header.",
        )

    token = authorization[len("bearer "):].strip()

    try:
        response = auth_client.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {exc}",
        ) from exc

    if not response or not response.user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return response.user.__dict__
