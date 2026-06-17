/**
 * services/dashboard.js
 *
 * Centralises all fetch calls to the FastAPI /dashboard/* endpoints.
 * Both functions read the access token from localStorage (written by
 * auth.js → saveSession) and attach it as an Authorization header —
 * the backend derives the user identity from this token, never from
 * request body fields.
 */

import { getSession } from '../utils/auth.js'

const API_BASE = 'http://localhost:8000'

/**
 * Build the standard auth headers for every protected request.
 * Returns an empty object if no session is found (the backend will
 * respond 401 and the router guard will catch it on next navigation).
 */
function authHeaders() {
  const session = getSession()
  if (!session?.access_token) return {}
  return { Authorization: `Bearer ${session.access_token}` }
}

/**
 * Fetch analytics metrics for the current user.
 *
 * @returns {Promise<{
 *   total_cards: number,
 *   active_cards: number,
 *   revoked_cards: number,
 *   total_granted: number,
 *   total_rejected: number,
 * }>}
 */
export async function fetchAnalytics() {
  const res = await fetch(`${API_BASE}/dashboard/analytics`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.message || err.detail || `Analytics request failed (${res.status})`)
  }

  return res.json()
}

/**
 * Fetch access history for the current user.
 *
 * @param {number | null} limit  Maximum records to return; pass null for full history
 * @returns {Promise<{ logs: Array, total: number }>}
 */
export async function fetchHistory(limit = 10) {
  const query = limit == null ? '' : `?limit=${encodeURIComponent(limit)}`
  const res = await fetch(`${API_BASE}/dashboard/history${query}`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.message || err.detail || `History request failed (${res.status})`)
  }

  return res.json()
}
