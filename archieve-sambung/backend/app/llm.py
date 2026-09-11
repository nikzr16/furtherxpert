import json
import os
from typing import Any, Dict

from openai import OpenAI

SYSTEM_PROMPT = (
    "You are an academic guidance assistant for Malaysian SPM graduates. "
    "Use the provided static JSON data to return up to 3 concise program recommendations. "
    "Each recommendation must include: name, institution, reason, eligibility flag (Eligible / Conditional / Not Eligible), "
    "location, and 2–3 related financing options. Always include at least one nearby or online option. "
    "Output JSON strictly matching the schema. Keep total response <120 words per field. "
    "If unsure, mark eligibility as \"Conditional\". Include a disclaimer and list of data sources used. "
    "Academic Results: {{ACADEMIC_RESULTS}}"
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=api_key)


def call_llm(prompt: str) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        # temperature=0.2,
    )
    return response.choices[0].message.content or "{}"


def call_llm_text(system_prompt: str, prompt: str) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        # temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()


def validate_recommendations_json(text: str) -> Dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data.get("recommendations"), list):
        raise ValueError("Invalid recommendations JSON format")
    return data
