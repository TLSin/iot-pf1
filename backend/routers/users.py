from typing import List, Optional
from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from deps.auth import get_current_user
from supabase_client.supabase import client

router = APIRouter()
logger = logging.getLogger(__name__)


class CardRequest(BaseModel):
    card_name: str
    card_role: str
    card_uuid_hash: Optional[str] = None


class CardResponse(BaseModel):
    card_id: str
    card_uuid_hash: Optional[str]
    card_name: Optional[str]
    card_role: Optional[str]
    status: str
    created_at: Optional[str] = None


class CardsResponse(BaseModel):
    cards: List[CardResponse]
    total: int


def _supabase_error(operation: str, exc: Exception) -> HTTPException:
    logger.error(f"Supabase error during '{operation}': {exc}")
    return HTTPException(status_code=502, detail=f"Database error: {exc}")


def _card_response(row: dict) -> CardResponse:
    return CardResponse(
        card_id=row["card_id"],
        card_uuid_hash=row.get("card_uuid_hash"),
        card_name=row.get("card_name"),
        card_role=row.get("card_role"),
        status=row.get("status") or "active",
        created_at=row.get("created_at"),
    )


@router.get("/users/cards", response_model=CardsResponse)
def get_cards(user: dict = Depends(get_current_user)):
    user_id = user["id"]

    try:
        response = (
            client.table("rfid_cards")
            .select("card_id, card_uuid_hash, card_name, card_role, status, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("fetch rfid_cards", exc)

    cards = [_card_response(row) for row in (response.data or [])]
    return CardsResponse(cards=cards, total=len(cards))


@router.post("/add-card", response_model=CardResponse)
def add_card(payload: CardRequest, user: dict = Depends(get_current_user)):
    user_id = user["id"]

    card_name = payload.card_name.strip()
    card_role = payload.card_role.strip()

    if not card_name:
        raise HTTPException(status_code=422, detail="Card holder name is required.")

    if not card_role:
        raise HTTPException(status_code=422, detail="Card role is required.")

    try:
        response = (
            client.table("rfid_cards")
            .insert(
                {
                    "card_uuid_hash": payload.card_uuid_hash or uuid4().hex,
                    "user_id": user_id,
                    "card_name": card_name,
                    "card_role": card_role,
                    "status": "active",
                }
            )
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("insert rfid_card", exc)

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=502, detail="Card was not returned after insert.")

    return _card_response(rows[0])


@router.patch("/users/cards/{card_id}/revoke", response_model=CardResponse)
def revoke_card(card_id: str, user: dict = Depends(get_current_user)):
    user_id = user["id"]

    try:
        response = (
            client.table("rfid_cards")
            .update({"status": "revoke"})
            .eq("card_id", card_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("revoke rfid_card", exc)

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Card not found.")

    return _card_response(rows[0])


@router.delete("/users/cards/{card_id}")
def remove_card(card_id: str, user: dict = Depends(get_current_user)):
    user_id = user["id"]

    try:
        response = (
            client.table("rfid_cards")
            .delete()
            .eq("card_id", card_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise _supabase_error("delete rfid_card", exc)

    if not response.data:
        raise HTTPException(status_code=404, detail="Card not found.")

    return {"ok": True}
