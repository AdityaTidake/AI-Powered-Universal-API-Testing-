# ⚡ SpecGuard AI

> **AI-Powered API Testing SaaS Platform** — Automatically generate, execute, and analyze API tests from OpenAPI specs using AI, with real-time insights, security scoring, and CI/CD integration.

---

## 🏗️ Project Structure

```
specguard-ai/
├── backend/                  ← FastAPI Python backend
│   ├── aitester/             ← Core application package
│   │   ├── api/              ← FastAPI routes & middleware
│   │   ├── core/             ← Config, exceptions, logging
│   │   ├── db/               ← SQLAlchemy models & sessions
│   │   ├── ai/               ← AI providers (Gemini + Ollama) + RAG
│   │   ├── executor/         ← Async test runner
│   │   ├── generators/       ← Test case generators
│   │   ├── parser/           ← OpenAPI spec parser
│   │   ├── security/         ← OWASP security scanner
│   │   └── worker/           ← Celery async task workers
│   ├── alembic/              ← Database migrations
│   ├── tests/                ← Pytest test suite
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/                 ← Vite + React + TypeScript SPA
│   ├── src/
│   │   ├── api/              ← Axios client + API service layer
│   │   ├── components/       ← Reusable UI components
│   │   ├── pages/            ← Route-level page components
│   │   ├── store/            ← Zustand state management
│   │   └── types/            ← TypeScript type definitions
│   ├── public/
│   └── package.json
│
├── docker/                   ← Docker & orchestration
│   ├── docker-compose.yml
│   └── Dockerfile
│
└── .github/                  ← GitHub Actions CI/CD
    └── workflows/
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 16 (or use Docker)
- Redis 7 (or use Docker)

### 1. Start Infrastructure (PostgreSQL + Redis)
```bash
docker compose -f docker/docker-compose.yml up -d postgres redis
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # Edit with your values

# Run migrations
alembic upgrade head

# Start the FastAPI server
uvicorn aitester.api.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env            # Edit VITE_API_URL if needed
npm run dev                     # Runs at http://localhost:5173
```

### 4. Open the App
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🧠 AI Configuration

SpecGuard AI supports two AI providers. Set `AI_PROVIDER` in `backend/.env`:

| Value | Provider | Cost |
|-------|----------|------|
| `auto` | Gemini if key set, else Ollama | Automatic |
| `gemini` | Google Gemini (cloud) | API credits |
| `ollama` | Llama3 via Ollama (local) | Free |

**For local Ollama (free dev)**:
```bash
ollama pull llama3
# Set: OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🔥 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React + TypeScript |
| Styling | Vanilla CSS (design tokens) |
| State | Zustand + TanStack Query |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 (asyncpg + SQLAlchemy 2.0) |
| Cache / Queue | Redis 7 |
| Workers | Celery + Redis |
| Auth | JWT (access + refresh tokens) |
| AI | Google Gemini + Ollama (RAG pipeline) |
| DevOps | Docker + GitHub Actions |

---

## 📋 Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Foundation cleanup + Vite frontend scaffold |
| 2 | 🔜 Next | JWT Auth + Multi-tenant DB schema |
| 3 | ⬜ | Core API revamp (user-scoped endpoints) |
| 4 | ⬜ | AI layer upgrade (RAG + LLM monitoring) |
| 5 | ⬜ | Async workers (Celery + Redis) |
| 6 | ⬜ | Full frontend dashboard |
| 7 | ⬜ | Usage limits + free/pro tiers |
| 8 | ⬜ | CI/CD + security hardening + deployment |

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v --cov=aitester --cov-report=html
```

---

## 🏛️ Architecture Principles

- **SOLID** — each module has one responsibility, open for extension
- **OOP** — domain models, service classes, provider abstractions
- **Async-first** — asyncio throughout (asyncpg, httpx, Celery)
- **Multi-tenant** — all data scoped to users/organizations

---

*Built as a portfolio-grade SaaS platform demonstrating full-stack engineering, AI integration, and production-ready DevOps.*
