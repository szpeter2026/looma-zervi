"""
Credit / Company evaluation routes.
Resume → Job Match → Company Credit: the third leg of the HR evaluation tripod.

Endpoints:
  POST /v1/credit/analyze       — parse raw credit report text via LLM
  POST /v1/credit/check-company  — evaluate a company by name (post-match flow)
                                   ⭐ Now powered by QCC (企查查) official data source
"""
from __future__ import annotations

import json
import logging
import re

from flask import Blueprint, request, jsonify, g

from src.api.auth.decorators import require_auth
from src.agents.central_brain import _call_llm
from src.compliance.consent import require_consent
from src.credit.qcc_client import (
    check_company_credit,
    format_credit_summary,
    QccMcpError,
    QccCreditReport,
)

logger = logging.getLogger("looma.credit_routes")

credit_bp = Blueprint("credit", __name__)


# ---- Helpers ----

def _parse_credit_text(text: str) -> dict | None:
    """LLM-powered credit text extraction: entity_name, report_type, summary."""
    prompt = (
        "你是一个企业征信评估专家。根据以下文本，提取并评估该企业的信用状况，"
        "输出 JSON 格式：\n"
        "{{\n"
        '  "entity_name": "企业名称",\n'
        '  "report_type": "报告类型（如：企业信用报告/经营风险评估/工商信息摘要）",\n'
        '  "summary": "信用评估摘要（200字以内，包含经营状态、风险提示、信用等级评估）"\n'
        "}}\n\n"
        "只输出 JSON，不要任何解释或前缀。\n\n"
        f"待评估文本：\n{text[:4000]}"
    )

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


def _build_qcc_credit_response(report: QccCreditReport) -> dict:
    """Build a structured credit response from a QCC report.

    Returns a dict compatible with the frontend CreditAnalysis type,
    plus additional fields for rich display.
    """
    c = report.company

    # Determine report type based on what data we have
    report_type = "企业信用报告"
    if report.risk.risk_items and report.operation.raw:
        report_type = "企业综合信用评估（含经营数据）"
    elif report.risk.risk_items:
        report_type = "企业风险评估报告"

    extracted = {
        "entity_name": c.company_name,
        "report_type": report_type,
        "summary": format_credit_summary(report),
    }

    # Extended fields for rich UI display
    extended = {
        "source": report.source,
        "company": {
            "name": c.company_name,
            "legal_person": c.legal_person,
            "registered_capital": c.registered_capital,
            "established_date": c.established_date,
            "credit_code": c.credit_code,
            "status": c.status,
            "industry": c.industry,
            "address": c.address,
            "business_scope": c.business_scope,
        },
        "risk": {
            "level": report.risk.risk_level,
            "summary": report.risk.summary,
            "count": len(report.risk.risk_items),
            "items": report.risk.risk_items[:10],  # top 10 risk items
        },
        "operation": {
            "summary": report.operation.summary,
        },
        "executives": report.executives[:10],
        "ipr": report.ipr[:10] if report.ipr else [],
        "history": report.history[:10] if report.history else [],
        "legal_cases": report.legal_cases[:10] if report.legal_cases else [],
    }

    return {"extracted": extracted, "extended": extended}


# ---- Routes ----

@credit_bp.route("/analyze", methods=["POST"])
@require_auth
@require_consent("credit_analyze")
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
@require_auth
@require_consent("credit_query")
def check_company():
    """Evaluate a company's credit / business status by name.

    ⭐ Now powered by QCC (企查查) official MCP data source — no longer LLM-only.

    Body: { "company_name": "XX科技", "location"?: "深圳", "industry"?: "互联网" }

    The endpoint first tries the QCC official data source.  If QCC is unavailable,
    it falls back to the previous LLM-based evaluation.

    Returns: { "extracted": { entity_name, report_type, summary },
               "extended": { company, risk, operation, executives, ... },
               "source": "qcc" | "llm" }
    """
    body = request.get_json(silent=True) or {}
    company_name = (body.get("company_name") or "").strip()
    if not company_name:
        return jsonify(error="missing_company", message="请提供公司名称"), 400

    location = (body.get("location") or "").strip()
    industry = (body.get("industry") or "").strip()

    # ── Primary: QCC official data source ──
    try:
        report = check_company_credit(
            company_name=company_name,
            include_risk=True,
            include_operation=True,
            include_executives=True,
            include_ipr=False,
            include_history=False,
            include_legal_cases=False,
            include_documents=False,
        )

        if report.company.company_name:
            logger.info(
                f"[Credit] QCC data retrieved for '{company_name}' → "
                f"risk={report.risk.risk_level}, items={len(report.risk.risk_items)}"
            )
            response = _build_qcc_credit_response(report)
            response["source"] = "qcc"
            return jsonify(response)

    except QccMcpError as e:
        logger.warning(f"[Credit] QCC unavailable for '{company_name}', falling back to LLM: {e}")

    except Exception as e:
        logger.error(f"[Credit] QCC unexpected error for '{company_name}': {e}")

    # ── Fallback: LLM-based evaluation (legacy) ──
    logger.info(f"[Credit] Using LLM fallback for '{company_name}'")

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

    return jsonify(
        extracted=extracted,
        source="llm",
        warning=(
            "⚠️ 正式数据源暂不可用，当前为 AI 训练知识评估。"
            "本评估基于大语言模型训练数据，不可作为正式征信/风控依据。"
        ),
    )


@credit_bp.route("/check-company/detail", methods=["POST"])
@require_auth
@require_consent("credit_query")
def check_company_detail():
    """Full detailed credit check with all QCC data categories.

    Body: { "company_name": "XX科技" }

    Includes: company info, risk, operation, executives, IPR, history,
              legal cases, and documents.

    Returns: { "extracted": {...}, "extended": {...}, "source": "qcc" }
    """
    body = request.get_json(silent=True) or {}
    company_name = (body.get("company_name") or "").strip()
    if not company_name:
        return jsonify(error="missing_company", message="请提供公司名称"), 400

    try:
        report = check_company_credit(
            company_name=company_name,
            include_risk=True,
            include_operation=True,
            include_executives=True,
            include_ipr=True,
            include_history=True,
            include_legal_cases=True,
            include_documents=True,
        )

        if not report.company.company_name:
            return jsonify(error="not_found", message=f"未找到企业 '{company_name}' 的信息"), 404

        response = _build_qcc_credit_response(report)
        response["source"] = "qcc"

        # Add full extended data for detail view
        response["extended"]["ipr"] = report.ipr
        response["extended"]["history"] = report.history
        response["extended"]["legal_cases"] = report.legal_cases
        response["extended"]["documents"] = report.documents

        return jsonify(response)

    except QccMcpError as e:
        logger.error(f"[Credit] QCC detail failed for '{company_name}': {e}")
        return jsonify(error="qcc_unavailable", message=f"企查查服务暂不可用: {e}"), 503

    except Exception as e:
        logger.error(f"[Credit] QCC detail unexpected error: {e}")
        return jsonify(error="internal_error", message="征信查询服务异常，请稍后重试"), 500
