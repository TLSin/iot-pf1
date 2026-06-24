<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import UserCard from './UserCard.vue'
import RegistrationModal from './RegistrationModal.vue'
import {
    fetchCards,
    addCard,
    revokeCard as revokeCardRequest,
    removeCard as removeCardRequest,
    registerCardMode,
} from '@/services/user.js'
import { useWebSocket } from '@/composables/useWebSocket.js'

// ── Card list ─────────────────────────────────────────────────────────────────
const users = ref([])
const usersLoading = ref(true)
const userError = ref('')
const savingCard = ref(false)
const saveError = ref('')

const activeCount  = computed(() => users.value.filter(u => u.status === 'active').length)
const revokedCount = computed(() => users.value.filter(u => u.status === 'revoked').length)

function makeInitials(name) {
    const parts = (name || '').trim().split(/\s+/).filter(Boolean)
    if (parts.length > 1) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return 'RF'
}

function normalizeStatus(status) {
    return status === 'revoke' ? 'revoked' : status
}

function cardToUser(card) {
    const status = normalizeStatus(card.status)
    const name   = card.card_name || 'Unnamed Card'
    return {
        id:       card.card_id,
        name,
        role:     card.card_role || 'Standard User',
        initials: makeInitials(name),
        status,
        accent:   status === 'active' ? 'var(--neon-green)' : 'var(--neon-red)',
    }
}

async function loadCards() {
    usersLoading.value = true
    userError.value = ''
    try {
        const result = await fetchCards()
        users.value = (result.cards || []).map(cardToUser)
    } catch (error) {
        userError.value = error?.message || 'Failed to load registered cards.'
    } finally {
        usersLoading.value = false
    }
}

const revokeUser = async (id) => {
    userError.value = ''
    try {
        const card = await revokeCardRequest(id)
        users.value = users.value.map(user => user.id === id ? cardToUser(card) : user)
    } catch (error) {
        userError.value = error?.message || 'Failed to revoke card.'
    }
}

const removeCard = async (id) => {
    userError.value = ''
    try {
        await removeCardRequest(id)
        users.value = users.value.filter(user => user.id !== id)
    } catch (error) {
        userError.value = error?.message || 'Failed to remove card.'
    }
}

// ── Registration flow ─────────────────────────────────────────────────────────
const isRegistering = ref(false)       // true while waiting for RFID scan
const showModal     = ref(false)
const scannedCardHash = ref('')        // populated by WebSocket event

/** Step 1 — User clicks "+ REGISTER CARD" */
const registerCard = async () => {
    if (isRegistering.value || usersLoading.value) return
    isRegistering.value = true
    saveError.value = ''
    scannedCardHash.value = ''

    try {
        // Tell FastAPI to enter registration mode.
        // scan.py will poll and send 'R' to Arduino.
        await registerCardMode()
        // isRegistering stays true — we wait for the WebSocket event
    } catch (error) {
        saveError.value = error?.message || 'Failed to activate registration mode.'
        isRegistering.value = false
    }
}

/** Step 6 — User clicked Save in the modal */
const saveNewUser = async (fields) => {
    savingCard.value = true
    saveError.value = ''
    try {
        const card = await addCard({
            card_name:      fields.name,
            card_role:      fields.role,
            card_uuid_hash: fields.card_hash,  // the real scanned RFID hash
        })
        users.value.unshift(cardToUser(card))
        showModal.value = false
        scannedCardHash.value = ''
    } catch (error) {
        saveError.value = error?.message || 'Failed to register card.'
    } finally {
        savingCard.value = false
    }
}

// ── WebSocket — listen for registration_card_detected ─────────────────────────
const { onEvent } = useWebSocket()
let offEvent = null

function handleWsEvent(msg) {
    if (msg.event === 'registration_card_detected' && isRegistering.value) {
        scannedCardHash.value = msg.card_hash
        isRegistering.value   = false
        showModal.value       = true
    }
}

onMounted(() => {
    loadCards()
    offEvent = onEvent(handleWsEvent)
})

onUnmounted(() => {
    offEvent?.()
})
</script>

<template>
    <div class="dashboard">
        <header class="page-header">
            <div class="logo">
                <span class="icon-pulse"></span>
                <h1>USER DIRECTORY</h1>
            </div>
            <div class="status-indicator">
                <span class="pulse"></span>
                SYSTEM ONLINE
            </div>
        </header>

        <main class="main-content">
            <section class="panel">

                <!-- Panel toolbar -->
                <div class="panel-toolbar">
                    <div class="toolbar-left">
                        <h2 class="panel-title">AUTHORIZED USERS</h2>
                        <span class="cards-status">{{ activeCount }} ACTIVE &bull; {{ revokedCount }} REVOKED</span>
                    </div>

                    <button
                        class="btn-register"
                        @click="registerCard"
                        :disabled="isRegistering || usersLoading"
                        :class="{ 'is-scanning': isRegistering }"
                    >
                        <span v-if="!isRegistering">+ REGISTER CARD</span>
                        <span v-else class="scanning-text">
                            <span class="dot-pulse">⬤</span> WAITING FOR RFID...
                        </span>
                    </button>
                </div>

                <!-- Scanning notice banner -->
                <div v-if="isRegistering" class="register-notice">
                    <span class="notice-icon">📡</span>
                    PLACE YOUR RFID CARD ON THE READER
                </div>

                <!-- Error banner -->
                <div v-if="userError" class="state-banner state-error">
                    {{ userError }}
                </div>

                <!-- Loading skeletons -->
                <div v-if="usersLoading" class="user-grid">
                    <div class="user-skeleton" v-for="n in 6" :key="n"></div>
                </div>

                <!-- User grid -->
                <div v-else class="user-grid">
                    <UserCard
                        v-for="user in users"
                        :key="user.id"
                        :user="user"
                        @revoke="revokeUser"
                        @remove="removeCard"
                    />
                    <div v-if="users.length === 0" class="empty-state">
                        NO USERS REGISTERED IN SYSTEM
                    </div>
                </div>
            </section>
        </main>

        <!-- Registration Modal — only appears after RFID card is detected -->
        <RegistrationModal
            v-if="showModal"
            :saving="savingCard"
            :error="saveError"
            :cardHash="scannedCardHash"
            @close="showModal = false; scannedCardHash = ''"
            @save="saveNewUser"
        />
    </div>
</template>

<style scoped>
/* ── Dashboard shell ──────────────────────────────────────────── */
.dashboard {
    min-height: 100vh;
    padding: 1.5rem 1.25rem;
    box-sizing: border-box;
    background-image:
        radial-gradient(circle at 10% 20%, rgba(0, 210, 255, 0.03) 0%, transparent 20%),
        linear-gradient(rgba(0, 210, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 210, 255, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 40px 40px, 40px 40px;
}

/* ── Page header ──────────────────────────────────────────────── */
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: nowrap;
    gap: 1rem;
}

.logo { display: flex; align-items: center; gap: 10px; }

.icon-pulse {
    width: 8px;
    height: 15px;
    background-color: var(--neon-blue);
    box-shadow: 0 0 10px var(--neon-blue);
}

.logo h1 {
    font-size: 1.3rem;
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 2px;
    margin: 0;
    color: var(--text-main);
    text-shadow: 0 0 5px rgba(226, 241, 248, 0.3);
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--neon-green);
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 1px;
    white-space: nowrap;
    flex-shrink: 0;
}

.pulse {
    width: 8px;
    height: 8px;
    background-color: var(--neon-green);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--neon-green);
    animation: pulse-anim 1.5s infinite alternate;
}

@keyframes pulse-anim {
    0%   { opacity: 0.5; box-shadow: 0 0 2px var(--neon-green); }
    100% { opacity: 1;   box-shadow: 0 0 12px var(--neon-green); }
}

/* ── Panel ────────────────────────────────────────────────────── */
.main-content { display: flex; flex-direction: column; }

.panel {
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05);
}

/* ── Panel toolbar ────────────────────────────────────────────── */
.panel-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    flex-wrap: wrap;
}

.toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.panel-title {
    font-size: 0.85rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    border-left: 2px solid var(--neon-blue);
    padding-left: 12px;
    margin: 0;
}

.cards-status {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--neon-blue);
    background: rgba(0, 210, 255, 0.1);
    padding: 4px 10px;
    border-radius: 10px;
    letter-spacing: 1px;
    white-space: nowrap;
}

/* ── Register button ──────────────────────────────────────────── */
.btn-register {
    background: rgba(12, 255, 154, 0.1);
    border: 1px solid var(--neon-green);
    color: var(--neon-green);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.75rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 1px;
    transition: all 0.2s;
    box-shadow: 0 0 10px rgba(12, 255, 154, 0.1);
    white-space: nowrap;
    flex-shrink: 0;
}

.btn-register:hover:not(:disabled) {
    background: rgba(12, 255, 154, 0.2);
    box-shadow: 0 0 15px rgba(12, 255, 154, 0.3);
}

.btn-register.is-scanning {
    border-color: #ffcc00;
    color: #ffcc00;
    background: rgba(255, 204, 0, 0.1);
    box-shadow: 0 0 12px rgba(255, 204, 0, 0.2);
    cursor: wait;
}

.btn-register:disabled {
    opacity: 0.85;
    cursor: wait;
}

.scanning-text {
    display: flex;
    align-items: center;
    gap: 6px;
    animation: blink 1s infinite;
}

.dot-pulse {
    font-size: 0.5rem;
    animation: pulse-dot 1s infinite alternate;
}

@keyframes pulse-dot {
    0%   { opacity: 0.3; }
    100% { opacity: 1;   }
}

@keyframes blink { 50% { opacity: 0.6; } }

/* ── Notices ──────────────────────────────────────────────────── */
.register-notice {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: rgba(255, 204, 0, 0.06);
    border: 1px solid rgba(255, 204, 0, 0.25);
    border-radius: 8px;
    color: #ffcc00;
    font-size: 0.78rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 1.2rem;
    animation: blink 1.5s infinite;
}

.notice-icon { font-size: 1rem; animation: none; }

/* ── User grid — single col mobile, multi-col desktop ─────────── */
.user-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
}

/* ── State elements ───────────────────────────────────────────── */
.state-banner {
    padding: 14px 18px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.5px;
    text-align: center;
    margin-bottom: 1rem;
}

.state-error {
    background: rgba(255, 51, 102, 0.07);
    border: 1px solid rgba(255, 51, 102, 0.3);
    color: var(--neon-red);
}

.user-skeleton {
    height: 79px;
    border-radius: 10px;
    background: linear-gradient(90deg,
        rgba(0, 210, 255, 0.04) 25%,
        rgba(0, 210, 255, 0.10) 50%,
        rgba(0, 210, 255, 0.04) 75%);
    background-size: 800px 100%;
    animation: shimmer 1.6s infinite linear;
    border: 1px solid var(--border-color);
}

@keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position:  400px 0; }
}

.empty-state {
    text-align: center;
    padding: 2rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    font-size: 0.9rem;
    grid-column: 1 / -1; /* span full width in grid */
}

/* ══════════════════════════════════════════════════════════════ */
/* Tablet (768px+) — 2-column card grid                          */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 768px) {
    .dashboard { padding: 2rem 2.5rem; }

    .user-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* ══════════════════════════════════════════════════════════════ */
/* Desktop (1024px+) — wider spacing, toolbar tweaks             */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 1024px) {
    .dashboard { padding: 2rem 2.5rem; }

    .panel-toolbar { flex-wrap: nowrap; }
}

/* ══════════════════════════════════════════════════════════════ */
/* Large desktop (1280px+) — 3-column card grid                  */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 1280px) {
    .user-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
</style>
