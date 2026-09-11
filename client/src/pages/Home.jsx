import { useEffect, useState } from 'react'
import { getHealth } from '../api'

export default function Home() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main className="mx-auto max-w-xl p-6">
      <h2 className="text-xl font-semibold">Home</h2>
      <p className="mt-2 text-gray-600">
        This is a placeholder page. Backend health check:
      </p>
      {error && <p className="mt-2 text-red-600">Error: {error}</p>}
      {!error && !health && <p className="mt-2 text-gray-500">Checking...</p>}
      {health && (
        <pre className="mt-2 rounded bg-gray-100 p-3 text-sm">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}
    </main>
  )
}
