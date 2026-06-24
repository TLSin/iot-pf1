<script setup>
import { ref } from 'vue'

const props = defineProps({
    saving:   { type: Boolean, default: false },
    error:    { type: String,  default: '' },
    /** RFID hash received from the physical card scan — read-only */
    cardHash: { type: String,  default: '' },
})

const emit = defineEmits(['close', 'save'])

const userFields = ref({
    name: '',
    role: 'Standard User',
})

const handleSave = () => {
    emit('save', {
        ...userFields.value,
        card_hash: props.cardHash,   // pass the real scanned hash
    })
    userFields.value.name = ''
    userFields.value.role = 'Standard User'
}
</script>

<template>
    <div class="modal-overlay">
        <div class="modal card-modal">
            <h2>RFID CHIP DETECTED</h2>
            <p>Register a new user identity for this card signature.</p>

            <div class="form-group">
                <label>CARD HOLDER NAME</label>
                <input v-model="userFields.name" type="text" placeholder="e.g. John Doe" />
            </div>

            <div class="form-group">
                <label>USER PRIVILEGES</label>
                <select v-model="userFields.role">
                    <option>Standard User</option>
                    <option>Admin Access</option>
                    <option>Guest User</option>
                </select>
            </div>

            <!-- Read-only RFID hash field -->
            <div class="form-group">
                <label>RFID HASH</label>
                <div class="hash-display">
                    <span class="hash-icon">🔑</span>
                    <span class="hash-value">{{ cardHash || '—' }}</span>
                </div>
            </div>

            <div v-if="error" class="modal-error">{{ error }}</div>

            <div class="modal-actions">
                <button class="btn-cancel" :disabled="saving" @click="$emit('close')">CANCEL</button>
                <button class="btn-save"   :disabled="saving || !cardHash" @click="handleSave">
                    {{ saving ? 'BINDING...' : 'BIND TO CARD' }}
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(5px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
}

.modal {
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 2rem;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8), inset 0 1px 1px rgba(255, 255, 255, 0.1);
}

.modal h2 {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--neon-blue);
    font-size: 1.2rem;
    margin: 0 0 5px 0;
    letter-spacing: 2px;
}

.modal p {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}

.form-group { margin-bottom: 1.2rem; }

.form-group label {
    display: block;
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-bottom: 5px;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 10px 12px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 210, 255, 0.2);
    border-radius: 8px;
    color: var(--text-main);
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    transition: all 0.2s;
    box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--neon-blue);
    box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

.form-group select option {
    background: var(--bg-base);
    color: var(--text-main);
}

/* RFID hash read-only display */
.hash-display {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: rgba(0, 210, 255, 0.04);
    border: 1px solid rgba(0, 210, 255, 0.2);
    border-radius: 8px;
    box-sizing: border-box;
    min-height: 42px;
}

.hash-icon { font-size: 1rem; flex-shrink: 0; }

.hash-value {
    font-family: 'Space Grotesk', monospace;
    font-size: 0.85rem;
    color: var(--neon-blue);
    letter-spacing: 1.5px;
    word-break: break-all;
    text-shadow: 0 0 6px rgba(0, 210, 255, 0.3);
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 2rem;
}

.modal-error {
    padding: 10px 12px;
    border: 1px solid rgba(255, 51, 102, 0.3);
    border-radius: 8px;
    background: rgba(255, 51, 102, 0.08);
    color: var(--neon-red);
    font-size: 0.78rem;
    font-family: 'Space Grotesk', sans-serif;
}

.btn-cancel {
    background: transparent;
    border: 1px solid var(--text-muted);
    color: var(--text-muted);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
}

.btn-cancel:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-main);
}

.btn-save {
    background: rgba(0, 210, 255, 0.1);
    border: 1px solid var(--neon-blue);
    color: var(--neon-blue);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    transition: all 0.2s;
    box-shadow: 0 0 10px rgba(0, 210, 255, 0.1);
}

.btn-save:hover:not(:disabled) {
    background: rgba(0, 210, 255, 0.2);
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.3);
}

.btn-cancel:disabled,
.btn-save:disabled {
    opacity: 0.65;
    cursor: wait;
}
</style>
