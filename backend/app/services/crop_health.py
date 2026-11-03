"""Crop image analysis. Inference is separated behind DiseaseClassifier so the model can be swapped.
Nothing is predicted unless a real model is loaded; predictions are never fabricated."""
import io, json, logging, uuid
from pathlib import Path
from typing import Protocol
from PIL import Image, UnidentifiedImageError
from app.core.config import settings

log = logging.getLogger("agri360.health")
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
DISCLAIMER = ("This is an AI-assisted indication, not a confirmed diagnosis. Confirm with a local agriculture "
              "officer or KVK before treating the crop. Never apply chemicals without expert advice.")


class ImageValidationError(ValueError):
    pass


def validate_image(data: bytes, max_bytes: int | None = None) -> tuple[str, tuple[int, int]]:
    """Validate by decoding the content, not by trusting filename or content-type."""
    max_bytes = max_bytes or settings.max_upload_mb * 1024 * 1024
    if not data:
        raise ImageValidationError("The file is empty.")
    if len(data) > max_bytes:
        raise ImageValidationError(f"The image is larger than {max_bytes // (1024 * 1024)} MB.")
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt, size = im.format, im.size
            im.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ImageValidationError("The file is not a valid image. Use JPEG, PNG or WebP.")
    if fmt not in ALLOWED_FORMATS:
        raise ImageValidationError("Unsupported image type. Use JPEG, PNG or WebP.")
    if min(size) < 64 or max(size) > 8000:
        raise ImageValidationError("Image dimensions must be between 64 px and 8000 px.")
    return fmt, size


def save_image(data: bytes, fmt: str) -> str:
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ALLOWED_FORMATS[fmt]}"
    (folder / name).write_bytes(data)
    return name


class DiseaseClassifier(Protocol):
    available: bool
    reason: str

    def predict(self, image: Image.Image) -> list[tuple[str, float]]:
        """Return (label, probability) pairs sorted by probability, highest first."""


class UnavailableClassifier:
    available = False

    def __init__(self, reason: str):
        self.reason = reason

    def predict(self, image):  # pragma: no cover
        raise RuntimeError(self.reason)


class KerasClassifier:
    """Loads a Keras image classifier (.keras/.h5). Labels JSON: list of '<crop>__<condition>' strings in output order."""
    available = True
    reason = ""

    def __init__(self, model_path: str, labels_path: str, size: int):
        import tensorflow as tf  # lazy import: TensorFlow is optional
        self.model = tf.keras.models.load_model(model_path)
        self.labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))
        self.size = size

    def predict(self, image):
        import numpy as np
        arr = np.asarray(image.convert("RGB").resize((self.size, self.size)), dtype="float32") / 255.0
        probs = self.model.predict(arr[None, ...], verbose=0)[0]
        order = probs.argsort()[::-1][:3]
        return [(self.labels[i], float(probs[i])) for i in order]


_classifier: DiseaseClassifier | None = None


def load_classifier() -> DiseaseClassifier:
    global _classifier
    if not settings.model_path or not settings.model_labels_path:
        _classifier = UnavailableClassifier("No model configured. Set MODEL_PATH and MODEL_LABELS_PATH (see README).")
    elif not Path(settings.model_path).exists() or not Path(settings.model_labels_path).exists():
        _classifier = UnavailableClassifier("Model or labels file not found at the configured path.")
    else:
        try:
            _classifier = KerasClassifier(settings.model_path, settings.model_labels_path, settings.model_input_size)
        except Exception as exc:  # noqa: BLE001
            log.exception("Model load failed")
            _classifier = UnavailableClassifier(f"Model could not be loaded ({type(exc).__name__}).")
    return _classifier


def get_classifier() -> DiseaseClassifier:
    return _classifier or load_classifier()


def set_classifier(c: DiseaseClassifier | None):
    """Test hook / runtime swap."""
    global _classifier
    _classifier = c


def _kb() -> dict:
    return json.loads((Path(settings.data_dir) / "disease_info.json").read_text(encoding="utf-8"))


def problem_options() -> list[str]:
    return _kb()["problem_options"]


def analyse(image_bytes: bytes, crop_name: str) -> dict:
    clf = get_classifier()
    base = {"disclaimer": DISCLAIMER, "predictions": [], "info": None, "confidence": None, "predicted_label": None}
    if not clf.available:
        return {**base, "status": "model_unavailable",
                "message": f"AI analysis is unavailable until a model is configured. {clf.reason}"}
    with Image.open(io.BytesIO(image_bytes)) as im:
        preds = clf.predict(im.copy())
    label, conf = preds[0]
    out = {**base, "predictions": [{"label": l, "confidence": round(c, 4)} for l, c in preds],
           "predicted_label": label, "confidence": round(conf, 4)}
    info = _kb()["labels"].get(label)
    label_crop = info["crop"] if info else None
    if conf < settings.min_confidence:
        return {**out, "status": "uncertain",
                "message": "The model is not confident about this image. Try a clearer, closer photo of one leaf in daylight."}
    if label_crop and label_crop.lower() != crop_name.lower():
        return {**out, "status": "uncertain",
                "message": f"The prediction relates to {label_crop}, not {crop_name}. Check the crop selection or use a clearer photo."}
    if not label.startswith(crop_name.lower().replace(" ", "")) and label != "healthy" and not info:
        return {**out, "status": "uncertain", "message": "This result is outside the supported conditions for the selected crop."}
    return {**out, "status": "analysed", "info": info or {"title": label.replace("__", ": ").replace("_", " "),
            "description": "No guidance is stored for this class yet.", "monitoring": [], "prevention": []},
            "message": "Possible condition found. Treat this as an indication to check the crop, not a diagnosis."}
