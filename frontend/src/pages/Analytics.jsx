import { Link } from 'react-router-dom'
import '../styles/analytics.css'

export default function Analytics() {
  return (
    <div className="cs-page">
      <div className="cs-blob cs-blob--tl"></div>
      <div className="cs-blob cs-blob--br"></div>
      <div className="cs-card">
        <div className="cs-corner cs-corner--tr"></div>
        <div className="cs-corner cs-corner--bl"></div>
        <div className="cs-icon-wrap">
          <div className="cs-icon-glow"></div>
          <div className="cs-icon-box">
            <svg className="cs-icon-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        <div className="cs-badge">
          <span>Coming Soon</span>
        </div>
        <h2 className="cs-title">Advanced Analytics</h2>
        <p className="cs-description">
          We're working on powerful insights and visualizations to help you
          understand your spending patterns better.
        </p>
        <div className="cs-dots">
          <div className="cs-dot"></div>
          <div className="cs-dot cs-dot--2"></div>
          <div className="cs-dot cs-dot--3"></div>
        </div>
        <p className="cs-crafting">We're crafting something special</p>
        <div className="cs-bottom-line"></div>
        <Link to="/profile" className="btn-ghost cs-back">← Back to dashboard</Link>
      </div>
    </div>
  )
}
