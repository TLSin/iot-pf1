from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from supabase_auth.errors import AuthApiError, AuthError, AuthWeakPasswordError
import logging

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
def signup(payload: SignupRequest):
    # Step 1: Register user in Supabase Auth
    try:
        response = auth_client.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })
    except Exception as exc:
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

    return response.model_dump(mode="json")
