"""
Trust layer API — memory records and claim attestations.

See: backend/contracts/trust.v1.json, docs/TRUST_LAYER.md
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app, g

from src.api.auth.decorators import require_auth
from src.trust.service import INTERSECTION_CREDIT_CHECK

trust_bp = Blueprint("trust", __name__)


def _get_db():
    return current_app._db


# ---------------------------------------------------------------------------
# GET /v1/trust/memories — 查询记忆体
# ---------------------------------------------------------------------------
@trust_bp.route("/memories", methods=["GET"])
@require_auth
def list_memories():
    """本人参与的信任记忆体列表。"""
    db = _get_db()
    memories = db.list_trust_memories_for_user(g.user_id)
    return jsonify(memories=memories, count=len(memories))


# ---------------------------------------------------------------------------
# POST /v1/trust/memories — CLI 上报征信记录（或其他 trust 事件）
# ---------------------------------------------------------------------------
@trust_bp.route("/memories", methods=["POST"])
@require_auth
def create_memory():
    """CLI / 外部客户端上报信任记忆体。

    Request body (JSON):
      {
        "intersection_type": "enterprise_credit_check",
        "evidence": {
          "behavior": {
            "company_name": "腾讯科技",
            "registered_capital": "10000万人民币",
            "credit_code": "91440300...",
            "legal_person": "马化腾",
            "status": "存续",
            "established": "2000-02-24",
            "region": "深圳市"
          },
          "channels": ["cli"]
        },
        "platform": "cli",
        "visibility": "trusted"
      }

    Response:
      201 { "memory_id": "...", "intersection_type": "...", "occurred_at": "..." }
    """
    db = _get_db()
    body = request.get_json(silent=True) or {}

    intersection_type = body.get("intersection_type", "").strip()
    if not intersection_type:
        return jsonify(error="bad_request", message="intersection_type is required"), 400

    # 目前只接受已知类型的上报
    allowed_types = {INTERSECTION_CREDIT_CHECK, "consensus_exchange", "personality_completion"}
    if intersection_type not in allowed_types:
        return jsonify(
            error="bad_request",
            message=f"unknown intersection_type: {intersection_type}. Allowed: {', '.join(sorted(allowed_types))}",
        ), 400

    evidence = body.get("evidence") or {}
    platform = body.get("platform", "cli")
    visibility = body.get("visibility", "trusted")

    memory_id = db.create_trust_memory(
        intersection_type=intersection_type,
        participants=[g.user_id],
        evidence=evidence,
        visibility=visibility,
        platform=platform,
    )

    memory = db.get_trust_memory(memory_id)

    return jsonify(
        memory_id=memory_id,
        intersection_type=intersection_type,
        occurred_at=memory.get("occurred_at") if memory else None,
    ), 201


@trust_bp.route("/memories/<memory_id>", methods=["GET"])
@require_auth
def get_memory(memory_id: str):
    db = _get_db()
    memory = db.get_trust_memory(memory_id)
    if not memory:
        return jsonify(error="not_found", message="memory not found"), 404
    if g.user_id not in memory.get("participants", []):
        return jsonify(error="forbidden", message="not a participant"), 403
    return jsonify(memory)


@trust_bp.route("/claims", methods=["GET"])
@require_auth
def list_claims():
    """当前用户 claim 级 attestation 聚合。"""
    db = _get_db()
    attestations = db.list_trust_attestations_for_user(g.user_id)
    return jsonify(
        user_id=g.user_id,
        attestations=attestations,
        count=len(attestations),
    )


@trust_bp.route("/claims/<claim_key>", methods=["GET"])
@require_auth
def get_claim(claim_key: str):
    db = _get_db()
    att = db.get_trust_attestation(g.user_id, claim_key)
    if not att:
        return jsonify(
            user_id=g.user_id,
            claim_key=claim_key,
            status="unverified",
            attestation=None,
        )
    memories = []
    for mid in att.get("evidence_memory_ids") or []:
        m = db.get_trust_memory(mid)
        if m:
            memories.append(m)
    return jsonify(
        user_id=g.user_id,
        claim_key=claim_key,
        attestation=att,
        evidence_memories=memories,
    )
