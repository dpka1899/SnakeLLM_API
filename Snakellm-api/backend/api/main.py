# api/main.py
import json
import logging
import os
import time
import uuid
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException, Query, Depends, Header, Request
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.settings import settings
from api.db import ensure_db, get_db, SessionLocal
from api.models import Job, JobStatus
from api.schemas import GenerateRequest
from api.tasks import run_generation
from api.logging_config import setup_logging

# -------------------------
# Logging
# -------------------------
setup_logging(getattr(settings, "log_level", "INFO"))
log = logging.getLogger("api")

# -------------------------
# FastAPI app
# -------------------------
app = FastAPI(title="SnakeLLM API (Prod Ready)")

# -------------------------
# Rate limiting
# -------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

STAGES = {s.value for s in JobStatus}


def require_api_key(x_api_key: str | None = Header(default=None)):
    # If API_KEY not set, auth is disabled
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.on_event("startup")
def _startup():
    ensure_db()
    Path(settings.artifacts_dir).mkdir(parents=True, exist_ok=True)
    log.info("startup_complete", extra={"artifacts_dir": settings.artifacts_dir})


@app.get("/health")
@limiter.limit("120/minute")
def health(request: Request):
    """
    Infra-aware healthcheck:
    - API OK
    - Postgres OK (SELECT 1)
    - Redis OK (PING)
    Returns 503 if redis or postgres fails.
    """
    checks = {"api": "ok", "provider_mode": settings.llm_provider}

    # Postgres
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"fail: {type(e).__name__}"

    # Redis (broker)
    try:
        r = redis.Redis.from_url(settings.celery_broker_url)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"fail: {type(e).__name__}"

    if checks["postgres"].startswith("fail") or checks["redis"].startswith("fail"):
        raise HTTPException(status_code=503, detail=checks)

    return checks


@app.post("/generate", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
def generate(request: Request, req: GenerateRequest, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    now = time.time()

    # ✅ guard against Swagger "string" and normalize
    provider = (req.provider or "").strip().lower()
    if provider in ("", "string", "none", "null"):
        provider = None

    job = Job(
        job_id=job_id,
        prompt=req.prompt,
        provider=provider,
        model=req.model,
        status=JobStatus.QUEUED,
        created_at=now,
        updated_at=now,
        result_json=None,
        artifact_path=None,
        error=None,
    )
    db.add(job)
    db.commit()

    run_generation.delay(job_id)

    log.info("job_created", extra={"job_id": job_id, "provider": provider, "model": req.model})
    return {"job_id": job_id, "status": JobStatus.QUEUED.value}


@app.get("/status/{job_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("120/minute")
def status(request: Request, job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    st = job.status.value if job.status else JobStatus.FAILED.value
    if st not in STAGES:
        st = JobStatus.FAILED.value

    return {"job_id": job_id, "status": st, "error": job.error}


@app.get("/result/{job_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("120/minute")
def result(request: Request, job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    if job.status != JobStatus.DONE:
        return {"job_id": job_id, "status": job.status.value, "result": None, "error": job.error}

    payload = json.loads(job.result_json) if job.result_json else None
    return {"job_id": job_id, "status": job.status.value, "result": payload}


@app.get("/pipelines", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
def list_pipelines(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    return {
        "pipelines": [
            {
                "job_id": j.job_id,
                "status": j.status.value,
                "created_at": j.created_at,
                "updated_at": j.updated_at,
                "error": j.error,
                "provider": j.provider,
                "model": j.model,
                "prompt_preview": (j.prompt[:80] + "...") if len(j.prompt) > 80 else j.prompt,
            }
            for j in jobs
        ]
    }


@app.delete("/pipelines/{job_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def delete_pipeline(request: Request, job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    # delete artifact file if present
    if job.artifact_path and os.path.exists(job.artifact_path):
        try:
            os.remove(job.artifact_path)
        except Exception:
            pass

    # delete job folder
    d = Path(settings.artifacts_dir) / job_id
    if d.exists() and d.is_dir():
        for p in d.glob("*"):
            try:
                p.unlink()
            except Exception:
                pass
        try:
            d.rmdir()
        except Exception:
            pass

    db.delete(job)
    db.commit()

    log.info("job_deleted", extra={"job_id": job_id})
    return {"deleted": True, "job_id": job_id}


@app.get("/download/{job_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
def download(
    request: Request,
    job_id: str,
    wait: int = Query(0, ge=0, le=120, description="Wait up to N seconds for job to finish"),
    db: Session = Depends(get_db),
):
    """
    Ensures the DB session sees fresh values while polling (expire_all()).
    """
    start = time.time()

    while True:
        db.expire_all()

        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")

        if job.status == JobStatus.DONE:
            path = job.artifact_path
            if not path or not os.path.exists(path):
                raise HTTPException(status_code=404, detail="artifact not found")
            return FileResponse(path, filename="pipeline_spec.json", media_type="application/json")

        if job.status == JobStatus.FAILED:
            raise HTTPException(status_code=500, detail=f"job failed: {job.error}")

        if wait == 0:
            raise HTTPException(status_code=202, detail=f"job still processing (status={job.status.value})")

        if time.time() - start >= wait:
            raise HTTPException(
                status_code=202,
                detail=f"still processing after wait={wait}s (status={job.status.value})",
            )

        time.sleep(0.5)