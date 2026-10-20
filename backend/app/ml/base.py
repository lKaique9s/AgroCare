from typing import Protocol

from PIL import Image

HEALTHY = "Folha saudável"


class Classifier(Protocol):
    version: str

    def predict(self, image: Image.Image, labels: list[str]) -> dict[str, float]:
        """Retorna probabilidade por rótulo (soma 1) restrita aos rótulos informados."""
