import { Link } from 'react-router-dom'

export default function Terms() {
  return (
    <section className="legal-section">
      <div className="legal-inner">
        <h1 className="legal-title">Terms and Conditions</h1>
        <p className="legal-updated">Last updated: October 2026</p>
        <div className="legal-card">
          <h2>Acceptance of Terms</h2>
          <p>By accessing or using Budgetly, you agree to be bound by these terms and conditions. If you do not agree with any part of these terms, you should not use the service.</p>

          <h2>Use of Service</h2>
          <p>Budgetly is a personal expense tracking application. You may use it to:</p>
          <ul>
            <li>Record and categorise your personal expenses.</li>
            <li>View summaries and breakdowns of your spending.</li>
            <li>Filter and search your transaction history.</li>
          </ul>
          <p>You agree not to misuse the service, attempt to gain unauthorised access, or use it for any unlawful purpose.</p>

          <h2>User Data</h2>
          <p>You are responsible for the accuracy of the data you enter. Budgetly stores your account information and expense records to provide the service. For details on how we handle your data, please refer to our <Link to="/privacy" style={{ color: 'var(--accent)', fontWeight: 500 }}>Privacy Policy</Link>.</p>

          <h2>Account Responsibility</h2>
          <p>You are responsible for maintaining the confidentiality of your login credentials. Any activity that occurs under your account is your responsibility. Notify us immediately if you suspect unauthorised use of your account.</p>

          <h2>Limitations of Liability</h2>
          <p>Budgetly is provided on an "as is" and "as available" basis. We make no warranties, expressed or implied, regarding the reliability, accuracy, or availability of the service.</p>
          <p>To the fullest extent permitted by law, Budgetly and its creators shall not be liable for any indirect, incidental, or consequential damages arising from your use of the service, including but not limited to loss of data or financial decisions made based on information displayed in the app.</p>

          <h2>Changes to Terms</h2>
          <p>We reserve the right to update these terms at any time. Changes will be reflected on this page with an updated revision date. Continued use of the service after changes are posted constitutes your acceptance of the revised terms.</p>

          <h2>Contact Us</h2>
          <p>If you have any questions about these terms, please contact us at <strong>support@budgetly.app</strong>.</p>
        </div>
      </div>
    </section>
  )
}
