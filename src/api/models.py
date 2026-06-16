"""Looma api — 请求/响应模型（对齐 api.yaml v1.1.0）"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ── 通用枚举 ──────────────────────────────

class ExecutionHint(str, Enum):
    local = "local"
    remote = "remote"
    auto = "auto"


class Tier(str, Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class TerminalType(str, Enum):
    zervi_desktop = "zervi_desktop"
    zervi_rpi = "zervi_rpi"
    mobile_applet = "mobile_applet"
    mobile_app = "mobile_app"
    web = "web"
    api = "api"


class Scope(str, Enum):
    private = "private"
    public = "public"
    both = "both"


class JobScope(str, Enum):
    private = "private"
    public = "public"


class RagScope(str, Enum):
    local = "local"
    remote = "remote"
    hybrid = "hybrid"


class Intent(str, Enum):
    rag = "rag"
    resume_parse = "resume_parse"
    job_match = "job_match"
    credit_analysis = "credit_analysis"
    mbti = "mbti"
    poetry = "poetry"
    report = "report"
    unknown = "unknown"


class SourceLocation(str, Enum):
    local = "local"
    remote = "remote"


class ExecutedOn(str, Enum):
    local = "local"
    remote = "remote"
    hybrid = "hybrid"


# ── /v1/ask ──────────────────────────────

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    execution_hint: ExecutionHint = Field(default=ExecutionHint.auto)
    context_scope: Scope = Field(default=Scope.private)
    stream: bool = Field(default=False)


class SourceNode(BaseModel):
    doc_id: str | None = None
    chunk_text: str
    score: float | None = None


class AskResponse(BaseModel):
    answer: str
    intent: Intent = Intent.rag
    sources: list[SourceNode] = []
    executed_on: ExecutedOn = ExecutedOn.remote
    session_id: str | None = None
    tokens_used: int = 0


# ── /v1/rag/query ───────────────────────

class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    scope: RagScope = RagScope.hybrid
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.3)
    execution_hint: ExecutionHint = ExecutionHint.auto


class RagResultItem(BaseModel):
    chunk_id: str | None = None
    doc_id: str | None = None
    text: str
    score: float
    metadata: dict | None = None
    source: SourceLocation = SourceLocation.remote


class RagQueryResponse(BaseModel):
    results: list[RagResultItem]
    answer: str | None = None
    executed_on: ExecutedOn = ExecutedOn.hybrid


# ── /v1/upload/presign ──────────────────

class PresignRequest(BaseModel):
    filename: str
    content_type: str | None = None
    scope: Scope = Scope.private
    file_size: int | None = Field(default=None, gt=0)


class PresignResponse(BaseModel):
    upload_url: str
    file_key: str
    expires_at: str
    max_file_size: int


# ── /v1/upload/confirm ──────────────────

class UploadConfirmRequest(BaseModel):
    file_key: str
    scope: Scope = Scope.private
    chunk_size: int = 500
    chunk_overlap: int = 50
    metadata: dict | None = None


# ── /v1/documents ───────────────────────

class DocumentMeta(BaseModel):
    id: str
    title: str
    file_type: str | None = None
    status: str
    chunk_count: int | None = None
    scope: Scope = Scope.private
    created_at: str


class DocumentImportResponse(BaseModel):
    task_id: str
    status: str
    estimated_seconds: int | None = None


# ── /v1/resume ──────────────────────────

class ResumeAnalysis(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education: list[dict] | None = None
    experience: list[dict] | None = None
    skills: list[str] | None = None
    summary: str | None = None


# ── /v1/jobs ────────────────────────────

class JobMatchRequest(BaseModel):
    resume_text: str
    scope: JobScope = JobScope.public
    top_k: int = 10
    include_analysis: bool = True


class JobScores(BaseModel):
    money: float
    workload: float
    proximity: float
    overall: float


class JobMatchItem(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    salary_range: str | None = None
    scores: JobScores
    reason: str | None = None


class JobMatchResponse(BaseModel):
    matches: list[JobMatchItem]
    total_evaluated: int


# ── /v1/auth ────────────────────────────

class AuthRegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    display_name: str | None = None


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    tier: Tier = Tier.free
    expires_in: int
    user_id: str | None = None
    terminal_types: list[TerminalType] | None = None


# ── /v1/quota ───────────────────────────

class QuotaRecord(BaseModel):
    resource: str
    used: int
    daily_limit: int
    resets_at: str | None = None


class QuotaResponse(BaseModel):
    tier: Tier
    records: list[QuotaRecord]


# ── /v1/reports ─────────────────────────

class ReportGenerateRequest(BaseModel):
    type: str = Field(..., pattern="^(daily|weekly|monthly)$")
    scope: Scope = Scope.private
    stream: bool = False


class ReportMeta(BaseModel):
    id: str
    type: str
    title: str | None = None
    status: str
    created_at: str
    download_url: str | None = None


class ReportDetail(BaseModel):
    id: str
    type: str
    title: str
    content: str
    created_at: str


# ── 错误 ────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict | None = None
