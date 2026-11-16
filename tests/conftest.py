"""Test setup. The environment must be set BEFORE the application imports."""

import os
import tempfile
from pathlib import Path

_ROOT = Path(tempfile.mkdtemp(prefix="music-tools-tests-"))
for _name in ("outputs", "uploads", "temp"):
    (_ROOT / _name).mkdir()

os.environ.update({
    "OUTPUT_DIR": str(_ROOT / "outputs"),
    "UPLOAD_DIR": str(_ROOT / "uploads"),
    "TEMP_DIR": str(_ROOT / "temp"),
    "REQUIRE_API_KEY": "true",
    "VALID_API_KEYS": "test-key",
    "ENABLE_RATE_LIMITING": "true",
    "RATE_LIMIT_STORAGE_URI": "memory://",
    "REDIS_URL": "redis://user:secret@redis.invalid:6379/0",
    "LOG_LEVEL": "CRITICAL",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402

AUTH = {"X-API-Key": "test-key"}


@pytest.fixture(scope="session")
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_limits():
    if limiter is not None:
        limiter.reset()
    yield


@pytest.fixture
def auth():
    return dict(AUTH)


@pytest.fixture
def out_dir():
    return settings.OUTPUT_DIR
