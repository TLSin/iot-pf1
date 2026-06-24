import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi.util import get_remote_address
from supabase_auth.errors import AuthApiError, AuthError, AuthWeakPasswordError

from deps.rate_limit import limiter
from supabase_client.supabase import auth_client, client

router = APIRouter()
logger = logging.getLogger(__name__)


class SignupRequest(BaseModel):
    first_name: str
    last_name: str = ""
    email: str
    password: str = Field(min_length=8)


def handle_auth_exception(exc: Exception):
    if isinstance(exc, (AuthWeakPasswordError, AuthApiError)):
        raise HTTPException(
            status_code=exc.status,
            detail=exc.to_dict(),
        ) from exc
    elif isinstance(exc, AuthError):
        raise HTTPException(
            status_code=400,
            detail={
                "name": exc.name,
                "message": exc.message,
                "code": exc.code,
            },
        ) from exc
    else:
        logger.error(f"Unexpected signup error: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to sign up: {exc}",
        ) from exc


@router.post("/")
@limiter.limit(
    "3/15minutes",
    error_message="Too many signup attempts. Please try again later.",
)
def signup(request: Request, payload: SignupRequest):
    """
    Register a new user.

    Rate limit: 3 signup attempts per IP per 15 minutes.
    Violations are logged for monitoring purposes.
    """
    client_ip = get_remote_address(request)

    # Step 1: Register user in Supabase Auth
    try:
        response = auth_client.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })
    except Exception as exc:
        logger.warning(
            "Signup failed for email=%s from IP=%s: %s",
            payload.email, client_ip, exc,
        )
        handle_auth_exception(exc)

    user_id = response.user.id if response.user else None

    if not user_id:
        raise HTTPException(status_code=400, detail="User creation failed in authentication step.")

    # Step 2: Insert profile data into `users` table
    try:
        db_response = client.table("users").insert({
            "user_id": user_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "email": payload.email
            # password is not inserted to db as requested
        }).execute()

    except Exception as exc:
        # Note: Depending on rules, you might want to rollback the user creation here
        # using the admin client. For now, we will log the error and return 500.
        logger.error(f"Failed to create user profile in table for user {user_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="User authentication was created, but failed to initialize profile. Please contact support."
        ) from exc

    logger.info("New account created: email=%s user_id=%s from IP=%s", payload.email, user_id, client_ip)
    return response.model_dump(mode="json")
