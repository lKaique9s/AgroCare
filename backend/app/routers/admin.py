from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import CROPS, ROLES, SEVERITIES, Disease, User
from ..schemas import DiseaseIn, DiseaseOut, DiseaseUpdate, RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["administração"])
admin_only = require_roles("admin")
curators = require_roles("admin", "agronomist")


def _check(crop: str | None, sev: str | None):
    if crop is not None and crop not in CROPS:
        raise HTTPException(422, f"Cultura deve ser uma de {CROPS}")
    if sev is not None and sev not in SEVERITIES:
        raise HTTPException(422, f"Severidade deve ser uma de {SEVERITIES}")


@router.post("/diseases", response_model=DiseaseOut, status_code=201)  # RF15
def create_disease(body: DiseaseIn, db: Session = Depends(get_db), _: User = Depends(curators)):
    _check(body.crop, body.severity)
    d = Disease(**body.model_dump())
    db.add(d)
    db.commit()
    return d


@router.put("/diseases/{disease_id}", response_model=DiseaseOut)  # RF16
def update_disease(disease_id: int, body: DiseaseUpdate, db: Session = Depends(get_db),
                   _: User = Depends(curators)):
    d = db.get(Disease, disease_id)
    if not d:
        raise HTTPException(404, "Doença não encontrada")
    data = body.model_dump(exclude_unset=True)
    _check(data.get("crop"), data.get("severity"))
    for k, v in data.items():
        setattr(d, k, v)
    d.validated, d.validated_at, d.validated_by_id = False, None, None  # editou: precisa revalidar
    db.commit()
    return d


@router.delete("/diseases/{disease_id}", status_code=204)  # RF16 (remoção lógica preserva o histórico)
def delete_disease(disease_id: int, db: Session = Depends(get_db), _: User = Depends(curators)):
    d = db.get(Disease, disease_id)
    if not d:
        raise HTTPException(404, "Doença não encontrada")
    d.is_active = False
    db.commit()


@router.post("/diseases/{disease_id}/validate", response_model=DiseaseOut)  # RF24
def validate_disease(disease_id: int, db: Session = Depends(get_db),
                     user: User = Depends(require_roles("agronomist", "admin"))):
    d = db.get(Disease, disease_id)
    if not d:
        raise HTTPException(404, "Doença não encontrada")
    d.validated, d.validated_by_id, d.validated_at = True, user.id, datetime.now(timezone.utc)
    db.commit()
    return d


@router.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/users/{user_id}", response_model=UserOut)  # RF17
def update_user(user_id: int, body: RoleUpdate, db: Session = Depends(get_db), me: User = Depends(admin_only)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    if body.role is not None:
        if body.role not in ROLES:
            raise HTTPException(422, f"Perfil deve ser um de {ROLES}")
        u.role = body.role
    if body.is_active is not None:
        if u.id == me.id and not body.is_active:
            raise HTTPException(400, "Você não pode desativar a própria conta")
        u.is_active = body.is_active
    db.commit()
    return u
