"""
Trust layer tests — consensus → memory_record → rule attestation.
Run: pytest tests/test_trust.py -v
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def app():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    os.environ["DATABASE_PATH"] = tmp.name
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-local-testing-only-2026"
    os.environ["SECRET_KEY"] = "test-flask-secret"
    from src.app import create_app
    _app = create_app("testing")
    yield _app
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, email, name):
    resp = client.post("/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "name": name,
    })
    data = resp.get_json()
    return data["access_token"], data["user"]["id"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _setup_fleet_match(client, token_a, token_b):
    client.post(
        "/v1/game/profile-sync",
        headers=_headers(token_a),
        json={"personality_type": "星云艺术家"},
    )
    client.post(
        "/v1/game/profile-sync",
        headers=_headers(token_b),
        json={"personality_type": "黑洞程序员"},
    )
    fleet = client.post(
        "/v1/game/fleet/create",
        headers=_headers(token_a),
        json={"name": "Trust Fleet"},
    ).get_json()
    client.post(
        "/v1/game/fleet/join",
        headers=_headers(token_b),
        json={"fleet_id": fleet["id"]},
    )
    return client.post("/v1/game/match", headers=_headers(token_a), json={})


def test_consensus_flow_memory_and_attestation(client):
    token_a, uid_a = _register(client, "trust_a@test.com", "Initiator")
    token_b, uid_b = _register(client, "trust_b@test.com", "Candidate")

    match_resp = _setup_fleet_match(client, token_a, token_b)
    assert match_resp.status_code == 200
    match_data = match_resp.get_json()
    assert match_data["consensus_status"] == "consensus_passed"
    assert match_data["can_complete_mission"] is False
    assert match_data["pending_consensus_id"]

    blocked = client.post(
        "/v1/game/mission-complete",
        headers=_headers(token_a),
        json={"mission_id": "match", "xp_reward": 40},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["error"] == "consensus_required"

    ack = client.post(
        "/v1/game/match/acknowledge",
        headers=_headers(token_b),
        json={"consensus_id": match_data["pending_consensus_id"], "action": "accept"},
    )
    assert ack.status_code == 200
    ack_data = ack.get_json()
    assert ack_data["status"] == "verified"
    assert ack_data["trust"]["memory_id"]
    assert ack_data["trust"]["claim_key"] == "match_mission"

    memory_id = ack_data["trust"]["memory_id"]

    mem = client.get(f"/v1/trust/memories/{memory_id}", headers=_headers(token_a))
    assert mem.status_code == 200
    mem_data = mem.get_json()
    assert mem_data["intersection_type"] == "consensus_exchange"
    assert uid_a in mem_data["participants"]
    assert uid_b in mem_data["participants"]

    claim = client.get("/v1/trust/claims/match_mission", headers=_headers(token_a))
    assert claim.status_code == 200
    claim_data = claim.get_json()
    assert claim_data["attestation"]["status"] == "verified"
    assert claim_data["attestation"]["validator"] == "rule_v0"
    assert memory_id in claim_data["attestation"]["evidence_memory_ids"]

    done = client.post(
        "/v1/game/mission-complete",
        headers=_headers(token_a),
        json={"mission_id": "match", "xp_reward": 40},
    )
    assert done.status_code == 200

    match2 = client.post("/v1/game/match", headers=_headers(token_a), json={})
    assert match2.get_json()["consensus_status"] == "consensus_verified"
    assert match2.get_json()["can_complete_mission"] is True


def test_acknowledge_wrong_user_forbidden(client):
    token_a, _ = _register(client, "wrong_a@test.com", "A")
    token_b, _ = _register(client, "wrong_b@test.com", "B")
    token_c, _ = _register(client, "wrong_c@test.com", "C")

    match_resp = _setup_fleet_match(client, token_a, token_b)
    consensus_id = match_resp.get_json()["pending_consensus_id"]

    resp = client.post(
        "/v1/game/match/acknowledge",
        headers=_headers(token_c),
        json={"consensus_id": consensus_id, "action": "accept"},
    )
    assert resp.status_code == 404
