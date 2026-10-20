from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CROPS, Disease
from ..schemas import DiseaseOut

router = APIRouter(prefix="/diseases", tags=["catálogo"])


@router.get("", response_model=list[DiseaseOut])  # RF20: consulta livre, sem diagnóstico
def list_diseases(crop: str | None = None, q: str | None = Query(None, max_length=100),
                  only_validated: bool = False, db: Session = Depends(get_db)):
    stmt = select(Disease).where(Disease.is_active.is_(True)).order_by(Disease.name)
    if crop:
        if crop not in CROPS:
            raise HTTPException(422, f"Cultura deve ser uma de {CROPS}")
        stmt = stmt.where(Disease.crop == crop)
    if only_validated:
        stmt = stmt.where(Disease.validated.is_(True))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Disease.name.ilike(like), Disease.scientific_name.ilike(like),
                              Disease.description.ilike(like)))
    return db.scalars(stmt).all()


@router.get("/{disease_id}", response_model=DiseaseOut)
def get_disease(disease_id: int, db: Session = Depends(get_db)):
    d = db.get(Disease, disease_id)
    if not d or not d.is_active:
        raise HTTPException(404, "Doença não encontrada")
    return d
