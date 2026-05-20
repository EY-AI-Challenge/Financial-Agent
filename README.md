# Financial Decision Support Platform

An AI-powered investment platform prototype created for the EY AI Challenge. The project combines a React + Vite frontend, a FastAPI backend, PostgreSQL for persistence, and ML-ready hooks for price prediction and portfolio recommendations.

This repository is intended as a hackathon prototype: readable, Docker-first, and easy for teammates to start with one command.

---

## Quick Overview

- Frontend: React 18 + Vite, Tailwind CSS, Recharts for charts.
- Backend: FastAPI, SQLAlchemy, PostgreSQL. Background updater fetches historical data (yfinance).
- Orchestration: Docker Compose (frontend served by nginx, backend using Uvicorn).

---

## Quickstart (Docker - Recommended)

Prerequisites:
- Docker & Docker Compose
- ~2 GB free disk (more recommended for datasets)

Start everything:

```powershell
docker compose up --build -d
```

Then open:
- Frontend: http://localhost/ or http://localhost:80
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

Notes:
- In local development, the frontend can run with Vite HMR on port 3000.
- In Docker, frontend is built with Vite and served by nginx on port 80.

---

## Project Structure (Short)

```text
Financial-Agent/
├─ backend/                # FastAPI app, models, routers, updater
├─ frontend/               # React + Vite app (Tailwind, Recharts)
├─ financial_data/         # CSVs used by backend for historical data
├─ docker-compose.yml      # Compose orchestration (db, backend, frontend)
└─ README.md               # This file
```

---

## Development Workflow

Backend (local, without Docker):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (local, Vite HMR):

```powershell
cd frontend
npm install
npm run dev
```

Docker build commands:

```powershell
docker compose build frontend
docker compose build backend
docker compose up -d
```

If frontend dependencies changed:

```powershell
docker compose build --no-cache frontend
```

---

## API (Selected Endpoints)

Authentication:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
```

Data:

```text
GET  /api/data/tickers
GET  /api/data/history/{ticker}
```

Portfolio:

```text
GET  /api/portfolio/
POST /api/portfolio/
```

Recommendations:

```text
GET  /api/recommendations/
POST /api/recommendations/{id}/accept
```

Full docs: http://localhost:8000/docs

---

## Troubleshooting

Build stuck at `npm install` or failing in `vite build`:

- Ensure `frontend/package.json` includes dev dependencies: `vite`, `@vitejs/plugin-react`, `tailwindcss`, `postcss`, `autoprefixer`.
- Ensure Node 20+ for local frontend build.
- Run with plain output:

```powershell
$env:DOCKER_BUILDKIT=0; docker compose --progress=plain build frontend
```

Vite ESM plugin error (`@vitejs/plugin-react` ESM only):

- Keep `vite.config.mjs` (ESM).
- Keep `"type": "module"` in `frontend/package.json`.

Frontend shows briefly then blank (e.g., Dashboard):

- Check browser DevTools Console for runtime errors.
- Check container logs:

```powershell
docker compose logs --tail=100 frontend
docker compose logs --tail=100 backend
```

- Check for duplicate route files with wrong extension (`.js` with JSX) and rename/remove.

---

## Helpful Commands

Stop everything:

```powershell
docker compose down
```

Stop + remove volumes:

```powershell
docker compose down -v
```

Follow logs:

```powershell
docker compose logs -f
```

---

## Development Notes

- Backend starts an async updater to refresh financial CSV data.
- Frontend sends JWT token from localStorage in `Authorization` header.
- Asset Details consumes `/api/data/history/{ticker}` and renders a Recharts line chart.

---

## Contributors

EY AI Challenge 2026 Hackathon

---

## License

MIT
