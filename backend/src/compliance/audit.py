from __future__ import annotations
import json, logging, uuid
from datetime import datetime
from flask import g, current_app
logger = logging.getLogger('looma.compliance.audit')

def _now_iso(): return datetime.now().isoformat()

class AuditLogger:
    def __init__(self, db=None): self._db = db
    @property
    def db(self):
        if self._db is not None:
            return self._db
        try:
            return getattr(current_app, '_db', None) or getattr(g, '_db', None)
        except RuntimeError:
            return None
    def log(self, *, actor, action, resource_type, resource_id='', consent_id='', metadata=None, ip='', user_agent=''):
        db = self.db
        if not db: return ''
        eid = str(uuid.uuid4())
        now = _now_iso()
        sip = _anonymize_ip(ip) if ip else ''
        ua = (user_agent or '')[:256]
        mj = json.dumps(metadata or {}, ensure_ascii=False)
        with db.get_conn() as c:
            c.execute('INSERT INTO audit_logs (id,actor,action,resource_type,resource_id,consent_id,metadata,ip,user_agent,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)', (eid,actor,action,resource_type,resource_id,consent_id,mj,sip,ua,now))
        return eid
    def log_from_request(self, actor, action, resource_type, resource_id='', metadata=None):
        from flask import request
        return self.log(actor=actor,action=action,resource_type=resource_type,resource_id=resource_id,consent_id=getattr(g,'compliance_consent_id',''),metadata=metadata,ip=request.remote_addr or '',user_agent=request.headers.get('User-Agent',''))
    def query(self, actor='', action='', resource_type='', resource_id='', limit=50, offset=0):
        db = self.db
        if not db: return []
        cs, ps = [], []
        if actor: cs.append('actor=?'); ps.append(actor)
        if action: cs.append('action=?'); ps.append(action)
        if resource_type: cs.append('resource_type=?'); ps.append(resource_type)
        if resource_id: cs.append('resource_id=?'); ps.append(resource_id)
        w = ' AND '.join(cs) if cs else '1=1'
        with db.get_conn() as c:
            rs = c.execute(f'SELECT id,actor,action,resource_type,resource_id,consent_id,metadata,ip,created_at FROM audit_logs WHERE {w} ORDER BY created_at DESC LIMIT ? OFFSET ?', ps+[limit,offset]).fetchall()
        return [dict(r) for r in rs]

def _anonymize_ip(ip):
    p = ip.split('.')
    if len(p)==4 and all(x.isdigit() for x in p): return f'{p[0]}.{p[1]}.{p[2]}.0'
    return ''

_al = None
def get_audit_logger(db=None):
    global _al
    if _al is None: _al = AuditLogger(db=db)
    elif db and not _al._db: _al._db = db
    return _al
def reset_audit_logger():
    global _al; _al = None
