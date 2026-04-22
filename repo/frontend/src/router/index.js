import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ActivityCreate from '../views/ActivityCreate.vue'
import ActivityDetail from '../views/ActivityDetail.vue'
import ActivityList from '../views/ActivityList.vue'
import FinancialDashboard from '../views/FinancialDashboard.vue'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import NotFound from '../views/NotFound.vue'
import RegistrationWizard from '../views/RegistrationWizard.vue'
import ReviewDashboard from '../views/ReviewDashboard.vue'
import SystemAdminConsole from '../views/SystemAdminConsole.vue'
import UserManagement from '../views/UserManagement.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: Home, meta: { public: true } },
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { public: true, guestOnly: true },
    },
    {
      path: '/activities/new',
      name: 'activity-new',
      component: ActivityCreate,
      meta: { requiresAuth: true },
    },
    {
      path: '/activities/:id',
      name: 'activity-detail',
      component: ActivityDetail,
      meta: { requiresAuth: true },
    },
    {
      path: '/activities',
      name: 'activities',
      component: ActivityList,
      meta: { requiresAuth: true },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: UserManagement,
      meta: { requiresAuth: true, roles: ['system_admin'] },
    },
    {
      path: '/admin/console',
      name: 'admin-console',
      component: SystemAdminConsole,
      meta: { requiresAuth: true, roles: ['system_admin'] },
    },
    {
      path: '/registrations/new',
      name: 'registration-new',
      component: RegistrationWizard,
      meta: { requiresAuth: true, roles: ['applicant'] },
    },
    {
      path: '/registrations/:registrationId/wizard',
      name: 'registration-wizard',
      component: RegistrationWizard,
      meta: { requiresAuth: true, roles: ['applicant'] },
    },
    {
      path: '/reviews',
      name: 'reviews',
      component: ReviewDashboard,
      meta: { requiresAuth: true, roles: ['reviewer'] },
    },
    {
      path: '/funding',
      name: 'funding',
      component: FinancialDashboard,
      meta: { requiresAuth: true, roles: ['financial_admin', 'system_admin'] },
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFound, meta: { public: true } },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  auth.restoreSession()

  if (to.meta.public && to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'home' }
  }

  if (to.meta.requiresAuth) {
    if (!auth.accessToken) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (!auth.user) {
      try {
        await auth.loadMe()
      } catch {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }
    if (!auth.user) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    const roles = to.meta.roles
    if (Array.isArray(roles) && roles.length && !roles.includes(auth.user.role)) {
      return { name: 'home' }
    }
  }

  return true
})

export default router
