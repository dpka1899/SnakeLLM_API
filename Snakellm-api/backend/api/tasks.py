import json
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional

from api.celery_app import celery_app
from api.db import SessionLocal
from api.models import Job, JobStatus
from api.settings import settings

engine_lock = threading.Lock()
_ENGINE = None  # lazy singleton


def _job_dir(job_id: str) -> Path:
    d = Path(settings.artifacts_dir) / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _update(db, job_id: str, **fields):
    db.query(Job).filter(Job.job_id == job_id).update(fields)
    db.commit()


def _apply_provider_model(provider: Optional[str], model: Optional[str]) -> None:
    if provider:
        os.environ["LLM_PROVIDER"] = provider
    if model:
        os.environ["LLM_MODEL"] = model


def _resolve_engine_path() -> Path:
    """
    Resolve where the SnakeLLM engine code lives.

    Priority:
    1) SNAKELLM_PATH (settings.snakellm_path) if provided
    2) Monorepo engine directory at <repo_root>/engine
       where tasks.py is <repo_root>/backend/api/tasks.py
    """
    # 1) explicit override
    if settings.snakellm_path:
        p = Path(settings.snakellm_path).expanduser().resolve()
        if not p.exists():
            raise RuntimeError(f"SNAKELLM_PATH does not exist: {p}")
        return p

    # 2) monorepo default: backend/api/tasks.py -> repo_root -> engine
    repo_root = Path(__file__).resolve().parents[3]  # <repo_root>
    engine_dir = (repo_root / "engine").resolve()
    if not engine_dir.exists():
        raise RuntimeError(f"Engine directory not found at: {engine_dir}")

    return engine_dir


def _get_engine():
    """
    Lazy import SnakeLLM + initialize once per worker.
    Uses monorepo engine/ directory (or SNAKELLM_PATH override).
    """
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    engine_dir = _resolve_engine_path()

    # Ensure llm/ is importable (engine_dir contains llm/, core/, data/, etc.)
    sys.path.insert(0, str(engine_dir))

    # Import only when task runs (after path injection)
    from llm.plan_rag import PlanRAG  # noqa: E402
    from llm.execute_rag import ExecuteRAG  # noqa: E402
    from llm.inference import SnakeLLMInference  # noqa: E402

    plan_rag = PlanRAG()
    execute_rag = ExecuteRAG()
    _ENGINE = SnakeLLMInference(plan_rag=plan_rag, execute_rag=execute_rag, verbose=True)
    return _ENGINE


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def run_generation(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return False

        _update(db, job_id, status=JobStatus.LLM_GENERATION, updated_at=time.time())

        # call LLM (per-job provider/model)
        with engine_lock:
            _apply_provider_model(job.provider, job.model)
            engine = _get_engine()
            spec = engine.generate(job.prompt)

        result = spec.model_dump() if hasattr(spec, "model_dump") else spec

        # store artifact
        d = _job_dir(job_id)
        spec_path = d / "pipeline_spec.json"
        spec_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        _update(
            db,
            job_id,
            status=JobStatus.DONE,
            updated_at=time.time(),
            result_json=json.dumps(result),
            artifact_path=str(spec_path),
            error=None,
        )
        return True

    except Exception as e:
        _update(db, job_id, status=JobStatus.FAILED, updated_at=time.time(), error=str(e))
        raise
    finally:
        db.close()