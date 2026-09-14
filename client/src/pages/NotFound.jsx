import { Link } from 'react-router-dom'
import { Icon } from '../components/ui'

export default function NotFound() {
  return (
    <main className="container-page flex min-h-[60vh] flex-col items-center justify-center py-16 text-center">
      <p className="text-sm font-semibold text-indigo-600">404</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">Page not found</h1>
      <p className="mt-3 max-w-md text-slate-600">The page you're looking for doesn't exist or has moved.</p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link to="/" className="btn btn-primary">
          <Icon name="arrowLeft" className="size-4" />
          Back to home
        </Link>
        <Link to="/explore" className="btn btn-secondary">
          Explore programs
        </Link>
      </div>
    </main>
  )
}
