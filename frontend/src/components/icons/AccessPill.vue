<script setup>
defineProps({
    status: {
        type: String,
        default: 'granted'
    }
})
</script>

<template>
    <div class="pill" :class="status">
        <p>{{ status === 'rejected' ? 'DENIED' : 'GRANTED' }}</p>
    </div>
</template>

<style scoped>
.pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 1.5rem;
    padding: 0 12px;
    border-radius: 12px;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
    font-weight: 700;
}

.pill.granted {
    background-color: rgba(12, 255, 154, 0.1);
    color: var(--neon-green);
    border: 1px solid rgba(12, 255, 154, 0.3);
}

.pill.rejected {
    background-color: rgba(255, 51, 102, 0.1);
    color: var(--neon-red);
    border: 1px solid rgba(255, 51, 102, 0.3);
}

p {
    font-size: 0.65rem;
    margin: 0;
    text-transform: uppercase;
}
</style>