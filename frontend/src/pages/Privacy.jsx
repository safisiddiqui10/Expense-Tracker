export default function Privacy() {
  return (
    <section className="legal-section">
      <div className="legal-inner">
        <h1 className="legal-title">Privacy Policy</h1>
        <p className="legal-updated">Last updated: October 2026</p>
        <div className="legal-card">
          <h2>Data We Collect</h2>
          <p>When you use Budgetly, we collect the following information:</p>
          <ul>
            <li><strong>Account information</strong> — your name, email address, and password (stored securely using hashing).</li>
            <li><strong>Expense data</strong> — transaction amounts, categories, dates, and descriptions you enter.</li>
            <li><strong>Usage data</strong> — basic analytics such as login times and pages visited to improve the service.</li>
          </ul>

          <h2>How We Use Your Data</h2>
          <p>Your data is used solely to provide and improve the Budgetly service:</p>
          <ul>
            <li>To display your expenses, summaries, and spending patterns.</li>
            <li>To authenticate your account and keep it secure.</li>
            <li>To improve the app's performance and user experience.</li>
          </ul>
          <p>We do not sell, rent, or share your personal data with third parties for marketing purposes.</p>

          <h2>Data Storage</h2>
          <p>Your data is stored in a secure database. We use industry-standard practices to protect your information, including encrypted connections and hashed passwords. However, no method of electronic storage is 100% secure, and we cannot guarantee absolute security.</p>

          <h2>Third-Party Services</h2>
          <p>Budgetly may use the following third-party services:</p>
          <ul>
            <li><strong>Google Fonts</strong> — to serve typefaces used in the interface. Google may collect anonymous usage data; see their privacy policy for details.</li>
          </ul>
          <p>We do not integrate with advertising networks or data brokers.</p>

          <h2>Your Rights</h2>
          <p>You have the right to:</p>
          <ul>
            <li>Access the personal data we hold about you.</li>
            <li>Request correction of inaccurate data.</li>
            <li>Request deletion of your account and associated data.</li>
          </ul>

          <h2>Contact Us</h2>
          <p>If you have any questions or concerns about this privacy policy or your data, please reach out to us at <strong>support@budgetly.app</strong>.</p>
        </div>
      </div>
    </section>
  )
}
