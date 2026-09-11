import { createRouter, createWebHistory } from 'vue-router'
import Eligibility from './pages/Eligibility.vue'
import Profile from './pages/Profile.vue'
import QnA from './pages/QnA.vue'
import Catalog from './pages/Catalog.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/eligibility' },
    { path: '/eligibility', name: 'Eligibility', component: Eligibility },
    { path: '/profile', name: 'Profile', component: Profile },
    { path: '/qna', name: 'QnA', component: QnA },
    { path: '/explore', name: 'Explore', component: Catalog },
    { path: '/catalog', redirect: '/explore' }
  ]
})

export default router
