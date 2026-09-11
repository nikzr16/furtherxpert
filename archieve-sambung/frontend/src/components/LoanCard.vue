<template>
  <div class="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
    <h2 class="font-semibold mb-3 text-2xl text-emerald-700">Financial Aid</h2>
    <div v-if="!items || !items.length" class="text-slate-600">No items yet.</div>
    <div v-else class="space-y-3">
      <div v-for="l in items" :key="l.id" class="border border-emerald-200 rounded p-4 bg-emerald-50/50">
        <div class="flex items-center justify-between">
          <div class="font-medium text-emerald-900 text-lg">{{ l.name }}</div>
          <div class="flex items-center gap-2">
            <span v-if="typeOf(l) === 'Loan'" class="px-2 py-0.5 text-xs rounded bg-emerald-200 text-emerald-900 border border-emerald-300">Loan</span>
            <span v-else-if="typeOf(l) === 'Scholarship'" class="px-2 py-0.5 text-xs rounded bg-sky-200 text-sky-900 border border-sky-300">Scholarship</span>
          </div>
        </div>
        <div class="text-sm text-emerald-900/70 mt-1">
          <span v-if="l.max_amount_rm">Max: RM {{ l.max_amount_rm?.toLocaleString?.() }}</span>
          <span v-else-if="l.amount_rm">Amount: RM {{ l.amount_rm?.toLocaleString?.() }}</span>
          <span v-if="l.provider" class="ml-2 px-1.5 py-0.5 text-xs rounded bg-white border border-emerald-300 text-emerald-800">{{ l.provider }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ items: Array })
</script>
