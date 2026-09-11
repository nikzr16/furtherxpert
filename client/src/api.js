// Small fetch helper for talking to the backend API.
// Base URL comes from VITE_API_URL (set via root .env, see .env.example).

const API_BASE_URL = import.meta.env.VITE_API_URL

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`)
  }
  return response.json()
}
