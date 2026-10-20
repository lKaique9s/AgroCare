# AgroCare — backend (base do projeto)

API em **FastAPI + PostgreSQL** para diagnóstico preliminar de doenças em café, soja e milho.
O classificador está isolado em `backend/app/ml/`: hoje roda um **stub de demonstração**; quando existir
um modelo treinado, basta exportá-lo para ONNX e apontar `MODEL_PATH`/`LABELS_PATH` no `.env`.

## Rodar
```bash
cp .env.example .env          # edite SECRET_KEY e ADMIN_PASSWORD
docker compose up --build
# docs interativas: http://localhost:8000/docs
```
Sem Docker: `cd backend && pip install -r requirements-dev.txt && DATABASE_URL=sqlite:///dev.db uvicorn app.main:app --reload`
Testes: `cd backend && pytest`

## Mapa dos requisitos
| RF | Onde |
|---|---|
| RF01–RF04, RF18 | `POST /diagnostics` (1 a 4 fotos, verificação de qualidade, classificação) |
| RF05–RF07 | resposta de `DiagnosticOut` (doença, causas/cuidados, severidade, confiança) |
| RF08, RF09, RF23 | `GET /diagnostics/{id}/report.pdf` |
| RF10, RF21 | `GET /diagnostics` (cultura, doença, busca, período) |
| RF19 | `POST /diagnostics/{id}/feedback` |
| RF20 | `GET /diseases` (público) |
| RF13, RF14, RF17 | `/auth/*`, `/admin/users` |
| RF15, RF16, RF24 | `/admin/diseases` (CRUD + `validate` por agrônomo/admin) |
| RF22 | cliente guarda a fila offline e envia com `captured_at` |

Regras: **RN03** (sem agrotóxicos) no texto do relatório e do catálogo · **RN04** limite de confiança em
`CONFIDENCE_THRESHOLD` (`needs_review`) · **RN06** histórico só do próprio usuário.

## Pendências conhecidas
- Trocar `create_all` por **migrações Alembic**.
- Limite de tentativas de login, refresh token e recuperação de senha.
- Catálogo de partida (`app/seed.py`) **não está validado** por agrônomo (`validated=false`).
- Fotos em disco local; para produção usar S3 ou compatível.
- Modelo real: ver plano de dados e treino (próxima etapa).
