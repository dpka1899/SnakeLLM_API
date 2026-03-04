from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List, Literal


# =========================
# Pipeline Spec
# =========================

class ContainerRef(BaseModel):
    registry: str
    image: str
    tag: str
    full_uri: str
    source: str


class ToolSpec(BaseModel):
    name: str
    version: str
    container: ContainerRef
    purpose: str
    language: str = "CLI"


class RuleSpec(BaseModel):
    name: str
    tool: str
    input: List[str]
    output: List[str]
    params: Dict[str, Any] = Field(default_factory=dict)
    shell_cmd: str
    resources: Dict[str, Any] = Field(default_factory=dict)
    log: List[str] = Field(default_factory=list)


class PipelineSpec(BaseModel):
    pipeline_type: str
    description: str
    tools: List[ToolSpec]
    rules: List[RuleSpec]
    dag_edges: List[List[str]] = Field(default_factory=list)
    config_params: Dict[str, Any] = Field(default_factory=dict)
    wildcards: List[str] = Field(default_factory=list)


# =========================
# API Schemas
# =========================

class GenerateRequest(BaseModel):
    """
    Request body for POST /generate

    If provider/model are not provided,
    defaults from .env are used.
    """

    prompt: str = Field(
        ...,
        min_length=3,
        description="Natural language pipeline request",
        example="Run differential expression analysis using DESeq2",
    )

    # ✅ Strict validation — prevents Swagger 'string'
    provider: Optional[Literal["anthropic", "openai", "gemini"]] = Field(
        default=None,
        description='LLM provider override: "anthropic" | "openai" | "gemini"',
        example="anthropic",
    )

    model: Optional[str] = Field(
        default=None,
        description="Provider-specific model name",
        example="claude-sonnet-4-6",
    )

    pipeline_type: Optional[str] = Field(
        default=None,
        description="Optional pipeline type hint (e.g., rna-seq-de)",
        example="rna-seq-de",
    )


class GenerateResponse(BaseModel):
    job_id: str
    status: str = "QUEUED"


class StatusResponse(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None


class ResultResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None