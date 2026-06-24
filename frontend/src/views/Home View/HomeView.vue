<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ScanCard from './ScanCard.vue'
import StatsCard from './StatsCard.vue'
import UserStatCard from '@/components/UserStatCard.vue'
import { fetchAnalytics, fetchHistory } from '@/services/dashboard.js'
import { useWebSocket } from '@/composables/useWebSocket.js'

// ── Scan state ────────────────────────────────────────────────────────────────
const systemState = ref('idle')      // 'idle' | 'scanning' | 'granted' | 'rejected'
const lastScanName = ref(null)       // card holder name
const lastScanTime = ref(null)       // formatted time string
const rejectionReason = ref(null)    // reason string for rejected scans

// ── Analytics ─────────────────────────────────────────────────────────────────
const analytics = ref(null)
const analyticsLoading = ref(true)
const analyticsError = ref('')

// ── History ───────────────────────────────────────────────────────────────────
const historyLogs = ref([])
const historyLoading = ref(true)
const historyError = ref('')

// ── Helpers ───────────────────────────────────────────────────────────────────
function timeAgo(isoString) {
    const diff = Math.floor((Date.now() - new Date(isoString)) / 1000)
    if (diff < 60)    return `${diff}s ago`
    if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

let resetTimer = null

function resetToIdle() {
    if (resetTimer) clearTimeout(resetTimer)
    resetTimer = setTimeout(() => {
        systemState.value = 'idle'
        rejectionReason.value = null
    }, 5000)
}

// ── WebSocket event handler ───────────────────────────────────────────────────
const { onEvent } = useWebSocket()

let offEvent = null

function handleWsEvent(msg) {
    if (msg.event === 'scanning') {
        systemState.value = 'scanning'
        rejectionReason.value = null
        return
    }

    if (msg.event === 'scan_result') {
        const status = msg.status // 'granted' | 'rejected'
        systemState.value = status

        if (status === 'granted') {
            lastScanName.value = msg.user_name || msg.card_name || 'Unknown'
            lastScanTime.value = msg.timestamp ? timeAgo(msg.timestamp) : null
            rejectionReason.value = null

            // Update analytics counters live
            if (analytics.value) {
                analytics.value = {
                    ...analytics.value,
                    total_granted: (analytics.value.total_granted ?? 0) + 1,
                }
            }
        } else {
            rejectionReason.value = msg.reason || 'Card rejected'
            lastScanTime.value = msg.timestamp ? timeAgo(msg.timestamp) : null

            if (analytics.value) {
                analytics.value = {
                    ...analytics.value,
                    total_rejected: (analytics.value.total_rejected ?? 0) + 1,
                }
            }
        }

        // Prepend to recent history list
        const newEntry = {
            log_id: `ws-${Date.now()}`,
            card_name: msg.user_name || msg.card_name || 'Unknown',
            status,
            created_at: msg.timestamp || new Date().toISOString(),
        }
        historyLogs.value = [newEntry, ...historyLogs.value].slice(0, 10)

        // Auto-reset the scan card to idle after 5 s
        resetToIdle()
    }
}

// ── Fetch on mount ────────────────────────────────────────────────────────────
onMounted(async () => {
    offEvent = onEvent(handleWsEvent)

    const [analyticsResult, historyResult] = await Promise.allSettled([
        fetchAnalytics(),
        fetchHistory(10),
    ])

    analyticsLoading.value = false
    if (analyticsResult.status === 'fulfilled') {
        analytics.value = analyticsResult.value
    } else {
        analyticsError.value = analyticsResult.reason?.message || 'Failed to load analytics.'
    }

    historyLoading.value = false
    if (historyResult.status === 'fulfilled') {
        historyLogs.value = historyResult.value.logs
    } else {
        historyError.value = historyResult.reason?.message || 'Failed to load access history.'
    }
})

onUnmounted(() => {
    offEvent?.()
    if (resetTimer) clearTimeout(resetTimer)
})
</script>

<template>
    <div class="dashboard" :class="systemState">

        <!-- Page header -->
        <header class="page-header">
            <div class="logo">
                <span class="icon-pulse"></span>
                <h1>OVERVIEW</h1>
            </div>
            <div class="status-indicator">
                <span class="pulse"></span>
                SYSTEM ONLINE
            </div>
        </header>

        <!-- ── Desktop: 2-column grid ── Mobile: single column ── -->
        <div class="content-grid">

            <!-- LEFT COLUMN: scan terminal -->
            <section class="panel panel-primary">
                <div class="panel-header">
                    <h2>TERMINAL INTERFACE</h2>
                </div>

                <!-- Dynamic RFID Banner -->
                <div class="rfid-status">
                    <div class="glitch-wrapper">
                        <span v-if="systemState === 'idle'">WAITING FOR RFID SCAN</span>
                        <span v-else-if="systemState === 'scanning'">SCANNING RFID... VERIFYING CARD...</span>
                        <span v-else-if="systemState === 'granted'">ACCESS GRANTED — SAFE UNLOCKED</span>
                        <span v-else-if="systemState === 'rejected'">ACCESS DENIED — SAFE LOCKED</span>
                    </div>
                </div>

                <div class="scan-wrapper">
                    <ScanCard
                        :state="systemState"
                        :lastScanName="lastScanName"
                        :lastScanTime="lastScanTime"
                        :rejectionReason="rejectionReason"
                    />
                </div>
            </section>

            <!-- RIGHT COLUMN: analytics + history -->
            <div class="right-column">

                <!-- Analytics metrics row -->
                <section class="panel panel-secondary">
                    <div class="panel-header">
                        <h2>ANALYTICS &amp; METRICS</h2>
                    </div>

                    <!-- Loading skeleton -->
                    <div v-if="analyticsLoading" class="scan-stats">
                        <div class="stat-skeleton" v-for="n in 3" :key="n"></div>
                    </div>

                    <!-- Error state -->
                    <div v-else-if="analyticsError" class="state-banner state-error">
                        {{ analyticsError }}
                    </div>

                    <!-- Real data — 3 cards on mobile, 3-col on desktop -->
                    <div v-else class="scan-stats">
                        <StatsCard>
                            <div class="stat-icon text-green">✓</div>
                            <h2 class="stat-val text-green">{{ analytics?.total_granted ?? 0 }}</h2>
                            <p class="stat-label">Granted</p>
                        </StatsCard>
                        <StatsCard>
                            <div class="stat-icon text-red">✗</div>
                            <h2 class="stat-val text-red">{{ analytics?.total_rejected ?? 0 }}</h2>
                            <p class="stat-label">Denied</p>
                        </StatsCard>
                        <StatsCard>
                            <div class="stat-icon text-blue">⚑</div>
                            <h2 class="stat-val text-blue">{{ analytics?.active_cards ?? 0 }}</h2>
                            <p class="stat-label">Active</p>
                        </StatsCard>
                    </div>
                </section>

                <!-- Recent access logs -->
                <section class="panel panel-logs">
                    <div class="panel-header">
                        <h2>RECENT ACCESS LOGS</h2>
                    </div>

                    <!-- History loading -->
                    <div v-if="historyLoading" class="logs-container">
                        <div class="log-skeleton" v-for="n in 4" :key="n"></div>
                    </div>

                    <!-- History error -->
                    <div v-else-if="historyError" class="state-banner state-error">
                        {{ historyError }}
                    </div>

                    <!-- History empty -->
                    <div v-else-if="historyLogs.length === 0" class="state-banner state-empty">
                        No access events recorded yet.
                    </div>

                    <!-- History list -->
                    <div v-else class="logs-container">
                        <UserStatCard
                            v-for="log in historyLogs"
                            :key="log.log_id"
                            :name="log.card_name"
                            :status="log.status"
                            :time="timeAgo(log.created_at)"
                        />
                    </div>
                </section>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* ── Base dashboard shell ─────────────────────────────────────── */
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

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
}

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

/* ── Content grid — single column mobile, 2-col desktop ───────── */
.content-grid {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.right-column {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

/* ── Panels ───────────────────────────────────────────────────── */
.panel {
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05);
}

.panel-header h2 {
    font-size: 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    margin-bottom: 1.25rem;
    border-left: 2px solid var(--neon-blue);
    padding-left: 12px;
}

/* ── RFID status banner ───────────────────────────────────────── */
.rfid-status {
    width: 100%;
    padding: 1rem;
    text-align: center;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 700;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1.2px;
    margin-bottom: 1.25rem;
    transition: all 0.3s ease;
    border: 1px solid transparent;
}

.idle .rfid-status {
    background: rgba(0, 210, 255, 0.08);
    color: var(--neon-blue);
    border-color: rgba(0, 210, 255, 0.2);
    box-shadow: inset 0 0 15px rgba(0, 210, 255, 0.05);
}

.scanning .rfid-status {
    background: rgba(255, 204, 0, 0.08);
    color: #ffcc00;
    border-color: rgba(255, 204, 0, 0.3);
    box-shadow: inset 0 0 15px rgba(255, 204, 0, 0.1);
    animation: blink 0.8s infinite;
}

.granted .rfid-status {
    background: rgba(12, 255, 154, 0.08);
    color: var(--neon-green);
    border-color: var(--neon-green);
    box-shadow: 0 0 20px rgba(12, 255, 154, 0.15), inset 0 0 15px rgba(12, 255, 154, 0.1);
}

.rejected .rfid-status {
    background: rgba(255, 51, 102, 0.08);
    color: var(--neon-red);
    border-color: var(--neon-red);
    box-shadow: 0 0 20px rgba(255, 51, 102, 0.15), inset 0 0 15px rgba(255, 51, 102, 0.1);
}

@keyframes blink { 50% { opacity: 0.5; } }

/* ── Stats grid ───────────────────────────────────────────────── */
.scan-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
}

/* Text Colors */
.text-green { color: var(--neon-green) !important; text-shadow: 0 0 8px rgba(12,255,154,0.3); }
.text-red   { color: var(--neon-red)   !important; text-shadow: 0 0 8px rgba(255,51,102,0.3); }
.text-blue  { color: var(--neon-blue)  !important; text-shadow: 0 0 8px rgba(0,210,255,0.3); }

.stat-icon  { font-size: 1.4rem; margin-bottom: 5px; }
.stat-val   { font-size: 2rem; font-family: 'Space Grotesk', sans-serif; font-weight: 800; margin: 0; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-top: 5px; }

/* ── Logs list ────────────────────────────────────────────────── */
.logs-container { display: flex; flex-direction: column; gap: 0.75rem; }

/* ── Scan card state reactions ────────────────────────────────── */
.granted .scan-wrapper :deep(.scan-card) {
    border-color: rgba(12, 255, 154, 0.4);
    box-shadow: 0 0 30px rgba(12, 255, 154, 0.05), inset 0 0 20px rgba(12, 255, 154, 0.05);
}
.rejected .scan-wrapper :deep(.scan-card) {
    border-color: rgba(255, 51, 102, 0.4);
    box-shadow: 0 0 30px rgba(255, 51, 102, 0.05), inset 0 0 20px rgba(255, 51, 102, 0.05);
}

/* ── Loading skeletons ────────────────────────────────────────── */
@keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position:  400px 0; }
}

.stat-skeleton {
    height: 90px;
    border-radius: 12px;
    background: linear-gradient(90deg,
        rgba(0, 210, 255, 0.04) 25%,
        rgba(0, 210, 255, 0.10) 50%,
        rgba(0, 210, 255, 0.04) 75%);
    background-size: 800px 100%;
    animation: shimmer 1.6s infinite linear;
    border: 1px solid var(--border-color);
}

.log-skeleton {
    height: 58px;
    border-radius: 10px;
    background: linear-gradient(90deg,
        rgba(0, 210, 255, 0.04) 25%,
        rgba(0, 210, 255, 0.10) 50%,
        rgba(0, 210, 255, 0.04) 75%);
    background-size: 800px 100%;
    animation: shimmer 1.6s infinite linear;
    border: 1px solid var(--border-color);
}

/* ── State banners ────────────────────────────────────────────── */
.state-banner {
    padding: 14px 18px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.5px;
    text-align: center;
}

.state-error {
    background: rgba(255, 51, 102, 0.07);
    border: 1px solid rgba(255, 51, 102, 0.3);
    color: var(--neon-red);
}

.state-empty {
    background: rgba(0, 210, 255, 0.05);
    border: 1px solid rgba(0, 210, 255, 0.15);
    color: var(--text-muted);
}

/* ══════════════════════════════════════════════════════════════ */
/* Tablet (768px+)                                               */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 768px) {
    .dashboard {
        padding: 2rem 2.5rem;
    }

    /* Stats in 3 columns on tablet */
    .scan-stats {
        grid-template-columns: repeat(3, 1fr);
    }

    /* Logs side by side if there are many */
    .logs-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
    }
}

/* ══════════════════════════════════════════════════════════════ */
/* Desktop (1024px+) — 2-column split layout                     */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 1024px) {
    .dashboard {
        padding: 2rem 2.5rem;
    }

    /* Side-by-side: scan panel | right column */
    .content-grid {
        flex-direction: row;
        align-items: flex-start;
        gap: 1.5rem;
    }

    /* Left: scan terminal — fixed width */
    .panel-primary {
        flex: 0 0 380px;
        position: sticky;
        top: 1.5rem;
    }

    /* Right: expands to fill remaining space */
    .right-column {
        flex: 1;
        min-width: 0;
    }

    /* Logs revert to single column (more vertical space) */
    .logs-container {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
}

/* ══════════════════════════════════════════════════════════════ */
/* Large desktop (1280px+) — extra breathing room                */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 1280px) {
    .panel-primary {
        flex: 0 0 420px;
    }
}
</style>