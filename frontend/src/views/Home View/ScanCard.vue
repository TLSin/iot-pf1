<script setup>

</script>
<template>
    <div class="scan-card">
        <div class="icon">🔒</div>
        <h1>SECURED</h1>

        <p>Last Scan</p>
        <h3>John Doe • 10:20 PM</h3>
    </div>
</template>

<style scoped>
.scan-card {
    display: flex;
    flex-direction: column;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin-top: 0;
    padding: 2rem 1rem;
    width: 100%;
    height: auto;
    justify-content: center;
    align-items: center;
    color: var(--text-main);
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
    transition: all 0.3s ease;
}

.icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 6rem;
    height: 6rem;
    background-color: rgba(0, 210, 255, 0.05);
    border: 1px solid rgba(0, 210, 255, 0.3);
    box-shadow: 0 0 20px rgba(0, 210, 255, 0.1);
    border-radius: 50%;
    color: var(--neon-blue);
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    transition: all 0.3s ease;
}

h1 {
    color: var(--text-main);
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 3px;
    font-size: 1.2rem;
    margin-top: 1.2rem;
    margin-bottom: 1.5rem;
}

p {
    color: var(--text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}

h3 {
    color: var(--text-main);
    font-weight: 400;
    font-size: 0.95rem;
}
</style>