<script setup>
defineProps({
    /** 'idle' | 'scanning' | 'granted' | 'rejected' */
    state: { type: String, default: 'idle' },
    /** Name of the last-scanned card holder */
    lastScanName: { type: String, default: null },
    /** Formatted time string for the last scan */
    lastScanTime: { type: String, default: null },
    /** Rejection reason (only shown in rejected state) */
    rejectionReason: { type: String, default: null },
})
</script>

<template>
    <div class="scan-card" :class="state">
        <!-- Icon area — emoji changes per state -->
        <div class="icon">
            <span v-if="state === 'idle'">🔒</span>
            <span v-else-if="state === 'scanning'" class="spin-icon">⟳</span>
            <span v-else-if="state === 'granted'">🔓</span>
            <span v-else-if="state === 'rejected'">⛔</span>
        </div>

        <!-- Primary status label -->
        <h1 v-if="state === 'idle'">SECURED</h1>
        <h1 v-else-if="state === 'scanning'">VERIFYING...</h1>
        <h1 v-else-if="state === 'granted'">ACCESS GRANTED</h1>
        <h1 v-else-if="state === 'rejected'">ACCESS DENIED</h1>

        <!-- Scanning sub-label -->
        <p v-if="state === 'scanning'" class="sub-label">SCANNING RFID...</p>

        <!-- Rejected reason -->
        <p v-else-if="state === 'rejected' && rejectionReason" class="sub-label reason">
            {{ rejectionReason }}
        </p>

        <!-- Granted — safe unlocked notice -->
        <p v-else-if="state === 'granted'" class="sub-label granted-note">SAFE UNLOCKED</p>

        <!-- Last scan info (shown in idle/granted/rejected states when data exists) -->
        <template v-if="state !== 'scanning' && lastScanName">
            <p class="last-label">Last Scan</p>
            <h3>{{ lastScanName }}<span v-if="lastScanTime"> • {{ lastScanTime }}</span></h3>
        </template>

        <!-- Idle with no history -->
        <template v-else-if="state === 'idle' && !lastScanName">
            <p class="last-label">WAITING FOR RFID SCAN</p>
        </template>
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

/* State-specific icon colours — overridden by HomeView deep selectors too */
.granted .icon {
    background-color: rgba(12, 255, 154, 0.1);
    border-color: var(--neon-green);
    box-shadow: 0 0 25px rgba(12, 255, 154, 0.3);
    color: var(--neon-green);
}
.rejected .icon {
    background-color: rgba(255, 51, 102, 0.1);
    border-color: var(--neon-red);
    box-shadow: 0 0 25px rgba(255, 51, 102, 0.3);
    color: var(--neon-red);
}
.scanning .icon {
    background-color: rgba(255, 204, 0, 0.1);
    border-color: #ffcc00;
    box-shadow: 0 0 25px rgba(255, 204, 0, 0.3);
    color: #ffcc00;
    animation: scan-pulse 1s infinite alternate;
}

@keyframes scan-pulse {
    0%   { transform: scale(0.95); box-shadow: 0 0 10px rgba(255, 204, 0, 0.2); }
    100% { transform: scale(1.05); box-shadow: 0 0 30px rgba(255, 204, 0, 0.5); }
}

.spin-icon {
    display: inline-block;
    animation: spin 1.2s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}

h1 {
    color: var(--text-main);
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 3px;
    font-size: 1.2rem;
    margin-top: 1.2rem;
    margin-bottom: 0.5rem;
    transition: color 0.3s;
}
.granted h1 { color: var(--neon-green); text-shadow: 0 0 10px rgba(12,255,154,0.3); }
.rejected h1 { color: var(--neon-red);  text-shadow: 0 0 10px rgba(255,51,102,0.3); }

.sub-label {
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 0 0 1rem 0;
}
.sub-label.reason   { color: var(--neon-red); }
.sub-label.granted-note { color: var(--neon-green); }

.last-label {
    color: var(--text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
    margin-top: 0.5rem;
}

h3 {
    color: var(--text-main);
    font-weight: 400;
    font-size: 0.95rem;
    margin: 0;
}
</style>