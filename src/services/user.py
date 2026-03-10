from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.repositories.user import UserRepository
from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from src.core import log_error, log_debug
from src.core.security import hash_password, verify_password
from src.services.property_image import handle_service_errors


class UserService:
    """
    Business logic layer for User operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    @handle_service_errors("create user")
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user.

        Pydantic validates:
        - Required fields and data types
        - Email format
        - Username/password length constraints
        """
        log_debug(
            "Creating new user",
            {"username": user_data.username, "email": user_data.email},
        )

        # Business rule: Check if username already exists
        existing_username = await self.repository.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            )

        # Business rule: Check if email already exists
        existing_email = await self.repository.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

        # Hash password before storing
        user_dict = user_data.model_dump()
        user_dict["hashed_password"] = hash_password(user_dict.pop("password"))

        db_user = await self.repository.create(user_dict)

        log_debug(f"User created successfully with ID: {db_user.id}")
        return UserResponse.model_validate(db_user)

    @handle_service_errors("get user")
    async def get_user_by_id(self, user_id: int) -> UserResponse:
        """Get user by ID"""
        log_debug("Fetching user by ID", {"user_id": user_id})

        db_user = await self.repository.get_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        return UserResponse.model_validate(db_user)

    @handle_service_errors("get user by username")
    async def get_user_by_username(self, username: str) -> UserResponse:
        """Get user by username"""
        log_debug("Fetching user by username", {"username": username})

        db_user = await self.repository.get_by_username(username)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username '{username}' not found",
            )

        return UserResponse.model_validate(db_user)

    @handle_service_errors("get user by email")
    async def get_user_by_email(self, email: str) -> UserResponse:
        """Get user by email"""
        log_debug("Fetching user by email", {"email": email})

        db_user = await self.repository.get_by_email(email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{email}' not found",
            )

        return UserResponse.model_validate(db_user)

    @handle_service_errors("get all users")
    async def get_all_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserResponse]:
        """Get all users with pagination"""
        log_debug("Fetching all users", {"skip": skip, "limit": limit})

        users = await self.repository.get_all(skip, limit)
        return [UserResponse.model_validate(user) for user in users]

    @handle_service_errors("update user")
    async def update_user(self, user_id: int, update_data: UserUpdate) -> UserResponse:
        """
        Update user.

        Pydantic validates all field constraints.
        """
        log_debug("Updating user", {"user_id": user_id})

        # Check if user exists
        existing = await self.repository.get_by_id(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Get update data
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )

        # Business rule: If username is being updated, check for duplicates
        if update_data.username is not None:
            existing_username = await self.repository.get_by_username(
                update_data.username
            )
            if existing_username and existing_username.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken",
                )

        # Business rule: If email is being updated, check for duplicates
        if update_data.email is not None:
            existing_email = await self.repository.get_by_email(update_data.email)
            if existing_email and existing_email.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Email already taken"
                )

        # Hash password if being updated
        if "password" in update_dict:
            update_dict["hashed_password"] = hash_password(update_dict.pop("password"))

        updated_user = await self.repository.update(user_id, update_dict)

        log_debug(f"User updated successfully: {user_id}")
        return UserResponse.model_validate(updated_user)

    @handle_service_errors("delete user")
    async def delete_user(self, user_id: int) -> bool:
        """Hard delete user."""
        log_debug("Deleting user", {"user_id": user_id})

        existing = await self.repository.get_by_id(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        success = await self.repository.delete(user_id)
        if success:
            log_debug(f"User deleted successfully: {user_id}")

        return success

    @handle_service_errors("authenticate user")
    async def authenticate_user(self, username: str, password: str) -> UserResponse:
        """
        Authenticate user by username and password.
        Returns user if credentials are valid.
        """
        log_debug("Authenticating user", {"username": username})

        db_user = await self.repository.get_by_username(username)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not verify_password(password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        log_debug(f"User authenticated successfully: {username}")
        return UserResponse.model_validate(db_user)

    @handle_service_errors("check username exists")
    async def check_username_exists(self, username: str) -> Dict[str, Any]:
        """Check if a username is already taken"""
        log_debug("Checking if username exists", {"username": username})

        exists = await self.repository.get_by_username(username) is not None

        return {"username": username, "exists": exists}

    @handle_service_errors("check email exists")
    async def check_email_exists(self, email: str) -> Dict[str, Any]:
        """Check if an email is already registered"""
        log_debug("Checking if email exists", {"email": email})

        exists = await self.repository.get_by_email(email) is not None

        return {"email": email, "exists": exists}
