# Budgetly

A personal expense tracker — log your spending, understand your patterns, and stay on budget. Built with a Flask JSON API backend and a React (Vite) frontend, deployable to Vercel.

---

## Features

- **Expense logging** — add, edit, and delete expenses with category, amount, date, and description
- **Category breakdowns** — see where your money goes across Food, Transport, Bills, Health, Entertainment, Shopping, and Other
- **Date filtering** — filter your spending by any custom date range
- **Analytics page** — monthly summaries and spending trends *(coming soon)*
- **Secure auth** — session-based login and registration with password hashing
- **Profile dashboard** — personal spending overview at a glance

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.1, Werkzeug |
| Database | PostgreSQL (Neon) via psycopg2 |
| Frontend | React 18, React Router 6, Vite 5 |
| Deployment | Vercel (serverless Python + static SPA) |

---

## Project Structure

```
Budgetly/
├── api/
│   ├── index.py              # Flask JSON API — all routes
│   ├── requirements.txt      # flask, werkzeug, psycopg2-binary
│   └── database/
│       ├── db.py             # get_db(), init_db(), seed_db()
│       └── queries.py        # All parameterized SQL helpers
├── frontend/
│   ├── index.html
│   ├── vite.config.js        # Proxy /api → http://localhost:5001
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx           # Routes
│       ├── api/client.js     # Fetch wrappers for all /api/* endpoints
│       ├── context/AuthContext.jsx
│       ├── components/       # Layout, Navbar, Footer, ProtectedRoute
│       ├── pages/            # Landing, Login, Register, Profile, Analytics, etc.
│       └── styles/           # Vanilla CSS per page
└── vercel.json               # Build config + SPA rewrite
```

---

## API Reference

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `POST` | `/api/auth/register` | | Create account |
| `POST` | `/api/auth/login` | | Log in, returns user |
| `POST` | `/api/auth/logout` | | Clear session |
| `GET` | `/api/auth/me` | ✓ | Current user or 401 |
| `GET` | `/api/profile` | ✓ | Expenses (filterable by category, date_from, date_to) |
| `POST` | `/api/expenses` | ✓ | Add expense |
| `GET` | `/api/expenses/<id>` | ✓ | Get one expense (ownership-checked) |
| `PUT` | `/api/expenses/<id>` | ✓ | Edit expense |
| `DELETE` | `/api/expenses/<id>` | ✓ | Delete expense |

---

## Getting Started (Local)

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r api/requirements.txt
```

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=your-neon-postgres-connection-string
```

Start the Flask API on port 5001:

```bash
python -m api.index
```

### Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

The Vite dev server proxies `/api/*` requests to `http://localhost:5001`, so both servers must be running during development.

---

## Deployment (Vercel)

1. Push to GitHub and import the repo in [Vercel](https://vercel.com).
2. Set the following environment variables in your Vercel project settings:
   - `SECRET_KEY`
   - `DATABASE_URL` (Neon PostgreSQL connection string)
3. Vercel auto-detects `vercel.json` — no extra config needed.

The build command (`cd frontend && npm install && npm run build`) and output directory (`frontend/dist`) are already configured in `vercel.json`.

---

## License

MIT
