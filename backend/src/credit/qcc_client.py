"""
QCC (企查查) MCP Client — Official enterprise credit data source.

Integrates 9 QCC MCP services via SSE-based JSON-RPC 2.0:
  - qcc-company      : 企业工商信息
  - qcc-risk         : 企业风险信息
  - qcc-ipr          : 知识产权
  - qcc-operation    : 经营状况
  - qcc-executive    : 高管/法人信息
  - qcc-history      : 历史变更
  - qcc-legal-regulation : 法律法规
  - qcc-legal-case   : 司法案件
  - qcc-document     : 企业文书

Protocol: MCP over SSE (Server-Sent Events) via JSON-RPC 2.0.
Each service endpoint serves both the SSE stream and JSON-RPC calls.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

logger = logging.getLogger("looma.qcc_client")

# ── Configuration ──────────────────────────────────────────────────────────

QCC_BASE_URLS: dict[str, str] = {
    "company":       "https://agent.qcc.com/mcp/company/stream",
    "risk":          "https://agent.qcc.com/mcp/risk/stream",
    "ipr":           "https://agent.qcc.com/mcp/ipr/stream",
    "operation":     "https://agent.qcc.com/mcp/operation/stream",
    "executive":     "https://agent.qcc.com/mcp/executive/stream",
    "history":       "https://agent.qcc.com/mcp/history/stream",
    "legal_regulation": "https://agent.qcc.com/mcp/regulation/stream",
    "legal_case":    "https://agent.qcc.com/mcp/case/stream",
    "document":      "https://agent.qcc.com/mcp/document/stream",
}

QCC_AUTH_TOKEN = os.getenv("QCC_AUTH_TOKEN", "")

QCC_TIMEOUT = 30.0  # seconds per call
QCC_MAX_RETRIES = 2

# ── Data types ─────────────────────────────────────────────────────────────

@dataclass
class QccCompanyInfo:
    """Parsed company basic info from QCC company service."""
    company_name: str = ""
    legal_person: str = ""
    registered_capital: str = ""
    established_date: str = ""
    credit_code: str = ""
    status: str = ""
    industry: str = ""
    address: str = ""
    business_scope: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class QccRiskInfo:
    """Parsed risk info from QCC risk service."""
    risk_level: str = ""          # e.g. "低风险" / "中风险" / "高风险"
    risk_items: list[dict[str, str]] = field(default_factory=list)
    summary: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class QccOperationInfo:
    """Parsed operation / business data from QCC operation service."""
    annual_reports: list[dict[str, str]] = field(default_factory=list)
    key_financials: dict[str, str] = field(default_factory=dict)
    summary: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class QccCreditReport:
    """Aggregated enterprise credit report."""
    company: QccCompanyInfo = field(default_factory=QccCompanyInfo)
    risk: QccRiskInfo = field(default_factory=QccRiskInfo)
    operation: QccOperationInfo = field(default_factory=QccOperationInfo)
    executives: list[dict[str, str]] = field(default_factory=list)
    ipr: list[dict[str, str]] = field(default_factory=list)
    history: list[dict[str, str]] = field(default_factory=list)
    legal_cases: list[dict[str, str]] = field(default_factory=list)
    documents: list[dict[str, str]] = field(default_factory=list)
    source: str = "qcc"  # official data source marker


# ── MCP SSE Client ─────────────────────────────────────────────────────────

class QccMcpError(Exception):
    """QCC MCP service error."""
    pass


class QccMcpSession:
    """Lightweight MCP SSE client for a single QCC service endpoint.

    MCP over SSE flow:
    1. GET /stream → establish SSE connection, receive sessionId via endpoint event
    2. POST /stream?sessionId=... with JSON-RPC initialize
    3. POST /stream?sessionId=... with JSON-RPC tools/list
    4. POST /stream?sessionId=... with JSON-RPC tools/call
    """

    def __init__(self, service_name: str, url: str, auth_token: str, timeout: float = QCC_TIMEOUT):
        self.service_name = service_name
        self.url = url
        self.auth_token = auth_token
        self.timeout = timeout
        self._session_id: Optional[str] = None
        self._tools: list[dict] = []
        self._initialized = False
        self._lock = threading.Lock()

    # ── Session management ──

    def connect(self) -> str:
        """Establish SSE connection and retrieve session ID.

        Returns the session ID string.
        """
        if self._session_id:
            return self._session_id

        headers = {
            "Authorization": self.auth_token,
            "Accept": "text/event-stream",
        }

        try:
            resp = requests.get(self.url, headers=headers, timeout=self.timeout, stream=True)
            resp.raise_for_status()

            # Read SSE events until we get the endpoint/sessionId event
            session_id = None
            buffer = ""
            for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                if chunk is None:
                    continue
                text = chunk if isinstance(chunk, str) else chunk.decode("utf-8", errors="replace")
                buffer += text

                # Parse SSE events from buffer
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    for line in event_str.split("\n"):
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            # MCP SSE may deliver session in endpoint event
                            if isinstance(data, dict) and "sessionId" in data:
                                session_id = data["sessionId"]
                                break
                    if session_id:
                        break
                if session_id:
                    break

            resp.close()

            if not session_id:
                # Fallback: try to extract sessionId from response headers
                session_id = resp.headers.get("X-Session-Id") or resp.headers.get("Mcp-Session-Id")

            if not session_id:
                raise QccMcpError(f"[{self.service_name}] Failed to obtain SSE session ID")

            self._session_id = session_id
            logger.info(f"[{self.service_name}] SSE session established: {session_id[:12]}...")
            return session_id

        except requests.RequestException as e:
            raise QccMcpError(f"[{self.service_name}] SSE connect failed: {e}") from e

    def _rpc_call(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC 2.0 call via POST and return the result.

        MCP uses POST to the same URL with query param ?sessionId=xxx.
        The response is SSE-streamed but for JSON-RPC the result is in
        the SSE data field.
        """
        if not self._session_id:
            self.connect()

        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {},
        }

        post_url = f"{self.url}?sessionId={self._session_id}"
        headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json",
        }

        for attempt in range(QCC_MAX_RETRIES + 1):
            try:
                resp = requests.post(
                    post_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                resp.raise_for_status()

                content_type = resp.headers.get("Content-Type", "")

                # If JSON response directly
                if "application/json" in content_type:
                    result = resp.json()
                    if "error" in result:
                        raise QccMcpError(
                            f"[{self.service_name}] RPC error: {result['error'].get('message', str(result['error']))}"
                        )
                    return result.get("result", result)

                # If SSE response, parse the data
                if "text/event-stream" in content_type:
                    text = resp.text
                    # Extract data from SSE
                    for line in text.split("\n"):
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                if isinstance(data, dict):
                                    if "error" in data:
                                        raise QccMcpError(
                                            f"[{self.service_name}] RPC error: {data['error'].get('message', str(data['error']))}"
                                        )
                                    if "result" in data:
                                        return data["result"]
                                    return data
                            except json.JSONDecodeError:
                                continue

                # Fallback: try JSON parse of entire body
                try:
                    result = resp.json()
                    if "error" in result:
                        raise QccMcpError(
                            f"[{self.service_name}] RPC error: {result['error'].get('message', str(result['error']))}"
                        )
                    return result.get("result", result)
                except (json.JSONDecodeError, ValueError):
                    pass

                # Return raw text as fallback
                return {"_raw": text}

            except requests.RequestException as e:
                if attempt < QCC_MAX_RETRIES:
                    logger.warning(f"[{self.service_name}] RPC retry {attempt + 1}/{QCC_MAX_RETRIES}: {e}")
                    time.sleep(1)
                    # Re-establish session on retry
                    self._session_id = None
                    self.connect()
                    continue
                raise QccMcpError(f"[{self.service_name}] RPC call '{method}' failed: {e}") from e

        raise QccMcpError(f"[{self.service_name}] RPC call '{method}' exceeded max retries")

    # ── MCP Protocol Methods ──

    def initialize(self) -> dict:
        """Send MCP initialize request."""
        return self._rpc_call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "looma-zervi",
                "version": "1.0.0",
            },
        })

    def list_tools(self) -> list[dict]:
        """List available tools on this service."""
        if self._tools:
            return self._tools
        result = self._rpc_call("tools/list")
        tools = result.get("tools", []) if isinstance(result, dict) else []
        self._tools = tools
        logger.info(f"[{self.service_name}] Available tools: {[t.get('name') for t in tools]}")
        return tools

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Call a specific tool with arguments."""
        return self._rpc_call("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })


# ── Session Manager ────────────────────────────────────────────────────────

class QccSessionManager:
    """Manages lazy-initialized MCP sessions for all QCC services."""

    def __init__(self, auth_token: str = QCC_AUTH_TOKEN):
        self.auth_token = auth_token
        self._sessions: dict[str, QccMcpSession] = {}
        self._lock = threading.Lock()

    def _get_session(self, service: str) -> QccMcpSession:
        if service not in QCC_BASE_URLS:
            raise QccMcpError(f"Unknown QCC service: {service}")
        with self._lock:
            if service not in self._sessions:
                self._sessions[service] = QccMcpSession(
                    service_name=service,
                    url=QCC_BASE_URLS[service],
                    auth_token=self.auth_token,
                )
            return self._sessions[service]

    def call_tool(self, service: str, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Convenience: call a tool on a named service."""
        session = self._get_session(service)
        return session.call_tool(tool_name, arguments)

    def get_tools(self, service: str) -> list[dict]:
        """Get available tools for a service."""
        session = self._get_session(service)
        return session.list_tools()

    def close_all(self):
        """Release all sessions."""
        with self._lock:
            self._sessions.clear()


# ── High-level API ─────────────────────────────────────────────────────────

# Global session manager (lazy init)
_session_manager: Optional[QccSessionManager] = None


def _get_manager() -> QccSessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = QccSessionManager()
    return _session_manager


def _find_search_tool(session: QccMcpSession) -> dict | None:
    """Find the best search/query tool from a service's tool list."""
    tools = session.list_tools()
    # Priority: tools with 'search' or 'query' in name, or the first tool
    for t in tools:
        name = t.get("name", "").lower()
        if "search" in name or "query" in name or "get" in name:
            return t
    return tools[0] if tools else None


def _search_company_by_name(company_name: str) -> dict:
    """Search company basic info via qcc-company service."""
    mgr = _get_manager()
    session = mgr._get_session("company")

    tool = _find_search_tool(session)
    if not tool:
        raise QccMcpError("[company] No search tool available")

    tool_name = tool["name"]
    # Build arguments based on tool's input schema
    input_schema = tool.get("inputSchema", {})
    props = input_schema.get("properties", {})

    args: dict[str, Any] = {}
    if "companyName" in props or "company_name" in props:
        key = "companyName" if "companyName" in props else "company_name"
        args[key] = company_name
    elif "keyword" in props:
        args["keyword"] = company_name
    elif "name" in props:
        args["name"] = company_name
    else:
        # Generic fallback: pass company name as first recognized param
        args = {"keyword": company_name}

    return session.call_tool(tool_name, args)


def _parse_company_result(result: dict) -> QccCompanyInfo:
    """Parse raw QCC company result into structured QccCompanyInfo."""
    # Handle nested content from MCP tool responses
    content = result
    if isinstance(result, dict):
        # MCP tools/call returns content array
        if "content" in result:
            items = result["content"]
            if isinstance(items, list) and items:
                for item in items:
                    if isinstance(item, dict) and item.get("type") == "text":
                        try:
                            content = json.loads(item.get("text", "{}"))
                        except json.JSONDecodeError:
                            content = {"raw_text": item.get("text", "")}
                        break
                    elif isinstance(item, dict):
                        content = item
                        break

    if not isinstance(content, dict):
        content = {}

    return QccCompanyInfo(
        company_name=content.get("companyName") or content.get("company_name") or content.get("name", ""),
        legal_person=content.get("legalPerson") or content.get("legal_person") or content.get("legalPersonName", ""),
        registered_capital=content.get("registeredCapital") or content.get("registered_capital") or content.get("regCapital", ""),
        established_date=content.get("establishedDate") or content.get("established_date") or content.get("estiblishTime", ""),
        credit_code=content.get("creditCode") or content.get("credit_code") or content.get("unifiedSocialCreditCode", ""),
        status=content.get("status") or content.get("companyStatus") or content.get("regStatus", ""),
        industry=content.get("industry") or content.get("industryName", ""),
        address=content.get("address") or content.get("regLocation", ""),
        business_scope=content.get("businessScope") or content.get("scope", ""),
        raw=content,
    )


def _search_risk(company_name: str) -> QccRiskInfo:
    """Search company risk info via qcc-risk service."""
    mgr = _get_manager()
    session = mgr._get_session("risk")
    tool = _find_search_tool(session)
    if not tool:
        raise QccMcpError("[risk] No search tool available")

    tool_name = tool["name"]
    result = session.call_tool(tool_name, _build_search_args(tool, company_name))

    # Parse content
    items = _extract_content(result)
    return QccRiskInfo(
        risk_level=_extract_risk_level(items),
        risk_items=items if isinstance(items, list) else [],
        summary=_generate_risk_summary(items),
        raw=result,
    )


def _search_operation(company_name: str) -> QccOperationInfo:
    """Search company operation/business data via qcc-operation service."""
    mgr = _get_manager()
    session = mgr._get_session("operation")
    tool = _find_search_tool(session)
    if not tool:
        raise QccMcpError("[operation] No search tool available")

    tool_name = tool["name"]
    result = session.call_tool(tool_name, _build_search_args(tool, company_name))

    items = _extract_content(result)
    return QccOperationInfo(
        summary=_generate_operation_summary(items),
        raw=result,
    )


def _search_service(service_name: str, company_name: str) -> list[dict]:
    """Generic search on any QCC service, returns list of result dicts."""
    mgr = _get_manager()
    session = mgr._get_session(service_name)
    tool = _find_search_tool(session)
    if not tool:
        logger.warning(f"[{service_name}] No search tool available")
        return []

    tool_name = tool["name"]
    result = session.call_tool(tool_name, _build_search_args(tool, company_name))
    items = _extract_content(result)
    return items if isinstance(items, list) else [items] if items else []


# ── Helpers ────────────────────────────────────────────────────────────────

def _build_search_args(tool: dict, company_name: str) -> dict[str, Any]:
    """Build search arguments matching the tool's input schema."""
    input_schema = tool.get("inputSchema", {})
    props = input_schema.get("properties", {})

    args: dict[str, Any] = {}
    for key in ("companyName", "company_name", "keyword", "name", "enterpriseName"):
        if key in props:
            args[key] = company_name
            return args

    # Fallback
    args["keyword"] = company_name
    return args


def _extract_content(result: dict) -> Any:
    """Extract structured content from MCP tool/call result."""
    if not isinstance(result, dict):
        return result

    if "content" in result:
        items = result["content"]
        if isinstance(items, list):
            parsed = []
            for item in items:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        parsed.append(json.loads(item.get("text", "{}")))
                    except json.JSONDecodeError:
                        parsed.append({"text": item.get("text", "")})
                elif isinstance(item, dict):
                    parsed.append(item)
            return parsed if parsed else items
        return items

    return result


def _extract_risk_level(items: Any) -> str:
    """Heuristic to determine risk level from QCC data."""
    if not isinstance(items, list):
        return "暂无风险评级"

    total = len(items)
    if total == 0:
        return "暂无风险信息"

    # Count risk severity indicators
    high_keywords = ["破产", "失信", "被执行", "吊销", "严重违法", "清算"]
    medium_keywords = ["行政处罚", "经营异常", "欠税", "股权冻结", "限制高消费"]
    high_count = 0
    medium_count = 0

    text = json.dumps(items, ensure_ascii=False).lower()
    for kw in high_keywords:
        if kw in text:
            high_count += 1
    for kw in medium_keywords:
        if kw in text:
            medium_count += 1

    if high_count > 0:
        return "高风险"
    if medium_count > 0:
        return "中风险"
    return "低风险"


def _generate_risk_summary(items: Any) -> str:
    """Generate a concise risk summary."""
    if not isinstance(items, list) or not items:
        return "未发现明显风险信息"

    parts = []
    text = json.dumps(items, ensure_ascii=False)

    if "失信" in text:
        parts.append("存在失信记录")
    if "被执行" in text:
        parts.append("存在被执行信息")
    if "行政处罚" in text:
        parts.append("有行政处罚记录")
    if "经营异常" in text:
        parts.append("曾被列入经营异常名录")
    if "破产" in text or "清算" in text:
        parts.append("涉及破产/清算程序")
    if "吊销" in text:
        parts.append("存在吊销记录")

    if not parts:
        return f"共发现 {len(items)} 条记录，整体风险较低"

    return "；".join(parts) + f"。共 {len(items)} 条记录"


def _generate_operation_summary(items: Any) -> str:
    """Generate operation summary from QCC data."""
    if not isinstance(items, list) or not items:
        return "暂无经营数据"

    # Extract key financial indicators if available
    text = json.dumps(items, ensure_ascii=False)

    parts = []
    # Try to find revenue/profit keywords
    for item in items[:3] if isinstance(items, list) else []:
        if isinstance(item, dict):
            for k, v in item.items():
                if "收入" in k or "营收" in k or "利润" in k:
                    parts.append(f"{k}: {v}")

    if parts:
        return "经营数据: " + "; ".join(parts[:3])
    return f"共获取 {len(items)} 条经营数据"


# ── Public API ─────────────────────────────────────────────────────────────

def check_company_credit(
    company_name: str,
    include_risk: bool = True,
    include_operation: bool = True,
    include_executives: bool = True,
    include_ipr: bool = False,
    include_history: bool = False,
    include_legal_cases: bool = False,
    include_documents: bool = False,
) -> QccCreditReport:
    """Check company credit by name using QCC official data sources.

    This is the main entry point replacing the previous LLM-based credit
    evaluation.  Returns a comprehensive QccCreditReport with structured data
    from multiple QCC MCP services.

    Parameters
    ----------
    company_name : str
        Full company name to look up.
    include_* : bool
        Toggle individual data categories.  By default includes company info,
        risk, operation, and executives.

    Returns
    -------
    QccCreditReport
        Structured credit report with all requested data categories.

    Raises
    ------
    QccMcpError
        If the QCC service is unavailable or returns an error.
    """
    report = QccCreditReport()

    # 1. Company basic info (always fetched)
    try:
        company_result = _search_company_by_name(company_name)
        report.company = _parse_company_result(company_result)
        logger.info(f"[QCC] Company info fetched: {report.company.company_name}")
    except QccMcpError as e:
        logger.error(f"[QCC] Company search failed: {e}")
        raise

    # If company name was resolved differently, use the official name
    resolved_name = report.company.company_name or company_name

    # 2. Risk info
    if include_risk:
        try:
            report.risk = _search_risk(resolved_name)
            logger.info(f"[QCC] Risk info fetched: level={report.risk.risk_level}, items={len(report.risk.risk_items)}")
        except QccMcpError as e:
            logger.warning(f"[QCC] Risk search failed (non-fatal): {e}")

    # 3. Operation / business data
    if include_operation:
        try:
            report.operation = _search_operation(resolved_name)
            logger.info(f"[QCC] Operation data fetched: {report.operation.summary}")
        except QccMcpError as e:
            logger.warning(f"[QCC] Operation search failed (non-fatal): {e}")

    # 4. Executives
    if include_executives:
        try:
            report.executives = _search_service("executive", resolved_name)
            logger.info(f"[QCC] Executives fetched: {len(report.executives)} persons")
        except QccMcpError as e:
            logger.warning(f"[QCC] Executive search failed (non-fatal): {e}")

    # 5. IPR (optional)
    if include_ipr:
        try:
            report.ipr = _search_service("ipr", resolved_name)
        except QccMcpError as e:
            logger.warning(f"[QCC] IPR search failed (non-fatal): {e}")

    # 6. History
    if include_history:
        try:
            report.history = _search_service("history", resolved_name)
        except QccMcpError as e:
            logger.warning(f"[QCC] History search failed (non-fatal): {e}")

    # 7. Legal cases
    if include_legal_cases:
        try:
            report.legal_cases = _search_service("legal_case", resolved_name)
        except QccMcpError as e:
            logger.warning(f"[QCC] Legal case search failed (non-fatal): {e}")

    # 8. Documents
    if include_documents:
        try:
            report.documents = _search_service("document", resolved_name)
        except QccMcpError as e:
            logger.warning(f"[QCC] Document search failed (non-fatal): {e}")

    return report


def format_credit_summary(report: QccCreditReport) -> str:
    """Format a QccCreditReport into a human-readable summary string.

    Used to populate the 'summary' field in the frontend CreditAnalysis response.
    """
    parts = []

    c = report.company
    if c.company_name:
        parts.append(f"【{c.company_name}】")

    if c.status:
        status_map = {"存续": "✅ 正常经营", "在业": "✅ 正常经营", "注销": "⚠️ 已注销", "吊销": "🚫 已吊销"}
        parts.append(f"经营状态: {status_map.get(c.status, c.status)}")

    if c.registered_capital:
        parts.append(f"注册资本: {c.registered_capital}")

    if c.established_date:
        parts.append(f"成立日期: {c.established_date}")

    if c.legal_person:
        parts.append(f"法定代表人: {c.legal_person}")

    if c.industry:
        parts.append(f"行业: {c.industry}")

    # Risk summary
    if report.risk.risk_level:
        risk_emoji = {"低风险": "🟢", "中风险": "🟡", "高风险": "🔴"}.get(report.risk.risk_level, "⚪")
        parts.append(f"风险评级: {risk_emoji} {report.risk.risk_level}")

    if report.risk.summary and report.risk.summary != "未发现明显风险信息":
        parts.append(f"风险摘要: {report.risk.summary}")

    # Executives
    if report.executives:
        exec_names = [e.get("name", "") or e.get("姓名", "") for e in report.executives[:5] if isinstance(e, dict)]
        exec_names = [n for n in exec_names if n]
        if exec_names:
            parts.append(f"主要人员: {', '.join(exec_names[:5])}")

    # Source marker
    parts.append("— 数据来源: 企查查(QCC)")

    return "\n".join(parts)
