from __future__ import annotations
import json, logging
from typing import Any
logger = logging.getLogger('looma.analytics')
ALLOWED_PROPERTY_KEYS = frozenset({'event_category','event_source','funnel_step','page','route','referrer','duration_ms','scroll_depth','click_count','user_tier','is_early_adopter','user_role','session_duration_min','visit_count','job_id','job_count','match_score_range','resume_format','resume_parse_duration_ms','personality_type','mbti_confidence','domain','narrative_step','session_id','enterprise_id','enterprise_plan','candidate_count','candidate_status','poem_id','poem_author','poem_dynasty','query_length','intent_label','response_time_ms','feedback_rating','feedback_sentiment','plan_name','price_yuan','payment_status','success','error_code','error_type','cached','retry_count'})
FORBIDDEN_PROPERTY_KEYS = frozenset({'email','user_email','phone','mobile','user_phone','name','user_name','real_name','contact_name','id_card','id_number','passport','ssn','address','home_address','ip_address','wechat_openid','openid','password','token','secret','api_key'})
def _validate_properties(props):
    if not props: return {}, []
    s = {}; r = []
    for k, v in props.items():
        lk = k.lower()
        if lk in FORBIDDEN_PROPERTY_KEYS: logger.warning(f'Analytics PII blocked: key={k}'); r.append(k); continue
        if k not in ALLOWED_PROPERTY_KEYS and lk not in ALLOWED_PROPERTY_KEYS: logger.warning(f'Analytics: key={k} not in whitelist'); r.append(k); continue
        if isinstance(v, str) and len(v) > 500: v = v[:500]
        s[k] = v
    return s, r
def log_event(event_name, user_id='', properties=None, *, db=None):
    props = properties or {}
    sp, rj = _validate_properties(props)
    if rj: logger.info(f'Analytics {event_name}: {len(rj)} rejected')
    if db:
        try:
            from datetime import datetime
            n = datetime.now().isoformat()
            with db.get_conn() as c:
                c.execute('INSERT INTO analytics_events (event_name,user_id,properties,created_at) VALUES (?,?,?,?)', (event_name, user_id or '', json.dumps(sp, ensure_ascii=False), n))
        except Exception as e: logger.error(f'Analytics persist failed: {e}')
    logger.debug(f'Analytics: {event_name}')
def track_funnel_step(uid, step, success=True, properties=None, *, db=None):
    p = {'funnel_step': step, 'success': success}
    if properties: p.update(properties)
    log_event('funnel_step', user_id=uid, properties=p, db=db)
def track_job_match(uid, job_count, match_score_range='', *, db=None):
    log_event('job_match_completed', user_id=uid, properties={'job_count': job_count, 'match_score_range': match_score_range}, db=db)
def track_resume_upload(uid, resume_format, parse_duration_ms=0, success=True, *, db=None):
    log_event('resume_uploaded', user_id=uid, properties={'resume_format': resume_format, 'resume_parse_duration_ms': parse_duration_ms, 'success': success}, db=db)
def track_feedback(uid, rating, query_length=0, intent_label='', response_time_ms=0, *, db=None):
    log_event('feedback_submitted', user_id=uid, properties={'feedback_rating': rating, 'query_length': query_length, 'intent_label': intent_label, 'response_time_ms': response_time_ms}, db=db)
