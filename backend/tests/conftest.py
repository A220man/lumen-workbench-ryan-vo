import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LUMEN_DEMO_MODE"] = "true"
os.environ["LUMEN_SECRET_KEY"] = "test-secret-key-32-chars-long-1234"
os.environ["HOST"] = "127.0.0.1"

from backend.core.db import init_db, create_all
from backend.app.main import app

@pytest.fixture(autouse=True)
def setup_db():
    init_db("sqlite:///:memory:")
    create_all()

@pytest.fixture
def client():
    return TestClient(app)
