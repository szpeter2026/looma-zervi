"""Shared pytest fixtures for backend tests."""
import os
import tempfile

import pytest

from src.app import create_app


@pytest.fixture
def app():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_PATH"] = path
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["WECHAT_DEV_MODE"] = "true"
    os.environ["DEEPSEEK_API_KEY"] = "skip"
    application = create_app("testing")
    yield application
    os.unlink(path)


@pytest.fixture
def client(app):
    return app.test_client()
