import pytest
from conftest import png_bytes, register
from app.services import crop_health as ch


def test_validate_image_accepts_real_formats():
    for fmt in ["PNG", "JPEG", "WEBP"]:
        assert ch.validate_image(png_bytes(fmt=fmt))[0] == fmt


@pytest.mark.parametrize("data", [b"", b"not an image", b"GIF89a" + b"0" * 50, png_bytes()[:40]])
def test_validate_image_rejects_bad_content(data):
    with pytest.raises(ch.ImageValidationError):
        ch.validate_image(data)


def test_validate_rejects_oversize_tiny_and_gif():
    import io
    from PIL import Image
    with pytest.raises(ch.ImageValidationError, match="larger"):
        ch.validate_image(png_bytes(), max_bytes=100)
    with pytest.raises(ch.ImageValidationError):
        ch.validate_image(png_bytes(size=(10, 10)))
    buf = io.BytesIO(); Image.new("RGB", (100, 100)).save(buf, "GIF")
    with pytest.raises(ch.ImageValidationError, match="Unsupported"):
        ch.validate_image(buf.getvalue())


def test_model_unavailable_never_predicts(db):
    r = ch.analyse(png_bytes(), "Groundnut")
    assert r["status"] == "model_unavailable" and r["predicted_label"] is None and r["confidence"] is None
    assert "unavailable" in r["message"].lower()


class Fake:
    available, reason = True, ""
    def __init__(self, preds): self.preds = preds
    def predict(self, image): return self.preds


def test_confident_uncertain_and_wrong_crop(db):
    ch.set_classifier(Fake([("groundnut__early_leaf_spot", 0.93), ("healthy", 0.04)]))
    ok = ch.analyse(png_bytes(), "Groundnut")
    assert ok["status"] == "analysed" and ok["info"]["prevention"] and "not a confirmed diagnosis" in ok["disclaimer"]
    assert ch.analyse(png_bytes(), "Cotton")["status"] == "uncertain"
    ch.set_classifier(Fake([("groundnut__early_leaf_spot", 0.30)]))
    assert ch.analyse(png_bytes(), "Groundnut")["status"] == "uncertain"
    ch.set_classifier(None)


def test_analyse_endpoint_validation_and_history(client):
    h = register(client)
    files = lambda data, name="leaf.png", ct="image/png": {"file": (name, data, ct)}
    r = client.post("/api/health/analyse", files=files(png_bytes()), data={"crop_name": "Groundnut"}, headers=h)
    assert r.status_code == 201 and r.json()["status"] == "model_unavailable" and r.json()["has_image"]
    # a text file renamed .png with an image content-type is still rejected
    assert client.post("/api/health/analyse", files=files(b"hello", "x.png"), data={"crop_name": "Groundnut"}, headers=h).status_code == 400
    assert client.post("/api/health/analyse", files=files(png_bytes()), data={"crop_name": "Banana"}, headers=h).status_code == 422
    rid = r.json()["id"]
    assert len(client.get("/api/health/reports", headers=h).json()) == 1
    assert client.get(f"/api/health/reports/{rid}/image", headers=h).status_code == 200
    other = register(client, "b@example.com")
    assert client.get(f"/api/health/reports/{rid}", headers=other).status_code == 404
    assert client.get(f"/api/health/reports/{rid}/image", headers=other).status_code == 404
    assert client.get("/api/health/status", headers=h).json()["model_available"] is False
