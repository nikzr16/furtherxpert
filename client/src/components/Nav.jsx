import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Icon, Logo } from './ui'

const PUBLIC_LINKS = [{ to: '/explore', label: 'Explore programs' }]

const AUTHED_LINKS = [
  { to: '/my-results', label: 'My results' },
  { to: '/results', label: 'SPM results' },
  { to: '/interest-test', label: 'Interest test' },
  { to: '/explore', label: 'Explore' },
]

const desktopLinkClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
  }`

const mobileLinkClass = ({ isActive }) =>
  `block rounded-lg px-3 py-2.5 text-base font-medium ${
    isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-100'
  }`

export default function Nav() {
  const { isAuthenticated, initializing } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const links = isAuthenticated ? AUTHED_LINKS : PUBLIC_LINKS
  const closeMenu = () => setMenuOpen(false)

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/85 backdrop-blur-lg">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <Link to="/" onClick={closeMenu} className="rounded-lg" aria-label="FurtherXpert home">
          <Logo />
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {!initializing &&
            links.map((link) => (
              <NavLink key={link.to} to={link.to} className={desktopLinkClass}>
                {link.label}
              </NavLink>
            ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {!initializing && !isAuthenticated && (
            <>
              <Link to="/login" className="btn btn-ghost">
                Log in
              </Link>
              <Link to="/register" className="btn btn-primary">
                Get started
              </Link>
            </>
          )}
          {!initializing && isAuthenticated && (
            <NavLink
              to="/account"
              className={({ isActive }) =>
                `btn ${isActive ? 'bg-indigo-50 text-indigo-700' : 'btn-ghost'}`
              }
            >
              <Icon name="user" className="size-5" />
              Account
            </NavLink>
          )}
        </div>

        <button
          type="button"
          className="btn btn-ghost -mr-2 px-2.5 md:hidden"
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <Icon name={menuOpen ? 'close' : 'menu'} className="size-6" />
          <span className="sr-only">{menuOpen ? 'Close menu' : 'Open menu'}</span>
        </button>
      </div>

      {menuOpen && (
        <div id="mobile-menu" className="border-t border-slate-200 bg-white md:hidden">
          <nav aria-label="Mobile" className="container-page space-y-1 py-3">
            {!initializing &&
              links.map((link) => (
                <NavLink key={link.to} to={link.to} className={mobileLinkClass} onClick={closeMenu}>
                  {link.label}
                </NavLink>
              ))}
            {!initializing && isAuthenticated && (
              <NavLink to="/account" className={mobileLinkClass} onClick={closeMenu}>
                Account
              </NavLink>
            )}
            {!initializing && !isAuthenticated && (
              <div className="grid grid-cols-2 gap-2 pt-2">
                <Link to="/login" className="btn btn-secondary" onClick={closeMenu}>
                  Log in
                </Link>
                <Link to="/register" className="btn btn-primary" onClick={closeMenu}>
                  Get started
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
