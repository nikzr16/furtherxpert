<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-semibold">Interest Q&amp;A</h1>
    <p class="text-slate-600">Answer these questions to help us understand your preferences. Each has 5 options; the last is "None of the above".</p>

    <form @submit.prevent="submit" class="space-y-6">
      <div class="flex justify-end">
        <button type="button" @click="clearAll" class="px-3 py-2 bg-rose-50 hover:bg-rose-100 rounded border border-rose-300 text-rose-700 text-sm">Clear all</button>
      </div>
      <div v-for="(q, qi) in questions" :key="qi" class="p-4 bg-white rounded-xl border border-slate-200">
        <div class="font-medium mb-3">{{ qi + 1 }}. {{ q.text }}</div>
        <div class="grid sm:grid-cols-2 gap-2">
          <label v-for="(opt, oi) in q.options" :key="oi" class="flex items-start gap-3 p-2 rounded border border-slate-200 hover:bg-slate-50 cursor-pointer">
            <input type="radio" class="mt-1.5" :name="'q'+qi" :value="oi" v-model="answers[qi]" />
            <span class="text-slate-700">{{ opt.label }}</span>
          </label>
        </div>
      </div>

      <div class="flex gap-3">
        <button type="submit" :disabled="saving" class="px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-lg text-base">
          <span v-if="!saving">Save interests</span>
          <span v-else class="inline-flex items-center gap-2">
            <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
            Saving...
          </span>
        </button>
        <span v-if="message" class="self-center text-sm" :class="messageType === 'error' ? 'text-red-600' : 'text-green-700'">{{ message }}</span>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const TAGS = [
  'IT', 'Engineering', 'Business', 'Healthcare', 'Arts', 'Education', 'Science', 'Law', 'Hospitality', 'Agriculture',
  'Design', 'Communications', 'Finance', 'Computer Science', 'Data', 'Environment', 'Social Work', 'Architecture', 'Logistics', 'Language'
]

function noneOpt() { return { label: 'None of the above', tags: [] } }

// 20 neutral questions with 4 preference-mapping options + 1 none
const questions = [
  { text: 'Which activity sounds most engaging to you?', options: [
    { label: 'Building an app or website', tags: ['IT', 'Computer Science'] },
    { label: 'Designing and testing a device', tags: ['Engineering'] },
    { label: 'Planning a small business strategy', tags: ['Business', 'Finance'] },
    { label: 'Helping people manage their health', tags: ['Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which project would you pick for a community fair?', options: [
    { label: 'Create a digital info booth', tags: ['IT', 'Communications'] },
    { label: 'Build a simple machine model', tags: ['Engineering'] },
    { label: 'Run a mini market survey and report', tags: ['Business', 'Data'] },
    { label: 'Design a poster exhibition', tags: ['Arts', 'Design'] },
    noneOpt()
  ]},
  { text: 'Which subject area do you enjoy learning about?', options: [
    { label: 'Coding and algorithms', tags: ['Computer Science'] },
    { label: 'Physics and mechanics', tags: ['Engineering', 'Science'] },
    { label: 'Markets and finance', tags: ['Business', 'Finance'] },
    { label: 'Human body and wellness', tags: ['Healthcare', 'Science'] },
    noneOpt()
  ]},
  { text: 'Which task would you volunteer for in a group?', options: [
    { label: 'Manage the project timeline and tasks', tags: ['Business'] },
    { label: 'Create visuals and layout', tags: ['Design', 'Arts'] },
    { label: 'Analyze data to support decisions', tags: ['Data', 'Science'] },
    { label: 'Coordinate with speakers and attendees', tags: ['Communications'] },
    noneOpt()
  ]},
  { text: 'Which environment sounds most appealing?', options: [
    { label: 'Office with computers and software tools', tags: ['IT'] },
    { label: 'Workshop or lab with equipment', tags: ['Engineering', 'Science'] },
    { label: 'Customer-facing business setting', tags: ['Business', 'Hospitality'] },
    { label: 'Clinic, hospital, or care center', tags: ['Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which type of problem do you prefer solving?', options: [
    { label: 'Debugging technical issues', tags: ['IT', 'Computer Science'] },
    { label: 'Improving a physical product', tags: ['Engineering'] },
    { label: 'Optimizing budgets and plans', tags: ['Finance', 'Business'] },
    { label: 'Supporting people with needs', tags: ['Social Work', 'Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which topic would you like to present on?', options: [
    { label: 'Data privacy and cybersecurity', tags: ['IT', 'Computer Science'] },
    { label: 'Sustainable infrastructure', tags: ['Engineering', 'Environment'] },
    { label: 'Entrepreneurship case study', tags: ['Business'] },
    { label: 'Healthy lifestyle basics', tags: ['Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which skill would you most like to strengthen?', options: [
    { label: 'Programming and automation', tags: ['Computer Science', 'IT'] },
    { label: 'Technical drawing or prototyping', tags: ['Engineering', 'Design'] },
    { label: 'Persuasive communication', tags: ['Communications', 'Business'] },
    { label: 'Lab techniques or first aid', tags: ['Science', 'Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which field’s news do you follow most?', options: [
    { label: 'Tech innovations and AI', tags: ['IT', 'Data', 'Computer Science'] },
    { label: 'New materials and devices', tags: ['Engineering'] },
    { label: 'Markets, companies, and startups', tags: ['Business', 'Finance'] },
    { label: 'Healthcare breakthroughs', tags: ['Healthcare', 'Science'] },
    noneOpt()
  ]},
  { text: 'Which practical activity do you enjoy?', options: [
    { label: 'Creating digital content or tools', tags: ['IT', 'Design'] },
    { label: 'Hands-on building and fixing', tags: ['Engineering'] },
    { label: 'Planning events or promotions', tags: ['Business', 'Hospitality'] },
    { label: 'Organizing community help', tags: ['Social Work'] },
    noneOpt()
  ]},
  { text: 'Which sector would you explore internships in?', options: [
    { label: 'Software and data', tags: ['IT', 'Data'] },
    { label: 'Manufacturing or construction', tags: ['Engineering'] },
    { label: 'Retail, banking, or marketing', tags: ['Business', 'Finance'] },
    { label: 'Healthcare services', tags: ['Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which elective would you choose?', options: [
    { label: 'Intro to programming', tags: ['Computer Science'] },
    { label: 'Technical drawing', tags: ['Engineering', 'Design', 'Architecture'] },
    { label: 'Entrepreneurship basics', tags: ['Business'] },
    { label: 'Human biology', tags: ['Science', 'Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which challenge sounds rewarding?', options: [
    { label: 'Automate a tedious task', tags: ['IT'] },
    { label: 'Improve energy efficiency', tags: ['Engineering', 'Environment'] },
    { label: 'Grow sales for a small shop', tags: ['Business'] },
    { label: 'Improve patient waiting times', tags: ['Healthcare', 'Logistics'] },
    noneOpt()
  ]},
  { text: 'Which output do you like creating?', options: [
    { label: 'Code or dashboards', tags: ['Computer Science', 'Data'] },
    { label: 'Prototypes or models', tags: ['Engineering'] },
    { label: 'Plans, pitches, or reports', tags: ['Business', 'Communications'] },
    { label: 'Care guides or health posters', tags: ['Healthcare', 'Education'] },
    noneOpt()
  ]},
  { text: 'Which setting do you want to practice in?', options: [
    { label: 'Cloud / online systems', tags: ['IT'] },
    { label: 'Workshop and labs', tags: ['Engineering', 'Science'] },
    { label: 'Offices and shops', tags: ['Business'] },
    { label: 'Clinics and community centers', tags: ['Healthcare', 'Social Work'] },
    noneOpt()
  ]},
  { text: 'Which course project sounds fun?', options: [
    { label: 'Build a simple app', tags: ['Computer Science'] },
    { label: 'Design a bridge model', tags: ['Engineering', 'Architecture'] },
    { label: 'Market analysis case', tags: ['Business', 'Finance'] },
    { label: 'Health education campaign', tags: ['Healthcare', 'Education'] },
    noneOpt()
  ]},
  { text: 'Which topic would you teach a friend?', options: [
    { label: 'Basics of coding', tags: ['IT', 'Computer Science'] },
    { label: 'How engines work', tags: ['Engineering'] },
    { label: 'Managing money wisely', tags: ['Finance', 'Business'] },
    { label: 'Staying healthy', tags: ['Healthcare'] },
    noneOpt()
  ]},
  { text: 'Which industry values appeal to you?', options: [
    { label: 'Innovation and efficiency', tags: ['IT', 'Engineering'] },
    { label: 'Safety and reliability', tags: ['Engineering', 'Healthcare'] },
    { label: 'Growth and customer value', tags: ['Business'] },
    { label: 'Care and wellbeing', tags: ['Healthcare', 'Social Work'] },
    noneOpt()
  ]},
  { text: 'Which real-world issue would you help tackle?', options: [
    { label: 'Cybersecurity threats', tags: ['IT'] },
    { label: 'Infrastructure durability', tags: ['Engineering'] },
    { label: 'Financial literacy', tags: ['Finance', 'Education'] },
    { label: 'Public health awareness', tags: ['Healthcare', 'Education'] },
    noneOpt()
  ]},
  { text: 'Which collaboration do you prefer?', options: [
    { label: 'Solve a tech puzzle together', tags: ['Computer Science'] },
    { label: 'Build a working prototype', tags: ['Engineering'] },
    { label: 'Launch a small campaign', tags: ['Business', 'Communications'] },
    { label: 'Organize a wellness drive', tags: ['Healthcare', 'Social Work'] },
    noneOpt()
  ]}
]

const answers = ref(Array(questions.length).fill(null))
const saving = ref(false)
const message = ref('')
const messageType = ref('success')
let cachedProfile = null

async function loadProfile() {
  const resp = await fetch('http://localhost:8000/profile')
  cachedProfile = await resp.json()
  // Restore previous answers if present
  const prev = Array.isArray(cachedProfile.qna_answers) ? cachedProfile.qna_answers : []
  const arr = Array(questions.length).fill(null)
  for (let i = 0; i < Math.min(arr.length, prev.length); i++) {
    const v = prev[i]
    arr[i] = (v === 0 || v) ? v : null
  }
  answers.value = arr
}

function tallyScores() {
  const scores = {}
  answers.value.forEach((oi, qi) => {
    if (oi === null) return
    const opt = questions[qi].options[oi]
    ;(opt.tags || []).forEach(tag => {
      scores[tag] = (scores[tag] || 0) + 1
    })
  })
  return scores
}

function topInterests(scores) {
  const entries = Object.entries(scores)
  entries.sort((a,b) => b[1]-a[1])
  return entries.slice(0, 5).map(([k]) => k)
}

async function submit() {
  message.value = ''
  saving.value = true
  try {
    if (!cachedProfile) await loadProfile()
    const scores = tallyScores()
    const interests = topInterests(scores)
    const payload = {
      home_state: cachedProfile.home_state || null,
      academic_results: cachedProfile.academic_results || {},
      interest_scores: scores,
      qna_answers: answers.value
    }
    const resp = await fetch('http://localhost:8000/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!resp.ok) throw new Error('Save failed')
    messageType.value = 'success'
    message.value = 'Saved interests to profile'
  } catch (e) {
    messageType.value = 'error'
    message.value = 'Failed to save interests'
  } finally {
    saving.value = false
  }
}

function clearAll() {
  answers.value = Array(questions.length).fill(null)
}

loadProfile()
</script>


