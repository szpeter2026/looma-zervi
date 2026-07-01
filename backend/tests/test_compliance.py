"""Tests for Compliance Gate modules."""
import pytest
from unittest.mock import MagicMock

from src.compliance.consent import ConsentManager, ALL_SCOPES
from src.compliance.redact import redact_pii, detect_pii
from src.compliance.audit import AuditLogger, _anonymize_ip


class TestConsentManager:
    def test_grant_new(self):
        db = MagicMock()
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = None
        db.get_conn.return_value.__enter__.return_value = conn
        cm = ConsentManager(db=db)
        r = cm.grant("user-1", "resume_upload")
        assert r["already_granted"] is False
        assert r["consent_id"]

    def test_grant_duplicate(self):
        db = MagicMock()
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = {"id": "ex1"}
        db.get_conn.return_value.__enter__.return_value = conn
        cm = ConsentManager(db=db)
        r = cm.grant("user-1", "resume_upload")
        assert r["already_granted"] is True

    def test_check_true(self):
        db = MagicMock()
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = {"id": "c1"}
        db.get_conn.return_value.__enter__.return_value = conn
        cm = ConsentManager(db=db)
        assert cm.check("user-1", "credit_query") is True

    def test_check_false_unknown_scope(self):
        cm = ConsentManager(db=MagicMock())
        assert cm.check("user-1", "invalid_scope") is False

    def test_all_scopes_count(self):
        assert len(ALL_SCOPES) == 9


class TestRedactPii:
    def test_redact_mobile(self):
        text = "联系我 13812345678 谢谢"
        safe, mapping = redact_pii(text)
        assert "13812345678" not in safe
        assert len(mapping) == 1

    def test_detect_pii(self):
        findings = detect_pii("身份证 110101199001011234")
        assert any(f["type"] == "cn_id_card" for f in findings)

    def test_redact_cn_name(self):
        text = "我叫张三，请帮我看看简历"
        safe, mapping = redact_pii(text)
        assert "张三" not in safe
        assert "PII_NAME_" in safe
        assert len(mapping) >= 1


class TestAuditLogger:
    def test_anonymize_ip(self):
        assert _anonymize_ip("192.168.1.100") == "192.168.1.0"

    def test_log_writes(self):
        db = MagicMock()
        conn = MagicMock()
        db.get_conn.return_value.__enter__.return_value = conn
        al = AuditLogger(db=db)
        eid = al.log(actor="u1", action="consent_grant", resource_type="consent")
        assert eid
        conn.execute.assert_called()
