# SpecGuard AI — Docker Commands Reference

All commands should be run from the **project root**:
`D:\My Code\AI-Powered Universal API Testing Platform`

---

## 🚀 Starting the Backend

**Start all services (build + run in background):**
```bash
docker compose -f docker/docker-compose.yml up --build -d
```

**Start without rebuilding (faster, if no code changes):**
```bash
docker compose -f docker/docker-compose.yml up -d
```

---

## 🛑 Stopping the Backend

**Stop all services gracefully:**
```bash
docker compose -f docker/docker-compose.yml down
```

**Stop and delete all data volumes (MongoDB + Redis):**
```bash
docker compose -f docker/docker-compose.yml down -v
```

---

## 📋 Checking Logs

**Follow all services logs in real-time:**
```bash
docker compose -f docker/docker-compose.yml logs -f
```

**Only FastAPI backend logs:**
```bash
docker compose -f docker/docker-compose.yml logs -f backend
```

**Only Celery worker logs (email notifications print here):**
```bash
docker compose -f docker/docker-compose.yml logs -f celery_worker
```

**Multiple services at once:**
```bash
docker compose -f docker/docker-compose.yml logs -f backend celery_worker
```

**Last 100 lines only (no live follow):**
```bash
docker compose -f docker/docker-compose.yml logs --tail=100 backend
```

> **Tip:** Press `Ctrl+C` to stop following logs.

---

## 🔄 Rebuilding After Code Changes

**Backend code changed (Python files):**
```bash
docker compose -f docker/docker-compose.yml up --build -d
```

**Frontend code changed — no Docker rebuild needed:**
```bash
# Just run the Vite dev server in the frontend folder:
npm run dev
```

---

## 📊 Container Status

**Check running containers and health status:**
```bash
docker compose -f docker/docker-compose.yml ps
```

**Check resource usage (CPU, memory):**
```bash
docker stats
```

---

## 🐚 Exec Into a Container (Advanced)

**Open a shell inside the backend container:**
```bash
docker exec -it specguard_backend bash
```

**Open a shell inside the Celery worker container:**
```bash
docker exec -it specguard_celery_worker bash
```

---

## 🌐 Service URLs (When Running)

| Service         | URL                          |
|-----------------|------------------------------|
| FastAPI Backend | http://localhost:8000         |
| API Docs        | http://localhost:8000/docs    |
| MongoDB         | mongodb://localhost:27017     |
| Redis           | redis://localhost:6379        |
| Frontend (Vite) | http://localhost:5173         |
