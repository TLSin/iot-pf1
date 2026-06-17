<script setup>
import { ref, computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { logout } from './utils/auth.js'

const route = useRoute()
const router = useRouter()
const showNav = computed(() => route.name !== 'login' && route.name !== 'signup')

const isLoggingOut = ref(false)

const handleLogout = async () => {
  if (isLoggingOut.value) return
  isLoggingOut.value = true
  try {
    await logout()
    router.push('/login')
  } finally {
    isLoggingOut.value = false
  }
}
</script>

<template>
  <main class="main-content">
    <RouterView />
  </main>

  <header class="bottom-nav" v-if="showNav">
    <div class="wrapper">
      <nav>
        <RouterLink to="/">⬡ Dashboard</RouterLink>
        <RouterLink to="/access-log">≡ Access Logs</RouterLink>
        <RouterLink to="/users">◈ Users</RouterLink>
        <button
          class="nav-logout"
          @click="handleLogout"
          :disabled="isLoggingOut"
          :class="{ 'is-loading': isLoggingOut }"
          title="Logout"
        >
          <span class="logout-icon">⏻</span>
          <span class="logout-label">{{ isLoggingOut ? '...' : 'Logout' }}</span>
        </button>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.main-content {
  padding-bottom: 70px; /* Ensure content isn't hidden behind the fixed navbar */
}

header.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  margin: 0 auto;
  max-width: 480px;
  width: 100%;
  background-color: #0a0b10; /* Match HomeView.vue */
  z-index: 1000;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.6);
  border-radius: 15px 15px 0 0;
  border-top: 1px solid rgba(0, 210, 255, 0.15);
  border-left: 1px solid rgba(0, 210, 255, 0.05);
  border-right: 1px solid rgba(0, 210, 255, 0.05);
}

nav {
  width: 100%;
  font-size: 14px;
  text-align: center;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 1.2rem 0;
}

nav a.router-link-exact-active {
  color: #00d2ff;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 210, 255, 0.4);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6b8298;
  text-decoration: none;
  font-size: 0.8rem;
  letter-spacing: 1px;
  flex: 1;
  transition: all 0.3s ease;
}

nav a:hover {
  color: #e2f1f8;
  text-shadow: 0 0 5px rgba(226, 241, 248, 0.5);
}

nav a:first-of-type {
  border: 0;
}

/* ── Logout button ─────────────────────────────────────────── */
.nav-logout {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 2px;
  background: none;
  border: none;
  cursor: pointer;
  color: #6b8298;
  font-size: 1rem;
  letter-spacing: 1px;
  padding: 0;
  transition: all 0.3s ease;
  font-family: inherit;
}

.nav-logout:hover:not(:disabled) {
  color: #ff5577;
  text-shadow: 0 0 8px rgba(255, 85, 119, 0.5);
}

.nav-logout:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.nav-logout.is-loading .logout-icon {
  display: inline-block;
  animation: spin 0.9s linear infinite;
}

.logout-icon {
  font-size: 1.1rem;
  line-height: 1;
}

.logout-label {
  font-size: 0.75rem;
  margin-top: 2px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>

