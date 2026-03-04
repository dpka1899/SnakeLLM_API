from celery import Celery
from api.settings import settings

celery_app = Celery(
    "snakellm",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["api.tasks"],  # ✅ ensures tasks are imported at worker boot
)

celery_app.conf.update(
    # Reliability / execution semantics
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # ✅ Important for Celery 5+: retry broker connection on startup
    broker_connection_retry_on_startup=True,

    # Safer defaults (optional but recommended)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,

    # If you ever route tasks later, these help debugging
    task_send_sent_event=True,
    result_extended=True,
)

# ✅ Optional: autodiscover (safe to keep, but not required when include=[...])
celery_app.autodiscover_tasks(["api"], force=True)