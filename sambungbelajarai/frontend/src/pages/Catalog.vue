<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-semibold">Explore Courses & Universities</h1>

    <div class="grid grid-cols-12 gap-6">
      <!-- Filters Sidebar -->
      <aside class="col-span-12 lg:col-span-3 space-y-4">
        <div class="p-4 bg-white rounded-xl border border-slate-200 space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Subjects</h2>
            <button v-if="selectedSubjects.size" class="text-sm text-blue-700 hover:underline" @click="clearSubjects">Clear</button>
          </div>
          <input v-model="subjectQuery" type="text" placeholder="Search subjects..." class="w-full border border-slate-300 rounded p-2 text-sm" />
          <div class="max-h-80 overflow-auto pr-1 space-y-1">
            <label v-for="s in filteredSubjects" :key="s" class="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" :value="s" :checked="selectedSubjects.has(s)" @change="toggleSubject(s)" />
              <span>{{ s }}</span>
            </label>
          </div>
        </div>

        <div class="p-4 bg-white rounded-xl border border-slate-200 space-y-3">
          <h2 class="text-lg font-semibold">Search</h2>
          <input v-model="search" type="text" placeholder="Program or university..." class="w-full border border-slate-300 rounded p-2 text-sm" />
        </div>
      </aside>

      <!-- Results -->
      <section class="col-span-12 lg:col-span-9 space-y-5">
        <div class="text-slate-600 text-sm">Showing {{ totalPrograms }} programs at {{ groupedResults.length }} universities</div>

        <div v-for="grp in groupedResults" :key="grp.institution.id" class="bg-white rounded-xl border border-slate-200">
          <div class="px-5 py-4 border-b flex items-center justify-between">
            <div>
              <div class="text-xl font-semibold">{{ grp.institution.name }}</div>
              <div class="text-slate-600 text-sm">{{ grp.institution.region }} • {{ grp.institution.type }}</div>
            </div>
          </div>

          <div class="divide-y">
            <div v-for="p in grp.programs" :key="p.id" class="p-5">
              <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                  <div class="text-lg font-medium">{{ p.name }}</div>
                  <div class="text-slate-600 text-sm">Field: {{ p.field }} • Mode: {{ p.mode }} • {{ p.duration_years }} years • RM {{ p.tuition_fee_rm.toLocaleString() }}</div>
                </div>
                <button class="px-3 py-1.5 text-sm rounded border border-slate-300 hover:bg-slate-50" @click="toggleOpen(p.id)">
                  <span v-if="open.has(p.id)">Hide details</span>
                  <span v-else>Show details</span>
                </button>
              </div>

              <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 -translate-y-1">
                <div v-if="open.has(p.id)" class="mt-4 grid md:grid-cols-2 gap-4 text-sm">
                  <div class="space-y-2">
                    <div class="font-medium">Subjects</div>
                    <div class="flex flex-wrap gap-2">
                      <button
                        v-for="s in p.subjects || []"
                        :key="s"
                        class="px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 cursor-pointer"
                        @click="openSubjectDialog(s, p)"
                      >
                        {{ s }}
                      </button>
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
                    <div class="text-slate-700">Estimated per subject: RM {{ Math.round((p.tuition_fee_rm||0)/((p.subjects||[]).length||1)).toLocaleString() }}</div>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </div>

        <div v-if="!groupedResults.length" class="text-slate-600">No programs match your filters.</div>
      </section>
    </div>
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
import { ref, computed, onMounted } from 'vue'

const programs = ref([])
const institutions = ref([])
const loading = ref(false)
const error = ref('')

const subjectQuery = ref('')
const selectedSubjects = ref(new Set())
const search = ref('')
const open = ref(new Set())

// Subject dialog state
const subjectDialog = ref({ open: false, name: '', info: { description: '', topics: [] } })

function toggleOpen(id) {
  const s = new Set(open.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  open.value = s
}

function toggleSubject(s) {
  const set = new Set(selectedSubjects.value)
  if (set.has(s)) set.delete(s); else set.add(s)
  selectedSubjects.value = set
}
function clearSubjects() { selectedSubjects.value = new Set() }

const allSubjects = computed(() => {
  const acc = new Set()
  programs.value.forEach(p => (p.subjects || []).forEach(s => acc.add(s)))
  return Array.from(acc).sort()
})

const filteredSubjects = computed(() => {
  const q = subjectQuery.value.trim().toLowerCase()
  if (!q) return allSubjects.value
  return allSubjects.value.filter(s => s.toLowerCase().includes(q))
})

const filteredPrograms = computed(() => {
  const sels = selectedSubjects.value
  const q = search.value.trim().toLowerCase()
  return programs.value.filter(p => {
    const subjOk = !sels.size || (p.subjects || []).some(s => sels.has(s))
    const text = `${p.name} ${(p._institution || {}).name || ''}`.toLowerCase()
    const searchOk = !q || text.includes(q)
    return subjOk && searchOk
  })
})

const groupedResults = computed(() => {
  const map = new Map()
  filteredPrograms.value.forEach(p => {
    const inst = p._institution
    if (!map.has(inst.id)) map.set(inst.id, { institution: inst, programs: [] })
    map.get(inst.id).programs.push(p)
  })
  return Array.from(map.values()).sort((a,b) => a.institution.name.localeCompare(b.institution.name))
})

const totalPrograms = computed(() => filteredPrograms.value.length)

async function load() {
  loading.value = true
  try {
    const [instRes, progRes] = await Promise.all([
      fetch('http://localhost:8000/institutions'),
      fetch('http://localhost:8000/programs')
    ])
    const [inst, prog] = await Promise.all([instRes.json(), progRes.json()])
    institutions.value = inst
    // join institution onto program for rendering convenience
    const instById = new Map(inst.map(i => [i.id, i]))
    programs.value = prog.map(p => ({ ...p, _institution: instById.get(p.institution_id) }))
  } catch (e) {
    error.value = 'Failed to load data'
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Lightweight subject metadata for dialog content
const SUBJECT_META = {
  'Programming Fundamentals': {
    description: 'Introduction to programming concepts and problem-solving using a high-level language.',
    topics: ['Variables', 'Control flow', 'Functions', 'Arrays', 'Debugging']
  },
  'Data Structures': {
    description: 'Core structures for organizing and processing data efficiently.',
    topics: ['Lists', 'Stacks & Queues', 'Trees', 'Hash tables', 'Complexity basics']
  },
  'Databases': {
    description: 'Designing and querying relational databases to store and retrieve data.',
    topics: ['ER modeling', 'SQL', 'Joins', 'Indexes', 'Transactions']
  },
  'Web Development': {
    description: 'Building basic web applications and user interfaces.',
    topics: ['HTML', 'CSS', 'JavaScript basics', 'Client-server', 'HTTP']
  },
  'Computer Basics': {
    description: 'Essential computer literacy and productivity skills.',
    topics: ['Operating systems', 'Files & folders', 'Email & web', 'Office tools', 'Safety']
  },
  'Intro to Programming': {
    description: 'Getting started with coding and automating simple tasks.',
    topics: ['Syntax', 'Variables', 'Loops', 'Functions', 'Problem decomposition']
  },
  'Networking Fundamentals': {
    description: 'Basics of how computers communicate over networks.',
    topics: ['OSI model', 'IP addressing', 'Routing vs switching', 'LAN/WAN', 'Troubleshooting']
  },
  'Principles of Management': {
    description: 'Foundations of planning, organizing, leading, and controlling in organizations.',
    topics: ['Management roles', 'Motivation', 'Leadership', 'Decision-making', 'Strategy']
  },
  'Marketing': {
    description: 'Creating and delivering value to customers and markets.',
    topics: ['4Ps', 'Segmentation', 'Branding', 'Digital marketing', 'Market research']
  },
  'Accounting': {
    description: 'Recording and interpreting financial transactions and statements.',
    topics: ['Double-entry', 'Income statement', 'Balance sheet', 'Cash flow', 'Basic analysis']
  },
  'Business Communication': {
    description: 'Professional written and verbal communication in business contexts.',
    topics: ['Emails & reports', 'Presentations', 'Meetings', 'Visual aids', 'Etiquette']
  }
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

 
