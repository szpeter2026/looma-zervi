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
"""
import uuid
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth

game_bp = Blueprint("game", __name__)


def _get_db():
    return current_app._db


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
    return jsonify(message="profile synced", personality_type=personality_type)


@game_bp.route("/profile", methods=["GET"])
@require_auth
def get_game_profile():
    """Get current user's game profile."""
    db = _get_db()
    profile = db.get_game_profile(g.user_id)
    if not profile:
        return jsonify(error="not_found", message="no game profile yet"), 404
    return jsonify(**profile)


@game_bp.route("/mission-complete", methods=["POST"])
@require_auth
def complete_mission():
    """Complete a mission and earn XP."""
    data = request.get_json() or {}
    mission_id = data.get("mission_id", "")
    xp_reward = data.get("xp_reward", 10)

    if not mission_id:
        return jsonify(error="bad_request", message="mission_id required"), 400

    db = _get_db()
    # TODO: implement mission_completions table operations in manager.py
    return jsonify(message="mission completed", xp_earned=xp_reward)


@game_bp.route("/fleet/create", methods=["POST"])
@require_auth
def create_fleet():
    """Create a new fleet."""
    data = request.get_json() or {}
    name = data.get("name", "")
    description = data.get("description", "")

    if not name:
        return jsonify(error="bad_request", message="fleet name required"), 400

    # TODO: implement fleet operations in manager.py
    fleet_id = str(uuid.uuid4())
    return jsonify(id=fleet_id, name=name, captain_id=g.user_id), 201


@game_bp.route("/fleet/join", methods=["POST"])
@require_auth
def join_fleet():
    """Join an existing fleet."""
    data = request.get_json() or {}
    fleet_id = data.get("fleet_id", "")

    if not fleet_id:
        return jsonify(error="bad_request", message="fleet_id required"), 400

    # TODO: implement fleet join logic in manager.py
    return jsonify(message="joined fleet", fleet_id=fleet_id)


@game_bp.route("/fleet/mine", methods=["GET"])
@require_auth
def my_fleet():
    """Get the fleet the current user belongs to."""
    # TODO: implement fleet lookup in manager.py
    return jsonify(fleet=None)
