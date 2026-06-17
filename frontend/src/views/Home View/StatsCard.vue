<script setup>

</script>
<template>
    <div class="card">
        <slot></slot>
    </div>
</template>

<style scoped>
.card {
    display: flex;
    flex-direction: column;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    padding: 1.2rem;
    width: 100%;
    justify-content: center;
    align-items: center;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}

.card:hover {
    transform: translateY(-3px);
    border-color: var(--neon-blue);
    box-shadow: 0 8px 20px rgba(0, 210, 255, 0.1);
}
</style>