"""Looma Web 面板 — Jinja2 页面路由

将 DemoPeter 前端模板适配到 FastAPI，通过 /v1/* API 连接后端。
认证：页面通过 localStorage 存储 JWT token，请求时通过 Authorization 头携带。
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Undefined

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# 模板和静态文件路径
# __file__ = src/api/routes/web_panel.py → 上 4 级到项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WEB_DIR = _PROJECT_ROOT / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

class SilentUndefined(Undefined):
    """Jinja2 未定义变量返回空字符串，不抛异常"""
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""
    __str__ = lambda self: ""
    __iter__ = lambda self: iter([])
    __bool__ = lambda self: False

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.undefined = SilentUndefined

router = APIRouter(tags=["web"])


# ===== 页面路由 =====

@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """仪表盘首页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "hide_sidebar": False,
    })


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面（无侧边栏）"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "hide_sidebar": True,
    })


@router.get("/query", response_class=HTMLResponse)
async def query_page(request: Request):
    """智能问答页面"""
    return templates.TemplateResponse("query.html", {
        "request": request,
        "hide_sidebar": False,
    })


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    """文档管理页面"""
    return templates.TemplateResponse("documents.html", {
        "request": request,
        "hide_sidebar": False,
    })


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """报告中心页面"""
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "hide_sidebar": False,
    })


@router.get("/poetry", response_class=HTMLResponse)
async def poetry_page(request: Request):
    """诗词检索页面"""
    return templates.TemplateResponse("poetry.html", {
        "request": request,
        "hide_sidebar": False,
    })


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """职位匹配页面"""
    return templates.TemplateResponse("jobs.html", {
        "request": request,
        "hide_sidebar": False,
    })


@router.get("/resume", response_class=HTMLResponse)
async def resume_page(request: Request):
    """简历解析页面"""
    return templates.TemplateResponse("resume.html", {
        "request": request,
        "hide_sidebar": False,
    })
