<script setup>
defineProps({
    user: {
        type: Object,
        required: true
    }
})

defineEmits(['revoke', 'remove'])
</script>

<template>
    <div class="user-item">
        <div class="user-info">
            <span class="user-avatar" :style="{'--accent': user.accent}">{{ user.initials }}</span>
            <div>
                <h3>{{ user.name }}</h3>
                <p>{{ user.role }}</p>
            </div>
        </div>
        <div class="actions">
            <span class="status" :class="user.status">{{ user.status.toUpperCase() }}</span>
            <button v-if="user.status === 'active'" class="btn-revoke" @click="$emit('revoke', user.id)">REVOKE</button>
            <button v-if="user.status === 'revoked'" class="btn-remove" @click="$emit('remove', user.id)">REMOVE</button>
        </div>
    </div>
</template>

<style scoped>
.user-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1rem 1.5rem;
    transition: all 0.2s ease;
}

.user-item:hover {
    border-color: color-mix(in srgb, var(--neon-blue) 50%, transparent);
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.05);
}

.user-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.user-avatar {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 45px;
    height: 45px;
    background: color-mix(in srgb, var(--accent) 10%, transparent);
    color: var(--accent);
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
    border-radius: 10px;
    font-weight: bold;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
    transition: all 0.3s;
}

.user-info h3 {
    margin: 0 0 4px 0;
    color: var(--text-main);
    font-size: 1rem;
    font-family: 'Space Grotesk', sans-serif;
}

.user-info p {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.actions {
    display: flex;
    align-items: center;
    gap: 15px;
}

.status {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
}

.status.active {
    background: rgba(12, 255, 154, 0.1);
    color: var(--neon-green);
    border: 1px solid rgba(12, 255, 154, 0.3);
}

.status.revoked {
    background: rgba(255, 51, 102, 0.1);
    color: var(--neon-red);
    border: 1px solid rgba(255, 51, 102, 0.3);
}

.btn-revoke {
    background: transparent;
    border: 1px solid rgba(255, 51, 102, 0.5);
    color: var(--neon-red);
    padding: 5px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.65rem;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.2s;
}

.btn-revoke:hover {
    background: rgba(255, 51, 102, 0.15);
    border-color: var(--neon-red);
    box-shadow: 0 0 8px rgba(255, 51, 102, 0.3);
}

.btn-remove {
    background: transparent;
    border: 1px solid rgba(107, 130, 152, 0.5);
    color: var(--text-muted);
    padding: 5px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.65rem;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.2s;
}

.btn-remove:hover {
    background: rgba(107, 130, 152, 0.15);
    border-color: var(--text-main);
    color: var(--text-main);
}
</style>
