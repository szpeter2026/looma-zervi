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

# H5 用户端模板目录
USER_TEMPLATES_DIR = WEB_DIR / "user"


class SilentUndefined(Undefined):
    """Jinja2 未定义变量返回空字符串，不抛异常"""

    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""

    def __str__(self) -> str:
        return ""

    def __iter__(self):
        return iter([])

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return hash(None)


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.undefined = SilentUndefined

# H5 用户端使用原生 HTML（无需 Jinja2 继承），直接读文件返回
user_templates = Jinja2Templates(directory=str(USER_TEMPLATES_DIR))
user_templates.env.undefined = SilentUndefined

router = APIRouter(tags=["web"])


def _render(request: Request, name: str, **extra) -> HTMLResponse:
    """统一模板渲染：新版 Starlette 中 request 作为第一个位置参数传入。"""
    return templates.TemplateResponse(request, name, extra)


# ===== 页面路由 =====

@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return _render(request, "index.html", hide_sidebar=False)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return _render(request, "login.html", hide_sidebar=True)


@router.get("/query", response_class=HTMLResponse)
async def query_page(request: Request):
    return _render(request, "query.html", hide_sidebar=False)


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    return _render(request, "documents.html", hide_sidebar=False)


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return _render(request, "reports.html", hide_sidebar=False)


@router.get("/poetry", response_class=HTMLResponse)
async def poetry_page(request: Request):
    return _render(request, "poetry.html", hide_sidebar=False)


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    return _render(request, "jobs.html", hide_sidebar=False)


@router.get("/resume", response_class=HTMLResponse)
async def resume_page(request: Request):
    return _render(request, "resume.html", hide_sidebar=False)


# ===== H5 用户端路由 =====

def _render_user(request: Request, name: str) -> HTMLResponse:
    """渲染 H5 用户端页面（原生 HTML，无 Jinja2 继承）"""
    return user_templates.TemplateResponse(request, name)


@router.get("/user", response_class=HTMLResponse)
@router.get("/user/", response_class=HTMLResponse)
async def user_index(request: Request):
    return _render_user(request, "index.html")


@router.get("/user/login", response_class=HTMLResponse)
async def user_login(request: Request):
    return _render_user(request, "login.html")


@router.get("/user/profile", response_class=HTMLResponse)
async def user_profile(request: Request):
    return _render_user(request, "profile.html")
