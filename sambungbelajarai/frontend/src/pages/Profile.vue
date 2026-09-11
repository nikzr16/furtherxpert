<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-semibold">Profile</h1>

    <form @submit.prevent="save" class="space-y-6">
      <div class="p-6 bg-white rounded-xl border border-slate-200 space-y-3">
        <h2 class="text-xl font-semibold">Where you live</h2>
        <p class="text-slate-600 text-sm">Choose your home state</p>
        <select v-model="homeState" class="w-full border border-slate-300 rounded p-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-300">
          <option :value="null" disabled>Select state</option>
          <option v-for="state in MALAYSIAN_STATES" :key="state" :value="state">{{ state }}</option>
        </select>
      </div>

      <div class="p-6 bg-white rounded-xl border border-slate-200 space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold">Academic results</h2>
            <p class="text-slate-600 text-sm">Start with 6 subjects (4 are mandatory). Add more if needed.</p>
          </div>
          <button type="button" @click="addSubject" :disabled="subjects.length >= MAX_SUBJECTS" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded border border-slate-300 text-sm disabled:opacity-60">+ Add subject</button>
        </div>

        <div class="space-y-3">
          <div v-for="(row, idx) in subjects" :key="idx" class="grid grid-cols-12 gap-2 items-center">
            <div class="col-span-7">
              <div v-if="row.fixed" class="px-3 py-2 border border-slate-300 rounded bg-slate-50 text-slate-700">{{ row.subject }}</div>
              <select v-else v-model="row.subject" class="w-full border border-slate-300 rounded p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="" disabled>Select subject</option>
                <option v-for="opt in availableSubjects(idx)" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            <div class="col-span-4">
              <select v-model="row.grade" class="w-full border border-slate-300 rounded p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
                <option value="" disabled>Select grade</option>
                <option v-for="g in GRADE_OPTIONS" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
            <div class="col-span-1 flex justify-end">
              <button v-if="!row.fixed" type="button" @click="removeSubject(idx)" class="px-2 py-2 text-slate-600 hover:text-red-600" title="Remove">✕</button>
            </div>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <button type="submit" :disabled="saving" class="px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-lg text-base">
          <span v-if="!saving">Save Profile</span>
          <span v-else class="inline-flex items-center gap-2">
            <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a 8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"></path></svg>
            Saving...
          </span>
        </button>
        <span v-if="message" class="self-center text-sm" :class="messageType === 'error' ? 'text-red-600' : 'text-green-700'">{{ message }}</span>
      </div>
    </form>
  </div>
  </template>

<script setup>
import { ref, onMounted } from 'vue'

const MALAYSIAN_STATES = [
  'Johor', 'Kedah', 'Kelantan', 'Melaka', 'Negeri Sembilan', 'Pahang',
  'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak', 'Selangor',
  'Terengganu', 'Kuala Lumpur', 'Putrajaya', 'Labuan'
]

const SUBJECT_OPTIONS = [
  'BM', 'BI', 'Math', 'Sejarah', 'Science', 'Add Math', 'Physics', 'Chemistry', 'Biology',
  'Pendidikan Islam', 'Pendidikan Moral', 'Prinsip Perakaunan', 'Ekonomi', 'Perdagangan', 'Sains Komputer',
  'Seni Visual', 'Geografi', 'Kesusasteraan Melayu', 'English Literature', 'Reka Bentuk & Teknologi'
]

const GRADE_OPTIONS = ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E', 'G']
const MAX_SUBJECTS = 20

const homeState = ref(null)
const subjects = ref([])
const saving = ref(false)
const message = ref('')
const messageType = ref('success')

function ensureDefaultSubjects() {
  const existingSubjects = new Set(subjects.value.map(s => s.subject))
  const mandatory = ['BM', 'BI', 'Math', 'Sejarah']
  // Ensure mandatory entries exist and are fixed
  mandatory.forEach(m => {
    if (!existingSubjects.has(m)) {
      subjects.value.unshift({ subject: m, grade: '', fixed: true })
    } else {
      subjects.value = subjects.value.map(s => s.subject === m ? { ...s, fixed: true } : s)
    }
  })
  // Ensure at least 6 rows total
  while (subjects.value.length < 6) {
    subjects.value.push({ subject: '', grade: '', fixed: false })
  }
}

function availableSubjects(rowIndex) {
  const chosen = new Set(subjects.value.map((s, idx) => idx === rowIndex ? null : s.subject).filter(Boolean))
  return SUBJECT_OPTIONS.filter(s => !chosen.has(s))
}

function addSubject() {
  if (subjects.value.length >= MAX_SUBJECTS) return
  subjects.value.push({ subject: '', grade: '', fixed: false })
}

function removeSubject(index) {
  const row = subjects.value[index]
  if (row && !row.fixed) subjects.value.splice(index, 1)
}

async function load() {
  try {
    const resp = await fetch('http://localhost:8000/profile')
    const data = await resp.json()
    homeState.value = data.home_state || null
    const results = data.academic_results || {}
    subjects.value = Object.entries(results).map(([subject, grade]) => ({ subject, grade, fixed: ['BM','BI','Math','Sejarah'].includes(subject) }))
    ensureDefaultSubjects()
  } catch (e) {
    subjects.value = []
    ensureDefaultSubjects()
  }
}

async function save() {
  message.value = ''
  // Build dictionary, ignore empty rows
  const result = {}
  subjects.value.forEach(row => {
    if (row.subject && row.grade) {
      result[row.subject] = row.grade
    }
  })
  saving.value = true
  try {
    const resp = await fetch('http://localhost:8000/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ home_state: homeState.value, academic_results: result })
    })
    if (!resp.ok) throw new Error('Save failed')
    messageType.value = 'success'
    message.value = 'Saved'
  } catch (e) {
    messageType.value = 'error'
    message.value = 'Failed to save profile'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>


