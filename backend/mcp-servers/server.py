#!/usr/bin/env python3
"""
Looma-Zervi MCP Sidecar — MVP Temporary Adapter Layer.

Provides 3 tools for internal testing:
  - rag_query     RAG knowledge-base query with AI answer
  - match_jobs    Resume-to-job-posting matching
  - parse_resume  Resume text → structured JSON

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

mcp = FastMCP("looma-zervi", description="Looma-Zervi MCP Sidecar (MVP)")

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
        "tools": ["rag_query", "match_jobs", "parse_resume"],
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
    description="Parse resume text into structured JSON (requires JWT token)",
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
        _auth_guard(token, user_id)
    except MCPAuthError as e:
        return _error_dict(str(e))

    try:
        from src.agents.document_agents import run_document_analysis

        extracted = run_document_analysis("resume", resume_text)
        return {"extracted": extracted}
    except ImportError as e:
        return {"extracted": {}, "error": str(e)}

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    env_file = BACKEND_SRC.parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file)
    port = int(os.getenv("MCP_PORT", "8999"))
    logger.info(f"Looma MCP Sidecar on :{port}")
    mcp.run(transport="sse", host="127.0.0.1", port=port)