import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Logo } from './ui'

export default function Footer() {
  const { isAuthenticated } = useAuth()
  const year = new Date().getFullYear()

  const columns = [
    {
      title: 'Discover',
      links: [
        { to: '/explore', label: 'Explore programs' },
        { to: '/interest-test', label: 'Interest test' },
        { to: '/my-results', label: 'My results' },
      ],
    },
    {
      title: 'Account',
      links: isAuthenticated
        ? [
            { to: '/results', label: 'SPM results' },
            { to: '/account', label: 'Account settings' },
          ]
        : [
            { to: '/register', label: 'Create an account' },
            { to: '/login', label: 'Log in' },
          ],
    },
  ]

  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-page grid grid-cols-2 gap-10 py-12 md:grid-cols-[2fr_1fr_1fr]">
        <div className="col-span-2 max-w-sm md:col-span-1">
          <Logo />
          <p className="mt-4 text-sm leading-relaxed text-slate-500">
            Helping SPM leavers see what they're likely to excel in and love, and which UPU diploma programs they
            qualify for.
          </p>
        </div>
        {columns.map((column) => (
          <div key={column.title}>
            <h2 className="text-sm font-semibold text-slate-900">{column.title}</h2>
            <ul className="mt-4 space-y-3">
              {column.links.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className="text-sm text-slate-500 transition hover:text-indigo-600">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-slate-100">
        <div className="container-page flex flex-col gap-2 py-6 text-xs text-slate-400 sm:flex-row sm:justify-between">
          <p>© {year} FurtherXpert. All rights reserved.</p>
          <p>Program data: e-Panduan UPU, Kementerian Pendidikan Tinggi.</p>
        </div>
      </div>
    </footer>
  )
}
