"""
Credit / Company evaluation routes.
Resume → Job Match → Company Credit: the third leg of the HR evaluation tripod.

Endpoints:
  POST /v1/credit/analyze       — parse raw credit report text via LLM
  POST /v1/credit/check-company  — evaluate a company by name (post-match flow)
"""
from __future__ import annotations

import json
import logging
import re

from flask import Blueprint, request, jsonify

from src.agents.central_brain import _call_llm

logger = logging.getLogger("looma.credit_routes")

credit_bp = Blueprint("credit", __name__)


# ---- Helpers ----

def _parse_credit_text(text: str) -> dict | None:
    """LLM-powered credit text extraction: entity_name, report_type, summary."""
    prompt = (
        "你是一个企业征信评估专家。根据以下文本，提取并评估该企业的信用状况，"
        "输出 JSON 格式：\n"
        "{\n"
        '  "entity_name": "企业名称",\n'
        '  "report_type": "报告类型（如：企业信用报告/经营风险评估/工商信息摘要）",\n'
        '  "summary": "信用评估摘要（200字以内，包含经营状态、风险提示、信用等级评估）"\n'
        "}\n\n"
        "只输出 JSON，不要任何解释或前缀。\n\n"
        "待评估文本：\n{text}"
    ).format(text=text[:4000])

    try:
        response = _call_llm(prompt)
        if not response:
            return None
        resp = response.strip()
        if "```" in resp:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", resp)
            if m:
                resp = m.group(1).strip()
        return json.loads(resp)
    except Exception as e:
        logger.error(f"Credit parse failed: {e}")
        return None


# ---- Routes ----

@credit_bp.route("/analyze", methods=["POST"])
def analyze():
    """Parse raw credit / company info text via LLM.

    Body: { "text": "..." }
    Returns: { "extracted": { entity_name, report_type, summary } }
    """
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify(error="missing_text", message="请提供征信/企业信息文本"), 400

    extracted = _parse_credit_text(text)
    if not extracted:
        return jsonify(error="parse_failed", message="征信解析失败，请检查文本内容或重试"), 422

    return jsonify(extracted=extracted)


@credit_bp.route("/check-company", methods=["POST"])
def check_company():
    """Evaluate a company's credit / business status by name.

    Body: { "company_name": "XX科技", "location"?: "深圳", "industry"?: "互联网" }

    The LLM draws on its training knowledge to produce an assessment.
    Returns: { "extracted": { entity_name, report_type, summary } }
    """
    body = request.get_json(silent=True) or {}
    company_name = (body.get("company_name") or "").strip()
    if not company_name:
        return jsonify(error="missing_company", message="请提供公司名称"), 400

    location = (body.get("location") or "").strip()
    industry = (body.get("industry") or "").strip()

    location_hint = f"，位于{location}" if location else ""
    industry_hint = f"，主营{industry}" if industry else ""

    query = (
        f"请评估以下企业的经营状况与信用风险：\n"
        f"企业名称：{company_name}{location_hint}{industry_hint}\n"
        f"请基于你的知识，给出该企业的信用评估摘要，包括经营状态、行业地位、风险提示等。"
    )

    extracted = _parse_credit_text(query)
    if not extracted:
        return jsonify(error="parse_failed", message=f"无法评估 {company_name}，请稍后重试"), 422

    # Ensure the entity_name matches the requested company
    if not extracted.get("entity_name"):
        extracted["entity_name"] = company_name

    return jsonify(extracted=extracted)
