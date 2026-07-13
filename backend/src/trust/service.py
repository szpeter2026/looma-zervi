"""
Trust layer v0 — consensus verified → memory_record + rule attestation.

See: backend/contracts/trust.v1.json, docs/TRUST_LAYER.md
"""
from __future__ import annotations

from src.analytics.events import log_product_event


CLAIM_MATCH_MISSION = "match_mission"
INTERSECTION_CONSENSUS = "consensus_exchange"


def memorialize_and_attest_consensus(db, consensus: dict, *, platform: str = "server") -> dict:
    """
    On match_consensus status=verified:
      1. Append trust_memory (consensus_exchange)
      2. Rule v0: initiator match_mission claim → verified
    """
    memory_id = db.create_trust_memory(
        intersection_type=INTERSECTION_CONSENSUS,
        participants=[consensus["initiator_id"], consensus["candidate_id"]],
        evidence={
            "behavior": {
                "match_score": consensus["match_score"],
                "reason": consensus.get("reason") or "",
                "consensus_id": consensus["id"],
                "fleet_id": consensus["fleet_id"],
            },
            "channels": ["behavior"],
        },
        fleet_id=consensus["fleet_id"],
        consensus_id=consensus["id"],
        platform=platform,
        visibility="trusted",
    )

    attestation_id = db.upsert_trust_attestation(
        user_id=consensus["initiator_id"],
        claim_key=CLAIM_MATCH_MISSION,
        status="verified",
        validator="rule_v0",
        evidence_memory_ids=[memory_id],
        reason="consensus_exchange verified by candidate acknowledge",
        confidence=1.0,
    )

    log_product_event(
        db,
        "trust_memory_created",
        user_id=consensus["initiator_id"],
        platform=platform,
        source="server",
        properties={
            "intersection_type": INTERSECTION_CONSENSUS,
            "memory_id": memory_id,
            "consensus_id": consensus["id"],
            "claim_key": CLAIM_MATCH_MISSION,
        },
    )
    log_product_event(
        db,
        "trust_attestation_verified",
        user_id=consensus["initiator_id"],
        platform=platform,
        source="server",
        properties={
            "claim_key": CLAIM_MATCH_MISSION,
            "attestation_id": attestation_id,
            "validator": "rule_v0",
            "memory_id": memory_id,
        },
    )

    return {
        "memory_id": memory_id,
        "attestation_id": attestation_id,
        "claim_key": CLAIM_MATCH_MISSION,
        "status": "verified",
    }
