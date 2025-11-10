from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from src.conf import settings

# Dependency to get async database session
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
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
    print(f"Initializing database with URL: {settings.database_url}")
    print(f"Environment: {settings.environment}")
    await create_tables()
    print("Database tables created successfully")


# Health check function
async def check_db_health():
    """Check if database connection is healthy"""
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False


Base = declarative_base()
# Determine database configuration based on settings
if settings.is_production or settings.database_url.startswith("postgresql"):
    # Use PostgreSQL with asyncpg
    if settings.database_url.startswith("postgresql://"):
        # Convert to asyncpg URL if needed
        database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        database_url = settings.database_url

    # Async engine for PostgreSQL with connection pool
    engine = create_async_engine(
        database_url,
        echo=settings.is_development,  # Only echo SQL in development
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )

    # Async session factory
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Sync engine for migrations and other operations
    sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    sync_engine = create_engine(
        sync_database_url,
        echo=settings.is_development,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
else:
    # SQLite for development/testing
    if settings.database_url.startswith("sqlite:///"):
        # Convert to aiosqlite URL
        database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    else:
        database_url = settings.database_url

    engine = create_async_engine(
        database_url,
        echo=settings.is_development,
        future=True,
    )
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # Sync engine for migrations and other operations
    sync_database_url = database_url.replace("sqlite+aiosqlite:///", "sqlite:///")
    sync_engine = create_engine(
        sync_database_url,
        echo=settings.is_development,
    )
