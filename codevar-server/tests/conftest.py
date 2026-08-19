import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app
from app.models import Base
from app.rate_limit import events_rate_limiter


@pytest.fixture(autouse=True)
def _clean_state():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    events_rate_limiter._hits.clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def project(client):
    response = client.post("/projects", data={"name": "test-project"}, follow_redirects=False)
    api_key = response.headers["location"].split("api_key=")[1].split("&")[0]
    return {"api_key": api_key, "name": "test-project"}
