"""Looma api — 路由共享初始化"""
from src.api.routes.system import router as system_router
from src.api.routes.ask import router as ask_router
from src.api.routes.jobs import router as jobs_router
from src.api.routes.resume import router as resume_router
from src.api.routes.auth_routes import router as auth_router
from src.api.routes.region import router as region_router
from src.api.routes.reports import router as reports_router

__all__ = [
    "system_router",
    "ask_router",
    "jobs_router",
    "resume_router",
    "auth_router",
    "region_router",
    "reports_router",
]
