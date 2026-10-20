import io
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"

import numpy as np  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app.main import app  # noqa: E402


def png(arr) -> bytes:
    b = io.BytesIO()
    Image.fromarray(arr.astype("uint8")).save(b, "PNG")
    return b.getvalue()


def leaf_like(seed=0):
    r = np.random.default_rng(seed)
    return png(np.stack([r.integers(20, 80, (256, 256)), r.integers(110, 220, (256, 256)),
                         r.integers(20, 80, (256, 256))], -1))


def test_full_flow():
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}
        assert len(c.get("/diseases").json()) == 14
        assert len(c.get("/diseases", params={"crop": "Café"}).json()) == 5

        c.post("/auth/register", json={"name": "João", "email": "joao@x.com", "password": "senha1234"})
        tok = c.post("/auth/login", data={"username": "joao@x.com", "password": "senha1234"}).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        assert c.get("/diagnostics").status_code == 401

        # foto ruim é bloqueada
        bad = c.post("/diagnostics", headers=h, data={"crop": "Café"},
                     files=[("files", ("a.png", png(np.full((256, 256, 3), 128)), "image/png"))])
        assert bad.status_code == 422 and bad.json()["detail"]["photos"][0]["issues"]

        # duas fotos boas
        ok = c.post("/diagnostics", headers=h, data={"crop": "Café"},
                    files=[("files", ("a.png", leaf_like(1), "image/png")),
                           ("files", ("b.png", leaf_like(2), "image/png"))])
        assert ok.status_code == 201, ok.text
        d = ok.json()
        assert len(d["photos"]) == 2 and 0 < d["confidence"] <= 1

        assert c.get(d["photos"][0]["url"], headers=h).status_code == 200
        assert len(c.get("/diagnostics", headers=h, params={"crop": "Soja"}).json()) == 0
        assert len(c.get("/diagnostics", headers=h, params={"crop": "Café"}).json()) == 1

        assert c.post(f"/diagnostics/{d['id']}/feedback", headers=h, json={"is_correct": True}).status_code == 201
        assert c.post(f"/diagnostics/{d['id']}/feedback", headers=h, json={"is_correct": True}).status_code == 409
        pdf = c.get(f"/diagnostics/{d['id']}/report.pdf", headers=h)
        assert pdf.content[:4] == b"%PDF"

        # RN06: outro usuário não vê o diagnóstico
        c.post("/auth/register", json={"name": "Maria", "email": "m@x.com", "password": "senha1234"})
        t2 = c.post("/auth/login", data={"username": "m@x.com", "password": "senha1234"}).json()["access_token"]
        assert c.get(f"/diagnostics/{d['id']}", headers={"Authorization": f"Bearer {t2}"}).status_code == 404
        # produtor não acessa administração
        assert c.post("/admin/diseases", headers=h, json={}).status_code == 403

        # admin cria e agrônomo/admin valida
        ta = c.post("/auth/login", data={"username": "admin@agrocare.local", "password": "admin12345"}).json()["access_token"]
        ha = {"Authorization": f"Bearer {ta}"}
        new = c.post("/admin/diseases", headers=ha, json={"name": "Teste", "scientific_name": "T. t.", "crop": "Soja",
                     "severity": "baixa", "description": "d", "causes": "c", "care": "c"})
        assert new.status_code == 201 and new.json()["validated"] is False
        assert c.post(f"/admin/diseases/{new.json()['id']}/validate", headers=ha).json()["validated"] is True
