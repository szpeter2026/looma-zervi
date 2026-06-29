"""
Game routes blueprint.
Ownership: Jason

Endpoints:
  POST /v1/game/profile-sync    - Sync personality result
  GET  /v1/game/profile         - Get game profile (personality + XP + level)
  POST /v1/game/mission-complete- Complete a mission, earn XP
  POST /v1/game/fleet/create    - Create a fleet
  POST /v1/game/fleet/join      - Join a fleet
  GET  /v1/game/fleet/mine      - Get my fleet
  POST /v1/game/fleet/leave     - Leave current fleet
"""
import math
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth

game_bp = Blueprint("game", __name__)


def _get_db():
    return current_app._db


# ── XP / Level helpers ──

def _calculate_level(xp: int) -> int:
    """Level formula: level = floor(sqrt(xp / 100)) + 1.
    Every 100 XP ≈ 1 level at low levels, slows naturally."""
    return int(math.sqrt(xp / 100)) + 1 if xp > 0 else 1


# ── Personality & Profile ──

@game_bp.route("/profile-sync", methods=["POST"])
@require_auth
def sync_personality():
    """Sync personality test result to looma backend."""
    data = request.get_json() or {}
    personality_type = data.get("personality_type", "")
    personality_detail = data.get("personality_detail", "")

    if not personality_type:
        return jsonify(error="bad_request", message="personality_type required"), 400

    db = _get_db()
    db.upsert_game_profile(g.user_id, personality_type, personality_detail)

    # Return the full profile after sync (so frontend gets XP/level too)
    profile = db.get_game_profile(g.user_id)
    return jsonify(
        message="profile synced",
        personality_type=personality_type,
        xp=profile["xp"],
        level=profile["level"],
    )


@game_bp.route("/profile", methods=["GET"])
@require_auth
def get_game_profile():
    """Get current user's game profile (personality + XP + level)."""
    db = _get_db()
    profile = db.get_game_profile(g.user_id)
    if not profile:
        return jsonify(error="not_found", message="no game profile yet"), 404

    # Compute current level from XP (level column may be stale)
    computed_level = _calculate_level(profile["xp"])
    if computed_level != profile["level"]:
        db.update_level(g.user_id, computed_level)
        profile["level"] = computed_level

    # Count completed missions
    missions = db.get_user_missions(g.user_id)
    total_mission_xp = sum(m["xp_reward"] for m in missions)

    return jsonify(
        id=profile["id"],
        user_id=profile["user_id"],
        personality_type=profile["personality_type"],
        personality_detail=profile["personality_detail"],
        xp=profile["xp"],
        level=profile["level"],
        missions_completed=len(missions),
        total_mission_xp=total_mission_xp,
        updated_at=profile["updated_at"],
    )


# ── Mission ──

@game_bp.route("/mission-complete", methods=["POST"])
@require_auth
def complete_mission():
    """Complete a mission and earn XP. No double-completion allowed."""
    data = request.get_json() or {}
    mission_id = data.get("mission_id", "")
    xp_reward = int(data.get("xp_reward", 10))

    if not mission_id:
        return jsonify(error="bad_request", message="mission_id required"), 400

    if xp_reward < 0:
        return jsonify(error="bad_request", message="xp_reward must be non-negative"), 400

    db = _get_db()

    # Ensure user has a game profile (create stub if none)
    profile = db.get_game_profile(g.user_id)
    if not profile:
        db.upsert_game_profile(g.user_id, "", "")
        profile = db.get_game_profile(g.user_id)

    completion_id, was_new = db.complete_mission(g.user_id, mission_id, xp_reward)

    if not was_new:
        return jsonify(
            error="already_completed",
            message=f"Mission {mission_id} already completed",
        ), 409

    # Refresh profile to get updated XP
    profile = db.get_game_profile(g.user_id)
    new_level = _calculate_level(profile["xp"])
    if new_level != profile["level"]:
        db.update_level(g.user_id, new_level)

    return jsonify(
        message="mission completed",
        mission_id=mission_id,
        xp_earned=xp_reward,
        total_xp=profile["xp"] + xp_reward,
        level=_calculate_level(profile["xp"] + xp_reward),
    )


# ── Fleet ──

@game_bp.route("/fleet/create", methods=["POST"])
@require_auth
def create_fleet():
    """Create a new fleet. Creator becomes captain + auto-joins."""
    data = request.get_json() or {}
    name = data.get("name", "")
    description = data.get("description", "")

    if not name:
        return jsonify(error="bad_request", message="fleet name required"), 400

    if len(name) > 50:
        return jsonify(error="bad_request", message="fleet name too long (max 50)"), 400

    db = _get_db()

    # Check user not already in a fleet (MVP: one fleet per user)
    existing_fleet = db.get_user_fleet(g.user_id)
    if existing_fleet:
        return jsonify(
            error="already_in_fleet",
            message=f"User already in fleet '{existing_fleet['name']}'",
            fleet_id=existing_fleet["id"],
        ), 409

    fleet_id = db.create_fleet(g.user_id, name, description)
    fleet = db.get_fleet_by_id(fleet_id)
    members = db.get_fleet_members(fleet_id)

    return jsonify(
        id=fleet["id"],
        name=fleet["name"],
        captain_id=fleet["captain_id"],
        description=fleet["description"],
        member_count=len(members),
        created_at=fleet["created_at"],
    ), 201


@game_bp.route("/fleet/join", methods=["POST"])
@require_auth
def join_fleet():
    """Join an existing fleet."""
    data = request.get_json() or {}
    fleet_id = data.get("fleet_id", "")

    if not fleet_id:
        return jsonify(error="bad_request", message="fleet_id required"), 400

    db = _get_db()

    try:
        db.join_fleet(fleet_id, g.user_id)
    except ValueError as e:
        msg = str(e)
        if "does not exist" in msg:
            return jsonify(error="not_found", message=msg), 404
        if "already in fleet" in msg:
            existing = db.get_user_fleet(g.user_id)
            return jsonify(
                error="already_in_fleet",
                message=msg,
                current_fleet_id=existing["id"] if existing else None,
            ), 409
        return jsonify(error="bad_request", message=msg), 400

    fleet = db.get_fleet_by_id(fleet_id)
    members = db.get_fleet_members(fleet_id)

    return jsonify(
        message="joined fleet",
        fleet_id=fleet_id,
        fleet_name=fleet["name"],
        captain_id=fleet["captain_id"],
        member_count=len(members),
    )


@game_bp.route("/fleet/mine", methods=["GET"])
@require_auth
def my_fleet():
    """Get the fleet the current user belongs to, with member list."""
    db = _get_db()
    fleet = db.get_user_fleet(g.user_id)

    if not fleet:
        return jsonify(fleet=None, message="not in any fleet"), 200

    members = db.get_fleet_members(fleet["id"])

    return jsonify(
        fleet=dict(fleet),
        members=members,
        member_count=len(members),
    )


@game_bp.route("/fleet/leave", methods=["POST"])
@require_auth
def leave_fleet():
    """Leave current fleet. Captain cannot leave — must dissolve."""
    db = _get_db()

    try:
        db.leave_fleet(g.user_id)
    except ValueError as e:
        msg = str(e)
        if "Captain cannot leave" in msg:
            return jsonify(
                error="captain_cannot_leave",
                message="As captain, you must dissolve the fleet instead of leaving",
            ), 403
        return jsonify(error="bad_request", message=msg), 400

    return jsonify(message="left fleet")
