import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import auth, crops, dashboard, health, intercrop, markets, risk
from app.core.config import settings
from app.database.db import Base, SessionLocal, engine
from app.models import models  # noqa: F401  (register tables)
from app.services import crop_health, market_intelligence, seed

log = logging.getLogger("agri360")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # schema initialisation; see docs/architecture.md for migrations with Alembic
    with SessionLocal() as db:
        seed.seed_catalog(db)
        market_intelligence.seed_market_samples(db)
        if settings.seed_demo:
            seed.seed_demo(db)
    crop_health.load_classifier()  # app starts even when no model is configured
    yield


app = FastAPI(title="AGRI INTELLIGENCE 360", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, crops.router, health.router, risk.router, markets.router, intercrop.router, dashboard.router):
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse({"detail": "Something went wrong on the server. Please try again."}, status_code=500)


@app.get("/api/health-check")
def health_check():
    return {"status": "ok", "model_available": crop_health.get_classifier().available}
