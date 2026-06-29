"""
Document Agents — Resume / Credit / Document analysis via LLM.
Migrated from old document_agents.py, adapted for Flask.
"""
from __future__ import annotations
import json
import logging
import re

logger = logging.getLogger("looma.doc_agents")


def run_document_analysis(doc_type: str, text: str) -> dict | None:
    """Analyze a document (resume, credit report etc.) via LLM.

    Returns structured dict or None on failure.
    """
    prompts = {
        "resume": (
            "你是一个简历解析专家。从以下文本中提取结构化信息，输出 JSON 格式："
            "{\"name\": \"...\", \"email\": \"...\", \"phone\": \"...\", "
            "\"education\": [{\"school\": \"...\", \"degree\": \"...\", \"year\": \"...\"}], "
            "\"experience\": [{\"company\": \"...\", \"role\": \"...\", \"duration\": \"...\", \"description\": \"...\"}], "
            "\"skills\": [\"...\"], \"summary\": \"...\"}"
            "\n\n简历文本：\n{text}"
        ),
        "credit": (
            "你是一个征信分析专家。从以下信用报告文本中提取关键信息，输出 JSON 格式："
            "{\"credit_score\": \"...\", \"loan_history\": [], \"payment_status\": \"...\", "
            "\"risk_factors\": [], \"summary\": \"...\"}"
            "\n\n征信文本：\n{text}"
        ),
    }

    prompt_template = prompts.get(doc_type)
    if not prompt_template:
        logger.warning(f"Unknown doc_type: {doc_type}")
        return None

    prompt = prompt_template.format(text=text[:3000])

    try:
        from src.agents.central_brain import _call_llm
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
        logger.error(f"Document analysis failed for {doc_type}: {e}")
        return None
