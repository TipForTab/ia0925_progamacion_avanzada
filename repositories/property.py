from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from models.property import Property
from core import log_debug


class PropertyQueryBuilder:
    """
    Chainable query builder for Property filtering
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
        'query', 'get_by_id', 'get_all', 'get_available',
        'create', 'update', 'delete', 'soft_delete',
        'bulk_update_availability', 'count_total', 'count_available', 'count_by_type'
    }

    def __init__(self, db: Session):
        self.db = db

    def query(self) -> PropertyQueryBuilder:
        """Start a new chainable query"""
        return PropertyQueryBuilder(self.db)

    def __getattr__(self, name: str):
        """
        Automatically delegate filter_* and order_* methods to a new query builder.
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