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

const navItems = [
  { to: '/',           icon: '⬡', label: 'Dashboard'  },
  { to: '/access-log', icon: '≡', label: 'Access Logs' },
  { to: '/users',      icon: '◈', label: 'Users'       },
]
</script>

<template>
  <div class="app-shell" :class="{ 'with-nav': showNav }">
    <!-- ── Desktop Sidebar ─────────────────────────────────────── -->
    <aside v-if="showNav" class="sidebar">
      <!-- Brand -->
      <div class="sidebar-brand">
        <span class="brand-icon"></span>
        <div class="brand-text">
          <span class="brand-name">RFID</span>
          <span class="brand-sub">SECURE SYSTEM</span>
        </div>
      </div>

      <!-- Nav links -->
      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :title="item.label"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <!-- Spacer -->
      <div class="sidebar-spacer"></div>

      <!-- System status -->
      <div class="sidebar-status">
        <span class="status-dot"></span>
        <span class="status-text">SYSTEM ONLINE</span>
      </div>

      <!-- Logout -->
      <button
        class="sidebar-logout"
        @click="handleLogout"
        :disabled="isLoggingOut"
        :class="{ 'is-loading': isLoggingOut }"
        title="Logout"
      >
        <span class="logout-icon">⏻</span>
        <span class="nav-label">{{ isLoggingOut ? 'Logging out...' : 'Logout' }}</span>
      </button>
    </aside>

    <!-- ── Main content area ───────────────────────────────────── -->
    <main class="main-content">
      <RouterView />
    </main>

    <!-- ── Mobile Bottom Navigation ───────────────────────────── -->
    <header v-if="showNav" class="bottom-nav">
      <div class="wrapper">
        <nav>
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
          >{{ item.icon }} {{ item.label }}</RouterLink>
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
  </div>
</template>

<style scoped>
/* ── App shell ─────────────────────────────────────────────────── */
.app-shell {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-base);
}

/* Main content — sits next to sidebar on desktop */
.main-content {
  flex: 1;
  min-width: 0; /* prevent flex overflow */
  /* Mobile: leave room for bottom nav */
  padding-bottom: 70px;
}

/* ── Sidebar ───────────────────────────────────────────────────── */
.sidebar {
  display: none; /* hidden on mobile */
}

/* ── Mobile Bottom Navigation ──────────────────────────────────── */
header.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #0a0b10;
  z-index: 1000;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.6);
  border-top: 1px solid rgba(0, 210, 255, 0.15);
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

/* ── Mobile logout button ─────────────────────────────────────── */
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

/* ═══════════════════════════════════════════════════════════════ */
/* Tablet (768px+) — wider content, bottom nav retained           */
/* ═══════════════════════════════════════════════════════════════ */
@media (min-width: 768px) {
  header.bottom-nav {
    /* Keep bottom nav on tablet but style it wider */
    border-radius: 0;
  }

  .main-content {
    padding-bottom: 80px;
  }
}

/* ═══════════════════════════════════════════════════════════════ */
/* Desktop (1024px+) — sidebar replaces bottom nav                */
/* ═══════════════════════════════════════════════════════════════ */
@media (min-width: 1024px) {
  /* The sidebar is position:fixed so it needs NO grid column.
     We simply push the main content area with margin-left. */
  .app-shell.with-nav {
    display: block;
  }

  /* Show sidebar */
  .sidebar {
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    left: 0;
    width: 220px;
    height: 100vh;
    background: rgba(10, 11, 16, 0.97);
    border-right: 1px solid rgba(0, 210, 255, 0.12);
    box-shadow: 4px 0 30px rgba(0, 0, 0, 0.5);
    padding: 1.5rem 0;
    z-index: 100;
    backdrop-filter: blur(20px);
  }

  /* Brand section */
  .sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 1.25rem 1.5rem;
    border-bottom: 1px solid rgba(0, 210, 255, 0.1);
    margin-bottom: 1rem;
  }

  .brand-icon {
    width: 8px;
    height: 32px;
    background: linear-gradient(to bottom, var(--neon-blue), var(--neon-green));
    box-shadow: 0 0 12px var(--neon-blue);
    border-radius: 2px;
    flex-shrink: 0;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
  }

  .brand-name {
    font-size: 1.1rem;
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 3px;
    color: var(--text-main);
  }

  .brand-sub {
    font-size: 0.55rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 2px;
    color: var(--text-muted);
    font-weight: 600;
  }

  /* Sidebar nav links */
  .sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 0 0.75rem;
  }

  .sidebar-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.7rem 0.75rem;
    border-radius: 10px;
    color: var(--text-muted);
    text-decoration: none;
    font-size: 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1.5px;
    font-weight: 600;
    transition: all 0.2s ease;
    border: 1px solid transparent;
  }

  .sidebar-link:hover {
    color: var(--text-main);
    background: rgba(0, 210, 255, 0.06);
    border-color: rgba(0, 210, 255, 0.1);
  }

  .sidebar-link.router-link-exact-active {
    color: var(--neon-blue);
    background: rgba(0, 210, 255, 0.1);
    border-color: rgba(0, 210, 255, 0.2);
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.08), inset 0 0 10px rgba(0, 210, 255, 0.04);
  }

  .nav-icon {
    font-size: 1rem;
    width: 20px;
    text-align: center;
    flex-shrink: 0;
  }

  .nav-label {
    font-size: 0.78rem;
  }

  /* Spacer pushes status + logout to bottom */
  .sidebar-spacer {
    flex: 1;
  }

  /* System status badge */
  .sidebar-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.75rem 1.25rem;
    margin: 0 0.75rem 0.5rem;
    border-radius: 8px;
    background: rgba(12, 255, 154, 0.05);
    border: 1px solid rgba(12, 255, 154, 0.1);
  }

  .status-dot {
    width: 7px;
    height: 7px;
    background-color: var(--neon-green);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--neon-green);
    animation: pulse-anim 1.5s infinite alternate;
    flex-shrink: 0;
  }

  .status-text {
    font-size: 0.65rem;
    font-family: 'Space Grotesk', sans-serif;
    color: var(--neon-green);
    font-weight: 700;
    letter-spacing: 1.5px;
  }

  @keyframes pulse-anim {
    0%   { opacity: 0.5; box-shadow: 0 0 2px var(--neon-green); }
    100% { opacity: 1;   box-shadow: 0 0 12px var(--neon-green); }
  }

  /* Sidebar logout button */
  .sidebar-logout {
    display: flex;
    align-items: center;
    gap: 12px;
    width: calc(100% - 1.5rem);
    margin: 0 0.75rem;
    padding: 0.7rem 0.75rem;
    border-radius: 10px;
    background: none;
    border: 1px solid transparent;
    color: var(--text-muted);
    font-size: 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 1.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .sidebar-logout:hover:not(:disabled) {
    color: #ff5577;
    background: rgba(255, 85, 119, 0.07);
    border-color: rgba(255, 85, 119, 0.2);
  }

  .sidebar-logout:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .sidebar-logout.is-loading .logout-icon {
    animation: spin 0.9s linear infinite;
    display: inline-block;
  }

  /* Hide mobile bottom nav on desktop */
  header.bottom-nav {
    display: none;
  }

  /* Offset main content to account for fixed sidebar */
  .main-content {
    margin-left: 220px;
    padding-bottom: 0;
  }
}
</style>
