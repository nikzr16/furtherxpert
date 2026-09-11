<template>
  <form @submit.prevent="submitForm" class="p-6 bg-white rounded-xl shadow-sm border border-slate-200 space-y-4">
    <div class="space-y-3">
      <label class="block text-sm font-medium text-slate-700">Interests</label>
      <div class="relative">
        <button type="button" @click="interestsOpen = !interestsOpen" class="w-full flex items-center justify-between border border-slate-300 rounded p-3 bg-white">
          <span class="text-slate-700 text-base">{{ interestsLabel }}</span>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-500" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 011.08 1.04l-4.25 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
        </button>
        <div v-if="interestsOpen" class="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded shadow-lg max-h-72 overflow-auto">
          <div class="p-2 space-y-1">
            <label v-for="cat in INTEREST_OPTIONS" :key="cat" class="flex items-center gap-2 px-2 py-1 rounded hover:bg-slate-50">
              <input type="checkbox" :value="cat" v-model="selectedInterests" class="h-4 w-4" />
              <span class="text-slate-700 text-sm">{{ cat }}</span>
            </label>
          </div>
          <div class="p-2 border-t bg-slate-50 text-right">
            <button type="button" @click="interestsOpen = false" class="px-3 py-1.5 text-sm rounded border border-slate-300 bg-white hover:bg-slate-100">Done</button>
          </div>
        </div>
      </div>
    </div>
    <button type="submit" :disabled="loading" class="px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-lg text-base">
      <span v-if="!loading">Check Eligibility</span>
      <span v-else class="inline-flex items-center gap-2">
        <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
        Checking...
      </span>
    </button>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ loading: { type: Boolean, default: false } })

const INTEREST_OPTIONS = [
  'Science & Technology', 'Business & Management', 'Healthcare & Social Services', 'Arts & Design',
  'Education & Humanities', 'Law & Governance', 'Hospitality & Tourism', 'Agriculture & Environment',
  'Media & Communications'
]

const interestsOpen = ref(false)
const selectedInterests = ref([])
const emit = defineEmits(['submit'])

const interestsLabel = computed(() => {
  const sel = selectedInterests.value
  if (!sel || sel.length === 0) return 'Select interests'
  const VISIBLE = 5
  if (sel.length <= VISIBLE) return sel.join(', ')
  return sel.slice(0, VISIBLE).join(', ') + ` +${sel.length - VISIBLE} more`
})

function submitForm() {
  // Ensure dropdown popover is closed so it doesn't overlay navigation
  interestsOpen.value = false
  emit('submit', { interests: selectedInterests.value })
}
</script>
