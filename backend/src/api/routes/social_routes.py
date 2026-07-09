"""
社交图谱 API 路由 — 六度分隔算法的 looma-zervi 集成端点

新增端点（挂到 referral_bp 或独立 social_bp）：
  GET  /v1/social/connection/<user_id>     - 查找当前用户到目标的最短推荐链
  GET  /v1/social/degrees/<user_id>        - 计算分隔度数 + 信任度评分
  GET  /v1/social/reachable                - 统计当前用户 N 步内可达的用户
  GET  /v1/social/network-stats            - 网络拓扑分析（Admin only）

所有端点复用现有 JWT 认证，不新建表，纯读现有数据。
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth
from src.social.graph_builder import build_social_graph, get_graph_stats
from src.social.social_bfs import (
    bfs_shortest_path,
    compute_degrees_of_separation,
    compute_trust_score,
    bfs_reachable_users,
    compute_network_stats,
)

social_bp = Blueprint("social", __name__)


def _get_graph():
    """构建社交图谱（每次请求重建，数据量小时可接受）。
    生产环境可加缓存（TTL 5 分钟）。
    """
    db = current_app._db
    return build_social_graph(db)


def _get_user_display_name(db, user_id: str) -> str:
    """获取用户显示名"""
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        return "未知用户"
    name = row["name"] or ""
    email = row["email"] or ""
    if name:
        return name
    if email and "@" in email:
        return email.split("@")[0]
    return "用户"


@social_bp.route("/connection/<user_id>", methods=["GET"])
@require_auth
def find_connection(user_id: str):
    """查找当前用户到目标用户的最短社交路径（推荐链）。

    Query params:
      max_depth: 最大搜索深度（默认 6）

    Returns:
      path: [user_id, ...] 最短路径
      degrees: 分隔度数
      chain: [{step, user_id, display_name, role}, ...] 详细链
      trust_score: 信任度评分 (0-100)
    """
    target_id = user_id
    max_depth = int(request.args.get("max_depth", 6))

    if target_id == g.user_id:
        return jsonify(degrees=0, path=[g.user_id], chain=[], trust_score=100,
                       message="这是你自己")

    adj = _get_graph()

    # 限制 BFS 深度
    # 重建受限图（只到 max_depth）
    distances = bfs_reachable_users(adj, g.user_id, max_depth)
    if target_id not in distances:
        return jsonify(
            connected=False,
            degrees=-1,
            trust_score=0,
            message=f"在 {max_depth} 度分隔内无法建立连接"
        ), 404

    # 找最短路径
    path = bfs_shortest_path(adj, g.user_id, target_id)
    if path is None:
        return jsonify(connected=False, degrees=-1, trust_score=0), 404

    degrees = len(path) - 1
    trust_score = compute_trust_score(degrees)

    # 构建详细链
    db = current_app._db
    chain = []
    for i, uid in enumerate(path):
        chain.append({
            "step": i,
            "user_id": uid,
            "display_name": _get_user_display_name(db, uid),
            "role": "起点" if i == 0 else ("终点" if i == len(path) - 1 else f"中间人 {i}")
        })

    return jsonify(
        connected=True,
        degrees=degrees,
        path=path,
        chain=chain,
        trust_score=trust_score,
        message=f"通过 {degrees} 个中间人建立连接" if degrees > 0 else "直接连接"
    )


@social_bp.route("/degrees/<user_id>", methods=["GET"])
@require_auth
def get_degrees(user_id: str):
    """计算当前用户与目标用户的分隔度数和信任度评分。"""
    target_id = user_id

    if target_id == g.user_id:
        return jsonify(degrees=0, trust_score=100, connected=True)

    adj = _get_graph()
    degrees = compute_degrees_of_separation(adj, g.user_id, target_id)
    trust_score = compute_trust_score(degrees)

    return jsonify(
        degrees=degrees,
        trust_score=trust_score,
        connected=degrees >= 0,
        message="已连接" if degrees >= 0 else "无法建立连接"
    )


@social_bp.route("/reachable", methods=["GET"])
@require_auth
def get_reachable():
    """统计当前用户在 N 步内可达的用户数量。

    Query params:
      max_depth: 最大深度（默认 6）
    """
    max_depth = int(request.args.get("max_depth", 6))
    adj = _get_graph()

    distances = bfs_reachable_users(adj, g.user_id, max_depth)

    # 按度数分组统计
    by_degree = {}
    for uid, dist in distances.items():
        if uid == g.user_id:
            continue
        by_degree.setdefault(dist, 0)
        by_degree[dist] += 1

    total_reachable = sum(by_degree.values())
    total_users = len(adj)

    return jsonify(
        max_depth=max_depth,
        total_reachable=total_reachable,
        total_users=total_users,
        reach_percentage=round(total_reachable / max(total_users - 1, 1) * 100, 1),
        by_degree={str(k): v for k, v in sorted(by_degree.items())},
    )


@social_bp.route("/network-stats", methods=["GET"])
@require_auth
def network_stats():
    """网络拓扑分析（Admin only）。

    返回平均路径长度、Hub 节点排名、6步可达比例等。
    require_auth 已设置 g.user_role。
    """
    if getattr(g, "user_role", "user") != "admin":
        return jsonify(error="forbidden", message="需要管理员权限"), 403

    adj = _get_graph()
    stats = compute_network_stats(adj)
    graph_info = get_graph_stats(adj)

    return jsonify(network=stats, graph=graph_info)
