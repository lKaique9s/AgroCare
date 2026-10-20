import json
from pathlib import Path

import numpy as np
from PIL import Image

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class OnnxClassifier:
    """Modelo treinado exportado para ONNX. labels.json = lista de rótulos na ordem da saída."""

    def __init__(self, model_path: str, labels_path: str, size: int = 224):
        import onnxruntime as ort  # dependência opcional (requirements-ml.txt)
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input = self.session.get_inputs()[0].name
        self.labels: list[str] = json.loads(Path(labels_path).read_text(encoding="utf-8"))
        self.size = size
        self.version = f"onnx:{Path(model_path).stem}"

    def predict(self, image: Image.Image, labels: list[str]) -> dict[str, float]:
        x = np.asarray(image.convert("RGB").resize((self.size, self.size)), dtype=np.float32) / 255.0
        x = ((x - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
        logits = self.session.run(None, {self.input: x})[0][0]
        e = np.exp(logits - logits.max())
        raw = dict(zip(self.labels, (e / e.sum()).tolist()))
        sel = {l: raw.get(l, 0.0) for l in labels}  # restringe à cultura e renormaliza
        s = sum(sel.values()) or 1.0
        return {l: v / s for l, v in sel.items()}
