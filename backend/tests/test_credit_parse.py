"""Unit tests for credit JSON extraction / QCC error sanitization."""
from src.api.routes.credit_routes import _extract_json_object, _sanitize_qcc_error
from src.credit.qcc_client import QccMcpError


def test_extract_json_object_pure():
    data = _extract_json_object(
        '{"entity_name":"腾讯","report_type":"评估","summary":"存续"}'
    )
    assert data["entity_name"] == "腾讯"


def test_extract_json_object_from_prose_and_fence():
    prose = (
        "嗨，我是星际导航员。以下是结果：\n"
        "```json\n"
        '{"entity_name":"字节跳动","report_type":"经营风险评估","summary":"正常经营"}\n'
        "```\n"
        "还想继续探索吗？"
    )
    data = _extract_json_object(prose)
    assert data is not None
    assert data["entity_name"] == "字节跳动"
    assert "summary" in data


def test_extract_json_object_embedded_braces():
    text = '说明如下 {"entity_name":"阿里","report_type":"摘要","summary":"稳定"} 结束'
    data = _extract_json_object(text)
    assert data["entity_name"] == "阿里"


def test_sanitize_qcc_error_classes():
    assert _sanitize_qcc_error(QccMcpError("QCC_AUTH_TOKEN 未配置或为空")) == "token_missing"
    assert _sanitize_qcc_error(Exception("401 Unauthorized")) == "unauthorized"
    assert _sanitize_qcc_error(Exception("SSE connect failed")) == "unreachable"
    assert _sanitize_qcc_error(Exception("Read timeout")) == "timeout"
