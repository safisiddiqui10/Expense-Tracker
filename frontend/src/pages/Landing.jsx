import { useState, useEffect } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import '../styles/landing.css'

const VIDEO_URL = 'https://www.youtube.com/embed/dQw4w9WgXcQ'

export default function Landing() {
  const { user } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape' && isOpen) setIsOpen(false)
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen])

  if (user === undefined) return null
  if (user) return <Navigate to="/profile" replace />

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-badge"><span className="badge-dot"></span>Free to use &middot; No credit card needed</div>
          <h1 className="hero-title">
            Track every rupee.<br />
            <em>Know where it goes.</em>
          </h1>
          <p className="hero-subtitle">
            Budgetly helps you log expenses, spot patterns, and stay
            on budget — without the spreadsheet headache.
          </p>
          <div className="hero-actions">
            <Link to="/register" className="btn-primary">Create free account</Link>
            <button type="button" className="btn-ghost" onClick={() => setIsOpen(true)}>See how it works</button>
          </div>
        </div>
        <div className="hero-visual">
          <div className="mock-card">
            <div className="mock-dots">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
            </div>
            <div className="mock-stats">
              <div className="mock-stat">
                <span className="mock-stat-label">This month</span>
                <span className="mock-stat-value">₹18,240</span>
                <span className="mock-stat-change positive">+12% vs last</span>
              </div>
              <div className="mock-stat">
                <span className="mock-stat-label">Budget left</span>
                <span className="mock-stat-value">₹6,760</span>
                <span className="mock-stat-change positive">43% remaining</span>
              </div>
              <div className="mock-stat">
                <span className="mock-stat-label">Transactions</span>
                <span className="mock-stat-value">34</span>
                <span className="mock-stat-change muted">this month</span>
              </div>
            </div>
            <div className="mock-bars">
              <div className="mock-bar-row">
                <span className="mock-cat">Food</span>
                <div className="mock-bar-track">
                  <div className="mock-bar mock-bar-food" style={{ width: '68%' }}></div>
                </div>
              </div>
              <div className="mock-bar-row">
                <span className="mock-cat">Travel</span>
                <div className="mock-bar-track">
                  <div className="mock-bar mock-bar-travel" style={{ width: '48%' }}></div>
                </div>
              </div>
              <div className="mock-bar-row">
                <span className="mock-cat">Bills</span>
                <div className="mock-bar-track">
                  <div className="mock-bar mock-bar-bills" style={{ width: '35%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="features" id="features">
        <div className="features-inner">
          <div className="feature-card">
            <div className="feature-icon">₹</div>
            <h3 className="feature-title">Log expenses instantly</h3>
            <p className="feature-body">Add any expense in seconds. Category, amount, date, description — all in one simple form.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">◎</div>
            <h3 className="feature-title">Understand your patterns</h3>
            <p className="feature-body">See exactly where your money goes with category breakdowns and monthly summaries.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">◷</div>
            <h3 className="feature-title">Filter by time period</h3>
            <p className="feature-body">View your spending for any date range — last week, last month, or a custom period.</p>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-inner">
          <h2 className="cta-title">Ready to take control?</h2>
          <p className="cta-body">Join thousands of people who track their expenses with Budgetly.</p>
          <Link to="/register" className="btn-primary">Create free account</Link>
        </div>
      </section>

      <div
        className={`video-modal-overlay${isOpen ? ' active' : ''}`}
        onClick={(e) => e.target === e.currentTarget && setIsOpen(false)}
      >
        <div className="video-modal">
          <button type="button" className="video-modal-close" onClick={() => setIsOpen(false)}>&times;</button>
          <div className="video-modal-body">
            <iframe
              src={isOpen ? `${VIDEO_URL}?autoplay=1` : ''}
              title="Budgetly demo"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      </div>
    </>
  )
}
