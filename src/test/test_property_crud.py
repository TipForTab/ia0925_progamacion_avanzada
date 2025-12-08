import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestPropertyCRUDEndpoints:
    """Test suite for Property CRUD endpoints"""

    # Test data
    valid_property = {
        "title": "Beautiful Apartment in Madrid",
        "address": "Calle Gran Via, 123, Madrid",
        "price": 250000,
        "rooms": 3,
        "bathrooms": 2,
        "square_meters": 95,
        "is_apartment": True,
        "is_house": False,
        "building_floor": 4,
        "source_url": "https://example.com/property/123",
        "is_available": True,
        "amenities": {
            "elevator": True,
            "parking": True,
            "terrace": True
        }
    }

    # ========================================================================
    # CREATE TESTS
    # ========================================================================

    async def test_create_property_success(self, async_client: AsyncClient):
        """Test creating a property with valid data"""
        response = await async_client.post("/properties/", json=self.valid_property)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["title"] == self.valid_property["title"]
        assert data["price"] == self.valid_property["price"]
        assert data["rooms"] == self.valid_property["rooms"]
        assert data["is_apartment"] == True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_property_invalid_price(self, async_client: AsyncClient):
        """Test creating property with price below minimum"""
        invalid_data = self.valid_property.copy()
        invalid_data["price"] = 50  # Below minimum of 100
        invalid_data["source_url"] = "https://example.com/property/invalid-price"

        response = await async_client.post("/properties/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_property_invalid_square_meters(self, async_client: AsyncClient):
        """Test creating property with invalid square meters"""
        invalid_data = self.valid_property.copy()
        invalid_data["square_meters"] = 15000  # Above maximum of 10000
        invalid_data["source_url"] = "https://example.com/property/invalid-sqm"

        response = await async_client.post("/properties/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_property_no_type_selected(self, async_client: AsyncClient):
        """Test creating property without apartment or house type"""
        invalid_data = self.valid_property.copy()
        invalid_data["is_apartment"] = False
        invalid_data["is_house"] = False
        invalid_data["source_url"] = "https://example.com/property/no-type"

        response = await async_client.post("/properties/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_property_duplicate_source_url(self, async_client: AsyncClient):
        """Test creating property with duplicate source_url"""
        # Create first property
        response1 = await async_client.post("/properties/", json=self.valid_property)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create duplicate
        response2 = await async_client.post("/properties/", json=self.valid_property)
        assert response2.status_code == status.HTTP_409_CONFLICT

    async def test_create_property_missing_required_fields(self, async_client: AsyncClient):
        """Test creating property with missing required fields"""
        invalid_data = {
            "title": "Incomplete Property"
            # Missing required fields
        }

        response = await async_client.post("/properties/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================================================================
    # READ TESTS
    # ========================================================================

    async def test_get_property_by_id_success(self, async_client: AsyncClient):
        """Test getting a property by ID"""
        # Create property first
        create_response = await async_client.post("/properties/", json=self.valid_property)
        created_property = create_response.json()
        property_id = created_property["id"]

        # Get property
        response = await async_client.get(f"/properties/{property_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == property_id
        assert data["title"] == self.valid_property["title"]

    async def test_get_property_by_id_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent property"""
        response = await async_client.get("/properties/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_all_properties(self, async_client: AsyncClient):
        """Test getting all properties with pagination"""
        # Create multiple properties
        for i in range(3):
            property_data = self.valid_property.copy()
            property_data["source_url"] = f"https://example.com/property/test-{i}"
            property_data["title"] = f"Property {i}"
            await async_client.post("/properties/", json=property_data)

        # Get all properties
        response = await async_client.get("/properties/?skip=0&limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    async def test_get_all_properties_pagination(self, async_client: AsyncClient):
        """Test pagination parameters"""
        # Create 5 properties
        for i in range(5):
            property_data = self.valid_property.copy()
            property_data["source_url"] = f"https://example.com/property/pagination-{i}"
            await async_client.post("/properties/", json=property_data)

        # Get first page (2 items)
        response1 = await async_client.get("/properties/?skip=0&limit=2")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert len(data1) == 2

        # Get second page (2 items)
        response2 = await async_client.get("/properties/?skip=2&limit=2")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert len(data2) == 2

        # Ensure different results
        assert data1[0]["id"] != data2[0]["id"]

    async def test_get_available_properties(self, async_client: AsyncClient):
        """Test getting only available properties"""
        # Create available property
        available_property = self.valid_property.copy()
        available_property["source_url"] = "https://example.com/available"
        available_property["is_available"] = True
        create_response1 = await async_client.post("/properties/", json=available_property)

        # Create unavailable property
        unavailable_property = self.valid_property.copy()
        unavailable_property["source_url"] = "https://example.com/unavailable"
        unavailable_property["is_available"] = False
        await async_client.post("/properties/", json=unavailable_property)

        # Get available properties
        response = await async_client.get("/properties/available")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # All returned properties should be available
        for prop in data:
            assert prop["is_available"] == True

    # ========================================================================
    # UPDATE TESTS
    # ========================================================================

    async def test_update_property_success(self, async_client: AsyncClient):
        """Test updating a property"""
        # Create property
        create_response = await async_client.post("/properties/", json=self.valid_property)
        created_property = create_response.json()
        property_id = created_property["id"]

        # Update property
        update_data = {
            "price": 275000,
            "rooms": 4,
            "is_available": False
        }
        response = await async_client.put(f"/properties/{property_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["price"] == 275000
        assert data["rooms"] == 4
        assert data["is_available"] == False
        assert data["title"] == self.valid_property["title"]  # Unchanged

    async def test_update_property_partial(self, async_client: AsyncClient):
        """Test partial update (PATCH)"""
        # Create property
        create_response = await async_client.post("/properties/", json=self.valid_property)
        property_id = create_response.json()["id"]

        # Partial update
        update_data = {"price": 300000}
        response = await async_client.patch(f"/properties/{property_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["price"] == 300000
        assert data["rooms"] == self.valid_property["rooms"]  # Unchanged

    async def test_update_property_not_found(self, async_client: AsyncClient):
        """Test updating non-existent property"""
        update_data = {"price": 300000}
        response = await async_client.put("/properties/999999", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_property_invalid_data(self, async_client: AsyncClient):
        """Test updating with invalid data"""
        # Create property
        create_response = await async_client.post("/properties/", json=self.valid_property)
        property_id = create_response.json()["id"]

        # Try to update with invalid price
        update_data = {"price": 50}  # Below minimum
        response = await async_client.put(f"/properties/{property_id}", json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_property_duplicate_source_url(self, async_client: AsyncClient):
        """Test updating with duplicate source_url"""
        # Create first property
        property1 = self.valid_property.copy()
        property1["source_url"] = "https://example.com/prop1"
        response1 = await async_client.post("/properties/", json=property1)

        # Create second property
        property2 = self.valid_property.copy()
        property2["source_url"] = "https://example.com/prop2"
        response2 = await async_client.post("/properties/", json=property2)
        property2_id = response2.json()["id"]

        # Try to update property2 with property1's source_url
        update_data = {"source_url": "https://example.com/prop1"}
        response = await async_client.put(f"/properties/{property2_id}", json=update_data)

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_update_property_no_fields(self, async_client: AsyncClient):
        """Test updating with no fields provided"""
        # Create property
        create_response = await async_client.post("/properties/", json=self.valid_property)
        property_id = create_response.json()["id"]

        # Try to update with empty data
        response = await async_client.put(f"/properties/{property_id}", json={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ========================================================================
    # DELETE TESTS
    # ========================================================================

    async def test_delete_property_success(self, async_client: AsyncClient):
        """Test deleting a property"""
        # Create property without images
        property_data = self.valid_property.copy()
        property_data["source_url"] = "https://example.com/to-delete"
        create_response = await async_client.post("/properties/", json=property_data)
        property_id = create_response.json()["id"]

        # Delete property
        response = await async_client.delete(f"/properties/{property_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's deleted
        get_response = await async_client.get(f"/properties/{property_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_property_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent property"""
        response = await async_client.delete("/properties/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_soft_delete_property_success(self, async_client: AsyncClient):
        """Test soft deleting a property"""
        # Create property
        property_data = self.valid_property.copy()
        property_data["source_url"] = "https://example.com/soft-delete"
        create_response = await async_client.post("/properties/", json=property_data)
        property_id = create_response.json()["id"]

        # Soft delete
        response = await async_client.post(f"/properties/{property_id}/soft-delete")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_available"] == False
        assert data["id"] == property_id

        # Verify property still exists but is unavailable
        get_response = await async_client.get(f"/properties/{property_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["is_available"] == False

    async def test_soft_delete_property_not_found(self, async_client: AsyncClient):
        """Test soft deleting non-existent property"""
        response = await async_client.post("/properties/999999/soft-delete")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    async def test_create_property_with_minimal_data(self, async_client: AsyncClient):
        """Test creating property with only required fields"""
        minimal_property = {
            "title": "Minimal Property",
            "address": "Some Address",
            "price": 150000,
            "rooms": 2,
            "bathrooms": 1,
            "square_meters": 60,
            "is_apartment": True,
            "is_house": False,
            "source_url": "https://example.com/minimal"
        }

        response = await async_client.post("/properties/", json=minimal_property)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_available"] == True  # Default value

    async def test_property_response_includes_all_fields(self, async_client: AsyncClient):
        """Test that property response includes all expected fields"""
        create_response = await async_client.post("/properties/", json=self.valid_property)
        data = create_response.json()

        # Check all expected fields are present
        expected_fields = [
            "id", "title", "address", "price", "rooms", "bathrooms",
            "square_meters", "is_apartment", "is_house", "building_floor",
            "source_url", "is_available", "amenities", "created_at",
            "updated_at", "images"
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"