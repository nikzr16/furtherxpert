Product Requirements Document – SambungBelajarmu.ai
0 Executive Summary

A web-based AI guidance POC that helps Malaysian SPM graduates discover suitable tertiary programs, financial aid, and nearby or online study options using static JSON data and GPT-5 reasoning. Built with FastAPI, Vue 3, and Tailwind, it delivers instant, factual, privacy-safe recommendations without persistent data storage.

1 Narrative

Amir, a recent SPM graduate from Johor, dreams of becoming a software engineer but feels lost. He’s unsure which colleges accept his results and how to afford tuition. He opens SambungBelajarmu.ai, enters his SPM grades, interests, and location. Within seconds, he sees eligible diploma and certificate programs, clear reasons why he qualifies, and financing options flagged as “Eligible” or “Conditional.” A chatbot explains each option concisely and even suggests nearby institutions. Amir leaves the site confident, with a shortlist and financial plan — no counselor or confusing forms required.

2 Vision & Scope

A concise, LLM-aided recommendation engine for Malaysian SPM leavers to discover education pathways and financing options.

In scope

Static JSON–based eligibility engine (SPM programs, institutions, financial aid)

GPT-5 call for concise JSON recommendations

Frontend for eligibility input, recommendation display, and chat POC

Privacy-first local execution (no user storage)

Out of scope

Live APIs or databases

Persistent user accounts

Malay-language interface

Multi-turn chat

3 Goals
Category	Goal statement	Success metric
Business	Demonstrate AI-driven guidance can cut search time from hours to minutes	80% task completion rate
Business	Validate recommendation precision	≥75% match with SME evaluation
User	Students get 3 viable programs with reasons and aid options in <10s	≤10s response time
User	Positive comprehension of recommendation info	≥4/5 user clarity rating

Non-Goals

No account management

No real-time data sources

No Malay translation in MVP

Why it matters:
Faster, clearer, and more personalized tertiary guidance increases enrolment intent and reduces dropout risk among lower-income SPM graduates.

4 Personas & Key Stories

• Amir (SPM Graduate, 17) – Unsure what to study or where; needs clear, affordable paths.
• Siti (Guidance Teacher) – Helps students find accredited programs; wants verified info fast.

“As an SPM graduate, I want to know which programs and aid options I qualify for so I can plan my next step confidently.”

5 Use-Case Matrix
ID	User Story	Acceptance Criteria
UC-1	Submit SPM results and interests	Eligibility displayed with badges
UC-2	Get 3 program recommendations	GPT-5 returns valid JSON, all entries link to static data
UC-3	View loan/scholarship options	Aid cards show eligibility and funding amount
UC-4	See nearby or online institutions	Map mock lists results within 50 km or online tag
UC-5	Use ChatPOC for single-turn query	LLM response <120 words, factual, JSON format
6 Functional Requirements
FR-1 Eligibility Check

User enters grades and interests

Backend matches rules in JSON

Returns eligibility flags (Eligible, Conditional, Not Eligible)

FR-2 Course Recommendation

Combine eligibility + LLM inference

Return max 3 programs with reason, location, and sources

FR-3 Financial Aid Lookup

Query static JSON for applicable loans/scholarships

Return eligibility badge and conditions

FR-4 Institution Finder

Use coordinates to show nearby institutions

Include “Online” tag for distance-learning options

FR-5 LLM Wrapper

Pass prompt + structured JSON schema to GPT-5

Validate output and fall back to static-only recommendations if invalid

7 Non-Functional Requirements

Performance: <10s response

Privacy: no PII stored

Reliability: local JSON loading only

Compliance: no real financial submissions

Accessibility: responsive, keyboard-friendly, WCAG AA

8 High-Level UX Flow

EligibilityForm → user inputs grades, interests, location

Backend /eligibility → returns badge summary

/recommend → GPT-5 combines JSON + eligibility rules

RecommendationsPanel → shows 3 programs + reasoning

LoanCard → displays 2–3 financing options

InstitutionMap → lists nearest or online institutions

ChatPOC → optional “Ask AI” for short guidance

9 System Architecture (textual)
[Vue Frontend]
  ├─ EligibilityForm.vue
  ├─ RecommendationsPanel.vue
  ├─ LoanCard.vue
  ├─ InstitutionMap.vue
  └─ ChatPOC.vue
       ↓
[FastAPI Backend]
  ├─ /eligibility → JSON rules engine
  ├─ /recommend → LLM wrapper + JSON merge
  ├─ /loans, /institutions → static data
       ↓
[OpenAI GPT-5 API]
  ↔ Returns structured recommendations JSON

10 Data Design
JSON Schemas
student_qualifications.json
{
  "student_id": "string",
  "location": "Johor",
  "grades": {"BM": "A", "Math": "B", "Science": "A"},
  "interests": ["engineering", "IT"]
}

programs.json
{
  "id": "P001",
  "name": "Diploma in Computer Science",
  "institution_id": "I001",
  "min_requirements": {"Math": "C", "English": "C"},
  "field": "IT",
  "duration_years": 2,
  "mode": "On-campus",
  "tuition_fee_rm": 12000
}

institutions.json
{
  "id": "I001",
  "name": "Politeknik Johor Bahru",
  "geo": {"lat": 1.476, "lon": 103.763},
  "region": "Johor",
  "type": "Public"
}

loans.json
{
  "id": "L001",
  "name": "PTPTN Loan",
  "eligibility": {"nationality": "Malaysian", "min_gpa": 2.0},
  "max_amount_rm": 20000,
  "repayment": "After graduation"
}

scholarships.json
{
  "id": "S001",
  "name": "MARA Education Sponsorship",
  "eligibility": {"race": "Bumiputera", "min_gpa": 3.0},
  "amount_rm": 25000,
  "bond": "3 years public service"
}


DTO definitions

from pydantic import BaseModel
from typing import Dict, List

class Program(BaseModel):
    id: str
    name: str
    institution_id: str
    min_requirements: Dict[str, str]
    field: str
    duration_years: int
    mode: str
    tuition_fee_rm: int

class Institution(BaseModel):
    id: str
    name: str
    geo: Dict[str, float]
    region: str
    type: str

class Loan(BaseModel):
    id: str
    name: str
    eligibility: Dict[str, str]
    max_amount_rm: int
    repayment: str

11 Backend API Contract
Endpoint	Method	Description
/health	GET	Health check
/eligibility	POST	Check qualification eligibility
/recommend	POST	Get LLM-assisted recommendations
/loans	GET	List financial aid options
/institutions	GET	List all institutions
Example FastAPI Route Stubs
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json, openai, os

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

class StudentInput(BaseModel):
    grades: dict
    interests: list
    location: str

@app.post("/eligibility")
def check_eligibility(data: StudentInput):
    programs = json.load(open("data/programs.json"))
    eligible = []
    for p in programs:
        if all(
            data.grades.get(sub, "F") <= req
            for sub, req in p["min_requirements"].items()
        ):
            eligible.append({**p, "eligibility": "Eligible"})
    return {"eligible_programs": eligible}

@app.post("/recommend")
def recommend(data: StudentInput):
    prompt = f"""
You are an education advisor for Malaysian students. 
Based on these grades {data.grades} and interests {data.interests},
suggest up to 3 programs from the JSON list, with reason and eligibility status.
Return JSON strictly following schema.
"""
    completion = openai.ChatCompletion.create(
        model="gpt-5",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


Security notes

Store API keys in .env

Use ratelimit middleware (slowapi or similar)

Never log student data or LLM responses

Use Poetry for environment reproducibility

12 Frontend Contract (Vue 3 + Tailwind)

Component list

EligibilityForm.vue – form for grades, interests, location

RecommendationsPanel.vue – renders program + eligibility badges

LoanCard.vue – displays loan/scholarship info

InstitutionMap.vue – mock map or list view

ChatPOC.vue – single-turn GPT-5 chat window

Example SFC – EligibilityForm.vue
<template>
  <form @submit.prevent="submitForm" class="p-4 space-y-3">
    <input v-model="location" placeholder="Location" class="input" />
    <textarea v-model="grades" placeholder="Grades JSON" class="textarea" />
    <button type="submit" class="btn">Check Eligibility</button>
  </form>
</template>

<script setup>
import { ref } from 'vue'
const location = ref('')
const grades = ref('{}')
const emit = defineEmits(['submit'])
function submitForm() {
  emit('submit', { location: location.value, grades: JSON.parse(grades.value) })
}
</script>

Example SFC – ChatPOC.vue
<template>
  <div class="p-4">
    <textarea v-model="query" placeholder="Ask about your study options" class="textarea"></textarea>
    <button @click="askAI" class="btn mt-2">Ask</button>
    <pre v-if="response">{{ response }}</pre>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const query = ref('')
const response = ref('')
async function askAI() {
  const res = await fetch('/recommend', { method: 'POST', body: JSON.stringify({ query: query.value }) })
  response.value = await res.text()
}
</script>

13 LLM Prompting & Response Schema

System Prompt (≤300 tokens)

You are an academic guidance assistant for Malaysian SPM graduates. 
Use the provided static JSON data to return up to 3 concise program recommendations. 
Each recommendation must include: name, institution, reason, eligibility flag (Eligible / Conditional / Not Eligible), location, and 2–3 related financing options. 
Always include at least one nearby or online option. 
Output JSON strictly matching the schema below. 
Keep total response <120 words per field. 
If unsure, mark eligibility as "Conditional". 
Include a disclaimer and list of data sources used.


LLM JSON Response Schema

{
  "recommendations": [
    {
      "program_name": "Diploma in Computer Science",
      "institution": "Politeknik Johor Bahru",
      "reason": "Meets SPM Math and English requirement",
      "eligibility": "Eligible",
      "location": "Johor",
      "financing": [
        {"name": "PTPTN Loan", "eligible": true},
        {"name": "MARA Sponsorship", "eligible": false}
      ]
    }
  ],
  "loans": ["PTPTN Loan", "MARA Education Sponsorship"],
  "institutions": ["Politeknik Johor Bahru"],
  "disclaimer": "This is informational only. Verify details with official sources.",
  "sources": ["programs.json", "loans.json"]
}


Example user prompt

“I got SPM results BM A, Math B, Science A and I’m interested in IT near Johor.”

Expected JSON response
(as above, with Eligible status for IT diploma and nearby institution)

Hallucination mitigation

Cross-check LLM output against local JSON IDs

Reject responses with unknown program/institution IDs

Require sources[] field for traceability

14 Business & Policy Considerations

Accuracy: all programs/aids verified from MOHE public data in production

Privacy: no persistent storage or cookies

Disclaimer: non-binding, advisory only

Localization: English-only for POC; Malay support optional later

15 Acceptance Criteria & KPIs

Backend + frontend integrate smoothly with static JSON

Eligibility logic passes 6 test profiles

GPT-5 responses valid JSON ≥95% of time

Page loads <2s, total roundtrip <10s

≥75% match with human counselor outputs

16 Implementation Plan (2-week POC Sprint)
Day	Task	Owner
1–2	Setup repo, Poetry env, folder structure	Backend
3–4	Create static JSON datasets + DTOs	Backend
5–6	Implement eligibility + loan endpoints	Backend
7	Integrate GPT-5 wrapper	Backend
8–9	Build Vue components (form, results, chat)	Frontend
10	Wire frontend to FastAPI	Both
11	Add Tailwind styling & eligibility badges	Frontend
12	Run tests, sample data validation	Both
13	Internal demo & tuning	SME
14	Final QA & documentation	Both
17 Testing & Sample Data

Pytest Example

def test_eligibility_basic():
    from app.main import check_eligibility
    data = {"grades": {"Math": "A", "English": "B"}, "interests": ["IT"], "location": "Johor"}
    res = check_eligibility(data)
    assert any(p["eligibility"] == "Eligible" for p in res["eligible_programs"])


Sample Students

[
  {"name": "Amir", "grades": {"BM": "A", "Math": "B", "Science": "A"}, "interests": ["IT"], "location": "Johor"},
  {"name": "Siti", "grades": {"BM": "B", "Math": "C"}, "interests": ["business"], "location": "Selangor"},
  {"name": "Lim", "grades": {"BM": "A", "Science": "A", "Math": "A"}, "interests": ["engineering"], "location": "Penang"},
  {"name": "Aisyah", "grades": {"BM": "C", "Math": "B"}, "interests": ["arts"], "location": "Perak"},
  {"name": "Rahman", "grades": {"BM": "A", "Math": "C"}, "interests": ["accounting"], "location": "Kedah"},
  {"name": "Priya", "grades": {"BM": "A", "Math": "B", "English": "B"}, "interests": ["law"], "location": "KL"}
]

18 Extensibility Notes

Swap JSON for SQLite or Postgres later using SQLAlchemy

Add language toggle (English/Malay) via i18n plugin

Integrate APIs from PTPTN/MARA for live updates

Modularize eligibility logic to accept different qualification types

19 Developer Launch Checklist

 cp .env.example .env and add OpenAI key

 poetry install && poetry run uvicorn app.main:app --reload

 npm install && npm run dev in frontend

 Verify static JSON loads correctly

 Run unit tests with pytest

 Smoke test /health, /eligibility, /recommend endpoints

 Confirm GPT-5 responses follow JSON schema