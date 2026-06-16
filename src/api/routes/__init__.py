"""Looma api — 路由共享初始化"""
from src.api.routes.system import router as system_router
from src.api.routes.ask import router as ask_router

__all__ = ["system_router", "ask_router"]
