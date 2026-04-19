"""
Lendlyfin Backend API
FastAPI + SQLAlchemy + SQLite (dev) / PostgreSQL (prod)

Run locally:  uvicorn app.main:app --reload --port 8000
Docs:         http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import get_settings
from app.core.database import engine, Base, SessionLocal
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware, RequestLoggingMiddleware
from app.api import auth, leads, rates, calculator
from app.services.seeder import seed_database

settings = get_settings()

# ── CREATE TABLES ─────────────────────────────────────────────
# In production, use Alembic migrations instead
Base.metadata.create_all(bind=engine)

# ── SEED DATABASE ─────────────────────────────────────────────
print("Seeding database...")
with SessionLocal() as db:
    seed_database(db)

# ── APP ───────────────────────────────────────────────────────
app = FastAPI(
    title="Lendlyfin API",
    description="Backend API for Lendlyfin mortgage platform",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MIDDLEWARE ─────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)
if settings.APP_ENV == "production":
    app.add_middleware(RequestLoggingMiddleware)

# ── ROUTERS ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(rates.router)
app.include_router(calculator.router)


# ── HEALTH CHECK ──────────────────────────────────────────────
MARKER = "INLINE-V3-RUNNING"

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "marker": MARKER,
    }

@app.get("/api/test-marker")
def test_marker():
    return {"marker": MARKER}


# ── SERVE FRONTEND (production) ───────────────────────────────
# In production, FastAPI serves the static HTML files too.
# In development, open the HTML files directly in your browser.
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Default to index.html for SPA routing
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
