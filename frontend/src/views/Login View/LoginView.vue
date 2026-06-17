<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { saveSession } from '../../utils/auth.js'

const router = useRouter()
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
    isLoading.value = true
    errorMessage.value = ''
    try {
        const response = await fetch('http://localhost:8000/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email.value,
                password: password.value
            })
        })

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.detail?.message || data.detail || 'Authentication failed')
        }

        // Persist session via the shared auth utility (keeps token key consistent).
        if (data.session) {
            saveSession(data.session)
        }

        router.push('/')
    } catch (error) {
        console.error('Login error:', error)
        errorMessage.value = error.message
    } finally {
        isLoading.value = false
    }
}
</script>

<template>
    <div class="auth-container">
        <div class="auth-card">
            <div class="logo-section">
                <span class="icon-pulse"></span>
                <h1>NEXUS // SYS</h1>
                <p>AUTHORIZED ACCESS ONLY</p>
            </div>
            
            <form @submit.prevent="handleLogin" class="auth-form">
                <div v-if="errorMessage" class="error-banner">
                    {{ errorMessage }}
                </div>
                
                <div class="form-group">
                    <label>OPERATOR EMAIL</label>
                    <input v-model="email" type="email" placeholder="user@nexus.sys" required :disabled="isLoading" />
                </div>
                <div class="form-group">
                    <label>PASSCODE</label>
                    <input v-model="password" type="password" placeholder="••••••••" required :disabled="isLoading" />
                </div>
                
                <button type="submit" class="btn-submit" :disabled="isLoading">
                    {{ isLoading ? 'INITIALIZING...' : 'INITIALIZE SESSION' }}
                </button>
            </form>
            
            <div class="auth-footer">
                <span>NEW PROTOCOL?</span>
                <RouterLink to="/signup">REGISTER CORE</RouterLink>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* High-tech theme for Auth */
.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 2rem;
    box-sizing: border-box;
    /* Grid background */
    background-image: 
        radial-gradient(circle at 50% 50%, rgba(0, 210, 255, 0.05) 0%, transparent 50%),
        linear-gradient(rgba(0, 210, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 210, 255, 0.03) 1px, transparent 1px);
    background-size: 100% 100%, 40px 40px, 40px 40px;
}

.auth-card {
    background: var(--panel-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 3rem 2rem;
    width: 100%;
    max-width: 400px;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 50px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

.auth-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, transparent, var(--neon-blue), transparent);
}

.logo-section {
    text-align: center;
    margin-bottom: 2.5rem;
}

.icon-pulse {
    display: inline-block;
    width: 12px;
    height: 24px;
    background-color: var(--neon-blue);
    box-shadow: 0 0 15px var(--neon-blue);
    margin-bottom: 10px;
}

.logo-section h1 {
    font-size: 1.8rem;
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 3px;
    margin: 0 0 5px 0;
    color: var(--text-main);
    text-shadow: 0 0 8px rgba(0, 210, 255, 0.3);
}

.logo-section p {
    color: var(--neon-red);
    font-size: 0.7rem;
    letter-spacing: 2px;
    margin: 0;
    font-weight: 700;
}

.error-banner {
    background: rgba(255, 50, 50, 0.1);
    border: 1px solid rgba(255, 50, 50, 0.5);
    color: #ff5555;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    text-align: center;
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 8px;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1px;
}

.form-group input {
    width: 100%;
    padding: 12px 16px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 210, 255, 0.2);
    border-radius: 8px;
    color: var(--text-main);
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    transition: all 0.2s;
    box-sizing: border-box;
}

.form-group input:focus {
    outline: none;
    border-color: var(--neon-blue);
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.2);
}

.form-group input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-submit {
    width: 100%;
    background: rgba(0, 210, 255, 0.1);
    border: 1px solid var(--neon-blue);
    color: var(--neon-blue);
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 2px;
    transition: all 0.3s;
    margin-top: 1rem;
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.1);
}

.btn-submit:hover:not(:disabled) {
    background: rgba(0, 210, 255, 0.2);
    box-shadow: 0 0 20px rgba(0, 210, 255, 0.4);
    transform: translateY(-2px);
}

.btn-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.auth-footer {
    margin-top: 2rem;
    text-align: center;
    font-size: 0.8rem;
    color: var(--text-muted);
}

.auth-footer a {
    color: var(--neon-blue);
    text-decoration: none;
    margin-left: 8px;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.2s;
}

.auth-footer a:hover {
    text-shadow: 0 0 8px var(--neon-blue);
}
</style>

