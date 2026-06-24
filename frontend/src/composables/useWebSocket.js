/**
 * composables/useWebSocket.js
 *
 * Singleton WebSocket connection to FastAPI /ws/scan.
 *
 * Usage
 * -----
 *   import { useWebSocket } from '@/composables/useWebSocket.js'
 *
 *   const { onEvent, disconnect } = useWebSocket()
 *
 *   onEvent((msg) => {
 *     if (msg.event === 'scan_result') { ... }
 *   })
 *
 * Design notes
 * ------------
 * - A single WebSocket instance is shared across all components (module-level
 *   singleton).  Multiple calls to useWebSocket() register additional
 *   listeners but do NOT open extra connections.
 * - Auto-reconnects with exponential back-off (capped at 30 s).
 * - Exposes `onEvent(cb)` to subscribe and returns an `off` function to
 *   unsubscribe — useful inside onUnmounted() to avoid memory leaks.
 */

const WS_URL = 'ws://localhost:8000/ws/scan'
const MAX_RECONNECT_DELAY_MS = 30_000
const BASE_RECONNECT_DELAY_MS = 1_000

// ── Singleton state ──────────────────────────────────────────────────────────

let socket = null
let reconnectAttempt = 0
let reconnectTimer = null
let isIntentionallyClosed = false

/** All registered event listeners (component callbacks). */
const listeners = new Set()

// ── Internal helpers ─────────────────────────────────────────────────────────

function _reconnectDelay() {
  // Exponential back-off: 1s, 2s, 4s, 8s … capped at 30s
  return Math.min(BASE_RECONNECT_DELAY_MS * 2 ** reconnectAttempt, MAX_RECONNECT_DELAY_MS)
}

function _dispatch(msg) {
  listeners.forEach((cb) => {
    try { cb(msg) } catch (e) { console.error('[useWebSocket] listener error', e) }
  })
}

function _connect() {
  if (socket && (socket.readyState === WebSocket.CONNECTING || socket.readyState === WebSocket.OPEN)) {
    return // already alive
  }

  isIntentionallyClosed = false
  socket = new WebSocket(WS_URL)

  socket.addEventListener('open', () => {
    console.log('[useWebSocket] Connected to', WS_URL)
    reconnectAttempt = 0
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  })

  socket.addEventListener('message', (event) => {
    try {
      const msg = JSON.parse(event.data)
      _dispatch(msg)
    } catch {
      console.warn('[useWebSocket] Unparseable message:', event.data)
    }
  })

  socket.addEventListener('close', (event) => {
    if (isIntentionallyClosed) return
    const delay = _reconnectDelay()
    console.warn(`[useWebSocket] Disconnected (code=${event.code}). Reconnecting in ${delay}ms…`)
    reconnectAttempt++
    reconnectTimer = setTimeout(_connect, delay)
  })

  socket.addEventListener('error', (event) => {
    console.error('[useWebSocket] Error:', event)
    // 'close' will fire right after; reconnect logic lives there
  })
}

// Start the singleton connection immediately when this module is first imported
_connect()

// ── Public composable ────────────────────────────────────────────────────────

/**
 * Returns WebSocket utilities.
 *
 * @returns {{
 *   onEvent: (callback: (msg: object) => void) => (() => void),
 *   disconnect: () => void,
 *   reconnect: () => void,
 * }}
 */
export function useWebSocket() {
  /**
   * Register a listener for incoming WebSocket messages.
   *
   * @param {(msg: object) => void} callback
   * @returns {() => void}  Call this in onUnmounted() to clean up.
   */
  function onEvent(callback) {
    listeners.add(callback)
    return () => listeners.delete(callback)
  }

  /** Permanently close the connection (e.g. on logout). */
  function disconnect() {
    isIntentionallyClosed = true
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    socket?.close()
  }

  /** Force an immediate reconnect attempt. */
  function reconnect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    reconnectAttempt = 0
    _connect()
  }

  return { onEvent, disconnect, reconnect }
}
