<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-semibold">Check Eligibility</h1>
    <EligibilityForm @submit="onSubmit" :loading="loading" />

    <div v-if="loading" class="space-y-4">
      <div class="h-32 rounded shimmer"></div>
      <div class="grid md:grid-cols-2 gap-6">
        <div class="h-40 rounded shimmer"></div>
        <div class="h-40 rounded shimmer"></div>
      </div>
    </div>

    <template v-else>
      <template v-if="hasChecked">
        <RecommendationsPanel :data="recommendations" :aid="loans" />
        <div class="grid md:grid-cols-2 gap-6">
          <LoanCard :items="loans" />
          <InstitutionMap :items="institutions" />
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import EligibilityForm from '../components/EligibilityForm.vue'
import RecommendationsPanel from '../components/RecommendationsPanel.vue'
import LoanCard from '../components/LoanCard.vue'
import InstitutionMap from '../components/InstitutionMap.vue'

const recommendations = ref(null)
const loans = ref([])
const institutions = ref([])
const loading = ref(false)
const hasChecked = ref(false)

async function onSubmit(payload) {
  loading.value = true
  try {
    const resp = await fetch('http://localhost:8000/eligibility', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload })
    })
    const data = await resp.json()
    // Show recommendations immediately
    recommendations.value = data
    // Fetch financial aid and institutions but don't block display
    try {
      const [aidRes, instRes] = await Promise.all([
        fetch('http://localhost:8000/financial_aid'),
        fetch('http://localhost:8000/institutions_filtered', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ preferred_locations: payload.preferred_locations })
        })
      ])
      loans.value = await aidRes.json()
      institutions.value = await instRes.json()
    } catch (e) {
      loans.value = []
      institutions.value = []
    }
  } finally {
    hasChecked.value = true
    loading.value = false
  }
}
</script>
