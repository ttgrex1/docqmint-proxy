# DocQmint Proxy Starter (FastAPI + SQLite + JWT + Usage Logging)

A minimal backend you can deploy on Render to centralize API keys, hide model settings,
authenticate users, and track per-user token usage/costs. The app proxies chat/embedding
requests to OpenRouter by default, but you can swap providers in one place.

## Features
- Email/password login (JWT)
- Roles: `admin` and `user`
- Proxy for chat completions (`/chat/completions`) with usage logging
- Admin endpoints for usage export and settings
- SQLite by default (Render persistent disk recommended)
- CORS enabled for a simple web UI or a Tauri client

## Quick start (local)
```bash
python -m venv .venv && . .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your secrets (OPENROUTER_API_KEY, ADMIN_EMAIL, ADMIN_PASSWORD, JWT_SECRET)
uvicorn app.main:app --reload --port 8000
```

Login with the admin seed credentials and create more users via `/admin/users` (or seed more in code).

## Deploy to Render
1. Push this folder to a GitHub repo.
2. Create a new Web Service on Render, connect the repo.
3. Runtime: **Docker** (this repo includes a Dockerfile).
4. Add Environment Variables (from `.env.example`).
5. Add a persistent disk if you want SQLite to persist between deploys (mount at `/data`).
6. Click Deploy.

### Required Env Vars
See `.env.example` for full list. Minimum:
- `OPENROUTER_API_KEY`
- `JWT_SECRET` (long random string)
- `ADMIN_EMAIL` and `ADMIN_PASSWORD` (seed admin on first run)

## API (high level)
- `POST /auth/login` -> `{token}`
- `GET /me`
- `POST /chat/completions` -> forwards to OpenRouter (model from settings)
- `GET /admin/usage?from=YYYY-MM-DD&to=YYYY-MM-DD&user=<email>` (admin)
- `GET /admin/settings` / `POST /admin/settings` (admin)

## Notes
- Costs are *estimated* based on model rate metadata if provided (you can refine later).
- Swap to a different provider by editing `app/providers/openrouter.py` and switching the import in `main.py`.
