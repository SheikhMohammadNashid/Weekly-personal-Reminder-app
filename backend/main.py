"""
main.py — FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes.reminders import router as reminders_router
from routes.notifications import router as notifications_router
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.APP_ENV)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="WeeklyReminder API",
    description="Random weekly reminders via Email, SMS, and WhatsApp.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
# nginx intercepts OPTIONS preflights before they reach here.
# This wildcard is a safety net for direct port-8000 access.
# allow_credentials MUST be False when allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(reminders_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")


# ── Health ────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/", tags=["System"])
async def root():
    return {"message": "WeeklyReminder API — see /docs"}
