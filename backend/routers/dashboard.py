"""
routers/dashboard.py

GET /dashboard/analytics  — card counts scoped to the authenticated user
GET /dashboard/history    — recent access_logs scoped to the authenticated user

Authentication: every route requires a valid Bearer token (enforced by the
get_current_user dependency in deps/auth.py).  The user_id is always derived
from the verified token — never from the request body or query params.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from deps.auth import get_current_user
from supabase_client.supabase import client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Response schemas ────────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    total_cards: int
    active_cards: int
    revoked_cards: int
    total_granted: int
    total_rejected: int


class AccessLogEntry(BaseModel):
    log_id: str
    card_name: Optional[str]
    status: str          # 'granted' | 'rejected'
    created_at: str


class HistoryResponse(BaseModel):
    logs: List[AccessLogEntry]
    total: int


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _supabase_error(operation: str, exc: Exception) -> HTTPException:
    logger.error(f"Supabase error during '{operation}': {exc}")
    return HTTPException(status_code=502, detail=f"Database error: {exc}")


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(user: dict = Depends(get_current_user)):
    """
    Returns card-level statistics for the authenticated user.

    Card counts come from rfid_cards filtered by user_id.
    Access attempt counts come from access_logs joined through
    the cards owned by this user.
    """
    user_id = user["id"]

    # 1. Fetch all cards belonging to this user
    try:
        cards_resp = (
            client.table("rfid_cards")
            .select("card_id, status")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("fetch rfid_cards", exc)

    cards = cards_resp.data or []
    total_cards = len(cards)
    active_cards = sum(1 for c in cards if c.get("status") == "active")
    revoked_cards = sum(1 for c in cards if c.get("status") in {"revoke", "revoked"})

    card_ids = [c["card_id"] for c in cards]

    # 2. Fetch access_logs for those cards (no cards → zero counts)
    total_granted = 0
    total_rejected = 0

    if card_ids:
        try:
            logs_resp = (
                client.table("access_logs")
                .select("status")
                .in_("card_id", card_ids)
                .execute()
            )
        except Exception as exc:
            raise _supabase_error("fetch access_logs for analytics", exc)

        logs = logs_resp.data or []
        total_granted = sum(1 for l in logs if l.get("status") == "granted")
        total_rejected = sum(1 for l in logs if l.get("status") == "rejected")

    return AnalyticsResponse(
        total_cards=total_cards,
        active_cards=active_cards,
        revoked_cards=revoked_cards,
        total_granted=total_granted,
        total_rejected=total_rejected,
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    limit: Optional[int] = None,
    user: dict = Depends(get_current_user),
):
    """
    Returns access_log entries for RFID cards
    owned by the authenticated user, newest first.

    Accepts an optional ?limit= query param for compact widgets.
    Omitting limit returns the full available history.
    """
    user_id = user["id"]

    # Resolve the user's card IDs first
    try:
        cards_resp = (
            client.table("rfid_cards")
            .select("card_id")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("fetch rfid_cards for history", exc)

    card_ids = [c["card_id"] for c in (cards_resp.data or [])]

    if not card_ids:
        return HistoryResponse(logs=[], total=0)

    # Fetch access logs for those cards, newest first
    try:
        query = (
            client.table("access_logs")
            .select("log_id, card_id, card_name, status, created_at")
            .in_("card_id", card_ids)
            .order("created_at", desc=True)
        )

        if limit is not None:
            query = query.limit(max(1, limit))

        logs_resp = query.execute()
    except Exception as exc:
        raise _supabase_error("fetch access_logs history", exc)

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

    return HistoryResponse(logs=logs, total=len(logs))
