import enum
from sqlalchemy import String, Text, Float, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from api.db import Base


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PLAN_RAG = "PLAN_RAG"
    LLM_PLANNING = "LLM_PLANNING"
    EXECUTE_RAG = "EXECUTE_RAG"
    LLM_GENERATION = "LLM_GENERATION"
    DONE = "DONE"
    FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Per-request overrides
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )

    created_at: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    updated_at: Mapped[float] = mapped_column(Float, nullable=False)

    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


# Optional helpful DB indexes (production ready)
Index("idx_jobs_status_created", Job.status, Job.created_at)