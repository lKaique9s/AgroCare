"""Verificação de qualidade da foto (mesma lógica usada no protótipo)."""
import numpy as np
from PIL import Image


def check_quality(img: Image.Image) -> list[str]:
    issues: list[str] = []
    if min(img.size) < 224:
        issues.append("Resolução muito baixa")
    small = img.convert("RGB").resize((96, 96))
    rgb = np.asarray(small, dtype=np.float32)
    g = rgb @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
    lap = np.abs(4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:])
    if np.percentile(lap, 95) < 14:
        issues.append("Imagem desfocada")
    mean = float(g.mean())
    if mean < 45 or mean > 225:
        issues.append("Iluminação inadequada")
    r, gc, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if ((gc > 50) & (gc > r * 1.05) & (gc > b * 1.1)).mean() < 0.05:
        issues.append("Folha não identificável")
    return issues
