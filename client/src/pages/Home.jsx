import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { isAuthenticated, initializing } = useAuth()

  return (
    <main className="mx-auto max-w-xl p-6">
      <h2 className="text-xl font-semibold">See what you're likely to excel in, and love</h2>
      <p className="mt-2 text-gray-600">
        FurtherXpert turns your SPM results and a short interest test into two charts, a shortlist of diploma
        programs you're likely to love, and which official UPU programs you qualify for.
      </p>

      {!initializing && !isAuthenticated && (
        <div className="mt-4 flex gap-3">
          <Link to="/register" className="rounded bg-blue-700 px-4 py-2 text-white hover:bg-blue-800">
            Create an account
          </Link>
          <Link to="/login" className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-100">
            Log in
          </Link>
        </div>
      )}

      {!initializing && isAuthenticated && (
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/results" className="rounded bg-blue-700 px-4 py-2 text-white hover:bg-blue-800">
            Add SPM results
          </Link>
          <Link to="/interest-test" className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-100">
            Take the interest test
          </Link>
          <Link to="/my-results" className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-100">
            View my results
          </Link>
        </div>
      )}

      <p className="mt-6 text-sm text-gray-500">
        <Link to="/explore" className="underline hover:no-underline">
          Browse every diploma program
        </Link>{' '}
        without logging in.
      </p>
    </main>
  )
}
