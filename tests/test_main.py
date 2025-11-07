import base64
from fastapi.testclient import TestClient
from src.backend.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_generate_requires_prompt():
    client = TestClient(app)
    r = client.post("/generate", json={"prompt": "", "text_max_length": 50, "prefer_local_image": False, "save_to_s3": False})
    assert r.status_code == 400


def test_generate_text_and_image(monkeypatch):
    # Patch heavy generator functions to return deterministic values
    # Patch the functions imported into the main module so the endpoint uses the mocks
    monkeypatch.setattr("src.backend.main.generate_text", lambda prompt, max_length=150: "TEXT:" + prompt)
    sample_img_b64 = base64.b64encode(b"fakeimagebytes").decode()
    monkeypatch.setattr("src.backend.main.generate_image", lambda prompt, prefer_local=False: {"image_base64": sample_img_b64})

    client = TestClient(app)
    r = client.post("/generate", json={"prompt": "hello", "text_max_length": 50, "prefer_local_image": False, "save_to_s3": False})
    assert r.status_code == 200
    d = r.json()
    assert d["text"].startswith("TEXT:")
    assert d["image_base64"] == sample_img_b64
    assert d["image_s3_url"] is None


def test_generate_with_s3(monkeypatch):
    monkeypatch.setattr("src.backend.main.generate_text", lambda prompt, max_length=150: "TEXT:" + prompt)
    sample_img_b64 = base64.b64encode(b"fakeimagebytes2").decode()
    monkeypatch.setattr("src.backend.main.generate_image", lambda prompt, prefer_local=False: {"image_base64": sample_img_b64})
    monkeypatch.setattr("src.backend.s3_utils.upload_bytes", lambda data, key: "https://example-bucket.s3.amazonaws.com/" + key)
    monkeypatch.setattr("src.backend.s3_utils.make_key", lambda prefix="generated", extension="png": "generated/test.png")

    client = TestClient(app)
    r = client.post("/generate", json={"prompt": "hello", "text_max_length": 50, "prefer_local_image": False, "save_to_s3": True})
    assert r.status_code == 200
    d = r.json()
    assert d["image_s3_url"] is not None
    assert d["image_base64"] == sample_img_b64


def test_image_failure_returns_500(monkeypatch):
    monkeypatch.setattr("src.backend.main.generate_text", lambda prompt, max_length=150: "TEXT")

    def bad(prompt, prefer_local=False):
        raise RuntimeError("boom")

    monkeypatch.setattr("src.backend.main.generate_image", bad)

    client = TestClient(app)
    r = client.post("/generate", json={"prompt": "hi", "text_max_length": 50, "prefer_local_image": False, "save_to_s3": False})
    assert r.status_code == 500
