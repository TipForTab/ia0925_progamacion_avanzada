from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.conf import settings
from src.core.database import init_db, check_db_health
from src.routers import property_router, property_image_router, auth_router

# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    print(f"Starting application in {settings.environment} mode...")
    print(f"Database URL: {settings.database_url}")
    await init_db()
    print("Database initialized and tables created")
    yield
    # Shutdown: Add any cleanup here if needed
    print("Application shutting down")


app = FastAPI(
    title="Property Management API",
    description="API for managing properties and their images",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware with settings from .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(property_router)
app.include_router(property_image_router)
app.include_router(auth_router)


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
        # Check database connectivity
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