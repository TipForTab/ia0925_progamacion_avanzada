import asyncio
import json
import re
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict
from sqlalchemy import select
from passlib.context import CryptContext
from src.core import get_async_db, init_db
from src.models import Property
from src.models.property_image import Image
from src.models.user import User
from src.core import log_error

# Constants
JSON_FILE_PATH = os.getenv('PROPERTIES_JSON_PATH', './src/parsed_properties.json')

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Default users to seed
DEFAULT_USERS = [
    {
        "username": "antonio",
        "email": "antonio@example.com",
        "password": "admin*2026"
    },
    {
        "username": "daniellab",
        "email": "daniellab@example.com",
        "password": "admin*2026"
    },
    {
        "username": "danielgo",
        "email": "danielgo@example.com",
        "password": "admin*2026"
    }
]


@dataclass
class ParsedPropertyData:
    """Data class to hold parsed property information ready for database insertion."""
    title: str
    address: str
    price: float
    operation_type: Optional[str]  # 'rent' or 'sale'
    rooms: int
    bathrooms: int
    square_meters: float
    building_floor: Optional[int]
    is_apartment: bool
    is_house: bool
    source_url: str
    amenities: Optional[Dict]
    image_urls: List[str]
    
    def to_property_dict(self) -> Dict:
        """Convert to dictionary for Property model creation."""
        return {
            'title': self.title,
            'address': self.address,
            'price': self.price,
            'operation_type': self.operation_type,
            'rooms': self.rooms,
            'bathrooms': self.bathrooms,
            'square_meters': self.square_meters,
            'building_floor': self.building_floor,
            'is_apartment': self.is_apartment,
            'is_house': self.is_house,
            'source_url': self.source_url,
            'is_available': True,
            'amenities': self.amenities
        }


class PropertyParser:
    """Parses raw property data from JSON into database-ready format."""
    
    @staticmethod
    def parse_price(price_str: str) -> float:
        """
        Parse price string with Spanish/European number format.
        
        Spanish format:
        - "1.800€/mes" → 1800.0 (dot as thousand separator)
        - "1.800,50€/mes" → 1800.50 (comma as decimal separator)
        - "350.000€" → 350000.0
        
        Args:
            price_str: Price string in Spanish format
            
        Returns:
            Price as float
        """
        if not price_str:
            return 0.0

        # Remove currency symbols, /mes, /año, whitespace, etc.
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        
        if not cleaned:
            return 0.0
        
        # Handle Spanish/European number format
        # If both comma and dot present: dot=thousand, comma=decimal
        # If only dot present: check if it's thousand separator or decimal
        # If only comma present: it's decimal separator
        
        if ',' in cleaned and '.' in cleaned:
            # Both present: "1.800,50" → remove dots, replace comma with dot
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Only comma: "1800,50" → replace comma with dot
            cleaned = cleaned.replace(',', '.')
        elif '.' in cleaned:
            # Only dot: check position
            parts = cleaned.split('.')
            if len(parts) == 2:
                # Two parts: could be "1.800" (thousand) or "18.50" (decimal)
                # If last part has 3 digits, it's likely a thousand separator
                if len(parts[1]) == 3:
                    # "1.800" → "1800"
                    cleaned = ''.join(parts)
                # If last part has 1-2 digits, treat as decimal
                else:
                    # "18.50" → keep as is
                    pass
            elif len(parts) > 2:
                # Multiple dots: "1.234.567" → "1234567"
                cleaned = ''.join(parts)
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def parse_features(features: List[str]) -> Dict:
        """Parse features list to extract rooms, bathrooms, square_meters, and floor."""
        result = {
            'square_meters': None,
            'rooms': None,
            'bathrooms': None,
            'building_floor': None
        }
        
        for feature in features:
            feature_lower = feature.lower()
            
            if 'm²' in feature or 'm2' in feature:
                match = re.search(r'(\d+(?:[.,]\d+)?)\s*m', feature)
                if match:
                    result['square_meters'] = float(match.group(1).replace(',', '.'))
            
            if 'hab' in feature_lower or 'dormitorio' in feature_lower:
                match = re.search(r'(\d+)', feature)
                if match:
                    result['rooms'] = int(match.group(1))
            
            if 'baño' in feature_lower:
                match = re.search(r'(\d+)', feature)
                if match:
                    result['bathrooms'] = int(match.group(1))
            
            if 'planta' in feature_lower:
                match = re.search(r'planta\s+(\d+)', feature_lower)
                if match:
                    result['building_floor'] = int(match.group(1))
                elif 'baja' in feature_lower or 'bajo' in feature_lower:
                    result['building_floor'] = 0
        
        return result

    @staticmethod
    def build_address(location: Dict) -> str:
        """Build a complete address from location dictionary."""
        if not location:
            return "Sin dirección"
        
        parts = []
        if location.get('street'):
            parts.append(location['street'])
        if location.get('neighborhood'):
            parts.append(location['neighborhood'])
        if location.get('district'):
            parts.append(location['district'])
        if location.get('city'):
            parts.append(location['city'])
        
        return ', '.join(parts) if parts else "Sin dirección"

    @staticmethod
    def determine_property_type(property_type: str) -> Dict[str, bool]:
        """Convert property_type string to is_apartment/is_house booleans."""
        if property_type == 'apartment':
            return {'is_apartment': True, 'is_house': False}
        elif property_type == 'house':
            return {'is_apartment': False, 'is_house': True}
        else:
            return {'is_apartment': True, 'is_house': False}

    @staticmethod
    def estimate_bathrooms(rooms: Optional[int], features: List[str]) -> int:
        """Estimate bathrooms if not found in features."""
        if not rooms:
            return 1
        
        for feature in features:
            if 'baño' in feature.lower():
                match = re.search(r'(\d+)', feature)
                if match:
                    return int(match.group(1))
        
        return max(1, rooms // 2)

    def parse(self, raw_data: Dict) -> Optional[ParsedPropertyData]:
        """Parse raw JSON property data into ParsedPropertyData."""
        if not raw_data.get('title'):
            raise ValueError("Missing title")

        price = self.parse_price(raw_data.get('price', '0'))
        if price == 0:
            raise ValueError("Invalid price")

        features = raw_data.get('features', [])
        parsed_features = self.parse_features(features)
        
        square_meters = parsed_features.get('square_meters')
        if not square_meters or square_meters <= 0:
            raise ValueError("Invalid size")

        rooms = parsed_features.get('rooms') or 1
        bathrooms = parsed_features.get('bathrooms') or self.estimate_bathrooms(rooms, features)
        address = self.build_address(raw_data.get('location', {}))
        
        source_url = raw_data.get('source_file', '')
        if not source_url:
            raise ValueError("Missing source_file")
        
        operation_type = raw_data.get('operation_type')
        property_type = self.determine_property_type(raw_data.get('property_type'))
        
        amenities = {}
        if raw_data.get('description'):
            amenities['description'] = raw_data['description']
        if raw_data.get('operation_type'):
            amenities['operation_type'] = raw_data['operation_type']
        if raw_data.get('location'):
            amenities['location'] = raw_data['location']
        if features:
            amenities['features'] = features
        
        image_urls = raw_data.get('images', [])
        
        return ParsedPropertyData(
            title=raw_data['title'],
            address=address,
            price=price,
            operation_type=operation_type,
            rooms=rooms,
            bathrooms=bathrooms,
            square_meters=square_meters,
            building_floor=parsed_features.get('building_floor'),
            is_apartment=property_type['is_apartment'],
            is_house=property_type['is_house'],
            source_url=source_url,
            amenities=amenities if amenities else None,
            image_urls=image_urls
        )


class UserSeeder:
    """Handles seeding default users into the database."""
    
    def __init__(self, users: List[Dict] = None):
        """
        Initialize the user seeder.
        
        Args:
            users: List of user dictionaries with username, email, password
        """
        self.users = users or DEFAULT_USERS
        self.stats = {
            'created': 0,
            'skipped': 0
        }
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session."""
        async for session in get_async_db():
            try:
                yield session
            finally:
                try:
                    await session.close()
                except Exception:
                    pass
            break
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    async def user_exists(self, session, username: str) -> bool:
        """Check if user already exists."""
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None
    
    async def create_user(self, session, username: str, email: str, password: str) -> User:
        """Create a new user with hashed password."""
        hashed_password = self.hash_password(password)
        
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        
        session.add(user)
        return user
    
    async def seed(self):
        """Seed users into the database."""
        print(f"👥 Seeding users...")
        
        async with self.get_session() as session:
            try:
                for user_data in self.users:
                    username = user_data['username']
                    
                    if await self.user_exists(session, username):
                        print(f"⏭️  User '{username}': Already exists - Skipped")
                        self.stats['skipped'] += 1
                        continue
                    
                    await self.create_user(
                        session,
                        username=username,
                        email=user_data['email'],
                        password=user_data['password']
                    )
                    
                    self.stats['created'] += 1
                    print(f"✅ User '{username}': Created (email: {user_data['email']})")
                
                await session.commit()
                
                print(f"\n{'=' * 60}")
                print(f"✅ User seeding completed!")
                print(f"   - Users created: {self.stats['created']}")
                print(f"   - Users skipped: {self.stats['skipped']}")
                print(f"{'=' * 60}\n")
                
            except Exception as e:
                await session.rollback()
                print(f"\n❌ Failed to seed users: {str(e)}")
                log_error(e, "Failed to seed users")
                raise


class PropertyImporter:
    """Handles importing properties and images into the database."""
    
    def __init__(self, json_file_path: str = JSON_FILE_PATH):
        """
        Initialize the importer.
        
        Args:
            json_file_path: Path to the JSON file containing property data
        """
        self.json_file_path = Path(json_file_path)
        self.parser = PropertyParser()
        self.stats = {
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'total_images': 0
        }
    
    def load_json(self) -> List[Dict]:
        """Load and validate JSON file."""
        if not self.json_file_path.exists():
            raise FileNotFoundError(f"File not found: {self.json_file_path}")

        print(f"📄 Reading JSON file: {self.json_file_path}")
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'properties' in data:
            properties_data = data['properties']
            metadata = data.get('metadata', {})
            print(f"📊 Found {len(properties_data)} properties to import")
            if metadata.get('extraction_errors'):
                print(f"⚠️  Warning: {metadata['extraction_errors']} extraction errors in source")
        else:
            raise ValueError("Invalid JSON format. Expected {'properties': [...], 'metadata': {...}}")

        return properties_data
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session."""
        async for session in get_async_db():
            try:
                yield session
            finally:
                try:
                    await session.close()
                except Exception:
                    pass
            break
    
    async def check_duplicate(self, session, source_url: str) -> bool:
        """Check if property already exists in database."""
        result = await session.execute(
            select(Property).where(Property.source_url == source_url)
        )
        return result.scalar_one_or_none() is not None
    
    async def save_property(self, session, parsed_data: ParsedPropertyData) -> Property:
        """Save property to database."""
        db_property = Property(**parsed_data.to_property_dict())
        session.add(db_property)
        await session.flush()
        return db_property
    
    async def save_images(self, session, property_id: int, image_urls: List[str]) -> int:
        """Save property images to database."""
        saved_count = 0
        
        for img_url in image_urls:
            try:
                result = await session.execute(
                    select(Image).where(
                        Image.property_id == property_id,
                        Image.img_url == img_url
                    )
                )
                if result.scalar_one_or_none():
                    continue
                
                image = Image(
                    property_id=property_id,
                    img_url=img_url,
                    calculated_tags=None
                )
                session.add(image)
                saved_count += 1
                
            except Exception as e:
                log_error(e, f"Failed to save image: {img_url}")
                continue
        
        return saved_count
    
    async def import_property(self, session, raw_data: Dict, index: int) -> bool:
        """Import a single property with its images."""
        try:
            parsed_data = self.parser.parse(raw_data)
            
            if await self.check_duplicate(session, parsed_data.source_url):
                print(f"⏭️  Property {index}: Already exists - Skipped")
                self.stats['skipped'] += 1
                return False
            
            db_property = await self.save_property(session, parsed_data)
            
            if parsed_data.image_urls:
                images_saved = await self.save_images(
                    session,
                    db_property.id,
                    parsed_data.image_urls
                )
                self.stats['total_images'] += images_saved
            
            property_type_str = "Apartment" if parsed_data.is_apartment else "House"
            operation = parsed_data.amenities.get('operation_type', 'unknown') if parsed_data.amenities else 'unknown'
            print(
                f"✅ Property {index}: {property_type_str} ({operation}) - "
                f"{parsed_data.title[:50]}... "
                f"(€{parsed_data.price:.0f}, {len(parsed_data.image_urls)} images)"
            )
            
            self.stats['imported'] += 1
            return True
            
        except ValueError as e:
            print(f"⚠️  Property {index}: {str(e)} - Skipped")
            self.stats['skipped'] += 1
            return False
            
        except Exception as e:
            print(f"❌ Property {index}: Error - {str(e)}")
            log_error(e, f"Failed to import property {index}")
            self.stats['errors'] += 1
            return False
    
    async def import_all(self):
        """Import all properties from JSON file."""
        try:
            properties_data = self.load_json()
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            return
        
        print("")
        
        async with self.get_session() as session:
            try:
                for idx, property_data in enumerate(properties_data, 1):
                    await self.import_property(session, property_data, idx)
                
                await session.commit()
                self.print_summary()
                
            except Exception as e:
                await session.rollback()
                print(f"\n❌ Failed to commit changes: {str(e)}")
                log_error(e, "Failed to commit property import")
                raise
    
    def print_summary(self):
        """Print import statistics summary."""
        print(f"\n{'=' * 60}")
        print(f"✅ Property import completed!")
        print(f"   - Properties imported: {self.stats['imported']}")
        print(f"   - Images imported:     {self.stats['total_images']}")
        print(f"   - Skipped:             {self.stats['skipped']}")
        print(f"   - Errors:              {self.stats['errors']}")
        print(f"{'=' * 60}\n")


async def main():
    """Main function to seed users and import properties."""
    print(f"\n{'=' * 60}")
    print("🌱 Database Seeding Script")
    print(f"{'=' * 60}\n")
    
    # Initialize database
    print("📦 Initializing database tables...")
    await init_db()
    print("✅ Database initialized\n")
    
    # Seed users
    user_seeder = UserSeeder()
    await user_seeder.seed()
    
    # Import properties
    print("🏠 Seeding properties...")
    property_importer = PropertyImporter(JSON_FILE_PATH)
    await property_importer.import_all()
    
    print(f"{'=' * 60}")
    print("✅ All seeding completed successfully!")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())