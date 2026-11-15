import os
import tempfile

import pytest

# config.py reads these at import time, so set them before the app is imported.
_tmp = tempfile.mkdtemp()
os.environ["NOURISH_DB"] = os.path.join(_tmp, "test.db")
os.environ["NOURISH_MODE"] = "mock"
os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
