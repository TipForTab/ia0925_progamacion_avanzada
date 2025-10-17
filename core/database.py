import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Base class for ORM models
Base = declarative_base()

# Environment configuration
ENV = os.getenv("ENV", "develop")

if ENV == "production":
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "myapp")
    DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Async engine for PostgreSQL with connection pool
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    # Async session factory
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # Sync engine for migrations and other operations
    sync_engine = create_engine(
        DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
        echo=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
else:
    # SQLite configuration for development
    DATABASE_URL = "sqlite+aiosqlite:///./app.db"
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Sync engine for migrations and other operations
    sync_engine = create_engine(
        "sqlite:///./api.db",
        echo=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )

# Dependency to get async database session
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Function to create tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Function to drop tables (for testing)
async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Initialize database (create tables)
async def init_db():
    await create_tables()