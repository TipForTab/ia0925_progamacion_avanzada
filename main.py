from fastapi import FastAPI
from contextlib import asynccontextmanager

from core import init_db, log_debug
import models


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



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
