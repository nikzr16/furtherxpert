<template>
  <div class="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
    <h2 class="font-semibold mb-3 text-2xl text-slate-800">Recommendations</h2>
    <div v-if="!data" class="text-slate-600">Submit your details to see recommendations.</div>
    <div v-else>
      <div class="space-y-4">
        <div v-for="p in data.eligible_programs" :key="p.id" class="group border border-slate-200 rounded-lg p-4 bg-white">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-xl font-medium text-slate-900">{{ p.name }}</div>
              <div class="text-sm text-slate-600">Field: {{ p.field }} • Mode: {{ p.mode }} • Years: {{ p.duration_years }} • RM {{ p.tuition_fee_rm?.toLocaleString?.() }}</div>
            </div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-1 text-xs rounded bg-green-100 text-green-700">{{ p.eligibility }}</span>
              <button class="px-3 py-1.5 text-sm rounded border border-slate-300 hover:bg-slate-50" @click="toggleOpen(p.id)">
                <span v-if="open.has(p.id)">Hide details</span>
                <span v-else>Show details</span>
              </button>
            </div>
          </div>
          <div class="text-sm text-slate-600 mt-2">Min: {{ minReqInline(p.min_requirements) }}</div>

          <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-1">
            <div v-if="open.has(p.id)" class="mt-4 grid md:grid-cols-2 gap-4 text-sm">
              <div class="space-y-2">
                <div class="font-medium">Subjects</div>
                <div class="flex flex-wrap gap-2">
                  <button v-for="s in p.subjects || []" :key="s" class="px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100" @click="openSubjectDialog(s, p)">{{ s }}</button>
                </div>
              </div>
              <div class="space-y-2">
                <div class="font-medium">Topics</div>
                <div class="flex flex-wrap gap-2">
                  <span v-for="t in p.topics || []" :key="t" class="px-2 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200">{{ t }}</span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="font-medium">Career paths</div>
                <ul class="list-disc pl-5 space-y-1">
                  <li v-for="c in p.career_paths || []" :key="c">{{ c }}</li>
                </ul>
              </div>
              <div class="space-y-2">
                <div class="font-medium">Industries & hiring companies</div>
                <div class="text-slate-700"><span class="font-medium">Industries:</span> {{ (p.industries || []).join(', ') }}</div>
                <div class="text-slate-700"><span class="font-medium">Companies:</span> {{ (p.hiring_companies || []).join(', ') }}</div>
              </div>
              <div class="space-y-2">
                <div class="font-medium">Entry requirements (min SPM)</div>
                <ul class="list-disc pl-5 space-y-1">
                  <li v-for="(grade, subject) in (p.min_requirements || {})" :key="subject">{{ subject }}: {{ grade }}</li>
                </ul>
              </div>
              <div class="space-y-2">
                <div class="font-medium">Costs</div>
                <div class="text-slate-700">Tuition: RM {{ p.tuition_fee_rm?.toLocaleString?.() }}</div>
                <div class="text-slate-700">Estimated per subject: RM {{ perSubject(p).toLocaleString() }}</div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- Subject dialog overlay -->
    <div v-if="subjectDialog.open" class="fixed inset-0 z-40">
      <div class="absolute inset-0 bg-black/30" @click="closeSubjectDialog"></div>
      <div class="absolute inset-0 flex items-center justify-center p-4">
        <div class="w-full max-w-xl bg-white rounded-xl border border-slate-200 shadow-xl">
          <div class="px-5 py-4 border-b flex items-center justify-between">
            <div class="text-lg font-semibold">{{ subjectDialog.name }}</div>
            <button class="text-slate-500 hover:text-slate-700" @click="closeSubjectDialog">✕</button>
          </div>
          <div class="p-5 space-y-4">
            <div class="text-slate-700">{{ subjectDialog.info.description }}</div>
            <div>
              <div class="font-medium mb-2">Topics you will learn</div>
              <ul class="list-disc pl-5 space-y-1 text-slate-700">
                <li v-for="t in subjectDialog.info.topics" :key="t">{{ t }}</li>
              </ul>
            </div>
          </div>
          <div class="px-5 py-4 border-t flex justify-end">
            <button class="px-4 py-2 rounded border border-slate-300 hover:bg-slate-50" @click="closeSubjectDialog">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ data: Object })

const open = ref(new Set())
function toggleOpen(id) {
  const s = new Set(open.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  open.value = s
}

function minReqInline(req) {
  if (!req) return ''
  try {
    const parts = Object.entries(req).map(([subject, grade]) => `${subject}: ${grade}`)
    return parts.join(', ')
  } catch {
    return ''
  }
}

function perSubject(p) {
  const total = Number(p.tuition_fee_rm || 0)
  const n = (p.subjects || []).length || 1
  return Math.round(total / n)
}

// Subject dialog state & metadata
const subjectDialog = ref({ open: false, name: '', info: { description: '', topics: [] } })
const SUBJECT_META = {
  'Programming Fundamentals': { description: 'Introduction to programming concepts and problem-solving using a high-level language.', topics: ['Variables', 'Control flow', 'Functions', 'Arrays', 'Debugging'] },
  'Data Structures': { description: 'Core structures for organizing and processing data efficiently.', topics: ['Lists', 'Stacks & Queues', 'Trees', 'Hash tables', 'Complexity basics'] },
  'Databases': { description: 'Designing and querying relational databases to store and retrieve data.', topics: ['ER modeling', 'SQL', 'Joins', 'Indexes', 'Transactions'] },
  'Web Development': { description: 'Building basic web applications and user interfaces.', topics: ['HTML', 'CSS', 'JavaScript basics', 'Client-server', 'HTTP'] },
  'Principles of Management': { description: 'Foundations of planning, organizing, leading, and controlling in organizations.', topics: ['Management roles', 'Motivation', 'Leadership', 'Decision-making', 'Strategy'] },
  'Marketing': { description: 'Creating and delivering value to customers and markets.', topics: ['4Ps', 'Segmentation', 'Branding', 'Digital marketing', 'Market research'] },
  'Accounting': { description: 'Recording and interpreting financial transactions and statements.', topics: ['Double-entry', 'Income statement', 'Balance sheet', 'Cash flow', 'Basic analysis'] },
  'Business Communication': { description: 'Professional written and verbal communication in business contexts.', topics: ['Emails & reports', 'Presentations', 'Meetings', 'Visual aids', 'Etiquette'] },
}
function getSubjectInfo(subjectName, program) {
  const meta = SUBJECT_META[subjectName] || null
  const description = meta?.description || `Overview of ${subjectName} and its relevance to this program.`
  const topics = meta?.topics?.length ? meta.topics : (program.topics || [])
  return { description, topics }
}
function openSubjectDialog(subjectName, program) {
  const info = getSubjectInfo(subjectName, program)
  subjectDialog.value = { open: true, name: subjectName, info }
}
function closeSubjectDialog() {
  subjectDialog.value = { open: false, name: '', info: { description: '', topics: [] } }
}
</script>
