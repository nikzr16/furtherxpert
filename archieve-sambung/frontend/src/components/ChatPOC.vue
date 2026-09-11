<template>
  <div class="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
    <h2 class="font-semibold mb-3 text-2xl text-slate-800">Ask Me!</h2>
    <textarea v-model="query" placeholder="Tell us your SPM grades, interests, location" class="border border-slate-300 rounded p-3 w-full text-base focus:outline-none focus:ring-2 focus:ring-emerald-300" :disabled="loading"></textarea>
    <button @click="askAI" :disabled="loading" class="mt-3 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-lg text-base">
      <span v-if="!loading">Ask</span>
      <span v-else class="inline-flex items-center gap-2">
        <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
        Thinking...
      </span>
    </button>

    <div v-if="loading" class="mt-4 h-28 rounded shimmer"></div>
    <pre v-else-if="response" class="mt-4 text-base bg-slate-50 p-3 rounded overflow-auto whitespace-pre-wrap font-sans">{{ response }}</pre>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const query = ref('I got SPM Math B, English B and interested in IT near Johor')
const response = ref('')
const loading = ref(false)
async function askAI() {
  loading.value = true
  response.value = ''
  try {
    const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: query.value }) })
    const data = await res.json()
    response.value = data.text || JSON.stringify(data, null, 2)
  } catch (e) {
    response.value = 'Sorry, something went wrong.'
  } finally {
    loading.value = false
  }
}
</script>
