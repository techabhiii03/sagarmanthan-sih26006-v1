"""
SagarManthan API — Intelligent Freight Forecasting & Vessel Chartering Decision Platform
SIH 2026 — Problem Statement SIH26006
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings, get_cors_origins

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("sagarmanthan")

app = FastAPI(
    title="SagarManthan API",
    description=(
        "Intelligent Freight Forecasting Model for Optimized Vessel Chartering "
        "and Bulk Cargo Procurement — East Coast of India (SIH26006). "
        "Pipeline: Forecast → Constraint → Optimization → Risk → Decision → Savings."
    ),
    version="1.2.0-sih2026",
    docs_url="/docs",
    redoc_url="/redoc",
)

_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/api/info")
def api_info():
    return {
        "name": "SagarManthan",
        "tagline": "From Reactive Spot Chartering to Predictive Multi-Voyage Intelligence",
        "problem": "SIH26006",
        "organization": "Ministry of Steel / SAIL",
        "version": "1.2.0-sih2026",
        "data_mode": settings.data_mode,
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
    }


@app.on_event("startup")
def on_startup():
    logger.info(
        "SagarManthan started | data_mode=%s | bunker=%.1f | FX=%.2f | provider=%s",
        settings.data_mode,
        settings.bunker_price_usd_mt,
        settings.usd_inr_rate,
        settings.freight_data_provider,
    )


# In the production Docker image, the compiled React app is copied here.
# API and documentation routes are registered first and remain unaffected.
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend(full_path: str):
        requested = static_dir / full_path
        if full_path and requested.is_file() and static_dir in requested.resolve().parents:
            return FileResponse(requested)
        return FileResponse(static_dir / "index.html")
