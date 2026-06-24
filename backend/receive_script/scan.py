"""
receive_script/scan.py

Arduino ↔ FastAPI serial bridge.

Reads lines from the Arduino over a COM serial port and dispatches
them to the FastAPI backend via HTTP.

Supported Arduino messages
--------------------------
SCAN:<RFID_HASH>          — validate the card; reply G / D / E to Arduino
REGISTER:<RFID_HASH>      — forward registration hash to FastAPI (FastAPI
                             then broadcasts to Vue dashboard)

Arduino response bytes
----------------------
G  = Granted
D  = Denied
E  = Server Error
R  = Registration mode active — Arduino should display REGISTER MODE screen

Registration mode flow
----------------------
1. User clicks "+ REGISTER CARD" in Vue  → POST /scan-card/register
2. scan.py polls GET /scan-card/register-status every second
3. When pending=True, scan.py sends 'R' to Arduino
4. Arduino shows "REGISTER MODE / PLACE RFID CARD"
5. User places card; Arduino sends REGISTER:<HASH>
6. scan.py POSTs to /scan-card/forward-registration
7. FastAPI broadcasts registration_card_detected → Vue opens modal

Usage
-----
    python scan.py

Environment variables (loaded from backend/.env)
-------------------------------------------------
SERIAL_PORT             COM port to open, e.g. COM3
SERIAL_BAUD             Baud rate (default 9600)
SERIAL_RECONNECT_DELAY  Seconds to wait before reconnecting (default 5)
FASTAPI_BASE_URL        FastAPI base URL (default http://localhost:8000)
"""

import os
import sys
import time
import logging
import threading
import requests
import serial
from pathlib import Path
from dotenv import load_dotenv

# ─── Bootstrap ───────────────────────────────────────────────────────────────

# Load .env from the backend directory (one level up from receive_script/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scan")

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM8")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "9600"))
RECONNECT_DELAY = float(os.getenv("SERIAL_RECONNECT_DELAY", "5"))
API_BASE = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

# ─── State ───────────────────────────────────────────────────────────────────

# Shared flag: True while we are in registration mode
_in_registration_mode = threading.Event()


# ─── FastAPI helpers ──────────────────────────────────────────────────────────

def _post(path: str, payload: dict, *, timeout: int = 5) -> dict | None:
    """POST to FastAPI and return the parsed JSON, or None on error."""
    url = f"{API_BASE}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("POST %s failed: %s", path, exc)
        return None


def _get(path: str, *, timeout: int = 5) -> dict | None:
    """GET from FastAPI and return the parsed JSON, or None on error."""
    url = f"{API_BASE}{path}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("GET %s failed: %s", path, exc)
        return None


# ─── Registration poller (background thread) ──────────────────────────────────

def _registration_poller(ser: serial.Serial) -> None:
    """
    Background thread: polls FastAPI every second for registration pending.
    When pending=True, sends 'R' to Arduino exactly once and sets the
    local _in_registration_mode flag so the main loop knows to expect
    a REGISTER:<hash> line instead of a SCAN:<hash> line.
    """
    logger.info("Registration poller started.")
    while True:
        if not _in_registration_mode.is_set():
            status = _get("/scan-card/register-status")
            if status and status.get("pending"):
                logger.info("Registration mode detected — sending R to Arduino.")
                _in_registration_mode.set()
                try:
                    ser.write(b"R")
                except serial.SerialException as exc:
                    logger.error("Serial write error (R): %s", exc)
        time.sleep(1)


# ─── Validation handler ───────────────────────────────────────────────────────

def _handle_scan(ser: serial.Serial, card_hash: str) -> None:
    """Call validate endpoint and send a single-byte result to Arduino."""
    logger.info("SCAN received: %s", card_hash)
    result = _post("/scan-card/validate", {"card_hash": card_hash})

    if result is None:
        logger.warning("No response from FastAPI — sending E to Arduino.")
        _write_byte(ser, b"E")
        return

    status = result.get("status", "rejected")
    if status == "granted":
        logger.info("GRANTED for hash %s (card: %s)", card_hash, result.get("card_name"))
        _write_byte(ser, b"G")
    else:
        reason = result.get("reason", "rejected")
        logger.info("DENIED for hash %s — %s", card_hash, reason)
        _write_byte(ser, b"D")


# ─── Registration handler ─────────────────────────────────────────────────────

def _handle_register(ser: serial.Serial, card_hash: str) -> None:
    """Forward the scanned hash to FastAPI for broadcasting to Vue."""
    logger.info("REGISTER received: %s", card_hash)
    result = _post("/scan-card/forward-registration", {"card_hash": card_hash})
    _in_registration_mode.clear()

    if result and result.get("ok"):
        logger.info("Registration hash forwarded successfully.")
    else:
        logger.error("Failed to forward registration hash to FastAPI.")


# ─── Serial write helper ──────────────────────────────────────────────────────

def _write_byte(ser: serial.Serial, byte: bytes) -> None:
    try:
        ser.write(byte)
        logger.debug("Sent to Arduino: %s", byte)
    except serial.SerialException as exc:
        logger.error("Serial write error: %s", exc)


# ─── Main loop ────────────────────────────────────────────────────────────────

def _run_loop(ser: serial.Serial) -> None:
    """
    Main serial read loop.  Runs until a serial error forces a reconnect.
    Delegates each received line to the appropriate handler.
    """
    logger.info("Listening on %s @ %d baud…", SERIAL_PORT, SERIAL_BAUD)

    # Start registration poller in a daemon thread so it dies with the process
    poller = threading.Thread(
        target=_registration_poller, args=(ser,), daemon=True
    )
    poller.start()

    while True:
        try:
            raw = ser.readline()
        except serial.SerialException as exc:
            logger.error("Serial read error: %s", exc)
            raise  # let the reconnect wrapper handle it

        if not raw:
            continue

        try:
            line = raw.decode("utf-8", errors="replace").strip()
        except Exception:
            continue

        if not line:
            continue

        logger.debug("Arduino → %r", line)

        if line.startswith("SCAN:"):
            card_hash = line[len("SCAN:"):]
            _handle_scan(ser, card_hash)

        elif line.startswith("REGISTER:"):
            card_hash = line[len("REGISTER:"):]
            _handle_register(ser, card_hash)

        else:
            logger.debug("Unknown line from Arduino: %r", line)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("scan.py starting — port=%s baud=%d", SERIAL_PORT, SERIAL_BAUD)

    while True:
        try:
            with serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1) as ser:
                _run_loop(ser)
        except serial.SerialException as exc:
            logger.error(
                "Cannot open/use serial port '%s': %s. Retrying in %ds…",
                SERIAL_PORT, exc, RECONNECT_DELAY,
            )
        except KeyboardInterrupt:
            logger.info("scan.py stopped by user.")
            sys.exit(0)
        except Exception as exc:
            logger.exception("Unexpected error: %s — retrying in %ds…", exc, RECONNECT_DELAY)

        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
