"""
Jobs routes blueprint.
Ownership: szbenyx

Endpoints:
  GET  /v1/jobs/          - List jobs (alias of /list, for HarmonyOS)
  GET  /v1/jobs/list      - List persisted jobs (fallback to mock)
  GET  /v1/jobs/search    - Search jobs by keyword
  GET  /v1/jobs/recommend - AI-recommended jobs for current user
  GET  /v1/jobs/<job_id>  - Get job detail by ID
  POST /v1/jobs/upload    - Upload JD file (PDF/DOCX), auto-parsed via MarkItDown + LLM
  POST /v1/jobs/parse     - Parse plain job description text to structured data
  POST /v1/jobs/match     - Match resume to job listings via multi-dimension LLM scoring
"""
import io
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, optional_auth
from src.compliance.consent import require_consent
from src.utils.quota import consume_with_boost, RESOURCE_JOB_MATCH, build_upgrade_hint

logger = logging.getLogger("looma.jobs")
jobs_bp = Blueprint("jobs", __name__)

_SHA_TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(_SHA_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def _quota_exceeded_response(tier: str):
    upgrade = build_upgrade_hint(tier, 0)
    return jsonify(error="quota_exceeded", message="当日职位匹配配额已用尽", upgrade=upgrade), 429


# ── Mock jobs (fallback when no persisted jobs) ──
MOCK_JOBS = [
    {"id": "j1", "title": "前端开发工程师", "company": "字节跳动", "location": "深圳",
     "salary_range": "25-40K", "description": "负责抖音前端开发，React/Vue"},
    {"id": "j2", "title": "Python 后端开发", "company": "腾讯", "location": "深圳",
     "salary_range": "20-35K", "description": "微服务架构开发，FastAPI/Django"},
    {"id": "j3", "title": "AI 算法工程师", "company": "华为", "location": "深圳",
     "salary_range": "30-50K", "description": "NLP/推荐系统算法研发"},
    {"id": "j4", "title": "产品经理", "company": "阿里", "location": "杭州",
     "salary_range": "25-45K", "description": "电商产品规划与迭代"},
    {"id": "j5", "title": "数据分析师", "company": "美团", "location": "北京",
     "salary_range": "20-30K", "description": "业务数据分析与可视化"},
]


def _get_persisted_jobs() -> list[dict]:
    """Read all persisted jobs from DB, fallback to MOCK_JOBS if empty."""
    try:
        from src.db.manager import DatabaseManager

        db_path = current_app.config.get("DATABASE_PATH", "data/looma.db")
        db = DatabaseManager(db_path)
        with db.get_conn() as conn:
            rows = conn.execute(
                """SELECT title, file_path, doc_type, file_size, metadata, created_at
                   FROM documents WHERE doc_type = 'job' AND status = 'processed'
                   ORDER BY created_at DESC LIMIT 50"""
            ).fetchall()
        if rows:
            jobs = []
            for r in rows:
                meta = json.loads(r["metadata"] or "{}")
                parsed = meta.get("parsed") or {}
                jobs.append({
                    "id": parsed.get("id") or str(uuid.uuid4()),
                    "title": parsed.get("title") or r["title"],
                    "company": parsed.get("company") or "",
                    "location": parsed.get("location") or "",
                    "salary_range": parsed.get("salary_range") or "",
                    "description": parsed.get("description") or meta.get("markdown", "")[:500],
                    "requirements": parsed.get("requirements") or [],
                    "tags": parsed.get("tags") or [],
                    "posted_at": parsed.get("posted_at") or r["created_at"],
                    "url": parsed.get("url") or "",
                    "source": parsed.get("source") or "upload",
                })
            return jobs
    except Exception as e:
        logger.warning(f"Failed to read persisted jobs: {e}")
    return []


# ── Endpoints ──


@jobs_bp.route("/list", methods=["GET"])
@optional_auth
def list_jobs():
    """List available jobs: persisted first, then mock fallback."""
    persisted = _get_persisted_jobs()
    if persisted:
        return jsonify(jobs=persisted, total=len(persisted))
    return jsonify(jobs=MOCK_JOBS, total=len(MOCK_JOBS))


@jobs_bp.route("/upload", methods=["POST"])
@optional_auth
def upload_job():
    """Upload a job description file (PDF/DOCX) for AI parsing.

    Pipeline: MarkItDown binary→Markdown → LLM structured extraction → persist → return.
    Accepts multipart/form-data with field name ``file``.
    """
    user_id = g.get("user_id", "guest-anon")

    if "file" not in request.files:
        return jsonify(error="bad_request", message="未检测到上传文件"), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify(error="bad_request", message="文件名称为空"), 400

    filename = file.filename
    allowed = {".pdf", ".docx", ".doc", ".txt", ".md"}
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if f".{ext}" not in allowed:
        return jsonify(error="bad_request", message=f"不支持的文件格式: .{ext}，支持: {', '.join(allowed)}"), 400

    # Read file bytes
    try:
        content = file.read()
    except Exception as e:
        return jsonify(error="read_failed", message=f"文件读取失败: {e}"), 400

    if not content:
        return jsonify(error="read_failed", message="文件内容为空"), 400

    # Step 1: MarkItDown conversion (PDF/DOCX → Markdown)
    try:
        from src.ingest.markitdown_convert import stream_to_markdown

        markdown = stream_to_markdown(io.BytesIO(content), filename=filename)
    except Exception as e:
        logger.error(f"MarkItDown conversion failed for {filename}: {e}")
        return jsonify(error="convert_failed", message=f"文档解析失败（{filename} 格式未识别或文件损坏）"), 422

    if not markdown or not markdown.strip():
        return jsonify(error="convert_failed", message="文档内容为空，无法提取文字"), 422

    # Step 2: LLM structured extraction
    try:
        from src.agents.document_agents import run_document_analysis
        parsed = run_document_analysis("job", markdown)
    except Exception as e:
        logger.error(f"LLM extraction failed for job: {e}")
        return jsonify(
            parsed=None,
            markdown=markdown,
            filename=filename,
            error=f"结构化提取失败: {e}",
        ), 200

    # Step 3: Persist to DB
    job_id = None
    try:
        from src.db.manager import DatabaseManager

        db_path = current_app.config.get("DATABASE_PATH", "data/looma.db")
        db = DatabaseManager(db_path)
        doc_id = str(uuid.uuid4())
        if parsed:
            parsed["id"] = doc_id
        with db.get_conn() as conn:
            conn.execute(
                """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'processed', ?)""",
                (
                    parsed.get("title") or filename if parsed else filename,
                    filename,
                    "job",
                    len(content),
                    json.dumps({
                        "parsed": parsed,
                        "markdown": markdown,
                        "user_id": user_id,
                    }, ensure_ascii=False),
                    _now_iso(),
                ),
            )
        job_id = doc_id
    except Exception as e:
        logger.warning(f"Failed to persist job: {e}")

    return jsonify(
        parsed=parsed,
        markdown=markdown,
        filename=filename,
        job_id=job_id,
    )


@jobs_bp.route("/parse", methods=["POST"])
@optional_auth
def parse_job():
    """Parse plain job description text into structured data via LLM."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify(error="bad_request", message="请输入职位描述文本"), 400

    try:
        from src.agents.document_agents import run_document_analysis
        parsed = run_document_analysis("job", text)
        if parsed is None:
            return jsonify(error="parse_failed", message="职位解析未返回结果"), 500
        return jsonify(parsed=parsed)
    except Exception as e:
        return jsonify(error="parse_failed", message=str(e)), 500


@jobs_bp.route("/match", methods=["POST"])
@optional_auth
@require_consent("job_match")
def job_match():
    """Match a resume to job listings via multi-dimension LLM scoring.

    Accepts JSON body:
      - resume_text:        resume content (required)
      - job_id:             optional — match against a single persisted job
      - job_description:    optional — match against ad-hoc job text
    """
    data = request.get_json() or {}
    resume_text = data.get("resume_text", "").strip()

    if not resume_text:
        return jsonify(error="bad_request", message="resume_text required"), 400

    user_id = g.get("user_id", "guest-anon")
    tier = g.get("user_tier", "guest")

    # Quota check
    quota_result = consume_with_boost(user_id, tier, RESOURCE_JOB_MATCH)
    if not quota_result["ok"]:
        return _quota_exceeded_response(tier)

    # Determine job source
    target_jobs = []
    job_id_filter = data.get("job_id", "").strip()
    adhoc_description = data.get("job_description", "").strip()

    if adhoc_description:
        # Match against a single ad-hoc job description
        target_jobs = [{
            "id": "adhoc",
            "title": "",
            "company": "",
            "location": "",
            "salary_range": "",
            "description": adhoc_description,
        }]
    elif job_id_filter:
        # Match against a single persisted job
        persisted = _get_persisted_jobs()
        target_jobs = [j for j in persisted if j["id"] == job_id_filter]
        if not target_jobs:
            # Try mock
            target_jobs = [j for j in MOCK_JOBS if j["id"] == job_id_filter]
        if not target_jobs:
            return jsonify(error="not_found", message=f"职位 {job_id_filter} 不存在"), 404
    else:
        # Match against all available jobs
        persisted = _get_persisted_jobs()
        target_jobs = persisted if persisted else MOCK_JOBS

    try:
        from src.pipeline.job_match_pipeline import run_job_match_pipeline
        matches, total = run_job_match_pipeline(
            resume_text=resume_text,
            jobs=target_jobs,
        )
        return jsonify(matches=matches, total_evaluated=total)
    except Exception as e:
        logger.error(f"Job match failed: {e}")
        return jsonify(error="match_failed", message=str(e)), 500


# ── HarmonyOS 对齐端点 ──


@jobs_bp.route("/", methods=["GET"], strict_slashes=False)
@optional_auth
def list_jobs_root():
    """List available jobs (HarmonyOS alias for /list)."""
    return list_jobs()


@jobs_bp.route("/search", methods=["GET"])
@optional_auth
def search_jobs():
    """Search jobs by keyword query parameter.

    Query: ?q=前端&location=深圳&page=1&size=20
    """
    q = (request.args.get("q") or "").strip().lower()
    location = (request.args.get("location") or "").strip().lower()
    if not q and not location:
        # No filter → return all
        return list_jobs()

    persisted = _get_persisted_jobs()
    source = persisted if persisted else MOCK_JOBS

    filtered = []
    for j in source:
        title = (j.get("title") or "").lower()
        company = (j.get("company") or "").lower()
        desc = (j.get("description") or "").lower()
        loc = (j.get("location") or "").lower()
        tags_text = " ".join(j.get("tags") or []) if j.get("tags") else ""

        matches = True
        if q:
            matches = q in title or q in company or q in desc or q in tags_text
        if matches and location:
            matches = location in loc

        if matches:
            filtered.append(j)

    return jsonify(jobs=filtered, total=len(filtered))


# 注意：/recommend 必须注册在 /<job_id> 之前，否则 "recommend" 会
# 被 Flask 当作 job_id 捕获，导致 404。
@jobs_bp.route("/recommend", methods=["GET"])
@require_auth
def recommend_jobs():
    """AI-recommended jobs for the current user.

    Currently returns top-scored mock jobs; future: personalization via user profile.
    """
    # Build a simple sorted list with simulated match_score
    persisted = _get_persisted_jobs()
    source = persisted if persisted else MOCK_JOBS

    # Simulate match scores based on job index (MVP)
    import random
    random.seed(g.user_id)
    scored = []
    for j in source:
        j_copy = dict(j)
        j_copy["match_score"] = random.randint(60, 99)
        scored.append(j_copy)

    scored.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top = scored[:10]

    return jsonify(jobs=top, total=len(top))


@jobs_bp.route("/<job_id>", methods=["GET"])
@optional_auth
def job_detail(job_id: str):
    """Get job detail by ID (HarmonyOS JobDetailPage)."""
    persisted = _get_persisted_jobs()
    source = persisted if persisted else MOCK_JOBS

    for j in source:
        if j.get("id") == job_id:
            return jsonify(job=j)

    return jsonify(error="not_found", message=f"Job {job_id} not found"), 404
