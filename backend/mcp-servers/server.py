#!/usr/bin/env python3
from __future__ import annotations
import json, logging, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_SRC = HERE.parent / "src"
sys.path.insert(0, str(BACKEND_SRC))

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("looma.mcp")
logging.basicConfig(level=logging.INFO)

mcp = FastMCP("looma-zervi", description="Looma-Zervi MCP Sidecar")

@mcp.tool(name="rag_query", description="RAG knowledge base query with AI answer")
def rag_query(question: str, user_id: str = "", n_results: int = 3) -> dict:
    try:
        from src.rag.chroma_client import search_chroma
        from src.agents.central_brain import _call_llm
        results = search_chroma(question, n_results=n_results)
        ctx = "\n\n".join(r.get("content", "") for r in results) if results else ""
        prompt = f"Answer based on context:\n{ctx}\n\nQuestion: {question}\nAnswer:"
        answer = _call_llm(prompt) or "RAG query failed"
        sources = [{"chunk": r.get("content", "")[:200], "score": r.get("score")} for r in results]
        return {"answer": answer, "sources": sources, "n_results": len(results)}
    except ImportError as e:
        return {"answer": f"RAG unavailable: {e}", "sources": [], "n_results": 0}

@mcp.tool(name="match_jobs", description="Match resume text against job postings")
def match_jobs(resume_text: str, user_id: str = "", top_k: int = 10) -> dict:
    try:
        from src.pipeline.job_match_pipeline import run_job_match_pipeline
        results_list, total = run_job_match_pipeline(resume_text=resume_text, top_k=top_k)
        return {"matches": results_list, "total_evaluated": total}
    except ImportError as e:
        return {"matches": [], "total_evaluated": 0, "error": str(e)}

@mcp.tool(name="parse_resume", description="Parse resume text into structured JSON")
def parse_resume(resume_text: str, user_id: str = "") -> dict:
    try:
        from src.agents.document_agents import run_document_analysis
        extracted = run_document_analysis("resume", resume_text)
        return {"extracted": extracted}
    except ImportError as e:
        return {"extracted": {}, "error": str(e)}

if __name__ == "__main__":
    env_file = BACKEND_SRC.parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    port = int(os.getenv("MCP_PORT", "8999"))
    logger.info(f"Looma MCP Sidecar on :{port}")
    mcp.run(transport="sse", host="127.0.0.1", port=port)
