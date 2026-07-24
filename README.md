# ⚡ SpecGuard AI

> **AI-Powered Universal API Testing SaaS Platform**  
> *Zero-setup automated API testing using Generative AI. Upload an OpenAPI spec, and let AI generate, execute, and analyze thousands of test cases in minutes.*

---

## 🌟 Unique Selling Proposition (USP)

Traditional API testing requires QA engineers to manually write and maintain extensive test collections, often missing critical edge cases. **SpecGuard AI revolutionizes this workflow by completely automating API testing.**

By simply uploading an OpenAPI/Swagger specification, our platform leverages Large Language Models (Google Gemini) to instantly generate comprehensive functional, edge-case, and security tests—eliminating the need to write manual test scripts. 

### Core Features

- **🚀 Zero-Setup Testing:** Upload your OpenAPI spec and the platform automatically understands your API's constraints and business logic.
- **🧠 Intelligent Edge-Case Discovery:** AI predicts and generates edge cases that humans frequently overlook (e.g., negative integers, missing fields, malicious payloads).
- **🎭 Automated Mock Data:** Seamlessly injects realistic, dynamic payload data into test runs using advanced AI and mock data libraries.
- **⚡ Asynchronous Execution Engine:** Built on Celery and Redis to handle hundreds of concurrent API requests in the background, ensuring high performance.
- **📊 Actionable Analytics:** A beautiful, interactive React dashboard provides real-time test execution visualization, latency tracking, and AI-powered failure analysis.

---

## 🏗️ System Architecture

Our platform is designed for enterprise-grade scalability, utilizing a multi-tenant asynchronous architecture:

1. **Client-Side:** Fast, responsive Single Page Application built with React 19, Vite, Zustand, and React Query.
2. **REST API Gateway:** High-performance asynchronous backend powered by FastAPI and Pydantic.
3. **Background Processing:** Celery workers combined with Redis act as the asynchronous task queue for generating AI tests and firing hundreds of API calls concurrently.
4. **Data Layer:** PostgreSQL (or MongoDB for document flexibility) stores structured project data, nested API schemas, and historical test results.
5. **AI Brain:** Integration with Google Gemini / local Ollama models for parsing specs and generating assertions.

---

## 🔥 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vite, React 19, TypeScript |
| **Styling** | Vanilla CSS (Custom Design Tokens) |
| **State Management** | Zustand (Client), TanStack Query (Server State) |
| **Backend** | FastAPI (Python 3.12), Uvicorn |
| **Database** | PostgreSQL 16 (asyncpg + SQLAlchemy 2.0) / MongoDB (Beanie ODM) |
| **Cache & Queue** | Redis 7 |
| **Workers** | Celery + Redis |
| **Authentication** | JWT (access & refresh tokens) |
| **AI Integration** | Google Gemini, Ollama (Local Llama 3) |
| **DevOps** | Docker, GitHub Actions |

---

## 📂 Project Structure

```text
specguard-ai/
├── backend/                  ← FastAPI Python backend
│   ├── aitester/             ← Core application package
│   │   ├── api/              ← FastAPI routes & middleware
│   │   ├── core/             ← Config, exceptions, logging
│   │   ├── db/               ← SQLAlchemy models / ODM
│   │   ├── ai/               ← AI providers (Gemini + Ollama)
│   │   ├── executor/         ← Async API test runner
│   │   ├── generators/       ← Test case generators
│   │   ├── parser/           ← OpenAPI spec parser
│   │   ├── security/         ← Security scanner
│   │   └── worker/           ← Celery async task workers
│   └── tests/                ← Pytest test suite
│
├── frontend/                 ← Vite + React + TypeScript SPA
│   ├── src/
│   │   ├── api/              ← Axios client + API service layer
│   │   ├── components/       ← Reusable UI components
│   │   ├── pages/            ← Route-level page components
│   │   └── store/            ← Zustand state management
│   └── package.json
│
├── docker/                   ← Docker orchestration
└── .github/                  ← GitHub Actions CI/CD
```

---

## 🏛️ Architecture Principles

- **SOLID:** Each module has one responsibility and is open for extension.
- **OOP:** Clean domain models, service classes, and provider abstractions.
- **Async-First:** End-to-end asynchronous non-blocking I/O (asyncio, asyncpg, httpx, Celery).
- **Multi-Tenant:** All data safely scoped to individual users and organizations.

---

*SpecGuard AI is built as a portfolio-grade SaaS platform demonstrating advanced full-stack engineering, practical AI integration, and production-ready architecture.*
