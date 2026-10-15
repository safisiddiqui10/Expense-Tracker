import { useState, useEffect } from 'react'
import { Link, useSearchParams, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import '../styles/profile.css'

export default function Profile() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()

  const category = searchParams.get('category') || ''
  const dateFrom = searchParams.get('date_from') || ''
  const dateTo = searchParams.get('date_to') || ''

  const [localCategory, setLocalCategory] = useState(category)
  const [localDateFrom, setLocalDateFrom] = useState(dateFrom)
  const [localDateTo, setLocalDateTo] = useState(dateTo)

  // Keep filter inputs in sync when URL params change (e.g. browser back/forward)
  useEffect(() => {
    setLocalCategory(category)
    setLocalDateFrom(dateFrom)
    setLocalDateTo(dateTo)
  }, [category, dateFrom, dateTo])

  const [data, setData] = useState(null)
  const [flash, setFlash] = useState(location.state?.flash || null)

  // Clear flash from history state so refresh doesn't re-show it
  useEffect(() => {
    if (location.state?.flash) {
      navigate(location.pathname + location.search, { replace: true, state: {} })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    api.getProfile({ category, date_from: dateFrom, date_to: dateTo })
      .then(setData)
      .catch(console.error)
  }, [category, dateFrom, dateTo])

  const handleApply = (e) => {
    e.preventDefault()
    const params = {}
    if (localCategory) params.category = localCategory
    if (localDateFrom) params.date_from = localDateFrom
    if (localDateTo) params.date_to = localDateTo
    setSearchParams(params)
  }

  const handleClear = (e) => {
    e.preventDefault()
    setLocalCategory('')
    setLocalDateFrom('')
    setLocalDateTo('')
    setSearchParams({})
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this expense?')) return
    try {
      await api.deleteExpense(id)
      const fresh = await api.getProfile({ category, date_from: dateFrom, date_to: dateTo })
      setData(fresh)
    } catch (err) {
      console.error(err)
    }
  }

  if (!data) return (
    <div className="profile-page">
      <div className="profile-inner" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <p style={{ color: 'var(--ink-muted)', fontFamily: 'var(--font-body)' }}>Loading…</p>
      </div>
    </div>
  )

  const { user, expenses, stats, categories, filter_categories, filter_active } = data

  return (
    <div className="profile-page">
      <div className="profile-inner">

        <div className="profile-header">
          <div>
            <h1 className="profile-title">Dashboard</h1>
            <p className="profile-subtitle">Welcome back, {user.name}</p>
          </div>
          <Link to="/expenses/add" className="btn-accent">+ Add expense</Link>
        </div>

        <aside className="profile-sidebar">
          <section className="profile-section">
            <div className="user-card">
              <div className="avatar">{user.initials}</div>
              <div className="user-card-body">
                <h2 className="user-name">{user.name}</h2>
                <p className="user-email">{user.email}</p>
                <span className="user-since">Member since {user.member_since}</span>
              </div>
              <div className="user-card-actions">
                <a href="#" className="btn-ghost" onClick={(e) => { e.preventDefault(); logout() }}>Sign out</a>
              </div>
            </div>
          </section>

          <section className="profile-section">
            <h2 className="section-title">
              <span className="section-icon">▤</span>
              Spending by Category
            </h2>
            {categories.length > 0 ? (
              <div className="breakdown-list">
                {categories.map((cat) => (
                  <div className="breakdown-row" key={cat.name}>
                    <div className="breakdown-meta">
                      <span className="breakdown-name">
                        <span className={`cat-badge cat-badge--${cat.name.toLowerCase()}`}>{cat.name}</span>
                      </span>
                      <span className="breakdown-amount">₹{cat.total.toFixed(2)}</span>
                    </div>
                    <div className="breakdown-track">
                      <div
                        className={`breakdown-bar breakdown-bar--${cat.name.toLowerCase()}`}
                        style={{ width: `${cat.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">◎</div>
                <p className="empty-state-text">No data yet.</p>
              </div>
            )}
          </section>
        </aside>

        <main className="profile-main">
          <section className="profile-section">
            <h2 className="section-title">
              <span className="section-icon">◈</span>
              Overview
            </h2>
            <div className="stats-row">
              <div className="stat-card">
                <span className="stat-label">Total Spent</span>
                <span className="stat-value">₹{stats.total.toFixed(2)}</span>
                <span className="stat-sub">all time</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Transactions</span>
                <span className="stat-value">{stats.count}</span>
                <span className="stat-sub">entries logged</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Top Category</span>
                <span className="stat-value stat-value--category">{stats.top_category || '—'}</span>
                <span className="stat-sub">highest spending</span>
              </div>
            </div>
          </section>

          <section className="profile-section">
            <h2 className="section-title">
              <span className="section-icon">≡</span>
              Transaction History
            </h2>

            {flash && (
              <div className="auth-success" style={{ marginBottom: '1rem' }}>
                {flash}
              </div>
            )}

            <form className="filter-form" onSubmit={handleApply}>
              <div className="filter-row">
                <div className="filter-field">
                  <label className="filter-label" htmlFor="filter-category">Category</label>
                  <select
                    className="filter-select"
                    id="filter-category"
                    value={localCategory}
                    onChange={(e) => setLocalCategory(e.target.value)}
                  >
                    <option value="">All</option>
                    {filter_categories.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div className="filter-field">
                  <label className="filter-label" htmlFor="filter-date-from">From</label>
                  <input
                    className="filter-input"
                    type="date"
                    id="filter-date-from"
                    value={localDateFrom}
                    onChange={(e) => setLocalDateFrom(e.target.value)}
                  />
                </div>
                <div className="filter-field">
                  <label className="filter-label" htmlFor="filter-date-to">To</label>
                  <input
                    className="filter-input"
                    type="date"
                    id="filter-date-to"
                    value={localDateTo}
                    onChange={(e) => setLocalDateTo(e.target.value)}
                  />
                </div>
                <div className="filter-actions">
                  <button className="btn-primary filter-btn" type="submit">Apply</button>
                  <a className="btn-ghost filter-btn" href="#" onClick={handleClear}>Clear</a>
                </div>
              </div>
            </form>

            {filter_active && (
              <p className="filter-notice">
                ↳ {expenses.length} result{expenses.length !== 1 ? 's' : ''} filtered
              </p>
            )}

            {expenses.length > 0 ? (
              <div className="expense-table-wrap">
                <table className="expense-table">
                  <thead>
                    <tr>
                      <th className="col-date">Date</th>
                      <th>Description</th>
                      <th>Category</th>
                      <th className="col-amount">Amount</th>
                      <th className="col-actions">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expenses.map((expense) => (
                      <tr key={expense.id}>
                        <td className="col-date">{expense.date}</td>
                        <td className="col-desc">{expense.description}</td>
                        <td>
                          <span className={`cat-badge cat-badge--${expense.category.toLowerCase()}`}>
                            {expense.category}
                          </span>
                        </td>
                        <td className="col-amount">₹{expense.amount.toFixed(2)}</td>
                        <td className="col-actions">
                          <Link
                            to={`/expenses/${expense.id}/edit`}
                            className="action-link action-link--edit"
                          >Edit</Link>
                          <button
                            type="button"
                            className="btn-delete"
                            onClick={() => handleDelete(expense.id)}
                          >Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">◎</div>
                <p className="empty-state-text">No expenses logged yet.</p>
                <Link to="/expenses/add" className="btn-primary">Add your first expense</Link>
              </div>
            )}
          </section>
        </main>

      </div>
    </div>
  )
}
