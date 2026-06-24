"""
routers/scan_card.py

POST /scan-card/validate          — called by scan.py to validate an RFID scan
POST /scan-card/register          — called by Vue (auth required) to enter registration mode
GET  /scan-card/register-status   — called by scan.py to poll registration state
POST /scan-card/forward-registration — called by scan.py when REGISTER:hash is received

WebSocket /ws/scan                — Vue dashboard connects here for real-time events

Architecture
------------
scan.py (serial bridge) → HTTP → FastAPI → Supabase
                                         ↓ WebSocket
                                      Vue Dashboard

Registration state is held in-memory as a simple dataclass.  This works
correctly for a single-server deployment (which is the target here).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from deps.auth import get_current_user
from supabase_client.supabase import client
from websocket.manager import manager
from websocket.events import (
    broadcast_scanning,
    broadcast_scan_result,
    broadcast_registration_card_detected,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── In-memory registration state ────────────────────────────────────────────

@dataclass
class RegistrationState:
    pending: bool = False
    triggered_by_user_id: Optional[str] = None

_reg_state = RegistrationState()


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    card_hash: str
    user_id: Optional[str] = None  # Scope the lookup to a specific owner when known


class ValidateResponse(BaseModel):
    status: str                    # 'granted' | 'rejected'
    reason: Optional[str] = None   # populated on rejection
    user_id: Optional[str] = None
    card_name: Optional[str] = None
    card_role: Optional[str] = None


class RegisterResponse(BaseModel):
    ok: bool
    message: str


class ForwardRegistrationRequest(BaseModel):
    card_hash: str


class CreateLogRequest(BaseModel):
    card_hash: str
    status: str
    user_id: Optional[str] = None
    card_id: Optional[str] = None
    card_name: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _supabase_error(operation: str, exc: Exception) -> HTTPException:
    logger.error("Supabase error during '%s': %s", operation, exc)
    return HTTPException(status_code=502, detail=f"Database error: {exc}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _insert_access_log(
    *,
    card_id: Optional[str],
    card_name: Optional[str],
    user_id: Optional[str],
    status: str,
    card_hash: str,
    reason: Optional[str] = None,
) -> None:
    """Insert a record into access_logs.  Errors are logged but not re-raised
    so that the validate response still reaches scan.py even if logging fails."""
    try:
        record: dict = {
            "card_id": card_id,
            "card_name": card_name,
            "user_id": user_id,
            "status": status,
            "created_at": _now_iso(),
        }
        if reason:
            record["reason"] = reason
        client.table("access_logs").insert(record).execute()
    except Exception as exc:
        logger.error("Failed to insert access_log: %s", exc)


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/validate", response_model=ValidateResponse)
async def validate_card(payload: ValidateRequest) -> ValidateResponse:
    """
    Called by scan.py when Arduino sends SCAN:RFID_HASH.

    Ownership-aware validation logic
    ---------------------------------
    Validation is always scoped by (user_id, card_hash) when a user_id is
    supplied in the request.  When user_id is omitted (e.g. legacy scan.py
    that does not know the owner), we fetch *all* cards matching the hash and
    prefer the first active one, so that a revoked card registered to User A
    never blocks an active card with the same hash registered to User B.

    Steps
    -----
    1. Broadcast 'scanning' event to all Vue dashboards.
    2. Look up the card(s) in rfid_cards scoped by user_id when known.
    3. Determine grant/reject status.
    4. Insert an access_log entry.
    5. Broadcast 'scan_result' event.
    6. Return the result to scan.py.
    """
    card_hash = payload.card_hash.strip()
    request_user_id = payload.user_id  # may be None for hardware-only callers

    # — Step 1: Notify dashboards that a scan is in progress —
    await broadcast_scanning()

    # — Step 2: Look up the card, scoped by owner when known —
    card = None
    try:
        query = (
            client.table("rfid_cards")
            .select("card_id, card_uuid_hash, card_name, card_role, status, user_id")
            .eq("card_uuid_hash", card_hash)
        )
        if request_user_id:
            # Ownership-scoped lookup: only consider this user's card.
            query = query.eq("user_id", request_user_id).limit(1)
        else:
            # No user_id supplied (hardware scan): fetch all cards with this
            # hash so we can select the active one, avoiding cross-user
            # pollution from revoked records owned by other users.
            query = query.limit(50)

        resp = query.execute()
        rows: list[dict] = resp.data or []
    except Exception as exc:
        raise _supabase_error("lookup rfid_card by hash", exc)

    if request_user_id:
        # Single-user scope: use the exact record (or None).
        card = rows[0] if rows else None
    else:
        # Multi-user scope: prefer an active card over any revoked one.
        # This prevents a revoked card for User A blocking User B's active card.
        active_cards = [
            r for r in rows if r.get("status") not in {"revoke", "revoked"}
        ]
        card = active_cards[0] if active_cards else (rows[0] if rows else None)

    # — Step 3: Determine result —
    if card is None:
        result_status = "rejected"
        reason = "Card not registered"
        card_id = None
        card_name = None
        user_id = None
        logger.info(
            "Card not registered — hash=%s requested_user=%s",
            card_hash, request_user_id,
        )
    elif card.get("status") in {"revoke", "revoked"}:
        result_status = "rejected"
        reason = "Card revoked"
        card_id = card["card_id"]
        card_name = card.get("card_name")
        user_id = card.get("user_id")
        logger.info(
            "Card revoked — hash=%s card_id=%s owner=%s",
            card_hash, card_id, user_id,
        )
    else:
        result_status = "granted"
        reason = None
        card_id = card["card_id"]
        card_name = card.get("card_name")
        user_id = card.get("user_id")
        logger.info(
            "Card granted — hash=%s card_id=%s owner=%s",
            card_hash, card_id, user_id,
        )

    # — Step 4: Log the access attempt —
    _insert_access_log(
        card_id=card_id,
        card_name=card_name,
        user_id=user_id,
        status=result_status,
        card_hash=card_hash,
        reason=reason,
    )

    # — Step 5: Broadcast result to Vue dashboards —
    await broadcast_scan_result(
        status=result_status,
        user_name=card_name,
        card_name=card_name,
        timestamp=_now_iso(),
        reason=reason,
    )

    # — Step 6: Return to scan.py —
    if result_status == "granted":
        return ValidateResponse(
            status="granted",
            user_id=user_id,
            card_name=card_name,
            card_role=card.get("card_role") if card else None,
        )
    else:
        return ValidateResponse(status="rejected", reason=reason)


@router.post("/register", response_model=RegisterResponse)
def enter_registration_mode(
    user: dict = Depends(get_current_user),
) -> RegisterResponse:
    """
    Called by the Vue frontend (auth required) when the user clicks
    '+ REGISTER CARD'.  Sets the in-memory registration flag so that
    scan.py can detect it and send 'R' to Arduino.
    """
    _reg_state.pending = True
    _reg_state.triggered_by_user_id = user["id"]
    logger.info("Registration mode activated by user %s", user["id"])
    return RegisterResponse(ok=True, message="Waiting for RFID card scan...")


@router.get("/register-status")
def get_registration_status() -> dict:
    """
    Polled by scan.py to know whether to send 'R' to Arduino.
    Returns the current pending flag and clears it atomically
    only when scan.py acknowledges by calling forward-registration.
    """
    return {
        "pending": _reg_state.pending,
        "user_id": _reg_state.triggered_by_user_id,
    }


@router.post("/forward-registration")
async def forward_registration(payload: ForwardRegistrationRequest) -> dict:
    """
    Called by scan.py when Arduino sends REGISTER:RFID_HASH.

    Broadcasts registration_card_detected to Vue so the modal opens.
    Clears the in-memory registration flag.
    """
    card_hash = payload.card_hash.strip()

    # Clear registration mode
    _reg_state.pending = False
    _reg_state.triggered_by_user_id = None

    # Broadcast to all connected Vue clients
    await broadcast_registration_card_detected(card_hash)

    logger.info("Registration hash forwarded to dashboards: %s", card_hash)
    return {"ok": True, "card_hash": card_hash}


@router.post("/log")
def create_access_log(payload: CreateLogRequest) -> dict:
    """
    Dedicated POST route to manually create an access log.
    """
    _insert_access_log(
        card_id=payload.card_id,
        card_name=payload.card_name,
        user_id=payload.user_id,
        status=payload.status,
        card_hash=payload.card_hash,
    )
    return {"ok": True, "message": "Access log created"}


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@router.websocket("/scan")
async def websocket_scan(websocket: WebSocket) -> None:
    """
    Vue dashboard connects here to receive real-time RFID events.

    Messages pushed by the server:
        { "event": "scanning" }
        { "event": "scan_result", "status": "granted"|"rejected", ... }
        { "event": "registration_card_detected", "card_hash": "..." }
    """
    await manager.connect(websocket)
    try:
        # Keep the connection alive; client messages are ignored (server-push only)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
