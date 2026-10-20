from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image

from ..config import settings
from ..models import Disease
from .base import HEALTHY, Classifier
from .stub import StubClassifier


@lru_cache
def get_classifier() -> Classifier:
    if settings.model_path and settings.labels_path and Path(settings.model_path).exists():
        from .onnx_classifier import OnnxClassifier
        return OnnxClassifier(settings.model_path, settings.labels_path)
    return StubClassifier()


@dataclass
class Diagnosis:
    disease: Disease | None
    confidence: float
    needs_review: bool
    model_version: str
    per_photo: list[dict[str, float]]


def diagnose(images: list[Image.Image], diseases: list[Disease]) -> Diagnosis:
    """Combina várias fotos (RF18) por média das probabilidades e aplica o limite RN04."""
    clf = get_classifier()
    labels = [d.name for d in diseases] + [HEALTHY]
    per_photo = [clf.predict(im, labels) for im in images]
    avg = {l: sum(p[l] for p in per_photo) / len(per_photo) for l in labels}
    top = max(avg, key=avg.get)
    disease = next((d for d in diseases if d.name == top), None)
    conf = round(avg[top], 4)
    return Diagnosis(disease, conf, conf < settings.confidence_threshold, clf.version, per_photo)
