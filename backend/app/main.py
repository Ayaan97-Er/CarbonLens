import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.utils.logging_config import setup_logging
from app.utils.seed_data import seed_database
from app.routes import (
    auth,
    activities,
    dashboard,
    goals,
    recommendations,
    simulator,
    achievements,
    leaderboard,
    categories,
    admin,
)

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event lifecycle."""
    logger.info("Initializing CarbonLens platform...")
    try:
        seed_database()
        logger.info("Database schema and seed data initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    yield
    logger.info("Shutting down CarbonLens platform...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# CarbonLens API — Modern Carbon Footprint & Sustainability Intelligence Platform

CarbonLens is an enterprise-grade sustainability intelligence platform allowing users to:
* **Track** carbon-emitting and mitigation activities across transportation, electricity, heating, flights, food, and goods.
* **Calculate** precise estimated emissions in kg CO₂e using verified emission factors (EPA, DEFRA, IPCC).
* **Analyze** multi-month trends, category breakdowns, daily averages, and budget burn-down.
* **Set Goals** and track real-time monthly carbon allowances.
* **Simulate** What-If scenarios with projected emissions, monthly/annual savings, tree-equivalents, and avoided driving distance.
* **Earn Achievements** automatically based on logging habits and emission reductions.
* **Compete** on a privacy-safe community leaderboard with the CarbonLens Sustainability Score.
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Our engineering team has been notified.",
            "error_type": type(exc).__name__,
        },
    )


# Register API Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(activities.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(goals.router, prefix=api_v1_prefix)
app.include_router(recommendations.router, prefix=api_v1_prefix)
app.include_router(simulator.router, prefix=api_v1_prefix)
app.include_router(achievements.router, prefix=api_v1_prefix)
app.include_router(leaderboard.router, prefix=api_v1_prefix)
app.include_router(categories.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)


# Health Check Endpoints
@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Frontend Static Files Serving
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # Serve HTML pages directly on root routes for seamless local usage
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/{page_name}.html", include_in_schema=False)
    async def serve_page(page_name: str):
        page_path = frontend_dir / f"{page_name}.html"
        if page_path.exists():
            return FileResponse(page_path)
        return FileResponse(frontend_dir / "index.html")

    # Serve JS and CSS folders for direct root references
    css_dir = frontend_dir / "css"
    js_dir = frontend_dir / "js"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
