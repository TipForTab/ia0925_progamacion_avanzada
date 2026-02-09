from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.conf import settings
from src.core.database import init_db, check_db_health

# Routers existentes
from src.routers import property_router, property_image_router, auth_router

# Routers nuevos (orquestación)
from src.routers import extract_data_router, califier_router, jobs_router


# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting application in {settings.environment} mode...")
    print(f"Database URL: {settings.database_url}")

    # Si no quieres init_db en dev, comenta esta línea.
    await init_db()

    print("Database initialized and tables created")
    yield

    # Shutdown
    print("Application shutting down")


app = FastAPI(
    title="Property Management API",
    description="API for managing properties and their images",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Include existing routers
# ======================
app.include_router(property_router)
app.include_router(property_image_router)
app.include_router(auth_router)

# ======================
# Include orchestration routers
# ======================
app.include_router(extract_data_router)   # /extract-data/...
app.include_router(califier_router)        # /internal/califier (stub)
app.include_router(jobs_router)           # /jobs/{job_id}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Property Management API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health():
    try:
        db_healthy = await check_db_health()
        if not db_healthy:
            raise HTTPException(status_code=503, detail="Database connection failed")

        return {
            "status": "healthy",
            "environment": settings.environment,
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.is_development
    )
