import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <span className="brand-icon">◈</span>
        <span className="footer-name">Budgetly</span>
        <p className="footer-copy">Track every rupee. Own your finances.</p>
        <div className="footer-links">
          <Link to="/terms">Terms and Conditions</Link>
          <Link to="/privacy">Privacy Policy</Link>
        </div>
      </div>
    </footer>
  )
}
