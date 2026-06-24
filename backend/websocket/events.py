"""
websocket/events.py

Typed broadcast helpers.  Every module that needs to push a real-time
update to the Vue dashboard should import and await one of these functions
instead of calling manager.broadcast() directly.
"""

from datetime import datetime, timezone
from websocket.manager import manager


async def broadcast_scanning() -> None:
    """Notify all connected dashboards that an RFID scan has started."""
    await manager.broadcast({"event": "scanning"})


async def broadcast_scan_result(
    *,
    status: str,
    user_name: str | None = None,
    card_name: str | None = None,
    timestamp: str | None = None,
    reason: str | None = None,
) -> None:
    """
    Notify all connected dashboards of a completed RFID scan result.

    Parameters
    ----------
    status:    'granted' | 'rejected'
    user_name: Display name of the card holder (granted scans only)
    card_name: Card name stored in rfid_cards
    timestamp: ISO-8601 timestamp; defaults to now (UTC) if omitted
    reason:    Rejection reason (rejected scans only)
    """
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    payload: dict = {"event": "scan_result", "status": status, "timestamp": ts}

    if status == "granted":
        payload["user_name"] = user_name or card_name or "Unknown"
        payload["card_name"] = card_name
    else:
        payload["reason"] = reason or "Card rejected"

    await manager.broadcast(payload)


async def broadcast_registration_card_detected(card_hash: str) -> None:
    """
    Notify all connected dashboards that a new RFID card was placed
    during registration mode.  Vue will open RegistrationModal with
    the hash pre-filled.
    """
    await manager.broadcast(
        {
            "event": "registration_card_detected",
            "card_hash": card_hash,
        }
    )
