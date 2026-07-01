from __future__ import annotations
import logging
from flask import Blueprint, request, jsonify, g, current_app
from src.analytics.events import log_event, _validate_properties
logger = logging.getLogger('looma.analytics.routes')
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/event', methods=['POST'])
def submit_event():
    body = request.get_json(silent=True) or {}
    event_name = (body.get('event_name') or '').strip()
    if not event_name: return jsonify(error='missing_event_name', message='请提供 event_name'), 400
    user_id = getattr(g, 'user_id', '')
    props = body.get('properties') or {}
    safe_props, rejected = _validate_properties(props)
    db = getattr(current_app, '_db', None)
    log_event(event_name, user_id=user_id, properties=safe_props, db=db)
    resp = {'status': 'logged', 'event_name': event_name}
    if rejected: resp['rejected_keys'] = rejected
    return jsonify(resp), 201
