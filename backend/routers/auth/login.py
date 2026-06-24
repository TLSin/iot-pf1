import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from supabase_auth.errors import AuthApiError, AuthError

from deps.rate_limit import limiter
from supabase_client.supabase import auth_client

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


@router.post("/")
@limiter.limit(
    "5/15minutes",
    error_message="Too many login attempts. Please try again later.",
)
def login(request: Request, payload: LoginRequest):
    """
    Authenticate a user with email + password.

    Rate limit: 5 failed attempts per IP per 15 minutes.
    The counter is reset after a successful login.
    """
    client_ip = get_remote_address(request)

    try:
        response = auth_client.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
    except AuthApiError as exc:
        logger.warning(
            "Login failed for email=%s from IP=%s: %s",
            payload.email, client_ip, exc,
        )
        raise HTTPException(
            status_code=exc.status,
            detail=exc.to_dict(),
        ) from exc
    except AuthError as exc:
        logger.warning(
            "Login auth error for email=%s from IP=%s: %s",
            payload.email, client_ip, exc,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "name": exc.name,
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to log in: {exc}",
        ) from exc

    # Successful login — reset the rate-limit counter for this IP so that
    # a legitimate user is not penalised after a few typos in their password.
    try:
        limiter.reset(request)
    except Exception:
        pass  # resetting is best-effort; do not block a successful login

    logger.info("Successful login for email=%s from IP=%s", payload.email, client_ip)
    return response.model_dump(mode="json")
