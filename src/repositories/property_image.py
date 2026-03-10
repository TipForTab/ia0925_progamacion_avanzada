from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update as sql_update, delete as sql_delete
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any

from src.models import Image
from src.core import log_debug


class ImageQueryBuilder:
    """
    Chainable async query builder for Image filtering with aggregation support
    """

    def __init__(self, db: AsyncSession, stmt=None):
        self.db = db
        self.stmt = stmt or select(Image).options(selectinload(Image.property))
        self._pagination_skip = 0
        self._pagination_limit = 100

    def filter_by_id(self, image_id: int) -> "ImageQueryBuilder":
        """Filter by image ID"""
        self.stmt = self.stmt.where(Image.id == image_id)
        return self

    def filter_by_property_id(self, property_id: int) -> "ImageQueryBuilder":
        """Filter by property ID"""
        self.stmt = self.stmt.where(Image.property_id == property_id)
        return self

    def filter_by_property_ids(self, property_ids: List[int]) -> "ImageQueryBuilder":
        """Filter by multiple property IDs"""
        self.stmt = self.stmt.where(Image.property_id.in_(property_ids))
        return self

    def filter_by_url(self, url: str, exact: bool = True) -> "ImageQueryBuilder":
        """Filter by image URL"""
        if exact:
            self.stmt = self.stmt.where(Image.img_url == url)
        else:
            self.stmt = self.stmt.where(Image.img_url.ilike(f"%{url}%"))
        return self

    def filter_by_url_pattern(self, pattern: str) -> "ImageQueryBuilder":
        """Filter by URL pattern (case-insensitive)"""
        self.stmt = self.stmt.where(Image.img_url.ilike(f"%{pattern}%"))
        return self

    def filter_by_url_domain(self, domain: str) -> "ImageQueryBuilder":
        """Filter images from a specific domain"""
        self.stmt = self.stmt.where(Image.img_url.ilike(f"%{domain}%"))
        return self

    def filter_with_tags(self, has_tags: bool = True) -> "ImageQueryBuilder":
        """Filter images that have/don't have calculated tags"""
        if has_tags:
            self.stmt = self.stmt.where(Image.calculated_tags.isnot(None))
        else:
            self.stmt = self.stmt.where(Image.calculated_tags.is_(None))
        return self

    def filter_by_tag_key(self, tag_key: str) -> "ImageQueryBuilder":
        """Filter by presence of a specific tag key"""
        self.stmt = self.stmt.where(Image.calculated_tags.has_key(tag_key))
        return self

    def filter_by_tag_value(self, tag_key: str, tag_value: Any) -> "ImageQueryBuilder":
        """Filter by a specific tag key-value pair"""
        self.stmt = self.stmt.where(
            Image.calculated_tags[tag_key].astext == str(tag_value)
        )
        return self

    def filter_by_date_range(
        self,
        start_date: str = None,
        end_date: str = None,
        date_field: str = "created_at",
    ) -> "ImageQueryBuilder":
        """Filter by date range (created_at or updated_at)"""
        field = getattr(Image, date_field)
        if start_date:
            self.stmt = self.stmt.where(field >= start_date)
        if end_date:
            self.stmt = self.stmt.where(field <= end_date)
        return self

    # Ordering methods
    def order_by_id(self, ascending: bool = True) -> "ImageQueryBuilder":
        """Order by image ID"""
        if ascending:
            self.stmt = self.stmt.order_by(Image.id.asc())
        else:
            self.stmt = self.stmt.order_by(Image.id.desc())
        return self

    def order_by_property_id(self, ascending: bool = True) -> "ImageQueryBuilder":
        """Order by property ID"""
        if ascending:
            self.stmt = self.stmt.order_by(Image.property_id.asc())
        else:
            self.stmt = self.stmt.order_by(Image.property_id.desc())
        return self

    def order_by_created_at(self, ascending: bool = False) -> "ImageQueryBuilder":
        """Order by creation date (newest first by default)"""
        if ascending:
            self.stmt = self.stmt.order_by(Image.created_at.asc())
        else:
            self.stmt = self.stmt.order_by(Image.created_at.desc())
        return self

    def order_by_updated_at(self, ascending: bool = False) -> "ImageQueryBuilder":
        """Order by update date (newest first by default)"""
        if ascending:
            self.stmt = self.stmt.order_by(Image.updated_at.asc())
        else:
            self.stmt = self.stmt.order_by(Image.updated_at.desc())
        return self

    # Pagination
    def skip(self, offset: int) -> "ImageQueryBuilder":
        """Skip N records"""
        self._pagination_skip = offset
        self.stmt = self.stmt.offset(offset)
        return self

    def limit(self, limit: int) -> "ImageQueryBuilder":
        """Limit results to N records"""
        self._pagination_limit = limit
        self.stmt = self.stmt.limit(limit)
        return self

    def paginate(self, page: int = 1, page_size: int = 100) -> "ImageQueryBuilder":
        """Paginate results (1-indexed pages)"""
        offset = (page - 1) * page_size
        return self.skip(offset).limit(page_size)

    # Execution methods
    async def all(self) -> List[Image]:
        """Execute query and return all results"""
        result = await self.db.execute(self.stmt)
        images = result.scalars().unique().all()
        log_debug("Query executed", {"result_count": len(images)})
        return list(images)

    async def first(self) -> Optional[Image]:
        """Execute query and return first result"""
        result = await self.db.execute(self.stmt.limit(1))
        return result.scalars().first()

    async def one_or_none(self) -> Optional[Image]:
        """Execute query and expect at most one result"""
        result = await self.db.execute(self.stmt)
        return result.scalars().one_or_none()

    async def count(self) -> int:
        """Count results without fetching them"""
        count_stmt = select(func.count()).select_from(self.stmt.subquery())
        result = await self.db.execute(count_stmt)
        count = result.scalar()
        log_debug("Count executed", {"count": count})
        return count

    async def exists(self) -> bool:
        """Check if any records match the query"""
        count = await self.count()
        return count > 0

    # Aggregation methods
    async def count_by_property(self) -> Dict[int, int]:
        """Count images grouped by property_id"""
        stmt = select(Image.property_id, func.count(Image.id).label("count")).group_by(
            Image.property_id
        )

        result = await self.db.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def get_properties_with_image_counts(
        self, min_images: int = None, max_images: int = None
    ) -> List[Dict[str, Any]]:
        """Get property IDs with their image counts, optionally filtered by count range"""
        stmt = select(
            Image.property_id, func.count(Image.id).label("image_count")
        ).group_by(Image.property_id)

        if min_images is not None:
            stmt = stmt.having(func.count(Image.id) >= min_images)
        if max_images is not None:
            stmt = stmt.having(func.count(Image.id) <= max_images)

        result = await self.db.execute(stmt)
        return [{"property_id": row[0], "image_count": row[1]} for row in result.all()]


class ImageRepository:
    """
    Repository for Image model with CRUD operations and advanced queries
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def query(self) -> ImageQueryBuilder:
        """Start a new chainable query"""
        return ImageQueryBuilder(self.db)

    # Basic CRUD operations
    async def get_by_id(self, image_id: int) -> Optional[Image]:
        """Get image by ID"""
        return await self.query().filter_by_id(image_id).first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Image]:
        """Get all images with pagination"""
        return await self.query().skip(skip).limit(limit).order_by_created_at().all()

    async def get_by_property_id(
        self, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Image]:
        """Get all images for a specific property"""
        return (
            await self.query()
            .filter_by_property_id(property_id)
            .skip(skip)
            .limit(limit)
            .order_by_created_at()
            .all()
        )

    async def get_by_url(self, url: str) -> Optional[Image]:
        """Get image by exact URL"""
        return await self.query().filter_by_url(url, exact=True).first()

    async def create(self, image_data: Dict[str, Any]) -> Image:
        """Create a new image"""
        db_image = Image(**image_data)
        self.db.add(db_image)
        await self.db.commit()
        await self.db.refresh(db_image)
        log_debug(
            "Image created successfully",
            {"image_id": db_image.id, "property_id": db_image.property_id},
        )
        return db_image

    async def create_bulk(self, images_data: List[Dict[str, Any]]) -> List[Image]:
        """Bulk create images"""
        db_images = [Image(**image_data) for image_data in images_data]
        self.db.add_all(db_images)
        await self.db.commit()

        # Refresh all images to get their IDs
        for db_image in db_images:
            await self.db.refresh(db_image)

        log_debug("Bulk images created", {"count": len(db_images)})
        return db_images

    async def update(
        self, image_id: int, update_data: Dict[str, Any]
    ) -> Optional[Image]:
        """Update image by ID"""
        db_image = await self.get_by_id(image_id)
        if db_image:
            for key, value in update_data.items():
                setattr(db_image, key, value)
            await self.db.commit()
            await self.db.refresh(db_image)
            log_debug("Image updated successfully", {"image_id": image_id})
        return db_image

    async def update_tags(self, image_id: int, tags: Dict[str, Any]) -> Optional[Image]:
        """Update only the calculated_tags field"""
        return await self.update(image_id, {"calculated_tags": tags})

    async def delete(self, image_id: int) -> bool:
        """Delete image by ID"""
        db_image = await self.get_by_id(image_id)
        if db_image:
            await self.db.delete(db_image)
            await self.db.commit()
            log_debug("Image deleted successfully", {"image_id": image_id})
            return True
        return False

    async def delete_by_property_id(self, property_id: int) -> int:
        """Delete all images for a property"""
        stmt = sql_delete(Image).where(Image.property_id == property_id)
        result = await self.db.execute(stmt)
        await self.db.commit()

        log_debug(
            "Images deleted for property",
            {"property_id": property_id, "deleted_count": result.rowcount},
        )
        return result.rowcount

    # Bulk operations
    async def bulk_update_tags(self, image_ids: List[int], tags: Dict[str, Any]) -> int:
        """Bulk update tags for multiple images"""
        stmt = (
            sql_update(Image)
            .where(Image.id.in_(image_ids))
            .values(calculated_tags=tags)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        log_debug(
            "Bulk tags update",
            {"image_ids": image_ids, "updated_count": result.rowcount},
        )
        return result.rowcount

    async def bulk_delete(self, image_ids: List[int]) -> int:
        """Bulk delete images by IDs"""
        stmt = sql_delete(Image).where(Image.id.in_(image_ids))
        result = await self.db.execute(stmt)
        await self.db.commit()

        log_debug(
            "Bulk delete", {"image_ids": image_ids, "deleted_count": result.rowcount}
        )
        return result.rowcount

    # Statistics and counts
    async def count_total(self) -> int:
        """Get total count of images"""
        return await self.query().count()

    async def count_by_property(self, property_id: int) -> int:
        """Get count of images for a specific property"""
        return await self.query().filter_by_property_id(property_id).count()

    async def count_with_tags(self) -> int:
        """Get count of images that have calculated tags"""
        return await self.query().filter_with_tags(True).count()

    async def count_without_tags(self) -> int:
        """Get count of images that don't have calculated tags"""
        return await self.query().filter_with_tags(False).count()

    async def get_images_without_tags(
        self, skip: int = 0, limit: int = 100
    ) -> List[Image]:
        """Get images that don't have calculated tags"""
        return await self.query().filter_with_tags(False).skip(skip).limit(limit).all()

    # Advanced queries
    async def advanced_search(self, filters: Dict[str, Any]) -> List[Image]:
        """
        Advanced search with dynamic filters
        Translates a filter dictionary into chainable query builder calls
        """
        query = self.query()

        # Property filter
        if filters.get("property_id") is not None:
            query = query.filter_by_property_id(filters["property_id"])

        if filters.get("property_ids"):
            query = query.filter_by_property_ids(filters["property_ids"])

        # URL filters
        if filters.get("url"):
            exact = filters.get("url_exact", False)
            query = query.filter_by_url(filters["url"], exact=exact)

        if filters.get("url_pattern"):
            query = query.filter_by_url_pattern(filters["url_pattern"])

        if filters.get("url_domain"):
            query = query.filter_by_url_domain(filters["url_domain"])

        # Tags filters
        if filters.get("has_tags") is not None:
            query = query.filter_with_tags(filters["has_tags"])

        if filters.get("tag_key"):
            query = query.filter_by_tag_key(filters["tag_key"])

        if filters.get("tag_key") and filters.get("tag_value"):
            query = query.filter_by_tag_value(filters["tag_key"], filters["tag_value"])

        # Date filters
        if filters.get("start_date") or filters.get("end_date"):
            date_field = filters.get("date_field", "created_at")
            query = query.filter_by_date_range(
                filters.get("start_date"), filters.get("end_date"), date_field
            )

        # Ordering
        order_by = filters.get("order_by", "created_at")
        ascending = filters.get("ascending", False)

        if order_by == "id":
            query = query.order_by_id(ascending)
        elif order_by == "property_id":
            query = query.order_by_property_id(ascending)
        elif order_by == "updated_at":
            query = query.order_by_updated_at(ascending)
        else:  # default to created_at
            query = query.order_by_created_at(ascending)

        # Pagination
        skip = filters.get("skip", 0)
        limit = filters.get("limit", 100)
        query = query.skip(skip).limit(limit)

        return await query.all()

    async def find_duplicates_by_url(self) -> List[Dict[str, Any]]:
        """Find duplicate images based on URL"""
        stmt = (
            select(Image.img_url, func.count(Image.id).label("count"))
            .group_by(Image.img_url)
            .having(func.count(Image.id) > 1)
        )

        result = await self.db.execute(stmt)
        duplicates = [{"url": row[0], "count": row[1]} for row in result.all()]

        log_debug("Duplicate URLs found", {"duplicate_count": len(duplicates)})
        return duplicates

    async def get_recent_images(self, days: int = 7, limit: int = 100) -> List[Image]:
        """Get images created in the last N days"""
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        return (
            await self.query()
            .filter_by_date_range(start_date=cutoff_date, date_field="created_at")
            .order_by_created_at(ascending=False)
            .limit(limit)
            .all()
        )

    async def check_url_exists(self, url: str) -> bool:
        """Check if an image with this URL already exists"""
        return await self.query().filter_by_url(url, exact=True).exists()

    async def get_image_statistics(self) -> Dict[str, Any]:
        """Get comprehensive image statistics"""
        total = await self.count_total()
        with_tags = await self.count_with_tags()
        without_tags = await self.count_without_tags()
        by_property = await self.query().count_by_property()

        return {
            "total_images": total,
            "images_with_tags": with_tags,
            "images_without_tags": without_tags,
            "total_properties_with_images": len(by_property),
            "avg_images_per_property": total / len(by_property) if by_property else 0,
        }
