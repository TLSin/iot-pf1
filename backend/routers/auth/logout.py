from fastapi import APIRouter, HTTPException, Header
from supabase_auth.errors import AuthApiError, AuthError
import logging

from supabase_client.supabase import auth_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/")
def logout(authorization: str = Header(default=None)):
    """
    Invalidate the user's current Supabase session.

    Expects the client to pass:
        Authorization: Bearer <access_token>

    Supabase's sign_out() terminates the session server-side so the
    access token can no longer be used to authenticate future requests.
    """
    access_token: str | None = None

    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization[len("bearer "):].strip()

    try:
        if access_token:
            # Temporarily set the session on the auth client so that
            # sign_out() targets the correct user's server-side session.
            auth_client.auth.set_session(access_token, "")

        auth_client.auth.sign_out()

    except AuthApiError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail=exc.to_dict(),
        ) from exc
    except AuthError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "name": exc.name,
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected logout error: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to log out: {exc}",
        ) from exc

    return {"message": "Logged out successfully"}
