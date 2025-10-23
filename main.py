from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from core import init_db, log_debug
from routers import property_router, property_image_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    await init_db()
    log_debug("Database initialized and tables created")
    yield
    # Shutdown: Add any cleanup here if needed
    log_debug("Application shutting down")


app = FastAPI(
    title="Property Management API",
    description="API for managing properties and their images",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change for Production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(property_router)
app.include_router(property_image_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Property Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)