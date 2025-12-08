import asyncio
import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy import select
from src.core import get_async_db, init_db
from src.models import Property
from src.core import log_error

@asynccontextmanager
async def session_ctx():
    async for s in get_async_db():
        try:
            yield s
        finally:
            # If get_async_db() already manages closing, this is harmless; if not, it ensures cleanup.
            try:
                await s.close()
            except Exception:
                pass
        break  # consume only one yield


def parse_price(price_str: str) -> float:
    """
    Parse price string like '600 €/mes' to float
    """
    if not price_str:
        return 0.0

    # Remove everything except digits and decimal point
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_floor(floor_str: str) -> int | None:
    """
    Parse floor string like 'Planta 4ª interior con ascensor' to int
    """
    if not floor_str:
        return None

    # Try to extract number from string
    match = re.search(r'(\d+)', floor_str)
    if match:
        return int(match.group(1))

    # Handle special cases
    if 'bajo' in floor_str.lower() or 'planta baja' in floor_str.lower():
        return 0

    return None


def determine_property_type(bedrooms, title, address):
    """
    Determine if property is apartment or house based on available data
    """
    title_lower = (title or '').lower()
    address_lower = (address or '').lower()

    # Check for house indicators
    house_keywords = ['chalet', 'villa', 'casa', 'adosado', 'pareado']
    if any(keyword in title_lower or keyword in address_lower for keyword in house_keywords):
        return {'is_apartment': False, 'is_house': True}

    # Check for apartment indicators
    apt_keywords = ['piso', 'apartamento', 'estudio', 'ático', 'dúplex', 'loft']
    if any(keyword in title_lower or keyword in address_lower for keyword in apt_keywords):
        return {'is_apartment': True, 'is_house': False}

    # Default to apartment if bedrooms <= 3, otherwise house
    if bedrooms and bedrooms <= 3:
        return {'is_apartment': True, 'is_house': False}

    return {'is_apartment': True, 'is_house': False}  # Default to apartment


async def import_properties_from_json(json_file_path: str):
    """
    Import properties from Idealista JSON file into the database.

    Args:
        json_file_path: Path to the JSON file containing property data
    """
    # Read JSON file
    json_path = Path(json_file_path)
    if not json_path.exists():
        print(f"❌ Error: File not found: {json_file_path}")
        return

    print(f"📄 Reading JSON file: {json_file_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both array and single object
    if isinstance(data, dict):
        properties_data = [data]
    else:
        properties_data = data

    print(f"📊 Found {len(properties_data)} properties to import\n")

    # Create database session using direct session factory
    async with session_ctx() as session:
        imported_count = 0
        skipped_count = 0
        error_count = 0
        try:
            for idx, raw_data in enumerate(properties_data, 1):
                try:
                    # Skip if no URL (used as source_url)
                    if not raw_data.get('url'):
                        print(f"⚠️  Property {idx}: Missing URL - Skipped")
                        skipped_count += 1
                        continue

                    # Check for duplicate source_url
                    source_url = raw_data['url']
                    existing = await session.execute(
                        select(Property).where(Property.source_url == source_url)
                    )
                    if existing.scalar_one_or_none():
                        print(f"⏭️  Property {idx}: Already exists (ID: {raw_data.get('id')})")
                        skipped_count += 1
                        continue

                    # Parse and transform data
                    price = parse_price(raw_data.get('price', '0'))
                    if price == 0:
                        print(f"⚠️  Property {idx}: Invalid price - Skipped")
                        skipped_count += 1
                        continue

                    # Get bedrooms (rooms)
                    bedrooms = raw_data.get('bedrooms')
                    if bedrooms is None or bedrooms == 0:
                        # Default to 1 for studios
                        bedrooms = 1

                    # Estimate bathrooms (typically 1 per 2 bedrooms, minimum 1)
                    bathrooms = max(1, bedrooms // 2)

                    # Get size
                    size_m2 = raw_data.get('size_m2')
                    if not size_m2 or size_m2 <= 0:
                        print(f"⚠️  Property {idx}: Invalid size - Skipped")
                        skipped_count += 1
                        continue

                    # Determine property type
                    property_type = determine_property_type(
                        bedrooms,
                        raw_data.get('title'),
                        raw_data.get('address')
                    )

                    # Parse floor
                    building_floor = parse_floor(raw_data.get('floor'))

                    # Create amenities JSON from additional info
                    amenities = {}
                    if raw_data.get('description'):
                        amenities['description'] = raw_data['description']
                    if raw_data.get('agency'):
                        amenities['agency'] = raw_data['agency']
                    if raw_data.get('image_count'):
                        amenities['image_count'] = raw_data['image_count']
                    if raw_data.get('original_price'):
                        amenities['original_price'] = raw_data['original_price']
                    if raw_data.get('price_discount'):
                        amenities['discount'] = raw_data['price_discount']

                    # Build property data for DB
                    property_data = {
                        'title': raw_data.get('title', 'Sin título'),
                        'address': raw_data.get('address', raw_data.get('title', 'Sin dirección')),
                        'price': price,
                        'rooms': bedrooms,
                        'bathrooms': bathrooms,
                        'square_meters': float(size_m2),
                        'source_url': source_url,
                        'building_floor': building_floor,
                        'is_available': True,
                        'amenities': amenities if amenities else None,
                        **property_type
                    }

                    # Create property
                    db_property = Property(**property_data)
                    session.add(db_property)

                    imported_count += 1
                    property_type_str = "Apartment" if property_type['is_apartment'] else "House"
                    print(f"✅ Property {idx}: {property_type_str} - {property_data['title'][:50]}... (€{price})")

                except Exception as e:
                    error_count += 1
                    print(f"❌ Property {idx}: Error - {str(e)}")
                    log_error(e, f"Failed to import property {idx}")
                    continue

            # Explicit commit
            await session.commit()
            print(f"\n{'=' * 60}")
            print(f"✅ Import completed successfully!")
            print(f"   - Imported: {imported_count}")
            print(f"   - Skipped:  {skipped_count}")
            print(f"   - Errors:   {error_count}")
            print(f"{'=' * 60}")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Failed to commit changes: {str(e)}")
            log_error(e, "Failed to commit property import")
            raise


async def main():
    """Main function to run the import"""
    # Initialize database tables first
    await init_db()

    json_file = "./src/properties_data.json"

    print(f"\n{'=' * 60}")
    print("🏠 Idealista Property Import Script")
    print(f"{'=' * 60}\n")

    await import_properties_from_json(json_file)


if __name__ == "__main__":
    # Run the import
    asyncio.run(main())