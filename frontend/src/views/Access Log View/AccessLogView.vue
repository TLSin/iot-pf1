<script setup>
import { ref, computed, onMounted } from 'vue'
import UserStatCard from '@/components/UserStatCard.vue'
import { fetchHistory } from '@/services/dashboard.js'

const currentFilter = ref('all') // 'all', 'granted', 'rejected'
const historyLogs = ref([])
const historyLoading = ref(true)
const historyError = ref('')
const totalLogs = ref(0)

const filteredLogs = computed(() => {
    if (currentFilter.value === 'all') return historyLogs.value
    return historyLogs.value.filter(log => log.status === currentFilter.value)
})

function timeAgo(isoString) {
    const diff = Math.max(0, Math.floor((Date.now() - new Date(isoString)) / 1000))
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

onMounted(async () => {
    try {
        const history = await fetchHistory(null)
        historyLogs.value = history.logs || []
        totalLogs.value = history.total ?? historyLogs.value.length
    } catch (error) {
        historyError.value = error?.message || 'Failed to load access history.'
    } finally {
        historyLoading.value = false
    }
})
</script>

<template>
    <div class="dashboard">
        <header class="header">
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
            <section class="panel panel-secondary">
                <div class="panel-header d-flex-between">
                    <div>
                        <h2>FULL ACCESS HISTORY</h2>
                        <p class="log-count">{{ totalLogs }} LOGS</p>
                    </div>
                    <div class="filter-controls">
                        <button :class="{ active: currentFilter === 'all' }" @click="currentFilter = 'all'">ALL</button>
                        <button :class="{ active: currentFilter === 'granted' }" @click="currentFilter = 'granted'">GRANTED</button>
                        <button :class="{ active: currentFilter === 'rejected' }" @click="currentFilter = 'rejected'">REJECTED</button>
                    </div>
                </div>

                <div v-if="historyLoading" class="logs-container">
                    <div class="log-skeleton" v-for="n in 6" :key="n"></div>
                </div>

                <div v-else-if="historyError" class="state-banner state-error">
                    {{ historyError }}
                </div>

                <div v-else-if="historyLogs.length === 0" class="state-banner state-empty">
                    No access events recorded yet.
                </div>

                <div v-else class="logs-container">
                    <UserStatCard 
                        v-for="log in filteredLogs" 
                        :key="log.log_id"
                        :name="log.card_name"
                        :status="log.status"
                        :time="timeAgo(log.created_at)"
                    />
                    
                    <div v-if="filteredLogs.length === 0" class="empty-state">
                        NO LOGS FOUND FOR THIS FILTER
                    </div>
                </div>
            </section>
        </main>
    </div>
</template>

<style scoped>
/* Scoped layout styles for Dashboard wrapper */
.dashboard {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding: 1.5rem 2rem;
    box-sizing: border-box;
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

.panel-secondary {
    max-width: 800px; /* Wider for log listing */
}

/* Panel Header & Filters */
.d-flex-between {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.panel-header h2 {
    font-size: 0.85rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    border-left: 2px solid var(--neon-blue);
    padding-left: 12px;
    margin: 0;
}

.log-count {
    margin: 0.45rem 0 0 14px;
    color: var(--text-muted);
    font-size: 0.7rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
}

.filter-controls {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
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

.filter-controls button:hover, .filter-controls button.active {
    border-color: var(--neon-blue);
    color: var(--neon-blue);
    background: rgba(0, 210, 255, 0.1);
    box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

.logs-container { 
    display: flex; 
    flex-direction: column; 
    gap: 0.8rem; 
}

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
    0% { background-position: -400px 0; }
    100% { background-position: 400px 0; }
}

.empty-state {
    text-align: center;
    padding: 2rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
    letter-spacing: 2px;
    font-size: 0.9rem;
}

@media (max-width: 640px) {
    .dashboard {
        padding: 1rem;
    }

    .header,
    .d-flex-between {
        flex-direction: column;
        align-items: stretch;
    }

    .filter-controls {
        justify-content: flex-start;
    }
}
</style>
