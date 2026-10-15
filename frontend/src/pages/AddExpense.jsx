import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const VALID_CATEGORIES = ['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']

export default function AddExpense() {
  const navigate = useNavigate()
  const today = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({ amount: '', category: '', date: today, description: '' })
  const [error, setError] = useState(null)

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await api.addExpense(form)
      navigate('/profile', { state: { flash: 'Expense added successfully.' } })
    } catch (err) {
      setError(err.error || 'Could not save expense.')
    }
  }

  return (
    <div className="form-page">
      <div className="form-page-inner">
        <div className="form-page-header">
          <Link to="/profile" className="back-link">← Dashboard</Link>
          <h1 className="profile-title" style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', color: 'var(--ink)' }}>
            Add Expense
          </h1>
        </div>

        {error && <div className="auth-error" style={{ marginBottom: '1rem' }}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-card">
            <div className="form-card-header">
              <p className="form-card-title">New transaction</p>
              <p className="form-card-subtitle">Fill in the details below to log your expense.</p>
            </div>
            <div className="form-card-body">
              <div className="form-grid-2">
                <div className="form-group">
                  <label htmlFor="amount">Amount (₹)</label>
                  <input
                    type="number"
                    id="amount"
                    name="amount"
                    className="form-input"
                    step="0.01"
                    min="0.01"
                    value={form.amount}
                    placeholder="0.00"
                    required
                    onChange={handleChange}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="date">Date</label>
                  <input
                    type="date"
                    id="date"
                    name="date"
                    className="form-input"
                    value={form.date}
                    required
                    onChange={handleChange}
                  />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="category">Category</label>
                <select
                  id="category"
                  name="category"
                  className="form-input"
                  required
                  value={form.category}
                  onChange={handleChange}
                >
                  <option value="" disabled>Select a category</option>
                  {VALID_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="description">
                  Description <span className="label-optional">(optional)</span>
                </label>
                <input
                  type="text"
                  id="description"
                  name="description"
                  className="form-input"
                  maxLength="200"
                  value={form.description}
                  placeholder="e.g. Lunch at cafe"
                  onChange={handleChange}
                />
              </div>
            </div>
            <div className="form-card-footer">
              <Link to="/profile" className="btn-ghost">Cancel</Link>
              <button type="submit" className="btn-accent">Save Expense</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
