<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import UserStatCard from '@/components/UserStatCard.vue'
import { fetchHistory } from '@/services/dashboard.js'
import { useWebSocket } from '@/composables/useWebSocket.js'

const currentFilter = ref('all')  // 'all' | 'granted' | 'rejected'
const historyLogs   = ref([])
const historyLoading = ref(true)
const historyError   = ref('')
const totalLogs      = ref(0)

const currentPage  = ref(1)
const itemsPerPage = 10

const filteredLogs = computed(() => {
    if (currentFilter.value === 'all') return historyLogs.value
    return historyLogs.value.filter(log => log.status === currentFilter.value)
})

const totalPages = computed(() => Math.ceil(filteredLogs.value.length / itemsPerPage) || 1)

const paginatedLogs = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage
    return filteredLogs.value.slice(start, start + itemsPerPage)
})

const paginationDisplay = computed(() => {
    const total = filteredLogs.value.length
    if (total === 0) return ''
    const start = (currentPage.value - 1) * itemsPerPage + 1
    const end = Math.min(currentPage.value * itemsPerPage, total)
    return `Showing ${start}–${end} of ${total} records`
})

const visiblePages = computed(() => {
    const pages = []
    const total = totalPages.value
    let start = Math.max(1, currentPage.value - 2)
    let end = Math.min(total, start + 4)

    if (end - start < 4) {
        start = Math.max(1, end - 4)
    }

    for (let i = start; i <= end; i++) {
        pages.push(i)
    }
    return pages
})

function setFilter(filter) {
    currentFilter.value = filter
    currentPage.value = 1
}

function prevPage() {
    if (currentPage.value > 1) currentPage.value--
}

function nextPage() {
    if (currentPage.value < totalPages.value) currentPage.value++
}

function setPage(page) {
    currentPage.value = page
}

function timeAgo(isoString) {
    const diff = Math.max(0, Math.floor((Date.now() - new Date(isoString)) / 1000))
    if (diff < 60)    return `${diff}s ago`
    if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

function formatTime(isoString) {
    return new Date(isoString).toLocaleString(undefined, {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })
}

// ── WebSocket — live log append ───────────────────────────────────────────────
const { onEvent } = useWebSocket()
let offEvent = null

function handleWsEvent(msg) {
    if (msg.event === 'scan_result') {
        const newEntry = {
            log_id:     `ws-${Date.now()}`,
            card_name:  msg.user_name || msg.card_name || 'Unknown',
            status:     msg.status,
            created_at: msg.timestamp || new Date().toISOString(),
        }
        historyLogs.value  = [newEntry, ...historyLogs.value]
        totalLogs.value    += 1
    }
}

onMounted(async () => {
    offEvent = onEvent(handleWsEvent)
    try {
        const history = await fetchHistory(null)
        historyLogs.value = history.logs || []
        totalLogs.value   = history.total ?? historyLogs.value.length
    } catch (error) {
        historyError.value = error?.message || 'Failed to load access history.'
    } finally {
        historyLoading.value = false
    }
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
                <h1>ACCESS LOGS</h1>
            </div>
            <div class="status-indicator">
                <span class="pulse"></span>
                SYSTEM ONLINE
            </div>
        </header>

        <main class="main-content">
            <section class="panel">
                <!-- Panel toolbar: title + count + filters -->
                <div class="panel-toolbar">
                    <div class="toolbar-left">
                        <h2 class="panel-title">FULL ACCESS HISTORY</h2>
                        <p class="log-count">{{ totalLogs }} LOGS</p>
                    </div>
                    <div class="filter-controls">
                        <button :class="{ active: currentFilter === 'all' }"      @click="setFilter('all')">ALL</button>
                        <button :class="{ active: currentFilter === 'granted' }"  @click="setFilter('granted')">GRANTED</button>
                        <button :class="{ active: currentFilter === 'rejected' }" @click="setFilter('rejected')">REJECTED</button>
                    </div>
                </div>

                <!-- Loading -->
                <div v-if="historyLoading" class="logs-container">
                    <div class="log-skeleton" v-for="n in 8" :key="n"></div>
                </div>

                <!-- Error -->
                <div v-else-if="historyError" class="state-banner state-error">
                    {{ historyError }}
                </div>

                <!-- Empty -->
                <div v-else-if="historyLogs.length === 0" class="state-banner state-empty">
                    No access events recorded yet.
                </div>

                <!-- Log table — card view on mobile, table on desktop -->
                <template v-else>
                    <!-- Mobile: card list -->
                    <div class="logs-container mobile-logs">
                        <UserStatCard
                            v-for="log in paginatedLogs"
                            :key="log.log_id"
                            :name="log.card_name"
                            :status="log.status"
                            :time="timeAgo(log.created_at)"
                        />
                        <div v-if="filteredLogs.length === 0" class="empty-state">
                            NO LOGS FOUND FOR THIS FILTER
                        </div>
                    </div>

                    <!-- Desktop: table view -->
                    <div class="table-container desktop-logs">
                        <table class="log-table">
                            <thead>
                                <tr>
                                    <th>STATUS</th>
                                    <th>CARD / USER</th>
                                    <th>TIMESTAMP</th>
                                    <th>RELATIVE</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr
                                    v-for="log in paginatedLogs"
                                    :key="log.log_id"
                                    :class="log.status"
                                >
                                    <td>
                                        <span class="status-pill" :class="log.status">
                                            {{ log.status === 'granted' ? '✓' : '✗' }}
                                            {{ log.status.toUpperCase() }}
                                        </span>
                                    </td>
                                    <td class="td-name">{{ log.card_name || '—' }}</td>
                                    <td class="td-time">{{ formatTime(log.created_at) }}</td>
                                    <td class="td-relative">{{ timeAgo(log.created_at) }}</td>
                                </tr>
                            </tbody>
                        </table>
                        <div v-if="filteredLogs.length === 0" class="empty-state">
                            NO LOGS FOUND FOR THIS FILTER
                        </div>
                    </div>
                </template>

                <!-- Pagination -->
                <div v-if="filteredLogs.length > 0 && !historyLoading" class="pagination-footer">
                    <div class="pagination-info">
                        {{ paginationDisplay }}
                    </div>

                    <div class="pagination-controls">
                        <button
                            class="page-btn prev-next"
                            :disabled="currentPage === 1"
                            @click="prevPage"
                        >
                            &lt; Prev
                        </button>

                        <div class="page-numbers">
                            <button
                                v-for="p in visiblePages"
                                :key="p"
                                class="page-btn"
                                :class="{ active: p === currentPage }"
                                @click="setPage(p)"
                            >
                                {{ p }}
                            </button>
                        </div>

                        <button
                            class="page-btn prev-next"
                            :disabled="currentPage === totalPages"
                            @click="nextPage"
                        >
                            Next &gt;
                        </button>
                    </div>

                    <div class="pagination-summary">
                        Page {{ currentPage }} of {{ totalPages }}
                    </div>
                </div>
            </section>
        </main>
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

/* ── Main content ─────────────────────────────────────────────── */
.main-content {
    display: flex;
    flex-direction: column;
}

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
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.toolbar-left { display: flex; flex-direction: column; }

.panel-title {
    font-size: 0.85rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    border-left: 2px solid var(--neon-blue);
    padding-left: 12px;
    margin: 0;
}

.log-count {
    margin: 0.4rem 0 0 14px;
    color: var(--text-muted);
    font-size: 0.7rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
}

.filter-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.filter-controls button {
    background: rgba(255, 255, 255, 0.05);
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

.filter-controls button:hover,
.filter-controls button.active {
    border-color: var(--neon-blue);
    color: var(--neon-blue);
    background: rgba(0, 210, 255, 0.1);
    box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

/* ── Mobile card list ─────────────────────────────────────────── */
.logs-container { display: flex; flex-direction: column; gap: 0.75rem; }

/* Show mobile list, hide desktop table by default */
.mobile-logs  { display: flex; }
.desktop-logs { display: none; }

/* ── Desktop table ────────────────────────────────────────────── */
.table-container {
    overflow-x: auto;
    border-radius: 10px;
    border: 1px solid var(--border-color);
}

.log-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Space Grotesk', sans-serif;
}

.log-table thead tr {
    background: rgba(0, 210, 255, 0.05);
    border-bottom: 1px solid var(--border-color);
}

.log-table th {
    padding: 0.85rem 1.25rem;
    text-align: left;
    font-size: 0.68rem;
    letter-spacing: 2px;
    color: var(--text-muted);
    font-weight: 700;
    white-space: nowrap;
}

.log-table tbody tr {
    border-bottom: 1px solid rgba(0, 210, 255, 0.06);
    transition: background 0.15s;
}

.log-table tbody tr:last-child {
    border-bottom: none;
}

.log-table tbody tr:hover {
    background: rgba(0, 210, 255, 0.03);
}

.log-table td {
    padding: 0.9rem 1.25rem;
    font-size: 0.85rem;
    color: var(--text-main);
    vertical-align: middle;
}

.td-name { font-weight: 600; }
.td-time { color: var(--text-muted); font-size: 0.8rem; }
.td-relative { color: var(--text-muted); font-size: 0.8rem; }

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1px;
    white-space: nowrap;
}

.status-pill.granted {
    background: rgba(12, 255, 154, 0.1);
    color: var(--neon-green);
    border: 1px solid rgba(12, 255, 154, 0.3);
}

.status-pill.rejected {
    background: rgba(255, 51, 102, 0.1);
    color: var(--neon-red);
    border: 1px solid rgba(255, 51, 102, 0.3);
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

.log-skeleton {
    height: 61px;
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
}

/* ── Pagination ───────────────────────────────────────────────── */
.pagination-footer {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
}

.pagination-info {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
}

.pagination-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    justify-content: center;
}

.page-numbers { display: flex; gap: 6px; }

.page-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    transition: all 0.2s;
}

.page-btn.prev-next { padding: 6px 16px; }

.page-btn:hover:not(:disabled) {
    border-color: var(--neon-blue);
    color: var(--neon-blue);
    background: rgba(0, 210, 255, 0.1);
}

.page-btn.active {
    background: rgba(0, 210, 255, 0.15);
    border-color: var(--neon-blue);
    color: var(--neon-blue);
    box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

.page-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.pagination-summary {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
}

/* ══════════════════════════════════════════════════════════════ */
/* Tablet (768px+)                                               */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 768px) {
    .dashboard { padding: 2rem 2.5rem; }

    .pagination-footer { flex-direction: row; justify-content: space-between; }
}

/* ══════════════════════════════════════════════════════════════ */
/* Desktop (1024px+) — switch to table view                      */
/* ══════════════════════════════════════════════════════════════ */
@media (min-width: 1024px) {
    .dashboard { padding: 2rem 2.5rem; }

    /* Hide card list, show table */
    .mobile-logs  { display: none; }
    .desktop-logs { display: block; }

    .panel-toolbar { flex-wrap: nowrap; align-items: center; }
    .toolbar-left { flex-direction: row; align-items: center; gap: 12px; }
    .log-count { margin: 0; }
}
</style>
