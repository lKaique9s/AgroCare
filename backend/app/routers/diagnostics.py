import io
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..ml.service import diagnose
from ..models import CROPS, Diagnostic, DiagnosticPhoto, Disease, Feedback, User
from ..quality import check_quality
from ..reports import build_pdf
from ..schemas import DiagnosticOut, FeedbackIn

router = APIRouter(prefix="/diagnostics", tags=["diagnósticos"])
LOAD = (selectinload(Diagnostic.photos), selectinload(Diagnostic.disease), selectinload(Diagnostic.feedback))


def _own(db: Session, user: User, diag_id: int) -> Diagnostic:  # RN06: só o próprio usuário
    d = db.scalar(select(Diagnostic).options(*LOAD).where(Diagnostic.id == diag_id, Diagnostic.user_id == user.id))
    if not d:
        raise HTTPException(404, "Diagnóstico não encontrado")
    return d


@router.post("", response_model=DiagnosticOut, status_code=201)
async def create(crop: str = Form(...), captured_at: datetime | None = Form(None),
                 files: list[UploadFile] = File(...), db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    """RF01-RF04, RF18. `captured_at` permite sincronizar capturas feitas offline (RF22)."""
    if crop not in CROPS:
        raise HTTPException(422, f"Cultura deve ser uma de {CROPS}")
    if not 1 <= len(files) <= settings.max_photos:
        raise HTTPException(422, f"Envie de 1 a {settings.max_photos} fotos")
    images, raws, problems = [], [], []
    for i, f in enumerate(files):
        data = await f.read()
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"Foto {i + 1} excede {settings.max_upload_mb} MB")
        try:
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        except Exception:
            raise HTTPException(422, f"Foto {i + 1} não é uma imagem válida")
        issues = check_quality(img)
        if issues:
            problems.append({"index": i, "issues": issues})
        images.append(img)
        raws.append(len(data))
    if problems:  # imagem ruim bloqueia a análise
        raise HTTPException(422, {"message": "Qualidade de imagem insuficiente", "photos": problems})

    diseases = db.scalars(select(Disease).where(Disease.crop == crop, Disease.is_active.is_(True))).all()
    if not diseases:
        raise HTTPException(409, "Não há doenças cadastradas para esta cultura")
    result = diagnose(images, list(diseases))

    diag = Diagnostic(user_id=user.id, crop=crop, disease_id=result.disease.id if result.disease else None,
                      severity=result.disease.severity if result.disease else None,
                      confidence=result.confidence, needs_review=result.needs_review,
                      model_version=result.model_version, captured_at=captured_at or datetime.now().astimezone())
    folder = Path(settings.upload_dir) / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    for img, size, scores in zip(images, raws, result.per_photo):
        path = folder / f"{uuid4().hex}.jpg"
        img.save(path, "JPEG", quality=90)  # normaliza e remove EXIF
        diag.photos.append(DiagnosticPhoto(path=str(path), width=img.width, height=img.height,
                                           size_bytes=size, scores=scores))
    db.add(diag)
    db.commit()
    return _own(db, user, diag.id)


@router.get("", response_model=list[DiagnosticOut])  # RF10, RF21
def list_mine(crop: str | None = None, disease_id: int | None = None, search: str | None = None,
              date_from: datetime | None = None, date_to: datetime | None = None,
              skip: int = 0, limit: int = 50, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    stmt = select(Diagnostic).options(*LOAD).where(Diagnostic.user_id == user.id)
    if crop:
        stmt = stmt.where(Diagnostic.crop == crop)
    if disease_id:
        stmt = stmt.where(Diagnostic.disease_id == disease_id)
    if search:
        stmt = stmt.join(Disease, Diagnostic.disease_id == Disease.id).where(Disease.name.ilike(f"%{search}%"))
    if date_from:
        stmt = stmt.where(Diagnostic.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Diagnostic.created_at <= date_to)
    stmt = stmt.order_by(Diagnostic.created_at.desc()).offset(skip).limit(min(limit, 100))
    return db.scalars(stmt).all()


@router.get("/{diag_id}", response_model=DiagnosticOut)
def get_one(diag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _own(db, user, diag_id)


@router.get("/{diag_id}/photos/{photo_id}")
def photo(diag_id: int, photo_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = next((p for p in _own(db, user, diag_id).photos if p.id == photo_id), None)
    if not p:
        raise HTTPException(404, "Foto não encontrada")
    return FileResponse(p.path, media_type="image/jpeg")


@router.post("/{diag_id}/feedback", status_code=201)  # RF19
def feedback(diag_id: int, body: FeedbackIn, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    d = _own(db, user, diag_id)
    if d.feedback:
        raise HTTPException(409, "Retorno já registrado para este diagnóstico")
    db.add(Feedback(diagnostic_id=d.id, is_correct=body.is_correct, comment=body.comment))
    db.commit()
    return {"ok": True}


@router.get("/{diag_id}/report.pdf")  # RF08, RF09, RF23
def report(diag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = _own(db, user, diag_id)
    return Response(build_pdf(d), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="agrocare-{d.id}.pdf"'})
