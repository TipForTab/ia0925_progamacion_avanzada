# src/scripts/seed_users.py
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import async_session_maker
from src.services.user import UserService
from src.schemas.user import UserCreate


SEED_USERS = [
    {"username": "antonio", "email": "antonio@example.com", "password": "admin1234"},
    {"username": "daniel_l", "email": "daniel_l@example.com", "password": "admin1234"},
    {"username": "daniel_g", "email": "daniel_g@example.com", "password": "admin1234"},
]


async def seed_users():
    """Create seed users in the database."""
    async with async_session_maker() as db:
        service = UserService(db)
        
        for user_data in SEED_USERS:
            try:
                user = await service.create_user(UserCreate(**user_data))
                print(f"✓ Created user: {user.username} (ID: {user.id})")
            except Exception as e:
                if "already" in str(e.detail).lower():
                    print(f"⊘ User already exists: {user_data['username']}")
                else:
                    print(f"✗ Failed to create {user_data['username']}: {e}")


if __name__ == "__main__":
    print("Seeding users...")
    asyncio.run(seed_users())
    print("Done!")