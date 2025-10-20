from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any, Union

from models import Property
from models.property import Property
from core import log_debug


class PropertyQueryBuilder:
    """
    Chainable query builder for Property filtering with aggregation support
    """

    def __init__(self, db: Session, query=None):
        self.db = db
        self.query = query or db.query(Property)
        self._pagination_skip = 0
        self._pagination_limit = 100

    def filter_by_id(self, property_id: int) -> 'PropertyQueryBuilder':
        """Filter by property ID"""
        self.query = self.query.filter(Property.id == property_id)
        return self

    def filter_by_price_range(self, min_price: float = None, max_price: float = None) -> 'PropertyQueryBuilder':
        """Filter by price range"""
        if min_price is not None:
            self.query = self.query.filter(Property.price >= min_price)
        if max_price is not None:
            self.query = self.query.filter(Property.price <= max_price)
        return self

    def filter_by_price_min(self, min_price: float) -> 'PropertyQueryBuilder':
        """Filter by minimum price"""
        self.query = self.query.filter(Property.price >= min_price)
        return self

    def filter_by_price_max(self, max_price: float) -> 'PropertyQueryBuilder':
        """Filter by maximum price"""
        self.query = self.query.filter(Property.price <= max_price)
        return self

    def filter_by_property_type(self, is_apartment: bool = None, is_house: bool = None) -> 'PropertyQueryBuilder':
        """Filter by property type (apartment or house)"""
        if is_apartment is not None:
            self.query = self.query.filter(Property.is_apartment == is_apartment)
        if is_house is not None:
            self.query = self.query.filter(Property.is_house == is_house)
        return self

    def filter_by_apartment(self, is_apartment: bool = True) -> 'PropertyQueryBuilder':
        """Filter for apartments"""
        self.query = self.query.filter(Property.is_apartment == is_apartment)
        return self

    def filter_by_house(self, is_house: bool = True) -> 'PropertyQueryBuilder':
        """Filter for houses"""
        self.query = self.query.filter(Property.is_house == is_house)
        return self

    def filter_by_rooms(self, min_rooms: int = None, max_rooms: int = None) -> 'PropertyQueryBuilder':
        """Filter by room count range"""
        if min_rooms is not None:
            self.query = self.query.filter(Property.rooms >= min_rooms)
        if max_rooms is not None:
            self.query = self.query.filter(Property.rooms <= max_rooms)
        return self

    def filter_by_rooms_exact(self, rooms: int) -> 'PropertyQueryBuilder':
        """Filter by exact room count"""
        self.query = self.query.filter(Property.rooms == rooms)
        return self

    def filter_by_bathrooms(self, min_bathrooms: int = None, max_bathrooms: int = None) -> 'PropertyQueryBuilder':
        """Filter by bathroom count range"""
        if min_bathrooms is not None:
            self.query = self.query.filter(Property.bathrooms >= min_bathrooms)
        if max_bathrooms is not None:
            self.query = self.query.filter(Property.bathrooms <= max_bathrooms)
        return self

    def filter_by_bathrooms_exact(self, bathrooms: int) -> 'PropertyQueryBuilder':
        """Filter by exact bathroom count"""
        self.query = self.query.filter(Property.bathrooms == bathrooms)
        return self

    def filter_by_square_meters(self, min_sqm: float = None, max_sqm: float = None) -> 'PropertyQueryBuilder':
        """Filter by square meters range"""
        if min_sqm is not None:
            self.query = self.query.filter(Property.square_meters >= min_sqm)
        if max_sqm is not None:
            self.query = self.query.filter(Property.square_meters <= max_sqm)
        return self

    def filter_by_address(self, address_keyword: str, exact: bool = False) -> 'PropertyQueryBuilder':
        """Filter by address keyword"""
        if exact:
            self.query = self.query.filter(Property.address == address_keyword)
        else:
            self.query = self.query.filter(Property.address.ilike(f"%{address_keyword}%"))
        return self

    def filter_by_title(self, title_keyword: str, exact: bool = False) -> 'PropertyQueryBuilder':
        """Filter by title keyword"""
        if exact:
            self.query = self.query.filter(Property.title == title_keyword)
        else:
            self.query = self.query.filter(Property.title.ilike(f"%{title_keyword}%"))
        return self

    def filter_by_floor(self, floor: int) -> 'PropertyQueryBuilder':
        """Filter by building floor"""
        self.query = self.query.filter(Property.building_floor == floor)
        return self

    def filter_by_floor_range(self, min_floor: int = None, max_floor: int = None) -> 'PropertyQueryBuilder':
        """Filter by floor range"""
        if min_floor is not None:
            self.query = self.query.filter(Property.building_floor >= min_floor)
        if max_floor is not None:
            self.query = self.query.filter(Property.building_floor <= max_floor)
        return self

    def filter_by_availability(self, is_available: bool = True) -> 'PropertyQueryBuilder':
        """Filter by availability status"""
        self.query = self.query.filter(Property.is_available == is_available)
        return self

    def filter_by_source_url(self, source_url: str, exact: bool = True) -> 'PropertyQueryBuilder':
        """Filter by source URL"""
        if exact:
            self.query = self.query.filter(Property.source_url == source_url)
        else:
            self.query = self.query.filter(Property.source_url.ilike(f"%{source_url}%"))
        return self

    def filter_by_amenities(self, amenity_key: str, amenity_value: Any = None) -> 'PropertyQueryBuilder':
        """Filter by amenities JSON field"""
        if amenity_value is not None:
            # Filter by a specific key-value pair
            self.query = self.query.filter(Property.amenities[amenity_key].astext == str(amenity_value))
        else:
            # Filter by key existence
            self.query = self.query.filter(Property.amenities.has_key(amenity_key))
        return self

    def filter_with_images(self, has_images: bool = True) -> 'PropertyQueryBuilder':
        """Filter properties that have/don't have images"""
        if has_images:
            self.query = self.query.filter(Property.images.any())
        else:
            self.query = self.query.filter(~Property.images.any())
        return self

    def filter_by_date_range(self, start_date: str = None, end_date: str = None,
                             date_field: str = 'created_at') -> 'PropertyQueryBuilder':
        """Filter by date range (created_at or updated_at)"""
        field = getattr(Property, date_field)
        if start_date:
            self.query = self.query.filter(field >= start_date)
        if end_date:
            self.query = self.query.filter(field <= end_date)
        return self

    # Ordering methods
    def order_by_price(self, ascending: bool = True) -> 'PropertyQueryBuilder':
        """Order by price"""
        if ascending:
            self.query = self.query.order_by(Property.price.asc())
        else:
            self.query = self.query.order_by(Property.price.desc())
        return self

    def order_by_rooms(self, ascending: bool = True) -> 'PropertyQueryBuilder':
        """Order by room count"""
        if ascending:
            self.query = self.query.order_by(Property.rooms.asc())
        else:
            self.query = self.query.order_by(Property.rooms.desc())
        return self

    def order_by_square_meters(self, ascending: bool = True) -> 'PropertyQueryBuilder':
        """Order by square meters"""
        if ascending:
            self.query = self.query.order_by(Property.square_meters.asc())
        else:
            self.query = self.query.order_by(Property.square_meters.desc())
        return self

    def order_by_created_at(self, ascending: bool = False) -> 'PropertyQueryBuilder':
        """Order by creation date (newest first by default)"""
        if ascending:
            self.query = self.query.order_by(Property.created_at.asc())
        else:
            self.query = self.query.order_by(Property.created_at.desc())
        return self

    def order_by_updated_at(self, ascending: bool = False) -> 'PropertyQueryBuilder':
        """Order by update date (newest first by default)"""
        if ascending:
            self.query = self.query.order_by(Property.updated_at.asc())
        else:
            self.query = self.query.order_by(Property.updated_at.desc())
        return self

    # Pagination methods
    def skip(self, skip: int) -> 'PropertyQueryBuilder':
        """Set skip offset for pagination"""
        self._pagination_skip = skip
        return self

    def limit(self, limit: int) -> 'PropertyQueryBuilder':
        """Set limit for pagination"""
        self._pagination_limit = limit
        return self

    def paginate(self, skip: int, limit: int) -> 'PropertyQueryBuilder':
        """Set both skip and limit"""
        self._pagination_skip = skip
        self._pagination_limit = limit
        return self

    # Aggregation methods
    def aggregate_price_stats(self) -> Dict[str, float]:
        """
        Get price statistics for current query filters
        Returns min, max, avg price and count without loading all records
        """
        result = self.query.with_entities(
            func.min(Property.price).label('min_price'),
            func.max(Property.price).label('max_price'),
            func.avg(Property.price).label('avg_price'),
            func.count(Property.id).label('count')
        ).first()

        return {
            'min_price': float(result.min_price) if result.min_price else 0,
            'max_price': float(result.max_price) if result.max_price else 0,
            'avg_price': float(result.avg_price) if result.avg_price else 0,
            'count': int(result.count) if result.count else 0
        }

    def aggregate_by_field(self, field_name: str, aggregations: List[str] = None) -> Dict[str, Any]:
        """
        Generic aggregation method for any numeric field

        Args:
            field_name: Name of the field to aggregate (e.g., 'price', 'square_meters', 'rooms')
            aggregations: List of aggregation functions ['min', 'max', 'avg', 'sum', 'count']

        Returns:
            Dictionary with aggregation results
        """
        if aggregations is None:
            aggregations = ['min', 'max', 'avg', 'count']

        field = getattr(Property, field_name)
        agg_functions = []

        for agg in aggregations:
            if agg == 'min':
                agg_functions.append(func.min(field).label(f'min_{field_name}'))
            elif agg == 'max':
                agg_functions.append(func.max(field).label(f'max_{field_name}'))
            elif agg == 'avg':
                agg_functions.append(func.avg(field).label(f'avg_{field_name}'))
            elif agg == 'sum':
                agg_functions.append(func.sum(field).label(f'sum_{field_name}'))
            elif agg == 'count':
                agg_functions.append(func.count(Property.id).label('count'))

        result = self.query.with_entities(*agg_functions).first()

        output = {}
        for i, agg in enumerate(aggregations):
            value = result[i]
            key = f'{agg}_{field_name}' if agg != 'count' else 'count'
            output[key] = float(value) if value is not None and agg != 'count' else (int(value) if value else 0)

        return output

    def group_count_by(self, field_name: str) -> Dict[Any, int]:
        """
        Count properties grouped by a field

        Args:
            field_name: Field to group by (e.g., 'is_apartment', 'rooms', 'bathrooms')

        Returns:
            Dictionary mapping field values to counts
        """
        field = getattr(Property, field_name)
        results = self.query.with_entities(
            field,
            func.count(Property.id).label('count')
        ).group_by(field).all()

        return {value: count for value, count in results}

    # Execution methods
    def first(self) -> Optional[Property]:
        """Get the first result"""
        log_debug("Executing query - first()", {"query": str(self.query)})
        return self.query.first()

    def all(self) -> List[Property]:
        """Get all results with pagination"""
        log_debug("Executing query - all()", {
            "query": str(self.query),
            "skip": self._pagination_skip,
            "limit": self._pagination_limit
        })
        return self.query.offset(self._pagination_skip).limit(self._pagination_limit).all()

    def count(self) -> int:
        """Get count of results"""
        log_debug("Executing query - count()", {"query": str(self.query)})
        return self.query.count()

    def exists(self) -> bool:
        """Check if any results exist"""
        return self.query.first() is not None

    # Raw query access
    def get_query(self):
        """Get the raw SQLAlchemy query object"""
        return self.query


class PropertyRepository:
    """
    Repository with automatic delegation to PropertyQueryBuilder for filter methods.
    Handles CRUD operations, statistics, and bulk operations directly.
    """

    # Define which methods should NOT be delegated (repository-specific methods)
    _NON_DELEGATED_METHODS = {
        'query', 'get_by_id', 'get_all', 'get_available', 'get_by_source_url',
        'create', 'update', 'delete', 'soft_delete',
        'bulk_update_availability', 'count_total', 'count_available', 'count_by_type',
        'advanced_search', 'get_price_statistics', 'get_field_statistics'
    }

    def __init__(self, db: Session):
        self.db = db

    def query(self) -> PropertyQueryBuilder:
        """Start a new chainable query"""
        return PropertyQueryBuilder(self.db)

    def __getattr__(self, name: str):
        """
        Automatically delegate filter_* and order_* methods to a new query builder.
        This eliminates the need for wrapper methods in the repository.
        """
        if name.startswith(('filter_', 'order_')) and name not in self._NON_DELEGATED_METHODS:
            # Return a function that creates a new query builder and calls the method
            def delegated_method(*args, **kwargs):
                query_builder = self.query()
                method = getattr(query_builder, name)
                return method(*args, **kwargs)

            return delegated_method

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # Legacy convenience methods for backward compatibility
    def get_by_id(self, property_id: int) -> Optional[Property]:
        """Get property by ID"""
        return self.query().filter_by_id(property_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Property]:
        """Get all properties"""
        return self.query().skip(skip).limit(limit).all()

    def get_available(self, skip: int = 0, limit: int = 100) -> List[Property]:
        """Get available properties"""
        return self.query().filter_by_availability(True).skip(skip).limit(limit).all()

    def get_by_source_url(self, source_url: str) -> Optional[Property]:
        """Get property by source URL"""
        return self.query().filter_by_source_url(source_url, exact=True).first()

    # CRUD operations
    def create(self, property_data: dict) -> Property:
        """Create a new property"""
        db_property = Property(**property_data)
        self.db.add(db_property)
        self.db.commit()
        self.db.refresh(db_property)
        log_debug("Property created successfully", {"property_id": db_property.id})
        return db_property

    def update(self, property_id: int, update_data: dict) -> Optional[Property]:
        """Update property by ID"""
        db_property = self.get_by_id(property_id)
        if db_property:
            for key, value in update_data.items():
                if value is not None:
                    setattr(db_property, key, value)
            self.db.commit()
            self.db.refresh(db_property)
            log_debug("Property updated successfully", {"property_id": property_id})
        return db_property

    def delete(self, property_id: int) -> bool:
        """Delete property by ID"""
        db_property = self.get_by_id(property_id)
        if db_property:
            self.db.delete(db_property)
            self.db.commit()
            log_debug("Property deleted successfully", {"property_id": property_id})
            return True
        return False

    def soft_delete(self, property_id: int) -> Optional[Property]:
        """Soft delete by marking as unavailable"""
        return self.update(property_id, {"is_available": False})

    # Bulk operations
    def bulk_update_availability(self, property_ids: List[int], is_available: bool) -> int:
        """Bulk update availability status"""
        updated_count = self.db.query(Property).filter(
            Property.id.in_(property_ids)
        ).update({"is_available": is_available}, synchronize_session=False)
        self.db.commit()
        log_debug("Bulk availability update", {
            "property_ids": property_ids,
            "is_available": is_available,
            "updated_count": updated_count
        })
        return updated_count

    # Statistics
    def count_total(self) -> int:
        """Get total count of properties"""
        return self.query().count()

    def count_available(self) -> int:
        """Get count of available properties"""
        return self.query().filter_by_availability(True).count()

    def count_by_type(self) -> Dict[str, int]:
        """Get count by property type"""
        return {
            "apartments": self.query().filter_by_apartment().count(),
            "houses": self.query().filter_by_house().count()
        }

    def get_price_statistics(self, available_only: bool = True) -> Dict[str, float]:
        """
        Get price statistics using query builder aggregation

        Args:
            available_only: If True, only calculate stats for available properties

        Returns:
            Dictionary with min, max, avg price and count
        """
        query = self.query()

        if available_only:
            query = query.filter_by_availability(True)

        return query.aggregate_price_stats()

    def get_field_statistics(
            self,
            field_name: str,
            filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for any numeric field with optional filters

        Args:
            field_name: Name of field to aggregate (e.g., 'square_meters', 'rooms')
            filters: Optional filters to apply before aggregation

        Returns:
            Dictionary with min, max, avg, count for the field
        """
        query = self.query()

        # Apply filters if provided
        if filters:
            if filters.get('is_available') is not None:
                query = query.filter_by_availability(filters['is_available'])
            if filters.get('is_apartment') is not None:
                query = query.filter_by_apartment(filters['is_apartment'])
            if filters.get('is_house') is not None:
                query = query.filter_by_house(filters['is_house'])

        return query.aggregate_by_field(field_name)

    def advanced_search(self, filters: Dict[str, Any]) -> List[Property]:
        """
        Advanced search with dynamic filters
        Translates a filter dictionary into chainable query builder calls
        """
        query = self.query()

        # Property type filters
        if filters.get('is_apartment') is not None:
            query = query.filter_by_apartment(filters['is_apartment'])
        if filters.get('is_house') is not None:
            query = query.filter_by_house(filters['is_house'])

        # Price filters
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        if min_price is not None or max_price is not None:
            query = query.filter_by_price_range(min_price, max_price)

        # Room filters
        min_rooms = filters.get('min_rooms')
        max_rooms = filters.get('max_rooms')
        if filters.get('rooms') is not None:
            query = query.filter_by_rooms_exact(filters['rooms'])
        elif min_rooms is not None or max_rooms is not None:
            query = query.filter_by_rooms(min_rooms, max_rooms)

        # Bathroom filters
        min_bathrooms = filters.get('min_bathrooms')
        max_bathrooms = filters.get('max_bathrooms')
        if filters.get('bathrooms') is not None:
            query = query.filter_by_bathrooms_exact(filters['bathrooms'])
        elif min_bathrooms is not None or max_bathrooms is not None:
            query = query.filter_by_bathrooms(min_bathrooms, max_bathrooms)

        # Square meters filters
        min_sqm = filters.get('min_square_meters')
        max_sqm = filters.get('max_square_meters')
        if min_sqm is not None or max_sqm is not None:
            query = query.filter_by_square_meters(min_sqm, max_sqm)

        # Location filters
        if filters.get('address'):
            query = query.filter_by_address(filters['address'], exact=False)

        if filters.get('title'):
            query = query.filter_by_title(filters['title'], exact=False)

        # Floor filters
        if filters.get('floor') is not None:
            query = query.filter_by_floor(filters['floor'])

        min_floor = filters.get('min_floor')
        max_floor = filters.get('max_floor')
        if min_floor is not None or max_floor is not None:
            query = query.filter_by_floor_range(min_floor, max_floor)

        # Availability filter
        if filters.get('is_available') is not None:
            query = query.filter_by_availability(filters['is_available'])

        # Amenities filter
        if filters.get('amenity'):
            query = query.filter_by_amenities(filters['amenity'])

        # Images filter
        if filters.get('has_images') is not None:
            query = query.filter_with_images(filters['has_images'])

        # Date filters
        if filters.get('start_date') or filters.get('end_date'):
            date_field = filters.get('date_field', 'created_at')
            query = query.filter_by_date_range(
                filters.get('start_date'),
                filters.get('end_date'),
                date_field
            )

        # Ordering
        order_by = filters.get('order_by', 'created_at')
        ascending = filters.get('ascending', False)

        if order_by == 'price':
            query = query.order_by_price(ascending)
        elif order_by == 'rooms':
            query = query.order_by_rooms(ascending)
        elif order_by == 'square_meters':
            query = query.order_by_square_meters(ascending)
        elif order_by == 'updated_at':
            query = query.order_by_updated_at(ascending)
        else:  # default to created_at
            query = query.order_by_created_at(ascending)

        # Pagination
        skip = filters.get('skip', 0)
        limit = filters.get('limit', 100)
        query = query.skip(skip).limit(limit)

        return query.all()