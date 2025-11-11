from typing import List, Dict, Any, Callable
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.repositories import ImageRepository
from src.repositories.property import PropertyRepository
from src.schemas import (
    ImageCreate,
    ImageUpdate,
    ImageResponse,
    ImageBulkCreate,
    ImageTagsUpdate
)
from src.core import log_error, log_debug


def handle_service_errors(operation_name: str):
    """Decorator to reduce error handling boilerplate"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                log_error(e, f"Failed to {operation_name}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation_name}"
                )

        return wrapper

    return decorator


class ImageService:
    """
    Business logic layer for Image operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ImageRepository(db)
        self.property_repository = PropertyRepository(db)

    @handle_service_errors("create image")
    async def create_image(self, image_data: ImageCreate) -> ImageResponse:
        """
        Create a new image.

        Pydantic already validates:
        - Required fields and data types
        - URL format (must start with http:// or https://)
        - property_id > 0
        - URL length constraints
        """
        log_debug("Creating new image", {
            "property_id": image_data.property_id,
            "img_url": image_data.img_url
        })

        # Business rule: Check if property exists
        property_exists = await self.property_repository.get_by_id(image_data.property_id)
        if not property_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {image_data.property_id} not found"
            )

        # Business rule: Check for duplicate URL for the same property
        existing_image = await self.repository.get_by_url(image_data.img_url)
        if existing_image and existing_image.property_id == image_data.property_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Image with this URL already exists for property {image_data.property_id}"
            )

        # Create image
        image_dict = image_data.model_dump()
        db_image = await self.repository.create(image_dict)

        log_debug(f"Image created successfully with ID: {db_image.id}")
        return ImageResponse.model_validate(db_image)

    @handle_service_errors("get image")
    async def get_image_by_id(self, image_id: int) -> ImageResponse:
        """Get image by ID"""
        log_debug("Fetching image by ID", {"image_id": image_id})

        db_image = await self.repository.get_by_id(image_id)
        if not db_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found"
            )

        return ImageResponse.model_validate(db_image)

    @handle_service_errors("get all images")
    async def get_all_images(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[ImageResponse]:
        """Get all images with pagination"""
        log_debug("Fetching all images", {"skip": skip, "limit": limit})

        images = await self.repository.get_all(skip, limit)
        return [ImageResponse.model_validate(img) for img in images]

    @handle_service_errors("get images by property")
    async def get_images_by_property_id(
            self,
            property_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[ImageResponse]:
        """Get all images for a specific property"""
        log_debug("Fetching images for property", {
            "property_id": property_id,
            "skip": skip,
            "limit": limit
        })

        # Business rule: Check if property exists
        property_exists = await self.property_repository.get_by_id(property_id)
        if not property_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        images = await self.repository.get_by_property_id(property_id, skip, limit)
        return [ImageResponse.model_validate(img) for img in images]

    @handle_service_errors("update image")
    async def update_image(
            self,
            image_id: int,
            update_data: ImageUpdate
    ) -> ImageResponse:
        """
        Update image.

        Pydantic validates all field constraints.
        """
        log_debug("Updating image", {"image_id": image_id})

        # Check if image exists
        existing = await self.repository.get_by_id(image_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found"
            )

        # Get update data
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )

        # Business rule: If property_id is being updated, check if new property exists
        if update_data.property_id is not None:
            property_exists = await self.property_repository.get_by_id(update_data.property_id)
            if not property_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property with ID {update_data.property_id} not found"
                )

        # Business rule: Check for duplicate URL if being updated
        if update_data.img_url:
            existing_url = await self.repository.get_by_url(update_data.img_url)
            if existing_url and existing_url.id != image_id:
                new_property_id = update_data.property_id or existing.property_id
                if existing_url.property_id == new_property_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Another image with this URL already exists for this property"
                    )

        # Update image
        updated_image = await self.repository.update(image_id, update_dict)

        log_debug(f"Image updated successfully: {image_id}")
        return ImageResponse.model_validate(updated_image)

    @handle_service_errors("update image tags")
    async def update_image_tags(
            self,
            image_id: int,
            tags_data: ImageTagsUpdate
    ) -> ImageResponse:
        """
        Update only the calculated_tags field.

        Pydantic ImageTagsUpdate validates that tags are not empty.
        """
        log_debug("Updating image tags", {"image_id": image_id})

        # Check if image exists
        existing = await self.repository.get_by_id(image_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found"
            )

        # Update tags
        updated_image = await self.repository.update_tags(image_id, tags_data.calculated_tags)

        log_debug(f"Image tags updated successfully: {image_id}")
        return ImageResponse.model_validate(updated_image)

    @handle_service_errors("delete image")
    async def delete_image(self, image_id: int) -> bool:
        """
        Hard delete image.
        """
        log_debug("Deleting image", {"image_id": image_id})

        # Check if image exists
        existing = await self.repository.get_by_id(image_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found"
            )

        success = await self.repository.delete(image_id)
        if success:
            log_debug(f"Image deleted successfully: {image_id}")

        return success

    @handle_service_errors("delete images by property")
    async def delete_images_by_property_id(self, property_id: int) -> Dict[str, Any]:
        """
        Delete all images for a specific property.
        """
        log_debug("Deleting all images for property", {"property_id": property_id})

        # Business rule: Check if property exists
        property_exists = await self.property_repository.get_by_id(property_id)
        if not property_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        deleted_count = await self.repository.delete_by_property_id(property_id)

        log_debug(f"Images deleted for property {property_id}", {"count": deleted_count})
        return {
            "property_id": property_id,
            "deleted_count": deleted_count
        }

    @handle_service_errors("bulk create images")
    async def bulk_create_images(self, bulk_data: ImageBulkCreate) -> List[ImageResponse]:
        """
        Bulk create images for a property.

        Pydantic ImageBulkCreate validates:
        - property_id > 0
        - image_urls list has 1-50 items
        - All URLs are properly formatted
        """
        log_debug("Bulk creating images", {
            "property_id": bulk_data.property_id,
            "image_count": len(bulk_data.image_urls)
        })

        # Business rule: Check if property exists
        property_exists = await self.property_repository.get_by_id(bulk_data.property_id)
        if not property_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {bulk_data.property_id} not found"
            )

        # Business rule: Check for duplicate URLs in the same property
        existing_urls = set()
        for url in bulk_data.image_urls:
            existing_image = await self.repository.get_by_url(url)
            if existing_image and existing_image.property_id == bulk_data.property_id:
                existing_urls.add(url)

        if existing_urls:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Some URLs already exist for this property: {', '.join(list(existing_urls)[:3])}"
            )

        # Prepare images data
        images_data = [
            {
                "property_id": bulk_data.property_id,
                "img_url": url,
                "calculated_tags": None
            }
            for url in bulk_data.image_urls
        ]

        # Bulk create
        db_images = await self.repository.create_bulk(images_data)

        log_debug(f"Bulk images created successfully: {len(db_images)} images")
        return [ImageResponse.model_validate(img) for img in db_images]

    @handle_service_errors("bulk delete images")
    async def bulk_delete_images(self, image_ids: List[int]) -> Dict[str, Any]:
        """
        Bulk delete images by IDs.
        """
        log_debug("Bulk deleting images", {"image_ids_count": len(image_ids)})

        if not image_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image IDs provided"
            )

        deleted_count = await self.repository.bulk_delete(image_ids)

        return {
            "deleted_count": deleted_count,
            "requested_count": len(image_ids)
        }

    @handle_service_errors("bulk update tags")
    async def bulk_update_tags(
            self,
            image_ids: List[int],
            tags: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Bulk update tags for multiple images.
        """
        log_debug("Bulk updating tags", {
            "image_ids_count": len(image_ids),
            "tags_keys": list(tags.keys())
        })

        if not image_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image IDs provided"
            )

        if not tags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tags cannot be empty"
            )

        updated_count = await self.repository.bulk_update_tags(image_ids, tags)

        return {
            "updated_count": updated_count,
            "requested_count": len(image_ids)
        }

    @handle_service_errors("search images")
    async def search_images(self, filters: Dict[str, Any]) -> List[ImageResponse]:
        """
        Advanced image search with dynamic filters.
        """
        log_debug("Searching images", {"filters": filters})

        images = await self.repository.advanced_search(filters)
        return [ImageResponse.model_validate(img) for img in images]

    @handle_service_errors("get image statistics")
    async def get_image_statistics(self) -> Dict[str, Any]:
        """Get comprehensive image statistics"""
        log_debug("Calculating image statistics")

        stats = await self.repository.get_image_statistics()

        log_debug("Image statistics calculated", stats)
        return stats

    @handle_service_errors("get images without tags")
    async def get_images_without_tags(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[ImageResponse]:
        """Get images that don't have calculated tags"""
        log_debug("Fetching images without tags", {"skip": skip, "limit": limit})

        images = await self.repository.get_images_without_tags(skip, limit)
        return [ImageResponse.model_validate(img) for img in images]

    @handle_service_errors("find duplicate images")
    async def find_duplicate_images(self) -> List[Dict[str, Any]]:
        """Find images with duplicate URLs"""
        log_debug("Finding duplicate images")

        duplicates = await self.repository.find_duplicates_by_url()

        log_debug("Duplicate images found", {"count": len(duplicates)})
        return duplicates

    @handle_service_errors("check URL exists")
    async def check_url_exists(self, url: str) -> Dict[str, Any]:
        """Check if an image with this URL already exists"""
        log_debug("Checking if URL exists", {"url": url})

        exists = await self.repository.check_url_exists(url)
        existing_image = None

        if exists:
            existing_image = await self.repository.get_by_url(url)

        return {
            "exists": exists,
            "image_id": existing_image.id if existing_image else None,
            "property_id": existing_image.property_id if existing_image else None
        }

    @handle_service_errors("get recent images")
    async def get_recent_images(
            self,
            days: int = 7,
            limit: int = 100
    ) -> List[ImageResponse]:
        """Get images created in the last N days"""
        log_debug("Fetching recent images", {"days": days, "limit": limit})

        if days < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be at least 1"
            )

        if days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days cannot exceed 365"
            )

        images = await self.repository.get_recent_images(days, limit)
        return [ImageResponse.model_validate(img) for img in images]