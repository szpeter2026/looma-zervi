#!/usr/bin/env python3
"""
Looma-Zervi MCP Sidecar — MVP Temporary Adapter Layer.

Provides 4 tools for internal testing:
  - rag_query        RAG knowledge-base query with AI answer
  - match_jobs       Resume-to-job-posting matching
  - parse_resume     Resume text → structured JSON
  - credit_check     Enterprise credit check via QCC (企查查) official data

⚠  This is a **temporary** Python FastMCP adapter.  The permanent MCP
   implementation will be Rust zervi (origin/feature/llm-provider-fallback-k6-baseline).

Security: All tools require a valid looma JWT bearer token (3rd param).
"""
from __future__ import annotations

import json, logging, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_SRC = HERE.parent / "src"
sys.path.insert(0, str(BACKEND_SRC))

from mcp.server.fastmcp import FastMCP

from mcp_auth import MCPAuthError, verify_bearer_token_inline

logger = logging.getLogger("looma.mcp")
logging.basicConfig(level=logging.INFO)

_MCP_PORT = int(os.getenv("MCP_PORT", "8999"))
_MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")

mcp = FastMCP(
    "looma-zervi",
    instructions="Looma-Zervi MCP Sidecar (MVP)",
    host=_MCP_HOST,
    port=_MCP_PORT,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_guard(token: str, user_id: str) -> dict:
    """Verify JWT and return decoded payload.  Raises MCPAuthError on failure."""
    if not token:
        raise MCPAuthError("Missing authentication token (param 'token')")
    return verify_bearer_token_inline(token, user_id=user_id or None)


def _error_dict(msg: str, kind: str = "auth_error") -> dict:
    return {"error": kind, "message": msg}

# ---------------------------------------------------------------------------
# Health check resource
# ---------------------------------------------------------------------------

@mcp.resource("health://status")
def health_status() -> dict:
    """Health check endpoint for CI / verify-p0-local.sh."""
    return {
        "status": "ok",
        "service": "looma-mcp-sidecar",
        "tools": ["rag_query", "match_jobs", "parse_resume", "credit_check"],
    }

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="rag_query",
    description="RAG knowledge base query with AI answer (requires JWT token)",
)
def rag_query(question: str, token: str = "", user_id: str = "", n_results: int = 3) -> dict:
    """Query the RAG knowledge base and return an AI-generated answer.

    Parameters
    ----------
    question : str
        Natural-language query string.
    token : str
        Looma JWT bearer token (required).
    user_id : str
        Authenticated user id (optional, cross-checked against token).
    n_results : int
        Number of ChromaDB chunks to retrieve (default 3).
    """
    try:
        _auth_guard(token, user_id)
    except MCPAuthError as e:
        return _error_dict(str(e))

    try:
        from src.rag.chroma_client import search_chroma
        from src.agents.central_brain import _call_llm

        results = search_chroma(question, n_results=n_results)
        ctx = "\n\n".join(r.get("content", "") for r in results) if results else ""
        prompt = f"Answer based on context:\n{ctx}\n\nQuestion: {question}\nAnswer:"
        answer = _call_llm(prompt) or "RAG query failed"
        sources = [
            {"chunk": r.get("content", "")[:200], "score": r.get("score")}
            for r in results
        ]
        return {"answer": answer, "sources": sources, "n_results": len(results)}
    except ImportError as e:
        return {"answer": f"RAG unavailable: {e}", "sources": [], "n_results": 0}


@mcp.tool(
    name="match_jobs",
    description="Match resume text against job postings (requires JWT token)",
)
def match_jobs(resume_text: str, token: str = "", user_id: str = "", top_k: int = 10) -> dict:
    """Match a resume against available job postings.

    Parameters
    ----------
    resume_text : str
        Full text of the candidate's resume.
    token : str
        Looma JWT bearer token (required).
    user_id : str
        Authenticated user id (optional, cross-checked against token).
    top_k : int
        Max top matches to return from the scored list (default 10).
    """
    try:
        _auth_guard(token, user_id)
    except MCPAuthError as e:
        return _error_dict(str(e))

    try:
        from src.pipeline.job_match_pipeline import run_job_match_pipeline

        results_list, total = run_job_match_pipeline(resume_text=resume_text)
        return {"matches": results_list[:top_k], "total_evaluated": total}
    except ImportError as e:
        return {"matches": [], "total_evaluated": 0, "error": str(e)}


@mcp.tool(
    name="parse_resume",
    description="Parse resume text into structured JSON (requires JWT token + consent)",
)
def parse_resume(resume_text: str, token: str = "", user_id: str = "") -> dict:
    """Parse unstructured resume text into structured JSON fields.

    Parameters
    ----------
    resume_text : str
        Full text of the candidate's resume.
    token : str
        Looma JWT bearer token (required).
    user_id : str
        Authenticated user id (optional, cross-checked against token).
    """
    try:
        payload = _auth_guard(token, user_id)
    except MCPAuthError as e:
        return _error_dict(str(e))

    # Consent gate: align with resume_upload consent enforcement
    uid = payload["sub"]
    try:
        from src.compliance.consent import get_consent_manager
        cm = get_consent_manager()
        if not cm.check(uid, "resume_upload"):
            return _error_dict("Consent required: resume_upload (请先授权简历上传)", "consent_required")
    except Exception as e:
        logger.warning(f"Consent check skipped (DB unavailable): {e}")

    try:
        from src.agents.document_agents import run_document_analysis

        extracted = run_document_analysis("resume", resume_text)
        return {"extracted": extracted}
    except ImportError as e:
        return {"extracted": {}, "error": str(e)}


@mcp.tool(
    name="credit_check",
    description="Enterprise credit check via QCC (企查查) official data — company info, risk, operation, executives (requires JWT token + consent)",
)
def credit_check(company_name: str, token: str = "", user_id: str = "", detail: bool = False) -> dict:
    """Check enterprise credit using QCC (企查查) official MCP data source.

    Parameters
    ----------
    company_name : str
        Full company name to look up (e.g. "深圳市腾讯计算机系统有限公司").
    token : str
        Looma JWT bearer token (required).
    user_id : str
        Authenticated user id (optional, cross-checked against token).
    detail : bool
        If True, fetch all categories (IPR, history, legal cases, documents).
        Default False returns basic report (company + risk + operation + executives).
    """
    try:
        payload = _auth_guard(token, user_id)
    except MCPAuthError as e:
        return _error_dict(str(e))

    # Consent gate
    uid = payload["sub"]
    try:
        from src.compliance.consent import get_consent_manager
        cm = get_consent_manager()
        if not cm.check(uid, "credit_query"):
            return _error_dict("Consent required: credit_query (请先授权征信查询)", "consent_required")
    except Exception as e:
        logger.warning(f"Consent check skipped (DB unavailable): {e}")

    try:
        from src.credit.qcc_client import (
            check_company_credit,
            format_credit_summary,
            QccMcpError,
        )

        report = check_company_credit(
            company_name=company_name,
            include_risk=True,
            include_operation=True,
            include_executives=True,
            include_ipr=detail,
            include_history=detail,
            include_legal_cases=detail,
            include_documents=detail,
        )

        if not report.company.company_name:
            return _error_dict(f"Company not found: {company_name}", "not_found")

        c = report.company
        return {
            "source": "qcc",
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
                "items": report.risk.risk_items[:10],
            },
            "operation": {
                "summary": report.operation.summary,
            },
            "executives": report.executives[:10],
            "summary": format_credit_summary(report),
        }

    except QccMcpError as e:
        return _error_dict(f"QCC service error: {e}", "qcc_unavailable")
    except ImportError as e:
        return _error_dict(f"Credit module unavailable: {e}", "module_error")

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    env_file = BACKEND_SRC.parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file)
    logger.info(f"Looma MCP Sidecar on {_MCP_HOST}:{_MCP_PORT} (SSE /sse)")
    mcp.run(transport="sse")