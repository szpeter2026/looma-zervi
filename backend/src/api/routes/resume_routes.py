"""
Resume routes blueprint.
Ownership: szbenyx

Endpoints:
  POST /v1/resume/parse   - Parse plain resume text to structured data
  POST /v1/resume/upload  - Upload resume file (PDF/DOCX), auto-parsed via MarkItDown + LLM
  POST /v1/resume/improve - Generate improvement suggestions for a parsed resume
"""
import io
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, optional_auth
from src.utils.quota import consume_with_boost, QUOTA_LIMITS, RESOURCE_RESUME_PARSE, get_remaining, build_upgrade_hint

logger = logging.getLogger("looma.resume")
resume_bp = Blueprint("resume", __name__)

# Shanghai timezone
_SHA_TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(_SHA_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def _quota_exceeded_response(tier: str):
    upgrade = build_upgrade_hint(tier, 0)
    return jsonify(error="quota_exceeded", message="当日简历解析配额已用尽", upgrade=upgrade), 429


@resume_bp.route("/parse", methods=["POST"])
@optional_auth
def parse_resume():
    """Parse resume text to structured data."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify(error="bad_request", message="resume text required"), 400

    user_id = g.get("user_id", "guest-anon")
    tier = g.get("user_tier", "guest")

    # Quota check
    quota_result = consume_with_boost(user_id, tier, RESOURCE_RESUME_PARSE)
    if not quota_result["ok"]:
        return _quota_exceeded_response(tier)

    try:
        from src.agents.document_agents import run_document_analysis
        result = run_document_analysis("resume", text)
        if result is None:
            return jsonify(error="parse_failed", message="简历解析未返回结果"), 500
        return jsonify(extracted=result)
    except Exception as e:
        return jsonify(error="parse_failed", message=str(e)), 500


@resume_bp.route("/upload", methods=["POST"])
@optional_auth
def upload_resume():
    """Upload resume file (PDF/DOCX/Word) for AI parsing.

    Pipeline: MarkItDown binary→Markdown → LLM structured extraction → persist → return.

    Accepts multipart/form-data with field name ``file``.
    """
    user_id = g.get("user_id", "guest-anon")
    tier = g.get("user_tier", "guest")

    # Check file presence
    if "file" not in request.files:
        return jsonify(error="bad_request", message="未检测到上传文件"), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify(error="bad_request", message="文件名称为空"), 400

    # Validate extension
    filename = file.filename
    allowed = {".pdf", ".docx", ".doc", ".txt", ".md"}
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if f".{ext}" not in allowed:
        return jsonify(error="bad_request", message=f"不支持的文件格式: .{ext}，支持: {', '.join(allowed)}"), 400

    # Quota check
    quota_result = consume_with_boost(user_id, tier, RESOURCE_RESUME_PARSE)
    if not quota_result["ok"]:
        return _quota_exceeded_response(tier)

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

        markdown = stream_to_markdown(
            io.BytesIO(content),
            filename=filename,
        )
    except Exception as e:
        logger.error(f"MarkItDown conversion failed for {filename}: {e}")
        return jsonify(error="convert_failed", message=f"文档解析失败（{filename} 格式未识别或文件损坏）"), 422

    if not markdown or not markdown.strip():
        return jsonify(error="convert_failed", message="文档内容为空，无法提取文字"), 422

    # Step 2: LLM structured extraction
    try:
        from src.agents.document_agents import run_document_analysis
        extracted = run_document_analysis("resume", markdown)
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        # Return markdown only if extraction fails
        return jsonify(
            extracted=None,
            markdown=markdown,
            filename=filename,
            error=f"结构化提取失败: {e}",
        ), 200

    # Step 3: Persist to DB
    resume_id = None
    try:
        from src.db.manager import DatabaseManager
        db_path = current_app.config.get("DATABASE_PATH", "data/looma.db")
        db = DatabaseManager(db_path)
        doc_id = str(uuid.uuid4())
        with db.get_conn() as conn:
            conn.execute(
                """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'processed', ?)""",
                (
                    filename,
                    filename,
                    "resume",
                    len(content),
                    json.dumps({"extracted": extracted, "markdown": markdown, "user_id": user_id}, ensure_ascii=False),
                    _now_iso(),
                ),
            )
        resume_id = doc_id
    except Exception as e:
        logger.warning(f"Failed to persist resume: {e}")

    return jsonify(
        extracted=extracted,
        markdown=markdown,
        filename=filename,
        resume_id=resume_id,
    )


@resume_bp.route("/improve", methods=["POST"])
@optional_auth
def improve_resume():
    """Generate AI-powered improvement suggestions for a resume.

    Accepts JSON body with either:
      - ``resume_text``: raw resume text (plain or markdown)
      - ``extracted``:   already-parsed resume JSON
      - ``focus``:       optional — which area to focus on ("overall" | "skills" | "experience" | "education")
    """
    data = request.get_json() or {}
    resume_text = data.get("resume_text", "").strip()
    extracted = data.get("extracted")
    focus = data.get("focus", "overall").strip().lower()

    if not resume_text and not extracted:
        return jsonify(error="bad_request", message="请提供简历文本(resume_text)或已解析数据(extracted)"), 400

    # Build input for LLM
    if resume_text:
        text_for_prompt = resume_text[:4000]
    else:
        text_for_prompt = json.dumps(extracted, ensure_ascii=False, indent=2)[:4000]

    focus_hints = {
        "overall": "请从整体结构、内容完整度、关键信息呈现、语言表达等方面给出建议",
        "skills": "请重点分析技能描述是否充分、与目标岗位的匹配度、技能分类是否合理",
        "experience": "请重点分析工作/项目经历的写法是否突出了成果和量化指标，描述是否具体",
        "education": "请重点分析教育背景的呈现方式、与岗位要求的关联度",
    }
    focus_prompt = focus_hints.get(focus, focus_hints["overall"])

    prompt = (
        "你是一位资深HR和简历优化专家。请仔细分析以下简历内容，给出具体可操作的改进建议。\n\n"
        f"分析维度：{focus_prompt}\n\n"
        "请输出 JSON 格式：\n"
        "{\n"
        '  "overall_score": 数字(0-100),\n'
        '  "strengths": ["优点1", "优点2"],\n'
        '  "weaknesses": ["需改进的地方1", "需要改进的地方2"],\n'
        '  "suggestions": [\n'
        '    {"area": "区域", "issue": "问题", "advice": "具体操作建议", "example": "改后示例"}\n'
        '  ],\n'
        '  "summary": "总结性建议"\n'
        "}\n\n"
        f"简历内容：\n{text_for_prompt}"
    )

    try:
        from src.agents.central_brain import _call_llm
        import re as _re

        response = _call_llm(prompt)
        if not response:
            return jsonify(error="llm_failed", message="AI 分析服务暂不可用，请稍后重试"), 503

        resp = response.strip()
        if "```" in resp:
            m = _re.search(r"```(?:json)?\s*([\s\S]*?)```", resp)
            if m:
                resp = m.group(1).strip()
        parsed = json.loads(resp)
        return jsonify(improvements=parsed)
    except json.JSONDecodeError:
        return jsonify(error="llm_parse_failed", message="AI 返回格式异常，请重试"), 500
    except Exception as e:
        logger.error(f"Resume improve failed: {e}")
        return jsonify(error="improve_failed", message=str(e)), 500
