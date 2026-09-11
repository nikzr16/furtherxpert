<script setup>
import { ref } from 'vue'
import { useRoute, RouterLink, RouterView } from 'vue-router'
const route = useRoute()
const sidebarOpen = ref(true)
function isActive(path) {
  return route.path === path
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-text">
    <div class="flex relative">
      <!-- Sidebar container that smoothly grows/shrinks so main content shifts with a transition -->
      <div :class="[sidebarOpen ? 'w-80 border-slate-200' : 'w-0 border-transparent']" class="overflow-hidden bg-white border-r transition-all duration-500 ease-in-out">
        <Transition
          enter-active-class="transition transform duration-500 ease-out"
          enter-from-class="-translate-x-full opacity-0"
          enter-to-class="translate-x-0 opacity-100"
          leave-active-class="transition transform duration-500 ease-in"
          leave-from-class="translate-x-0 opacity-100"
          leave-to-class="-translate-x-full opacity-0"
        >
          <aside v-if="sidebarOpen" class="w-80 min-h-screen relative z-30">
            <div class="px-6 py-5 text-xl font-semibold flex items-center justify-between">
              <span>SambungBelajarmu.ai</span>
              <button @click="sidebarOpen = false" aria-label="Close sidebar" class="p-2 rounded-md text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors">✕</button>
            </div>
            <nav class="px-3 space-y-1">
              <RouterLink to="/explore" class="block px-4 py-3 rounded-lg text-lg text-slate-700 hover:bg-blue-50 hover:text-blue-700" :class="{ 'bg-blue-600 text-white hover:bg-blue-600': isActive('/explore') }">Explore</RouterLink>
              <RouterLink to="/eligibility" class="block px-4 py-3 rounded-lg text-lg text-slate-700 hover:bg-blue-50 hover:text-blue-700" :class="{ 'bg-blue-600 text-white hover:bg-blue-600': isActive('/eligibility') }">Check Eligibility</RouterLink>
              <RouterLink to="/qna" class="block px-4 py-3 rounded-lg text-lg text-slate-700 hover:bg-blue-50 hover:text-blue-700" :class="{ 'bg-blue-600 text-white hover:bg-blue-600': isActive('/qna') }">Interest Q&amp;A</RouterLink>
              <RouterLink to="/profile" class="block px-4 py-3 rounded-lg text-lg text-slate-700 hover:bg-blue-50 hover:text-blue-700" :class="{ 'bg-blue-600 text-white hover:bg-blue-600': isActive('/profile') }">Profile</RouterLink>
            </nav>
          </aside>
        </Transition>
      </div>

      <main class="flex-1">
        <div class="max-w-7xl mx-auto p-8">
          <Transition
            enter-active-class="transition-opacity duration-300"
            enter-from-class="opacity-0"
            enter-to-class="opacity-100"
            leave-active-class="transition-opacity duration-300"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
          >
            <button v-if="!sidebarOpen" @click="sidebarOpen = true" aria-label="Open sidebar"
              class="fixed top-5 left-5 z-20 inline-flex items-center justify-center w-11 h-11 rounded-lg border border-slate-300 bg-white text-slate-700 shadow hover:bg-slate-50 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6">
                <path d="M3 6.75A.75.75 0 0 1 3.75 6h16.5a.75.75 0 0 1 0 1.5H3.75A.75.75 0 0 1 3 6.75Zm0 5.25a.75.75 0 0 1 .75-.75h16.5a.75.75 0 0 1 0 1.5H3.75a.75.75 0 0 1-.75-.75Zm.75 4.5a.75.75 0 0 0 0 1.5h16.5a.75.75 0 0 0 0-1.5H3.75Z" />
              </svg>
            </button>
          </Transition>

          <!-- Route transition for page content -->
          <RouterView v-slot="{ Component }">
            <component :is="Component" :key="route.fullPath" />
          </RouterView>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
