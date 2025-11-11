import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestImageCRUDEndpoints:
    """Test suite for Image CRUD endpoints"""

    # Test data
    valid_property = {
        "title": "Test Property for Images",
        "address": "Calle Test, 123, Madrid",
        "price": 200000,
        "rooms": 2,
        "bathrooms": 1,
        "square_meters": 70,
        "is_apartment": True,
        "is_house": False,
        "source_url": "https://example.com/test-property",
        "is_available": True
    }

    valid_image = {
        "property_id": None,
        "img_url": "https://example.com/images/test1.jpg",
        "calculated_tags": {
            "room_type": "bedroom",
            "features": ["window", "door"],
            "style": "modern"
        }
    }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def create_test_property(self, async_client: AsyncClient) -> int:
        """Helper to create a test property and return its ID"""
        property_data = self.valid_property.copy()
        response = await async_client.post("/properties/", json=property_data)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()["id"]

    async def create_test_image(self, async_client: AsyncClient, property_id: int, img_url: str = None) -> dict:
        """Helper to create a test image and return the response data"""
        image_data = self.valid_image.copy()
        image_data["property_id"] = property_id
        if img_url:
            image_data["img_url"] = img_url
        response = await async_client.post("/images/", json=image_data)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    # ========================================================================
    # CREATE TESTS
    # ========================================================================

    async def test_create_image_success(self, async_client: AsyncClient):
        """Test creating an image with valid data"""
        property_id = await self.create_test_property(async_client)

        image_data = self.valid_image.copy()
        image_data["property_id"] = property_id

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["property_id"] == property_id
        assert data["img_url"] == self.valid_image["img_url"]
        assert data["calculated_tags"] == self.valid_image["calculated_tags"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_image_without_tags(self, async_client: AsyncClient):
        """Test creating image without calculated_tags"""
        property_id = await self.create_test_property(async_client)

        image_data = {
            "property_id": property_id,
            "img_url": "https://example.com/images/no-tags.jpg"
        }

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["calculated_tags"] is None

    async def test_create_image_invalid_property_id(self, async_client: AsyncClient):
        """Test creating image with non-existent property"""
        image_data = self.valid_image.copy()
        image_data["property_id"] = 999999

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_image_invalid_url_format(self, async_client: AsyncClient):
        """Test creating image with invalid URL format"""
        property_id = await self.create_test_property(async_client)

        image_data = self.valid_image.copy()
        image_data["property_id"] = property_id
        image_data["img_url"] = "invalid-url"  # No http:// or https://

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_image_duplicate_url_same_property(self, async_client: AsyncClient):
        """Test creating image with duplicate URL for same property"""
        property_id = await self.create_test_property(async_client)

        image_data = self.valid_image.copy()
        image_data["property_id"] = property_id

        # Create first image
        response1 = await async_client.post("/images/", json=image_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create duplicate
        response2 = await async_client.post("/images/", json=image_data)
        assert response2.status_code == status.HTTP_409_CONFLICT

    async def test_create_image_same_url_different_properties(self, async_client: AsyncClient):
        """Test that same URL can be used for different properties"""
        property1_id = await self.create_test_property(async_client)

        # Create second property
        property2_data = self.valid_property.copy()
        property2_data["source_url"] = "https://example.com/property2"
        response = await async_client.post("/properties/", json=property2_data)
        property2_id = response.json()["id"]

        # Create image for first property
        image_data1 = self.valid_image.copy()
        image_data1["property_id"] = property1_id
        response1 = await async_client.post("/images/", json=image_data1)
        assert response1.status_code == status.HTTP_201_CREATED

        # Create image with same URL for second property (should work)
        image_data2 = self.valid_image.copy()
        image_data2["property_id"] = property2_id
        response2 = await async_client.post("/images/", json=image_data2)
        assert response2.status_code == status.HTTP_201_CREATED

    async def test_create_image_missing_required_fields(self, async_client: AsyncClient):
        """Test creating image with missing required fields"""
        invalid_data = {
            "property_id": 1
            # Missing img_url
        }

        response = await async_client.post("/images/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================================================================
    # BULK CREATE TESTS
    # ========================================================================

    async def test_bulk_create_images_success(self, async_client: AsyncClient):
        """Test bulk creating images"""
        property_id = await self.create_test_property(async_client)

        bulk_data = {
            "property_id": property_id,
            "image_urls": [
                "https://example.com/images/bulk1.jpg",
                "https://example.com/images/bulk2.jpg",
                "https://example.com/images/bulk3.jpg"
            ]
        }

        response = await async_client.post("/images/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

        for image in data:
            assert image["property_id"] == property_id
            assert "id" in image
            assert image["img_url"] in bulk_data["image_urls"]

    async def test_bulk_create_images_invalid_property(self, async_client: AsyncClient):
        """Test bulk create with non-existent property"""
        bulk_data = {
            "property_id": 999999,
            "image_urls": [
                "https://example.com/images/test1.jpg",
                "https://example.com/images/test2.jpg"
            ]
        }

        response = await async_client.post("/images/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_bulk_create_images_invalid_url_format(self, async_client: AsyncClient):
        """Test bulk create with invalid URL"""
        property_id = await self.create_test_property(async_client)

        bulk_data = {
            "property_id": property_id,
            "image_urls": [
                "https://example.com/images/valid.jpg",
                "invalid-url",  # Invalid
                "https://example.com/images/valid2.jpg"
            ]
        }

        response = await async_client.post("/images/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_bulk_create_images_with_duplicates(self, async_client: AsyncClient):
        """Test bulk create with URLs that already exist"""
        property_id = await self.create_test_property(async_client)

        # Create first image
        await self.create_test_image(
            async_client,
            property_id,
            "https://example.com/images/existing.jpg"
        )

        # Try to bulk create including the existing URL
        bulk_data = {
            "property_id": property_id,
            "image_urls": [
                "https://example.com/images/existing.jpg",  # Already exists
                "https://example.com/images/new.jpg"
            ]
        }

        response = await async_client.post("/images/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_bulk_create_images_empty_list(self, async_client: AsyncClient):
        """Test bulk create with empty URL list"""
        property_id = await self.create_test_property(async_client)

        bulk_data = {
            "property_id": property_id,
            "image_urls": []
        }

        response = await async_client.post("/images/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_bulk_create_images_exceeds_limit(self, async_client: AsyncClient):
        """Test bulk create with more than 50 images"""
        property_id = await self.create_test_property(async_client)

        bulk_data = {
            "property_id": property_id,
            "image_urls": [f"https://example.com/images/img{i}.jpg" for i in range(51)]
        }

        response = await async_client.post("/images/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================================================================
    # READ TESTS
    # ========================================================================

    async def test_get_image_by_id_success(self, async_client: AsyncClient):
        """Test getting an image by ID"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        response = await async_client.get(f"/images/{image_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == image_id
        assert data["property_id"] == property_id

    async def test_get_image_by_id_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent image"""
        response = await async_client.get("/images/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_all_images(self, async_client: AsyncClient):
        """Test getting all images with pagination"""
        property_id = await self.create_test_property(async_client)

        # Create multiple images
        for i in range(3):
            await self.create_test_image(
                async_client,
                property_id,
                f"https://example.com/images/test{i}.jpg"
            )

        response = await async_client.get("/images/?skip=0&limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    async def test_get_all_images_pagination(self, async_client: AsyncClient):
        """Test pagination parameters"""
        property_id = await self.create_test_property(async_client)

        # Create 5 images
        for i in range(5):
            await self.create_test_image(
                async_client,
                property_id,
                f"https://example.com/images/page{i}.jpg"
            )

        # Get first page (2 items)
        response1 = await async_client.get("/images/?skip=0&limit=2")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert len(data1) == 2

        # Get second page (2 items)
        response2 = await async_client.get("/images/?skip=2&limit=2")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert len(data2) == 2

        # Ensure different results
        assert data1[0]["id"] != data2[0]["id"]

    async def test_get_images_by_property_id(self, async_client: AsyncClient):
        """Test getting images for a specific property"""
        property_id = await self.create_test_property(async_client)

        # Create images for this property
        for i in range(3):
            await self.create_test_image(
                async_client,
                property_id,
                f"https://example.com/images/prop{i}.jpg"
            )

        response = await async_client.get(f"/images/property/{property_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

        # All images should belong to this property
        for image in data:
            assert image["property_id"] == property_id

    async def test_get_images_by_invalid_property_id(self, async_client: AsyncClient):
        """Test getting images for non-existent property"""
        response = await async_client.get("/images/property/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_images_without_tags(self, async_client: AsyncClient):
        """Test getting images without calculated tags"""
        property_id = await self.create_test_property(async_client)

        # Create image without tags
        image_data = {
            "property_id": property_id,
            "img_url": "https://example.com/images/no-tags1.jpg"
        }
        await async_client.post("/images/", json=image_data)

        # Create image with tags
        image_with_tags = self.valid_image.copy()
        image_with_tags["property_id"] = property_id
        image_with_tags["img_url"] = "https://example.com/images/with-tags.jpg"
        await async_client.post("/images/", json=image_with_tags)

        response = await async_client.get("/images/without-tags/list")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # All returned images should not have tags
        for image in data:
            assert image["calculated_tags"] is None

    async def test_get_recent_images(self, async_client: AsyncClient):
        """Test getting recent images"""
        property_id = await self.create_test_property(async_client)
        await self.create_test_image(async_client, property_id)

        response = await async_client.get("/images/recent/list?days=7&limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_recent_images_invalid_days(self, async_client: AsyncClient):
        """Test getting recent images with invalid days parameter"""
        # Days less than 1
        response1 = await async_client.get("/images/recent/list?days=0")
        assert response1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Days more than 365
        response2 = await async_client.get("/images/recent/list?days=400")
        assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ========================================================================
    # UPDATE TESTS
    # ========================================================================

    async def test_update_image_success(self, async_client: AsyncClient):
        """Test updating an image"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        update_data = {
            "img_url": "https://example.com/images/updated.jpg",
            "calculated_tags": {
                "room_type": "kitchen",
                "features": ["sink", "stove"]
            }
        }
        response = await async_client.put(f"/images/{image_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["img_url"] == update_data["img_url"]
        assert data["calculated_tags"] == update_data["calculated_tags"]

    async def test_update_image_partial(self, async_client: AsyncClient):
        """Test partial update (PATCH)"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        update_data = {
            "calculated_tags": {
                "room_type": "bathroom"
            }
        }
        response = await async_client.patch(f"/images/{image_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["calculated_tags"] == update_data["calculated_tags"]
        assert data["img_url"] == self.valid_image["img_url"]  # Unchanged

    async def test_update_image_not_found(self, async_client: AsyncClient):
        """Test updating non-existent image"""
        update_data = {"img_url": "https://example.com/new.jpg"}
        response = await async_client.put("/images/999999", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_image_invalid_url(self, async_client: AsyncClient):
        """Test updating with invalid URL"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        update_data = {"img_url": "invalid-url"}
        response = await async_client.put(f"/images/{image_id}", json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_image_invalid_property_id(self, async_client: AsyncClient):
        """Test updating with non-existent property_id"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        update_data = {"property_id": 999999}
        response = await async_client.put(f"/images/{image_id}", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_image_no_fields(self, async_client: AsyncClient):
        """Test updating with no fields provided"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        response = await async_client.put(f"/images/{image_id}", json={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_update_image_tags_only(self, async_client: AsyncClient):
        """Test updating only tags using dedicated endpoint"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        tags_data = {
            "calculated_tags": {
                "room_type": "living_room",
                "features": ["sofa", "tv"],
                "confidence": 0.95
            }
        }
        response = await async_client.patch(f"/images/{image_id}/tags", json=tags_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["calculated_tags"] == tags_data["calculated_tags"]

    async def test_update_image_tags_empty(self, async_client: AsyncClient):
        """Test updating tags with empty dict"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        tags_data = {"calculated_tags": {}}
        response = await async_client.patch(f"/images/{image_id}/tags", json=tags_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


    # ========================================================================
    # DELETE TESTS
    # ========================================================================

    async def test_delete_image_success(self, async_client: AsyncClient):
        """Test deleting an image"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)
        image_id = created_image["id"]

        response = await async_client.delete(f"/images/{image_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's deleted
        get_response = await async_client.get(f"/images/{image_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_image_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent image"""
        response = await async_client.delete("/images/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_images_by_property(self, async_client: AsyncClient):
        """Test deleting all images for a property"""
        property_id = await self.create_test_property(async_client)

        # Create multiple images
        for i in range(3):
            await self.create_test_image(
                async_client,
                property_id,
                f"https://example.com/images/delete{i}.jpg"
            )

        response = await async_client.delete(f"/images/property/{property_id}/all")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 3
        assert data["property_id"] == property_id

        # Verify images are deleted
        get_response = await async_client.get(f"/images/property/{property_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert len(get_response.json()) == 0

    async def test_delete_images_by_invalid_property(self, async_client: AsyncClient):
        """Test deleting images for non-existent property"""
        response = await async_client.delete("/images/property/999999/all")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ========================================================================
    # SEARCH TESTS
    # ========================================================================

    async def test_search_images_by_property_id(self, async_client: AsyncClient):
        """Test searching images by property_id"""
        property_id = await self.create_test_property(async_client)
        await self.create_test_image(async_client, property_id)

        search_filters = {"property_id": property_id}
        response = await async_client.post("/images/search", json=search_filters)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for image in data:
            assert image["property_id"] == property_id

    async def test_search_images_by_has_tags(self, async_client: AsyncClient):
        """Test searching images by tag presence"""
        property_id = await self.create_test_property(async_client)

        # Create image without tags
        image_without_tags = {
            "property_id": property_id,
            "img_url": "https://example.com/images/search-no-tags.jpg"
        }
        await async_client.post("/images/", json=image_without_tags)

        search_filters = {"has_tags": False}
        response = await async_client.post("/images/search", json=search_filters)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for image in data:
            assert image["calculated_tags"] is None

    async def test_search_images_with_pagination(self, async_client: AsyncClient):
        """Test search with pagination"""
        property_id = await self.create_test_property(async_client)

        for i in range(5):
            await self.create_test_image(
                async_client,
                property_id,
                f"https://example.com/images/search{i}.jpg"
            )

        search_filters = {
            "property_id": property_id,
            "skip": 0,
            "limit": 2
        }
        response = await async_client.post("/images/search", json=search_filters)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    # ========================================================================
    # UTILITY TESTS
    # ========================================================================

    async def test_check_url_exists_true(self, async_client: AsyncClient):
        """Test checking if URL exists - should return true"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)

        response = await async_client.get(
            f"/images/check/url-exists?url={created_image['img_url']}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is True
        assert data["image_id"] == created_image["id"]
        assert data["property_id"] == property_id

    async def test_check_url_exists_false(self, async_client: AsyncClient):
        """Test checking if URL exists - should return false"""
        response = await async_client.get(
            "/images/check/url-exists?url=https://example.com/nonexistent.jpg"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is False
        assert data["image_id"] is None
        assert data["property_id"] is None

    async def test_find_duplicate_images(self, async_client: AsyncClient):
        """Test finding duplicate image URLs"""
        property1_id = await self.create_test_property(async_client)

        # Create second property
        property2_data = self.valid_property.copy()
        property2_data["source_url"] = "https://example.com/property2-dup"
        response = await async_client.post("/properties/", json=property2_data)
        property2_id = response.json()["id"]

        # Create images with same URL
        duplicate_url = "https://example.com/images/duplicate.jpg"
        await self.create_test_image(async_client, property1_id, duplicate_url)
        await self.create_test_image(async_client, property2_id, duplicate_url)

        response = await async_client.get("/images/duplicates/find")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # Check if our duplicate is in the list
        duplicate_found = any(item["url"] == duplicate_url for item in data)
        assert duplicate_found

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    async def test_image_response_includes_all_fields(self, async_client: AsyncClient):
        """Test that image response includes all expected fields"""
        property_id = await self.create_test_property(async_client)
        created_image = await self.create_test_image(async_client, property_id)

        expected_fields = [
            "id", "property_id", "img_url", "calculated_tags",
            "created_at", "updated_at"
        ]

        for field in expected_fields:
            assert field in created_image, f"Missing field: {field}"

    async def test_create_image_with_long_url(self, async_client: AsyncClient):
        """Test creating image with very long URL (within limit)"""
        property_id = await self.create_test_property(async_client)

        long_url = "https://example.com/" + "a" * 950 + ".jpg"  # Under 1000 chars
        image_data = {
            "property_id": property_id,
            "img_url": long_url
        }

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_201_CREATED

    async def test_create_image_with_url_exceeding_limit(self, async_client: AsyncClient):
        """Test creating image with URL exceeding 1000 chars"""
        property_id = await self.create_test_property(async_client)

        too_long_url = "https://example.com/" + "a" * 1100 + ".jpg"  # Over 1000
        image_data = {
            "property_id": property_id,
            "img_url": too_long_url
        }

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_image_with_complex_tags(self, async_client: AsyncClient):
        """Test creating image with complex nested tags structure"""
        property_id = await self.create_test_property(async_client)

        image_data = {
            "property_id": property_id,
            "img_url": "https://example.com/complex-tags.jpg",
            "calculated_tags": {
                "room_type": "bedroom",
                "features": {
                    "furniture": ["bed", "wardrobe", "nightstand"],
                    "lighting": ["ceiling_light", "bedside_lamp"],
                    "windows": 2
                },
                "style": "modern",
                "colors": ["white", "gray", "blue"],
                "confidence": 0.94,
                "metadata": {
                    "model": "vision-v1",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }

        response = await async_client.post("/images/", json=image_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["calculated_tags"] == image_data["calculated_tags"]