/**
 * services/user.js
 *
 * Centralises fetch calls for RFID card data used by UserView.
 * Every request attaches the Supabase access token stored by auth.js.
 */

import { getSession } from '../utils/auth.js'

const API_BASE = 'http://localhost:8000'

function authHeaders() {
  const session = getSession()
  if (!session?.access_token) return {}
  return { Authorization: `Bearer ${session.access_token}` }
}

async function readJsonError(res, fallback) {
  const err = await res.json().catch(() => ({}))
  throw new Error(err.detail?.message || err.detail || fallback)
}

/**
 * Fetch RFID cards owned by the current authenticated user.
 *
 * @returns {Promise<{ cards: Array, total: number }>}
 */
export async function fetchCards() {
  const res = await fetch(`${API_BASE}/users/cards`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })

  if (!res.ok) {
    await readJsonError(res, `Cards request failed (${res.status})`)
  }

  return res.json()
}

/**
 * Notify FastAPI that the user wants to register a new RFID card.
 * FastAPI sets a flag that scan.py polls, then scan.py sends 'R' to Arduino.
 *
 * @returns {Promise<{ ok: boolean, message: string }>}
 */
export async function registerCardMode() {
  const res = await fetch(`${API_BASE}/scan-card/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })

  if (!res.ok) {
    await readJsonError(res, `Register mode request failed (${res.status})`)
  }

  return res.json()
}

/**
 * Register a new RFID card for the current authenticated user.
 * card_uuid_hash must be the real hash received from the RFID reader.
 *
 * @param {{ card_name: string, card_role: string, card_uuid_hash: string }} card
 * @returns {Promise<Object>}
 */
export async function addCard(card) {
  const res = await fetch(`${API_BASE}/add-card`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(card),
  })

  if (!res.ok) {
    await readJsonError(res, `Add card request failed (${res.status})`)
  }

  return res.json()
}

/**
 * Mark an RFID card as revoked in the database.
 *
 * @param {string} cardId
 * @returns {Promise<Object>}
 */
export async function revokeCard(cardId) {
  const res = await fetch(`${API_BASE}/users/cards/${encodeURIComponent(cardId)}/revoke`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })

  if (!res.ok) {
    await readJsonError(res, `Revoke card request failed (${res.status})`)
  }

  return res.json()
}

/**
 * Remove an RFID card owned by the current authenticated user.
 *
 * @param {string} cardId
 * @returns {Promise<{ ok: boolean }>}
 */
export async function removeCard(cardId) {
  const res = await fetch(`${API_BASE}/users/cards/${encodeURIComponent(cardId)}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })

  if (!res.ok) {
    await readJsonError(res, `Remove card request failed (${res.status})`)
  }

  return res.json()
}
