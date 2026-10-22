import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")

import ipaddress
import socket

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


# Resolución DNS controlada: el laboratorio no depende de la red y cada
# nombre usado en las pruebas resuelve siempre a la misma dirección.
_DNS_LABORATORIO = {
    "discord.com": "162.159.135.232",
    "hooks.ejemplo-publico.com": "93.184.215.14",
    "localhost": "127.0.0.1",
    "interno.lab": "10.0.0.5",
}


@pytest.fixture(autouse=True)
def _dns_de_laboratorio(monkeypatch):
    real = socket.getaddrinfo

    def resolver(host, port, *args, **kwargs):
        try:
            ipaddress.ip_address(host)
            return real(host, port, *args, **kwargs)
        except ValueError:
            pass
        if host in _DNS_LABORATORIO:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (_DNS_LABORATORIO[host], port or 443))]
        raise socket.gaierror(f"{host} no existe en el DNS de laboratorio")

    monkeypatch.setattr(socket, "getaddrinfo", resolver)
