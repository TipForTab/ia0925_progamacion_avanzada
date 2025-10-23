from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status

from dependencies import get_property_service
from services import PropertyService
from schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertySearchFilters,
    BulkUpdateAvailability
)

router = APIRouter(
    prefix="/properties",
    tags=["Properties"]
)


@router.post(
    "/",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property",
    description="Create a new property with all required information"
)
async def create_property(
        property_data: PropertyCreate,
        service: PropertyService = Depends(get_property_service)
):
    """
    Create a new property.

    Validates:
    - All required fields are present
    - Price is at least $100
    - Square meters is between 5 and 10,000
    - At least one property type is selected (apartment or house)
    - Source URL is unique
    """
    return await service.create_property(property_data)


# ============================================================================
# READ ENDPOINTS
# ============================================================================

@router.get(
    "/",
    response_model=List[PropertyResponse],
    summary="Get all properties",
    description="Get a paginated list of all properties"
)
async def get_properties(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        service: PropertyService = Depends(get_property_service)
):
    """Get all properties with pagination"""
    return await service.get_all_properties(skip=skip, limit=limit)


@router.get(
    "/available",
    response_model=List[PropertyResponse],
    summary="Get available properties",
    description="Get a paginated list of available properties only"
)
async def get_available_properties(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        service: PropertyService = Depends(get_property_service)
):
    """Get only available properties"""
    return await service.get_available_properties(skip=skip, limit=limit)


@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get property by ID",
    description="Get detailed information about a specific property"
)
async def get_property(
        property_id: int,
        service: PropertyService = Depends(get_property_service)
):
    """Get a specific property by ID"""
    return await service.get_property_by_id(property_id)


@router.post(
    "/search",
    response_model=List[PropertyResponse],
    summary="Advanced property search",
    description="Search properties with multiple filters and sorting options"
)
async def search_properties(
        filters: PropertySearchFilters,
        service: PropertyService = Depends(get_property_service)
):
    """
    Advanced search with filters.

    Supports filtering by:
    - Property type (apartment/house)
    - Price range
    - Number of rooms/bathrooms
    - Square meters range
    - Floor number/range
    - Location (address/title)
    - Availability
    - Amenities
    - Images presence
    - Date ranges

    Also supports:
    - Sorting by multiple fields
    - Pagination
    """
    return await service.search_properties(filters)


@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update property",
    description="Update an existing property's information"
)
async def update_property(
        property_id: int,
        property_data: PropertyUpdate,
        service: PropertyService = Depends(get_property_service)
):
    """
    Update a property.

    Only provided fields will be updated.
    Validates source URL uniqueness if updated.
    """
    return await service.update_property(property_id, property_data)


@router.patch(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Partially update property",
    description="Partially update a property (same as PUT)"
)
async def partial_update_property(
        property_id: int,
        property_data: PropertyUpdate,
        service: PropertyService = Depends(get_property_service)
):
    return await service.update_property(property_id, property_data)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete property",
    description="Permanently delete a property (cannot have images)"
)
async def delete_property(
        property_id: int,
        service: PropertyService = Depends(get_property_service)
):
    """
    Hard delete a property.

    Business rule: Cannot delete properties with associated images.
    Use soft delete instead or delete images first.
    """
    await service.delete_property(property_id)


@router.post(
    "/{property_id}/soft-delete",
    response_model=PropertyResponse,
    summary="Soft delete property",
    description="Mark property as unavailable without deleting it"
)
async def soft_delete_property(
        property_id: int,
        service: PropertyService = Depends(get_property_service)
):
    """
    Soft delete by marking as unavailable.
    """
    return await service.soft_delete_property(property_id)



@router.post(
    "/bulk/update-availability",
    response_model=Dict[str, Any],
    summary="Bulk update availability",
    description="Update availability status for multiple properties at once"
)
async def bulk_update_availability(
        bulk_data: BulkUpdateAvailability,
        service: PropertyService = Depends(get_property_service)
):
    """
    Bulk update availability status.

    Can update up to 1000 properties at once.
    Property IDs must be unique.
    """
    return await service.bulk_update_availability(bulk_data)


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get(
    "/statistics/summary",
    response_model=Dict[str, Any],
    summary="Get property statistics",
    description="Get comprehensive statistics about all properties"
)
async def get_statistics(
        service: PropertyService = Depends(get_property_service)
):
    """
    Get property statistics including:
    - Total, available, and unavailable counts
    - Property type distribution (apartments vs houses)
    - Price statistics (min, max, avg)
    - Size statistics (min, max, avg square meters)
    - Availability percentage
    """
    return await service.get_property_statistics()
