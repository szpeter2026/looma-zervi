"""
Ask routes blueprint (RAG knowledge base).
Ownership: szbenyx

Endpoints:
  POST /v1/ask   - Ask a question with RAG-powered answer
"""
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth
from src.api.auth.jwt_handler import get_current_user_id

ask_bp = Blueprint("ask", __name__)


@ask_bp.route("/ask", methods=["POST"])
@require_auth
def ask_question():
    """
    Ask a question to the RAG knowledge base.
    Flow: query -> ChromaDB vector search -> DeepSeek completion -> streamed response
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify(error="bad_request", message="question required"), 400

    # TODO: migrate ask.py logic here
    # 1. Check daily quota
    # 2. Search ChromaDB for relevant chunks
    # 3. Call DeepSeek API with context
    # 4. Log usage
    # 5. Return answer with source citations

    return jsonify(
        answer="(placeholder - migrate ask.py logic here)",
        sources=[],
        question=question,
    )
