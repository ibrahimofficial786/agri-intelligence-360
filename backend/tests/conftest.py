import io, os, sys, tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ.update(DATABASE_URL=f"sqlite:///{_tmp}/test.db", SEED_DEMO="false", UPLOAD_DIR=f"{_tmp}/uploads",
                  SECRET_KEY="test-secret", MODEL_PATH="", MODEL_LABELS_PATH="")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.database.db import Base, SessionLocal, engine
from app.main import app
from app.services import crop_health


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    crop_health.set_classifier(None)
    with SessionLocal() as s:
        from app.services import market_intelligence, seed
        seed.seed_catalog(s)
        market_intelligence.seed_market_samples(s)
        yield s


@pytest.fixture()
def client(db):
    with TestClient(app) as c:  # lifespan seeds catalog + sample prices
        yield c


def register(client, email="a@example.com", district="Kurnool"):
    r = client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!", "full_name": "Test Farmer",
                                                  "district": district})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def png_bytes(size=(128, 128), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", size, (30, 120, 40)).save(buf, fmt)
    return buf.getvalue()
