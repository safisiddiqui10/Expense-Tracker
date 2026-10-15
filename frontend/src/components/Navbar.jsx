import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()

  const activeClass = (path) => pathname === path ? 'nav-link--active' : undefined

  return (
    <nav className="navbar">
      <div className="nav-inner">
        <Link to="/" className="nav-brand">
          <span className="brand-icon">◈</span>
          <span className="brand-name">Budgetly</span>
        </Link>
        <div className="nav-links">
          {user ? (
            <>
              <Link to="/profile" className={activeClass('/profile')}>Dashboard</Link>
              <Link to="/analytics" className={activeClass('/analytics')}>Analytics</Link>
              <Link to="/expenses/add" className={activeClass('/expenses/add')}>Add Expense</Link>
              <a href="#" onClick={(e) => { e.preventDefault(); logout() }}>Sign out</a>
            </>
          ) : (
            <>
              <Link to="/login" className={activeClass('/login')}>Sign in</Link>
              <Link to="/register" className={`nav-cta${pathname === '/register' ? ' nav-link--active' : ''}`}>Get started</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
