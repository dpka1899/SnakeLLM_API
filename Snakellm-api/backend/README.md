# 🐍 SnakeLLM
AI-Powered Bioinformatics Pipeline Generator

SnakeLLM is a production-ready AI system that converts natural language bioinformatics requests into validated, containerized Snakemake workflows.

It integrates a Dual RAG (Plan + Execute) LLM engine with a scalable FastAPI backend, asynchronous task execution, persistent job tracking, and reproducible artifact generation.

---

# 🚀 What SnakeLLM Does

Describe your analysis in plain English:

> "Run RNA-seq differential expression analysis using DESeq2"

SnakeLLM automatically:

- 🧠 Plans pipeline structure (Plan RAG)
- 🔍 Retrieves tool knowledge (Execute RAG)
- 📐 Validates output via Pydantic schema
- 🧾 Generates structured PipelineSpec JSON
- 📦 Stores artifact for download
- ⚙️ Produces Snakemake-compatible workflows

Same prompt → reproducible pipeline structure.

---

# 🏗 System Architecture

SnakeLLM follows a modular layered architecture:

## 1️⃣ API Layer
- FastAPI REST backend
- Async job execution via Celery
- PostgreSQL persistence
- Redis message broker
- Rate limiting (SlowAPI)
- Structured logging
- Infra-aware health checks
- Artifact download endpoints

## 2️⃣ LLM Engine (Dual RAG)
- Plan RAG → identifies pipeline type & structure
- Execute RAG → retrieves relevant bioinformatics tools
- Schema-constrained structured JSON output
- Retry loop on validation failure
- Multi-provider support (Anthropic / OpenAI / extensible)

## 3️⃣ Pipeline Generation Layer
- DAG construction
- RuleSpec & ToolSpec schema validation
- Container reference mapping
- Snakemake 8.x compatible specification

## 4️⃣ Infrastructure Layer
- Docker-ready services
- Redis broker
- PostgreSQL database
- Celery workers
- Artifact storage in `storage/jobs/`

---

# 🧠 Key Features

- ✅ Natural language → structured pipeline
- 🔄 Async background job processing
- 🗄 Persistent job tracking
- 📦 Artifact generation & download
- 🚦 Rate limiting protection
- 📊 Health monitoring (API + Redis + Postgres)
- 🧾 Structured logs
- 🔐 Optional API key protection
- 🐳 Docker compatible

---

# 🛠 Tech Stack

- Python 3.10+
- FastAPI
- Celery 5
- Redis
- PostgreSQL
- SQLAlchemy 2
- Pydantic v2
- SlowAPI
- Anthropic / OpenAI APIs
- Snakemake
- Docker

---

# 📂 Project Structure

```
snakellm-api/
│
├── api/
│   ├── main.py
│   ├── tasks.py
│   ├── celery_app.py
│   ├── models.py
│   ├── schemas.py
│   ├── settings.py
│   ├── db.py
│   ├── logging_config.py
│
├── storage/
│   └── jobs/
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation & Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/SnakeLLM.git
cd SnakeLLM
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3️⃣ Configure Environment

Create `.env` in project root:

```
# -------------------------
# AUTH (optional)
# -------------------------
API_KEY=your_api_key

# -------------------------
# LLM CONFIG
# -------------------------
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=your_real_key

# -------------------------
# DATABASE
# -------------------------
DATABASE_URL=postgresql+psycopg://snakellm:snakellm@localhost:5432/snakellm

# -------------------------
# CELERY / REDIS
# -------------------------
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# -------------------------
# STORAGE
# -------------------------
ARTIFACTS_DIR=storage/jobs
```

---

# 🐳 Start Services

## Start Redis + Postgres

```bash
docker compose up -d
```

---

## Start API

```bash
uvicorn api.main:app --reload
```

---

## Start Celery Worker

```bash
celery -A api.celery_app.celery_app worker --loglevel=info --pool=solo
```

---

# 🔎 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Submit pipeline request |
| GET | `/status/{job_id}` | Check job status |
| GET | `/result/{job_id}` | Retrieve JSON spec |
| GET | `/download/{job_id}` | Download artifact |
| GET | `/health` | Infra health check |

Swagger docs:

```
http://localhost:8000/docs
```

---

# 📊 Health Check

`/health` verifies:

- API status
- PostgreSQL connectivity
- Redis broker connectivity

Returns HTTP 503 if infrastructure is unhealthy.

---

# 🔄 Async Job Lifecycle

1. POST `/generate`
2. Job stored in Postgres
3. Celery worker processes request
4. LLM generates pipeline spec
5. Artifact stored in `storage/jobs/{job_id}/`
6. Download via `/download/{job_id}`

---

# 🔐 Security & Reliability

- Optional API key authentication
- Per-IP rate limiting
- JSON-only serialization
- Late task acknowledgment
- Worker crash recovery enabled
- Broker retry on startup
- Safe polling via DB session refresh

---

# 📦 Production Hardening

- `task_acks_late=True`
- `worker_prefetch_multiplier=1`
- `broker_connection_retry_on_startup=True`
- Structured logging
- Poll-safe download endpoint
- SQLAlchemy session refresh during polling

---

# 📈 Current Status

Backend Infrastructure: ✅  
Async Processing: ✅  
LLM Integration: ✅ (API key required)  
Health Monitoring: ✅  
Rate Limiting: ✅  
Artifact Packaging: ✅  
Docker Ready: ✅  

---

# 🎯 Vision

SnakeLLM lowers the scripting barrier in computational biology by enabling natural language–driven workflow synthesis while preserving reproducibility and containerized execution.

---

# 📜 License

MIT License (update if needed)

---

**SnakeLLM — AI for Reproducible Computational Biology**