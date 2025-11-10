from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status

from src.dependencies import get_image_service
from src.services import ImageService
from src.schemas import (
    ImageCreate,
    ImageUpdate,
    ImageResponse,
    ImageBulkCreate,
    ImageTagsUpdate
)

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)


# ============================================================================
# CREATE ENDPOINTS
# ============================================================================

@router.post(
    "/",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new image",
    description="Create a new image for a property"
)
async def create_image(
        image_data: ImageCreate,
        service: ImageService = Depends(get_image_service)
):
    """
    Create a new image.

    Validates:
    - Property exists
    - URL format is valid (http:// or https://)
    - URL doesn't already exist for the same property
    """
    return await service.create_image(image_data)


@router.post(
    "/bulk",
    response_model=List[ImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create images",
    description="Create multiple images for a property at once"
)
async def bulk_create_images(
        bulk_data: ImageBulkCreate,
        service: ImageService = Depends(get_image_service)
):
    """
    Bulk create images for a property.

    Validates:
    - Property exists
    - All URLs are properly formatted
    - Can create 1-50 images at once
    - No duplicate URLs for the same property
    """
    return await service.bulk_create_images(bulk_data)


# ============================================================================
# READ ENDPOINTS
# ============================================================================

@router.get(
    "/",
    response_model=List[ImageResponse],
    summary="Get all images",
    description="Get a paginated list of all images"
)
async def get_images(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        service: ImageService = Depends(get_image_service)
):
    """Get all images with pagination"""
    return await service.get_all_images(skip=skip, limit=limit)


@router.get(
    "/{image_id}",
    response_model=ImageResponse,
    summary="Get image by ID",
    description="Get detailed information about a specific image"
)
async def get_image(
        image_id: int,
        service: ImageService = Depends(get_image_service)
):
    """Get a specific image by ID"""
    return await service.get_image_by_id(image_id)


@router.get(
    "/property/{property_id}",
    response_model=List[ImageResponse],
    summary="Get images by property",
    description="Get all images for a specific property"
)
async def get_images_by_property(
        property_id: int,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        service: ImageService = Depends(get_image_service)
):
    """
    Get all images for a specific property.

    Validates that the property exists.
    """
    return await service.get_images_by_property_id(property_id, skip=skip, limit=limit)


@router.get(
    "/without-tags/list",
    response_model=List[ImageResponse],
    summary="Get images without tags",
    description="Get images that don't have calculated tags"
)
async def get_images_without_tags(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        service: ImageService = Depends(get_image_service)
):
    """
    Get images without calculated tags.

    Useful for finding images that need to be processed by AI tagging.
    """
    return await service.get_images_without_tags(skip=skip, limit=limit)


@router.get(
    "/recent/list",
    response_model=List[ImageResponse],
    summary="Get recent images",
    description="Get images created in the last N days"
)
async def get_recent_images(
        days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        service: ImageService = Depends(get_image_service)
):
    """
    Get images created in the last N days.

    Default: Last 7 days
    Max: 365 days
    """
    return await service.get_recent_images(days=days, limit=limit)


@router.post(
    "/search",
    response_model=List[ImageResponse],
    summary="Advanced image search",
    description="Search images with multiple filters and sorting options"
)
async def search_images(
        filters: Dict[str, Any],
        service: ImageService = Depends(get_image_service)
):
    """
    Advanced search with filters.

    Supports filtering by:
    - property_id: Filter by specific property
    - property_ids: Filter by multiple properties
    - url: Filter by URL (exact or pattern match)
    - url_pattern: Search in URL
    - url_domain: Filter by domain
    - has_tags: Filter by tag presence (true/false)
    - tag_key: Filter by specific tag key
    - tag_value: Filter by tag value (requires tag_key)
    - start_date: Filter by creation date start
    - end_date: Filter by creation date end
    - date_field: Which date field to filter (created_at/updated_at)

    Sorting:
    - order_by: id, property_id, created_at, updated_at
    - ascending: true/false (default: false for dates)

    Pagination:
    - skip: Number of records to skip
    - limit: Maximum records to return
    """
    return await service.search_images(filters)


# ============================================================================
# UPDATE ENDPOINTS
# ============================================================================

@router.put(
    "/{image_id}",
    response_model=ImageResponse,
    summary="Update image",
    description="Update an existing image's information"
)
async def update_image(
        image_id: int,
        image_data: ImageUpdate,
        service: ImageService = Depends(get_image_service)
):
    """
    Update an image.

    Only provided fields will be updated.
    Validates:
    - New property exists (if property_id is updated)
    - URL uniqueness (if URL is updated)
    """
    return await service.update_image(image_id, image_data)


@router.patch(
    "/{image_id}",
    response_model=ImageResponse,
    summary="Partially update image",
    description="Partially update an image (same as PUT)"
)
async def partial_update_image(
        image_id: int,
        image_data: ImageUpdate,
        service: ImageService = Depends(get_image_service)
):
    """Partial update (same as PUT for this API)"""
    return await service.update_image(image_id, image_data)


@router.patch(
    "/{image_id}/tags",
    response_model=ImageResponse,
    summary="Update image tags",
    description="Update only the calculated_tags field for an image"
)
async def update_image_tags(
        image_id: int,
        tags_data: ImageTagsUpdate,
        service: ImageService = Depends(get_image_service)
):
    """
    Update only the calculated_tags field.

    Useful for AI processing pipelines that add tags to images.
    Validates that tags are not empty.
    """
    return await service.update_image_tags(image_id, tags_data)



# ============================================================================
# DELETE ENDPOINTS
# ============================================================================

@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete image",
    description="Permanently delete an image"
)
async def delete_image(
        image_id: int,
        service: ImageService = Depends(get_image_service)
):
    """
    Hard delete an image.
    """
    await service.delete_image(image_id)


@router.delete(
    "/property/{property_id}/all",
    response_model=Dict[str, Any],
    summary="Delete all images for a property",
    description="Delete all images associated with a specific property"
)
async def delete_images_by_property(
        property_id: int,
        service: ImageService = Depends(get_image_service)
):
    """
    Delete all images for a specific property.

    Validates that the property exists.
    Returns the count of deleted images.
    """
    return await service.delete_images_by_property_id(property_id)


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get(
    "/check/url-exists",
    response_model=Dict[str, Any],
    summary="Check if URL exists",
    description="Check if an image with this URL already exists"
)
async def check_url_exists(
        url: str = Query(..., description="Image URL to check"),
        service: ImageService = Depends(get_image_service)
):
    """
    Check if an image with this URL already exists.

    Returns:
    - exists: boolean
    - image_id: ID of existing image (if exists)
    - property_id: ID of property (if exists)
    """
    return await service.check_url_exists(url)


@router.get(
    "/duplicates/find",
    response_model=List[Dict[str, Any]],
    summary="Find duplicate images",
    description="Find images with duplicate URLs"
)
async def find_duplicate_images(
        service: ImageService = Depends(get_image_service)
):
    """
    Find images with duplicate URLs.

    Returns list of URLs that appear more than once with their counts.
    Useful for data cleanup.
    """
    return await service.find_duplicate_images()


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get(
    "/statistics/summary",
    response_model=Dict[str, Any],
    summary="Get image statistics",
    description="Get comprehensive statistics about all images"
)
async def get_statistics(
        service: ImageService = Depends(get_image_service)
):
    """
    Get image statistics including:
    - Total images count
    - Images with/without tags
    - Total properties with images
    - Average images per property
    """
    return await service.get_image_statistics()