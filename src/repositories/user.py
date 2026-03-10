from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import User


class UserRepository:
    """Repository layer for User database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create(self, user_data: dict) -> User:
        """Create a new user"""
        db_user = User(**user_data)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update(self, user_id: int, update_data: dict) -> User:
        """Update user"""
        db_user = await self.get_by_id(user_id)
        if db_user:
            for key, value in update_data.items():
                setattr(db_user, key, value)
            await self.db.commit()
            await self.db.refresh(db_user)
        return db_user

    async def delete(self, user_id: int) -> bool:
        """Delete user"""
        db_user = await self.get_by_id(user_id)
        if db_user:
            await self.db.delete(db_user)
            await self.db.commit()
            return True
        return False

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
