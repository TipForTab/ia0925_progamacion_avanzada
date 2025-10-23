import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from repositories import PropertyRepository, PropertyQueryBuilder
import tempfile
import os


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test"""
    # Create temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    # Create engine and session
    engine = create_engine(f"sqlite:///{temp_db.name}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Clean up temporary database
        os.unlink(temp_db.name)


@pytest.fixture
def property_repo(test_db):
    """Create PropertyRepository instance with test database"""
    return PropertyRepository(test_db)