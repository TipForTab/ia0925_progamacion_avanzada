from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.database import init_db
import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
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



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
