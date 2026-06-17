<script setup>
import AccessPill from './icons/AccessPill.vue'

defineProps({
    name: { type: String, default: 'John Doe' },
    status: { type: String, default: 'granted' }, // 'granted' or 'rejected'
    time: { type: String, default: '40m ago' }
})
</script>

<template>
    <div class="card">
        <div class="user">
            <!-- Dynamic icon and style based on status -->
            <div class="icon" :class="status === 'rejected' ? 'denied' : 'granted'">
                {{ status === 'rejected' ? '✗' : '✓' }}
            </div>
            <h1>{{ name }}</h1>
            <AccessPill :status="status" />
        </div>
        <p class="time">{{ time }}</p>
    </div>
</template>

<style scoped>
.card {
    display: flex;
    justify-content: space-between;
    padding: 12px 16px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    align-items: center;
    transition: border-color 0.2s;
}

.card:hover {
    border-color: var(--neon-blue);
}

.user {
    display: flex;
    align-items: center;
    gap: 10px;
}

.icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 35px;
    height: 35px;
    font-size: 1rem;
    border-radius: 8px;
}

/* Granted Style */
.icon.granted {
    color: var(--neon-green);
    border: 1px solid rgba(12, 255, 154, 0.3);
    background: rgba(12, 255, 154, 0.05);
}

/* Denied Style */
.icon.denied {
    color: var(--neon-red);
    border: 1px solid rgba(255, 51, 102, 0.3);
    background: rgba(255, 51, 102, 0.05);
}

h1 {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-main);
    margin: 0 5px 0 0;
}

.time {
    color: var(--text-muted);
    font-size: 0.8rem;
    margin: 0;
}
</style>