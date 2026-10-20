from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import seed
from .config import settings
from .database import Base, SessionLocal, engine
from .routers import admin, auth, diagnostics, diseases


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # em produção, trocar por migrações Alembic
    with SessionLocal() as db:
        seed.run(db)
    yield


app = FastAPI(title="AgroCare API", version="0.1.0", lifespan=lifespan,
              description="Diagnóstico preliminar de doenças em café, soja e milho.")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, diseases.router, diagnostics.router, admin.router):
    app.include_router(r)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
