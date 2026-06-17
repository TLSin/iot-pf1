from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from supabase_auth.errors import AuthApiError, AuthError

from supabase_client.supabase import auth_client

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)

@router.post("/")
def login(payload: LoginRequest):
    try:
        response = auth_client.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
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
        raise HTTPException(
            status_code=502,
            detail=f"Failed to log in: {exc}",
        ) from exc

    return response.model_dump(mode="json")
