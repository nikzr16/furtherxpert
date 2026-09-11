<template>
  <div class="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
    <h2 class="font-semibold mb-3 text-2xl text-indigo-700">Nearby or Online Institutions</h2>
    <div v-if="!items || !items.length" class="text-slate-600">No items yet.</div>
    <ul v-else class="list-disc list-inside space-y-1">
      <li v-for="i in items" :key="i.id" class="text-indigo-900 text-base">
        {{ i.name }}
        <span class="text-xs text-indigo-900/70">• {{ i.region }}</span>
        <span v-if="i.distance_km != null" class="text-xs text-indigo-900/70">• {{ i.distance_km }} km</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
const props = defineProps({ items: Array })
</script>
