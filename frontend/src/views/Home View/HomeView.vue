<script setup>
import { ref, onMounted } from 'vue'
import ScanCard from './ScanCard.vue'
import StatsCard from './StatsCard.vue'
import UserStatCard from '@/components/UserStatCard.vue'
import { fetchAnalytics, fetchHistory } from '@/services/dashboard.js'

// ── ScanCard state (demo only — untouched per requirements) ──────────────────
const systemState = ref('idle')
const setMockState = (state) => {
    systemState.value = state
    if (state === 'scanning') {
        setTimeout(() => setMockState('granted'), 2000)
    }
}

// ── Analytics ────────────────────────────────────────────────────────────────
const analytics = ref(null)           // null = not yet loaded
const analyticsLoading = ref(true)
const analyticsError = ref('')

// ── History ──────────────────────────────────────────────────────────────────
const historyLogs = ref([])
const historyLoading = ref(true)
const historyError = ref('')

// ── Relative-time helper ─────────────────────────────────────────────────────
function timeAgo(isoString) {
    const diff = Math.floor((Date.now() - new Date(isoString)) / 1000)
    if (diff < 60)   return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

// ── Fetch on mount ────────────────────────────────────────────────────────────
onMounted(async () => {
    // Run both requests in parallel — independent of each other
    const [analyticsResult, historyResult] = await Promise.allSettled([
        fetchAnalytics(),
        fetchHistory(10),
    ])

    // Analytics
    analyticsLoading.value = false
    if (analyticsResult.status === 'fulfilled') {
        analytics.value = analyticsResult.value
    } else {
        analyticsError.value = analyticsResult.reason?.message || 'Failed to load analytics.'
    }

    // History
    historyLoading.value = false
    if (historyResult.status === 'fulfilled') {
        historyLogs.value = historyResult.value.logs
    } else {
        historyError.value = historyResult.reason?.message || 'Failed to load access history.'
    }
})
</script>

<template>
    <div class="dashboard" :class="systemState">
        <header class="header">
            <div class="logo">
                <span class="icon-pulse"></span>
                <h1>OVERVIEW</h1>
            </div>
            <div class="status-indicator">
                <span class="pulse"></span>
                SYSTEM ONLINE
            </div>
        </header>

        <main class="main-content">
            <section class="panel panel-primary">
                <div class="panel-header">
                    <h2>TERMINAL INTERFACE</h2>
                </div>
                
                <!-- Dynamic RFID Banner -->
                <div class="rfid-status">
                    <div class="glitch-wrapper">
                        <span v-if="systemState === 'idle'">WAITING FOR SCRAMBLE CODE... (IDLE)</span>
                        <span v-else-if="systemState === 'scanning'">READING RFID TRACE...</span>
                        <span v-else-if="systemState === 'granted'">ACCESS GRANTED - SAFE UNLOCKED</span>
                        <span v-else-if="systemState === 'denied'">ACCESS DENIED - SAFE LOCKED</span>
                    </div>
                </div>

                <!-- Simulation Controls for UI UI Prototype Demonstration -->
                <div class="test-controls">
                    <button @click="setMockState('idle')" :class="{active: systemState === 'idle'}">IDLE</button>
                    <button @click="setMockState('scanning')" :class="{active: systemState === 'scanning'}">SCAN DEMO</button>
                    <button @click="setMockState('granted')" :class="{active: systemState === 'granted'}">GRANT</button>
                    <button @click="setMockState('denied')" :class="{active: systemState === 'denied'}">DENY</button>
                </div>

                <div class="scan-wrapper">
                    <ScanCard />
                </div>
            </section>

            <section class="panel panel-secondary">
                <div class="panel-header">
                    <h2>ANALYTICS & METRICS</h2>
                </div>
                <!-- Loading skeleton -->
                <div v-if="analyticsLoading" class="scan-stats">
                    <div class="stat-skeleton" v-for="n in 3" :key="n"></div>
                </div>

                <!-- Error state -->
                <div v-else-if="analyticsError" class="state-banner state-error">
                    {{ analyticsError }}
                </div>

                <!-- Real data -->
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

                <div class="panel-header mt-spaced">
                    <h2>RECENT ACCESS LOGS</h2>
                </div>
                <!-- History loading -->
                <div v-if="historyLoading" class="logs-container">
                    <div class="log-skeleton" v-for="n in 3" :key="n"></div>
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
        </main>
    </div>
</template>

<style scoped>
.dashboard {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding: 1.5rem 2rem;
    box-sizing: border-box;
    /* High-tech circuit board / grid background hint */
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(0, 210, 255, 0.03) 0%, transparent 20%),
        linear-gradient(rgba(0, 210, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 210, 255, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 40px 40px, 40px 40px;
}

/* Header */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1rem;
    margin-bottom: 2rem;
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
    font-size: 1.5rem;
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
    font-size: 0.85rem;
    color: var(--neon-green);
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 1px;
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
    0% { opacity: 0.5; box-shadow: 0 0 2px var(--neon-green); }
    100% { opacity: 1; box-shadow: 0 0 12px var(--neon-green); }
}

/* Layout */
.main-content {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
}

.panel {
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05);
    flex: 1;
    min-width: 300px;
}

.panel-primary {
    max-width: 420px;
}

.panel-secondary {
    max-width: 600px;
}

.panel-header h2 {
    font-size: 0.85rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    border-left: 2px solid var(--neon-blue);
    padding-left: 12px;
}

/* Dynamic RFID Status Banner */
.rfid-status {
    width: 100%;
    padding: 1.2rem 1rem;
    text-align: center;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 700;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1.2px;
    margin-bottom: 1.5rem;
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

.denied .rfid-status {
    background: rgba(255, 51, 102, 0.08);
    color: var(--neon-red);
    border-color: var(--neon-red);
    box-shadow: 0 0 20px rgba(255, 51, 102, 0.15), inset 0 0 15px rgba(255, 51, 102, 0.1);
}

@keyframes blink { 50% { opacity: 0.5; } }

/* Controls (Demo Only - for visually testing UI) */
.test-controls {
    display: flex;
    gap: 8px;
    margin-bottom: 1.5rem;
    justify-content: center;
}

.test-controls button {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.7rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.2s;
}

.test-controls button:hover, .test-controls button.active {
    border-color: var(--neon-blue);
    color: var(--neon-blue);
    background: rgba(0, 210, 255, 0.1);
    box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

/* Stats Row */
.scan-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 1rem;
}

/* Text Colors */
.text-green { color: var(--neon-green) !important; text-shadow: 0 0 8px rgba(12,255,154,0.3); }
.text-red { color: var(--neon-red) !important; text-shadow: 0 0 8px rgba(255,51,102,0.3); }
.text-blue { color: var(--neon-blue) !important; text-shadow: 0 0 8px rgba(0,210,255,0.3); }

.stat-icon { font-size: 1.4rem; margin-bottom: 5px; }
.stat-val { font-size: 2rem; font-family: 'Space Grotesk', sans-serif; font-weight: 800; margin: 0; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-top: 5px; }

.mt-spaced { margin-top: 2.5rem; }
.logs-container { display: flex; flex-direction: column; gap: 0.8rem; }
.opacity-muted { opacity: 0.4; filter: grayscale(50%); }


/* --- State Reactions for ScanCard Icon dynamically --- */

/* Granted State */
.granted .scan-wrapper :deep(.scan-card) {
    border-color: rgba(12, 255, 154, 0.4);
    box-shadow: 0 0 30px rgba(12, 255, 154, 0.05), inset 0 0 20px rgba(12, 255, 154, 0.05);
}
.granted .scan-wrapper :deep(.scan-card .icon) {
    background-color: rgba(12, 255, 154, 0.1);
    color: var(--neon-green);
    border-color: var(--neon-green);
    box-shadow: 0 0 25px rgba(12, 255, 154, 0.3);
}
.granted .scan-wrapper :deep(.scan-card h1) { 
    color: var(--neon-green); 
    text-shadow: 0 0 10px rgba(12,255,154,0.3); 
}

/* Denied State */
.denied .scan-wrapper :deep(.scan-card) {
    border-color: rgba(255, 51, 102, 0.4);
    box-shadow: 0 0 30px rgba(255, 51, 102, 0.05), inset 0 0 20px rgba(255, 51, 102, 0.05);
}
.denied .scan-wrapper :deep(.scan-card .icon) {
    background-color: rgba(255, 51, 102, 0.1);
    color: var(--neon-red);
    border-color: var(--neon-red);
    box-shadow: 0 0 25px rgba(255, 51, 102, 0.3);
}
.denied .scan-wrapper :deep(.scan-card h1) { 
    color: var(--neon-red); 
    text-shadow: 0 0 10px rgba(255,51,102,0.3); 
}

/* Scanning State */
.scanning .scan-wrapper :deep(.scan-card .icon) {
    background-color: rgba(255, 204, 0, 0.1);
    color: #ffcc00;
    border-color: #ffcc00;
    box-shadow: 0 0 25px rgba(255, 204, 0, 0.3);
    animation: scan-pulse 1s infinite alternate;
}
@keyframes scan-pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 10px rgba(255, 204, 0, 0.2); }
    100% { transform: scale(1.05); box-shadow: 0 0 30px rgba(255, 204, 0, 0.5); }
}

/* ── Loading skeletons ─────────────────────────────────────────────────────── */
@keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position: 400px 0; }
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

/* ── State banners ─────────────────────────────────────────────────────────── */
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

</style>