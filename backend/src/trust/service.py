"""
Trust layer v0 — consensus verified → memory_record + rule attestation.

See: backend/contracts/trust.v1.json, docs/TRUST_LAYER.md
"""
from __future__ import annotations

from typing import Any

from src.analytics.events import log_product_event


CLAIM_MATCH_MISSION = "match_mission"
INTERSECTION_CONSENSUS = "consensus_exchange"
INTERSECTION_CREDIT_CHECK = "enterprise_credit_check"

# Personality types → Chinese labels for Navigator context
PERSONALITY_LABELS: dict[str, str] = {
    "星云艺术家": "星云艺术家（创造力+社交）",
    "黑洞程序员": "黑洞程序员（深度思考+逻辑）",
    "超新星领航员": "超新星领航员（行动力+领导力）",
    "双星星系守护者": "双星星系守护者（共情+可靠）",
    "脉冲星修行者": "脉冲星修行者（长期主义+节奏）",
    "暗物质漫游者": "暗物质漫游者（自由+跨界）",
}


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


# ---------------------------------------------------------------------------
# Trust Context Builder — 为 Navigator 提供用户完整信任画像
# ---------------------------------------------------------------------------

def build_trust_context(db, user_id: str, limit: int = 5) -> dict:
    """Aggregate user's trust profile for Navigator system prompt injection.

    Returns a structured dict with:
      - verified_attestations: list of verified claims
      - recent_memories: recent trust_memories (human-readable summaries)
      - credit_check_summary: aggregated CLI 征信查询记录
      - partner_memory: the last consensus_exchange partner personality (if any)
    """
    ctx: dict[str, Any] = {
        "verified_attestations": [],
        "recent_memories": [],
        "credit_check_summary": None,
        "partner_memory": None,
        "has_data": False,
    }

    if db is None:
        return ctx

    try:
        # 1. Verified attestations
        attestations = db.list_trust_attestations_for_user(user_id)
        verified = [a for a in attestations if a.get("status") == "verified"]
        ctx["verified_attestations"] = [
            {
                "claim_key": a["claim_key"],
                "validator": a.get("validator", "rule_v0"),
                "attested_at": a.get("attested_at", ""),
            }
            for a in verified
        ]

        # 2. Recent trust memories (all types)
        memories = db.list_trust_memories_for_user(user_id, limit=limit * 2)
        recent = []
        for m in memories[:limit]:
            entry = _summarize_memory(m, user_id)
            if entry:
                recent.append(entry)
        ctx["recent_memories"] = recent

        # 3. CLI 征信查询记录
        credit_checks = [
            m for m in memories
            if m.get("intersection_type") == INTERSECTION_CREDIT_CHECK
        ]
        if credit_checks:
            ctx["credit_check_summary"] = _summarize_credit_checks(credit_checks)

        # 4. Partner memory — last consensus_exchange
        consensus_memories = [
            m for m in memories
            if m.get("intersection_type") == INTERSECTION_CONSENSUS
        ]
        if consensus_memories:
            latest = consensus_memories[0]
            ctx["partner_memory"] = _extract_partner_context(latest, user_id, db)

        if ctx["verified_attestations"] or ctx["recent_memories"] or ctx["credit_check_summary"]:
            ctx["has_data"] = True

    except Exception:
        pass  # Trust context is best-effort; never break Navigator flow

    return ctx


def _summarize_memory(memory: dict, user_id: str) -> dict | None:
    """Convert a raw trust_memory row into a human-readable Navigator context entry."""
    itype = memory.get("intersection_type", "")
    evidence = memory.get("evidence", {})
    participants = memory.get("participants", [])
    occurred = memory.get("occurred_at", "")[:10]

    if itype == INTERSECTION_CONSENSUS:
        behavior = evidence.get("behavior", {})
        score = behavior.get("match_score", 0)
        reason = behavior.get("reason", "")
        return {
            "type": "consensus",
            "summary": f"在{occurred}与另一位探索者确认了星际共识（匹配度{score}）",
            "detail": reason,
            "score": score,
        }

    if itype == INTERSECTION_CREDIT_CHECK:
        behavior = evidence.get("behavior", {})
        company = behavior.get("company_name", "未知企业")
        capital = behavior.get("registered_capital", "")
        return {
            "type": "credit_check",
            "summary": f"在{occurred}查询了「{company}」的工商信息",
            "company": company,
            "capital": capital,
        }

    if itype == "personality_completion":
        return {
            "type": "personality",
            "summary": f"在{occurred}完成了星际人格觉醒",
        }

    return {
        "type": itype,
        "summary": f"在{occurred}留下了探索足迹",
    }


def _summarize_credit_checks(memories: list[dict]) -> dict:
    """Aggregate multiple credit check memories into a summary."""
    companies = []
    big_capital_count = 0
    for m in memories:
        evidence = m.get("evidence", {})
        behavior = evidence.get("behavior", {})
        name = behavior.get("company_name", "")
        capital_raw = behavior.get("registered_capital", "")
        if name:
            companies.append(name)
        # Detect "big" companies (capital > 100M)
        if capital_raw:
            try:
                import re
                nums = re.findall(r'[\d.]+', str(capital_raw))
                if nums:
                    amount = float(nums[0])
                    unit = str(capital_raw).lower()
                    if "亿" in unit:
                        amount *= 100_000_000
                    elif "万" in unit:
                        amount *= 10_000
                    if amount > 100_000_000:
                        big_capital_count += 1
            except (ValueError, IndexError):
                pass

    unique = list(dict.fromkeys(companies))  # preserve order, deduplicate
    return {
        "total_checks": len(memories),
        "companies": unique,
        "big_capital_count": big_capital_count,
    }


def _extract_partner_context(memory: dict, user_id: str, db) -> dict | None:
    """Extract partner personality from the latest consensus_exchange memory."""
    participants = memory.get("participants", [])
    partner_id = None
    for pid in participants:
        if pid != user_id:
            partner_id = pid
            break

    if not partner_id or not db:
        return None

    try:
        profile = db.get_game_profile(partner_id)
        if profile and profile.get("personality_type"):
            ptype = profile["personality_type"]
            label = PERSONALITY_LABELS.get(ptype, ptype)
            return {
                "partner_personality": ptype,
                "partner_label": label,
            }
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Navigator prompt section builder
# ---------------------------------------------------------------------------

def build_trust_prompt_section(ctx: dict) -> str:
    """Convert trust_context dict into a Navigator system prompt section.

    Designed to be injected into convergence.py's build_system_prompt().
    """
    if not ctx.get("has_data"):
        return ""

    lines: list[str] = ["[信任感知 — 长期记忆体]"]

    # Verified attestations
    verified = ctx.get("verified_attestations", [])
    if verified:
        claim_labels = {
            "match_mission": "星际匹配",
            "personality_type": "人格觉醒",
        }
        labels = [claim_labels.get(a["claim_key"], a["claim_key"]) for a in verified]
        lines.append(f"来访者已获得可信凭证：{'、'.join(labels)}。"
                     f"这些不是来访者自述——是经过共识验证的事实。")

    # Recent memories
    recent = ctx.get("recent_memories", [])
    if recent:
        lines.append("你记得来访者最近的探索足迹：")
        for r in recent[:5]:
            lines.append(f"- {r['summary']}")

    # Partner memory
    partner = ctx.get("partner_memory")
    if partner:
        ptype = partner.get("partner_label", partner.get("partner_personality", ""))
        lines.append(f"来访者上一次星际共识的搭档是{ptype}。"
                     f"这会影响你对来访者社交倾向的直觉判断。")

    # Credit check summary
    credit = ctx.get("credit_check_summary")
    if credit:
        companies = credit.get("companies", [])
        big = credit.get("big_capital_count", 0)
        total = credit.get("total_checks", 0)
        lines.append(f"来访者最近查询了{total}家企业的征信信息。")

        if companies:
            names = "、".join(companies[:5])
            lines.append(f"查询过的企业包括：{names}。")

        if big > 0:
            lines.append(f"其中有{big}家注册资本过亿——来访者可能正在关注大型平台。"
                         f"你可以微妙地在职业域对话中提及这一点。")

    lines.append("注意：这些记忆来自信任层长期记忆体。你可以自然引用它们，"
                 "但不直接说出'根据你的征信记录'之类的话。")

    return "\n".join(lines)
