# CLAUDE.md

## Project overview

Budgetly is a personal expense tracker — Flask JSON API backend + React (Vite) frontend.

---

## Architecture
```
Budgetly/
├── api/
│   ├── index.py              # Flask JSON API — all routes
│   ├── requirements.txt      # flask, werkzeug
│   └── database/
│       ├── db.py             # get_db(), init_db(), seed_db() — DB_PATH from env
│       └── queries.py        # All SQL helpers (parameterized queries only)
├── frontend/
│   ├── index.html            # Google Fonts CDN links, div#root
│   ├── vite.config.js        # Proxy /api → http://localhost:5001
│   ├── package.json
│   └── src/
│       ├── main.jsx          # Entry — imports style.css globally
│       ├── App.jsx           # BrowserRouter + Routes
│       ├── api/client.js     # fetch wrappers for all /api/* endpoints
│       ├── context/AuthContext.jsx
│       ├── components/       # Layout, Navbar, Footer, ProtectedRoute
│       ├── pages/            # One .jsx per page
│       └── styles/           # style.css, landing.css, profile.css, analytics.css
└── vercel.json               # Vercel build + SPA rewrite config
```

**Where things belong:**
- New API endpoints → `api/index.py` only
- DB logic → `api/database/queries.py` only, never inline in routes
- New pages → new `.jsx` in `frontend/src/pages/`
- Page-specific styles → new `.css` in `frontend/src/styles/`, imported in the page component
- Shared components → `frontend/src/components/`

---

## Code style

### Python (api/)
- PEP 8, snake_case for all identifiers
- DB queries: always parameterized (`?` placeholders) — never f-strings in SQL
- Auth guard: use `require_auth()` helper at the top of every protected route
- Return JSON always: `jsonify({...})` — never render templates
- FK enforcement: `get_db()` runs `PRAGMA foreign_keys = ON` on every connection

### React (frontend/)
- Functional components + hooks only
- Navigation: always `<Link>` or `useNavigate()` — never `window.location` or `<a href>`
- Forms: fully controlled inputs (value + onChange on every field)
- Auth state: read from `useAuth()` (AuthContext) — never from localStorage directly
- Flash messages: pass via router state `navigate('/profile', { state: { flash: '...' } })`

---

## Tech constraints

- **Flask only** — no FastAPI, no Django
- **SQLite only** — no PostgreSQL, no SQLAlchemy ORM
- **React + Vite** — no other frontend frameworks; vanilla CSS (no Tailwind, no CSS-in-JS)
- **No new pip packages** without flagging — keep `api/requirements.txt` in sync
- **No new npm packages** without flagging — keep `frontend/package.json` in sync
- Python 3.10+ assumed

---

## Subagent Policy
- Always use a builtin explore subagent for codebase exploration
  before implementing any new feature
- Always use a subagent to verify test results
  after any implementation
- When asked to plan, delegate codebase research
  to a subagent before presenting the plan
- Always use a builtin plan subagent in plan mode

---

## Commands
```bash
# Setup — Python
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r api/requirements.txt

# Run Flask JSON API (Terminal 1)
python -m api.index          # serves on port 5001

# Setup — React
cd frontend
npm install

# Run Vite dev server (Terminal 2)
cd frontend
npm run dev                  # serves on http://localhost:5173

# Build for production
cd frontend
npm run build                # outputs to frontend/dist/
```

---

## API routes

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| `POST` | `/api/auth/login` | — | Returns user dict |
| `POST` | `/api/auth/register` | — | Validates + creates user |
| `POST` | `/api/auth/logout` | — | Clears session |
| `GET` | `/api/auth/me` | ✓ | Returns current user or 401 |
| `GET` | `/api/profile` | ✓ | Query params: category, date_from, date_to |
| `GET` | `/api/expenses/<id>` | ✓ | Ownership-checked |
| `POST` | `/api/expenses` | ✓ | Add expense |
| `PUT` | `/api/expenses/<id>` | ✓ | Edit expense |
| `DELETE` | `/api/expenses/<id>` | ✓ | Delete expense |

## React routes

| Path | Component | Protected |
|------|-----------|-----------|
| `/` | Landing | — |
| `/login` | Login | — |
| `/register` | Register | — |
| `/terms` | Terms | — |
| `/privacy` | Privacy | — |
| `/profile` | Profile | ✓ |
| `/analytics` | Analytics | ✓ |
| `/expenses/add` | AddExpense | ✓ |
| `/expenses/:id/edit` | EditExpense | ✓ |

---

## Warnings and things to avoid

- **Never put DB logic in route functions** — it belongs in `api/database/queries.py`
- **Never hardcode URLs** in React — always use `<Link>` or `navigate()`
- **Never install packages** mid-feature without flagging it
- **FK enforcement is manual** — `get_db()` must run `PRAGMA foreign_keys = ON`
- **SQLite will not persist on Vercel** — ephemeral filesystem; use Turso/Neon for production
- **Secret key** must come from `SECRET_KEY` env var — never hardcode in production
- The Flask API runs on **port 5001**; the Vite dev server on **port 5173**
