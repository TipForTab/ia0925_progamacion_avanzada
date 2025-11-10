from typing import List, Dict, Any, Callable
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.repositories.property import PropertyRepository
from src.schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertySearchFilters,
    BulkUpdateAvailability
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


class PropertyService:
    """
    Business logic layer for Property operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PropertyRepository(db)

    @handle_service_errors("create property")
    async def create_property(self, property_data: PropertyCreate) -> PropertyResponse:
        """
        Create a new property.

        Pydantic already validates:
        - Required fields and data types
        - Min/max values (price >= 100, square_meters <= 10000, etc.)
        - Property type (at least one must be true)
        - Reasonable value ranges
        """
        log_debug("Creating new property", {"title": property_data.title})

        # Business rule: Check for duplicate source_url
        if property_data.source_url:
            existing = await self.repository.get_by_source_url(property_data.source_url)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Property with source URL already exists: {property_data.source_url}"
                )

        # Create property
        property_dict = property_data.model_dump()
        db_property = await self.repository.create(property_dict)

        log_debug(f"Property created successfully with ID: {db_property.id}")
        return PropertyResponse.model_validate(db_property)

    @handle_service_errors("get property")
    async def get_property_by_id(self, property_id: int) -> PropertyResponse:
        """Get property by ID"""
        log_debug("Fetching property by ID", {"property_id": property_id})

        db_property = await self.repository.get_by_id(property_id)
        if not db_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        return PropertyResponse.model_validate(db_property)

    @handle_service_errors("get all properties")
    async def get_all_properties(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[PropertyResponse]:
        """Get all properties with pagination"""
        log_debug("Fetching all properties", {"skip": skip, "limit": limit})

        properties = await self.repository.get_all(skip, limit)
        return [PropertyResponse.model_validate(prop) for prop in properties]

    @handle_service_errors("get available properties")
    async def get_available_properties(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[PropertyResponse]:
        """Get only available properties"""
        log_debug("Fetching available properties", {"skip": skip, "limit": limit})

        properties = await self.repository.get_available(skip, limit)
        return [PropertyResponse.model_validate(prop) for prop in properties]

    @handle_service_errors("update property")
    async def update_property(
            self,
            property_id: int,
            property_data: PropertyUpdate
    ) -> PropertyResponse:
        """
        Create a new property.

        Pydantic already validates:
        - Required fields and data types
        - Min/max values (price >= 100, square_meters <= 10000, etc.)
        - Property type (at least one must be true)
        - Reasonable value ranges
        """
        log_debug("Creating new property", {"title": property_data.title})

        # Business rule: Check for duplicate source_url
        if property_data.source_url:
            existing = await self.repository.get_by_source_url(property_data.source_url)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Property with source URL already exists: {property_data.source_url}"
                )

        # Create property
        property_dict = property_data.model_dump()
        db_property = await self.repository.create(property_dict)

        log_debug(f"Property created successfully with ID: {db_property.id}")
        return PropertyResponse.model_validate(db_property)

    @handle_service_errors("get property")
    async def get_property_by_id(self, property_id: int) -> PropertyResponse:
        """Get property by ID"""
        log_debug("Fetching property by ID", {"property_id": property_id})

        db_property = await self.repository.get_by_id(property_id)
        if not db_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        return PropertyResponse.model_validate(db_property)

    @handle_service_errors("get all properties")
    async def get_all_properties(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[PropertyResponse]:
        """Get all properties with pagination"""
        log_debug("Fetching all properties", {"skip": skip, "limit": limit})

        properties = await self.repository.get_all(skip, limit)
        return [PropertyResponse.model_validate(prop) for prop in properties]

    @handle_service_errors("get available properties")
    async def get_available_properties(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[PropertyResponse]:
        """Get only available properties"""
        log_debug("Fetching available properties", {"skip": skip, "limit": limit})

        properties = await self.repository.get_available(skip, limit)
        return [PropertyResponse.model_validate(prop) for prop in properties]

    @handle_service_errors("update property")
    async def update_property(
            self,
            property_id: int,
            update_data: PropertyUpdate
    ) -> PropertyResponse:
        """
        Update property.

        Pydantic validates all field constraints.
        """
        log_debug("Updating property", {"property_id": property_id})

        # Check if property exists
        existing = await self.repository.get_by_id(property_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        # Get update data
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )

        # Business rule: Check for duplicate source_url if being updated
        if update_data.source_url:
            existing_url = await self.repository.get_by_source_url(update_data.source_url)
            if existing_url and existing_url.id != property_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another property with this source URL already exists"
                )

        # Update property
        updated_property = await self.repository.update(property_id, update_dict)

        log_debug(f"Property updated successfully: {property_id}")
        return PropertyResponse.model_validate(updated_property)

    @handle_service_errors("delete property")
    async def delete_property(self, property_id: int) -> bool:
        """
        Hard delete property.

        Business rule: Cannot delete properties with images.
        """
        log_debug("Deleting property", {"property_id": property_id})

        # Check if property exists
        existing = await self.repository.get_by_id(property_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        # Business rule: Prevent deletion if property has images
        if existing.images:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete property with associated images. Delete images first or use soft delete."
            )

        success = await self.repository.delete(property_id)
        if success:
            log_debug(f"Property deleted successfully: {property_id}")

        return success

    @handle_service_errors("soft delete property")
    async def soft_delete_property(self, property_id: int) -> PropertyResponse:
        """Soft delete property by marking as unavailable"""
        log_debug("Soft deleting property", {"property_id": property_id})

        updated_property = await self.repository.soft_delete(property_id)
        if not updated_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        log_debug(f"Property soft deleted successfully: {property_id}")
        return PropertyResponse.model_validate(updated_property)

    @handle_service_errors("search properties")
    async def search_properties(self, filters: PropertySearchFilters) -> List[PropertyResponse]:
        """
        Advanced property search.

        Pydantic PropertySearchFilters validates:
        - All field constraints
        - Range validations (min <= max)
        - Pagination limits
        """
        log_debug("Searching properties", {"filters": filters.model_dump()})

        # Apply business default: show available properties only if not specified
        filters_dict = filters.model_dump()
        if filters.is_available is None:
            filters_dict['is_available'] = True

        properties = await self.repository.advanced_search(filters_dict)
        return [PropertyResponse.model_validate(prop) for prop in properties]

    @handle_service_errors("get property statistics")
    async def get_property_statistics(self) -> Dict[str, Any]:
        """Get comprehensive property statistics efficiently using SQL aggregations"""
        log_debug("Calculating property statistics")

        # Get basic counts
        total_count = await self.repository.count_total()
        available_count = await self.repository.count_available()
        unavailable_count = total_count - available_count

        # Get type counts
        type_counts = await self.repository.count_by_type()

        # Get price statistics using QueryBuilder aggregation (efficient - no loading all records)
        price_stats = await self.repository.get_price_statistics(available_only=True)

        # Get square meters statistics
        sqm_stats = await self.repository.get_field_statistics(
            'square_meters',
            filters={'is_available': True}
        )

        stats = {
            "total_properties": total_count,
            "available_properties": available_count,
            "unavailable_properties": unavailable_count,
            "apartments": type_counts.get("apartments", 0),
            "houses": type_counts.get("houses", 0),
            "price_statistics": {
                "min_price": price_stats['min_price'],
                "max_price": price_stats['max_price'],
                "avg_price": round(price_stats['avg_price'], 2),
                "total_properties": price_stats['count']
            },
            "size_statistics": {
                "min_square_meters": sqm_stats.get('min_square_meters', 0),
                "max_square_meters": sqm_stats.get('max_square_meters', 0),
                "avg_square_meters": round(sqm_stats.get('avg_square_meters', 0), 2)
            },
            "availability_percentage": round(
                (available_count / total_count * 100) if total_count > 0 else 0,
                2
            )
        }

        log_debug("Property statistics calculated", stats)
        return stats

    @handle_service_errors("bulk update availability")
    async def bulk_update_availability(
            self,
            bulk_data: BulkUpdateAvailability
    ) -> Dict[str, Any]:
        """
        Bulk update availability status for multiple properties.

        Pydantic BulkUpdateAvailability validates:
        - Property IDs list is not empty
        - Property IDs are unique
        - List size constraints
        """
        log_debug("Bulk updating availability", {
            "property_ids_count": len(bulk_data.property_ids),
            "is_available": bulk_data.is_available
        })

        updated_count = await self.repository.bulk_update_availability(
            bulk_data.property_ids,
            bulk_data.is_available
        )

        return {
            "updated_count": updated_count,
            "requested_count": len(bulk_data.property_ids),
            "is_available": bulk_data.is_available
        }