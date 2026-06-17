from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from deps.auth import get_current_user
from supabase_client.supabase import client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class AccessLogEntry(BaseModel):
    log_id: str
    card_name: Optional[str]
    status: str          # 'granted' | 'rejected'
    created_at: str

class AccessResponse(BaseModel):
    logs: List[AccessLogEntry]
    total: int

def _supabase_error(operation: str, exc: Exception) -> HTTPException:
    logger.error(f"Supabase error during '{operation}': {exc}")
    return HTTPException(status_code=502, detail=f"Database error: {exc}")

@router.get("/", response_model=AccessResponse)
def get_access_logs(user: dict = Depends(get_current_user)):
    """
    Returns all access logs for the authenticated user.
    """
    user_id = user["id"]
    try:
        logs_resp = (
            client.table("access_logs")
            .select("log_id, card_id, card_name, status, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("fetch access_logs", exc)
    
    raw_logs = logs_resp.data or []
    
    logs = [
        AccessLogEntry(
            log_id=l["log_id"],
            card_name=l.get("card_name") or "Unknown Card",
            status=l["status"],
            created_at=l["created_at"],
        )
        for l in raw_logs
    ]
    
    return logs