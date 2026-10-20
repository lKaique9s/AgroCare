import hashlib
import random

from PIL import Image


class StubClassifier:
    """Classificador de DEMONSTRAÇÃO: determinístico por imagem, sem visão computacional real."""
    version = "stub-0"

    def predict(self, image: Image.Image, labels: list[str]) -> dict[str, float]:
        seed = hashlib.sha256(image.convert("RGB").resize((16, 16)).tobytes()).hexdigest()
        rng = random.Random(seed)
        weights = [rng.random() ** 3 + 0.01 for _ in labels]
        top = rng.randrange(len(labels))
        weights[top] += rng.uniform(1.5, 8)
        total = sum(weights)
        return {l: w / total for l, w in zip(labels, weights)}
