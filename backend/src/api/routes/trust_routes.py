"""
Trust layer API — memory records and claim attestations.

See: backend/contracts/trust.v1.json, docs/TRUST_LAYER.md
"""
from __future__ import annotations

from flask import Blueprint, jsonify, current_app, g

from src.api.auth.decorators import require_auth

trust_bp = Blueprint("trust", __name__)


def _get_db():
    return current_app._db


@trust_bp.route("/memories", methods=["GET"])
@require_auth
def list_memories():
    """本人参与的信任记忆体列表。"""
    db = _get_db()
    memories = db.list_trust_memories_for_user(g.user_id)
    return jsonify(memories=memories, count=len(memories))


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
