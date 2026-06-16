"""
Looma agents — PydanticAI 文档解读智能体

result_type 定义数据边界，AI 只返回结构化结果，避免「好的，这是你要的 JSON」导致解析崩溃。
来源：Tatha agents/document_agents.py，已迁入 looma-zervi。
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ResumeAnalysis(BaseModel):
    """简历解析结构化输出"""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education: list[dict] | None = None
    experience: list[dict] | None = None
    skills: list[str] | None = None
    summary: str | None = None


class PoetryAnalysis(BaseModel):
    """诗词解析结构化输出"""
    title: str | None = None
    author: str | None = None
    dynasty: str | None = None
    content: str | None = None
    theme: str | None = None


class CreditAnalysis(BaseModel):
    """征信文本解析结构化输出"""
    entity_name: str | None = None
    report_type: str | None = None
    summary: str | None = None


_agents: dict[str, Any] = {}


def _get_model():
    """获取 LiteLLM 模型实例"""
    from src.core.config import get_settings
    from src.core.llm import get_llm
    return get_llm()


def _get_agent(name: str):
    """懒加载 PydanticAI Agent"""
    if name in _agents:
        return _agents[name]

    try:
        from pydantic_ai import Agent
        from pydantic_ai_litellm import LiteLLMModel
        settings = __import__("src.core.config", fromlist=["get_settings"]).get_settings()
        model = LiteLLMModel(model_name=settings.LLM_MODEL)
    except ImportError:
        _agents[name] = None
        return None

    if name == "resume":
        _agents[name] = Agent(
            model=model,
            output_type=ResumeAnalysis,
            system_prompt=(
                "你是一个简历解析器。根据用户提供的简历文本，提取并仅返回结构化信息："
                "姓名、学历或毕业院校、技能关键词（逗号分隔）、工作经历摘要。"
                "不要输出任何解释或前缀（如「好的」「这是」），只输出符合 ResumeAnalysis 的 JSON 结构。"
            ),
        )
    elif name == "poetry":
        _agents[name] = Agent(
            model=model,
            output_type=PoetryAnalysis,
            system_prompt=(
                "你是一个诗词/赏析解析器。根据用户提供的诗词或赏析文本，提取并仅返回结构化信息："
                "诗词标题、作者、朝代、正文或摘录句、主题或情感（如送别、思乡）。"
                "不要输出任何解释或前缀，只输出符合 PoetryAnalysis 的 JSON 结构。"
            ),
        )
    elif name == "credit":
        _agents[name] = Agent(
            model=model,
            output_type=CreditAnalysis,
            system_prompt=(
                "你是一个征信/信用文本解析器。根据用户提供的文本，提取并仅返回结构化信息："
                "主体名称、报告类型、摘要说明。不要输出任何解释或前缀，只输出符合 CreditAnalysis 的 JSON 结构。"
            ),
        )
    else:
        raise ValueError(f"未知文档类型: {name}，支持 resume / poetry / credit")

    return _agents[name]


def run_document_analysis(document_type: str, text: str) -> Any:
    """统一入口：按 document_type 调用对应智能体，返回类型化结果。"""
    agent = _get_agent(document_type)
    if agent is None:
        raise RuntimeError("PydanticAI / pydantic_ai_litellm 未安装，无法执行文档分析")

    result = agent.run_sync(text)
    return result.output