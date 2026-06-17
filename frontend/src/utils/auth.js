/**
 * auth.js — Reusable authentication utilities
 *
 * Session data is stored as JSON in localStorage under the key
 * 'supabase.auth.token'. The same key is written by LoginView.vue
 * after a successful sign-in.
 *
 * Shape stored:
 *   { access_token, refresh_token, expires_at, ... }
 */

const SESSION_KEY = 'supabase.auth.token'
const API_BASE    = 'http://localhost:8000'

// ─── Session helpers ────────────────────────────────────────────────────────

/** Return the parsed session object, or null if none is stored. */
export function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    // return null
  }
}

/** Return true when a non-expired access token exists in localStorage. */
export function isAuthenticated() {
  const session = getSession()
  if (!session?.access_token) return false

  // Supabase sets `expires_at` as a Unix timestamp (seconds).
  if (session.expires_at) {
    const nowSeconds = Math.floor(Date.now() / 1000)
    if (nowSeconds >= session.expires_at) {
      clearSession()
      return false
    }
  }

  return true
}

/** Persist a session object returned by the backend. */
export function saveSession(session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

/** Remove all locally stored auth data. */
export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}

// ─── Logout ─────────────────────────────────────────────────────────────────

/**
 * Call the FastAPI logout endpoint, then wipe the local session.
 * Resolves with { ok: true } on success, or { ok: false, message } on failure.
 */
export async function logout() {
  const session = getSession()
  const accessToken = session?.access_token

  try {
    const response = await fetch(`${API_BASE}/auth/logout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    })

    // Always clear local session regardless of server response.
    clearSession()

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      return { ok: false, message: data.detail?.message || data.detail || 'Logout failed' }
    }

    return { ok: true }
  } catch (error) {
    // Network failure — still wipe the local session so the user is not stuck.
    clearSession()
    return { ok: false, message: error.message }
  }
}
