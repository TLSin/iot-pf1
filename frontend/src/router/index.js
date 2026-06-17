import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../utils/auth.js'
import HomeView from '../views/Home View/HomeView.vue'
import AccesLogView from '../views/Access Log View/AccessLogView.vue'
import UserView from '../views/User View/UserView.vue'
import LoginView from '../views/Login View/LoginView.vue'
import SignUpView from '../views/SignUp View/SignUpView.vue'

// Routes that require a valid session
const PROTECTED_ROUTES = ['home', 'AccessLog', 'Users']

// Routes that should not be accessible when already logged in
const AUTH_ROUTES = ['login', 'signup']

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
    },
    {
      path: '/access-log',
      name: 'AccessLog',
      component: AccesLogView,
      meta: { requiresAuth: true },
    },
    {
      path: '/users',
      name: 'Users',
      component: UserView,
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignUpView,
      meta: { requiresAuth: false },
    },
  ],
})

/**
 * Global navigation guard.
 *
 * Flow:
 *  1. Protected route + NOT authenticated → redirect to /login
 *  2. Auth-only route (login/signup) + IS authenticated → redirect to /
 *  3. Otherwise → allow navigation
 */
router.beforeEach((to, _from, next) => {
  const authenticated = isAuthenticated()

  if (to.meta.requiresAuth && !authenticated) {
    // User is trying to reach a protected page without a valid session.
    return next({ name: 'login' })
  }

  if (AUTH_ROUTES.includes(to.name) && authenticated) {
    // Authenticated user navigated to login/signup — bounce to dashboard.
    return next({ name: 'home' })
  }

  next()
})

export default router
