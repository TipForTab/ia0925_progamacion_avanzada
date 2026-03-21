import pytest
from src.test.property_fixtures import (
    get_seville_property_fixtures,
    get_specific_test_properties,
)
from src.repositories import PropertyQueryBuilder, PropertyRepository


class TestPropertyQueryBuilder:
    """Test suite for PropertyQueryBuilder - tests query building directly"""

    def test_query_builder_initialization(self, test_db):
        """Test query builder can be initialized"""
        builder = PropertyQueryBuilder(test_db)
        assert builder.db == test_db
        assert builder.query is not None
        assert builder._pagination_skip == 0
        assert builder._pagination_limit == 100

    def test_filter_by_id_chain(self, test_db, property_repo):
        """Test filter_by_id returns chainable builder"""
        test_data = get_specific_test_properties()[0]
        created = property_repo.create(test_data)

        builder = PropertyQueryBuilder(test_db)
        result = builder.filter_by_id(created.id)

        assert isinstance(result, PropertyQueryBuilder)
        assert result.first() is not None
        assert result.first().id == created.id

    def test_price_range_filtering(self, test_db, property_repo):
        """Test price range filtering in query builder"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        results = builder.filter_by_price_range(200000, 400000).all()

        for prop in results:
            assert 200000 <= prop.price <= 400000

    def test_price_min_and_max_separate(self, test_db, property_repo):
        """Test separate min and max price filters"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test min only
        builder = PropertyQueryBuilder(test_db)
        min_results = builder.filter_by_price_min(300000).all()
        for prop in min_results:
            assert prop.price >= 300000

        # Test max only
        builder2 = PropertyQueryBuilder(test_db)
        max_results = builder2.filter_by_price_max(300000).all()
        for prop in max_results:
            assert prop.price <= 300000

    def test_property_type_filtering(self, test_db, property_repo):
        """Test property type filtering"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test apartment filter
        builder = PropertyQueryBuilder(test_db)
        apartments = builder.filter_by_apartment(True).all()
        for apt in apartments:
            assert apt.is_apartment is True

        # Test house filter
        builder2 = PropertyQueryBuilder(test_db)
        houses = builder2.filter_by_house(True).all()
        for house in houses:
            assert house.is_house is True

    def test_room_filtering_exact_and_range(self, test_db, property_repo):
        """Test room count filtering"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test exact
        builder = PropertyQueryBuilder(test_db)
        exact_results = builder.filter_by_rooms_exact(3).all()
        for prop in exact_results:
            assert prop.rooms == 3

        # Test range
        builder2 = PropertyQueryBuilder(test_db)
        range_results = builder2.filter_by_rooms(2, 4).all()
        for prop in range_results:
            assert 2 <= prop.rooms <= 4

    def test_bathroom_filtering(self, test_db, property_repo):
        """Test bathroom count filtering"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        results = builder.filter_by_bathrooms(1, 2).all()

        for prop in results:
            assert 1 <= prop.bathrooms <= 2

    def test_square_meters_filtering(self, test_db, property_repo):
        """Test square meters filtering"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        results = builder.filter_by_square_meters(80, 150).all()

        for prop in results:
            assert 80 <= prop.square_meters <= 150

    def test_address_filtering_fuzzy_and_exact(self, test_db, property_repo):
        """Test address filtering with fuzzy and exact match"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test fuzzy search
        builder = PropertyQueryBuilder(test_db)
        fuzzy_results = builder.filter_by_address("Triana", exact=False).all()
        assert len(fuzzy_results) > 0
        for prop in fuzzy_results:
            assert "Triana" in prop.address

        # Test exact search
        exact_address = fixtures[0]["address"]
        builder2 = PropertyQueryBuilder(test_db)
        exact_results = builder2.filter_by_address(exact_address, exact=True).all()
        for prop in exact_results:
            assert prop.address == exact_address

    def test_title_filtering(self, test_db, property_repo):
        """Test title filtering"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        results = builder.filter_by_title("Santa", exact=False).all()

        assert len(results) > 0
        for prop in results:
            assert "Santa" in prop.title or "santa" in prop.title.lower()

    def test_floor_filtering(self, test_db, property_repo):
        """Test floor filtering"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test specific floor
        builder = PropertyQueryBuilder(test_db)
        floor_0 = builder.filter_by_floor(0).all()
        for prop in floor_0:
            assert prop.building_floor == 0

        # Test floor range
        builder2 = PropertyQueryBuilder(test_db)
        floor_range = builder2.filter_by_floor_range(1, 3).all()
        for prop in floor_range:
            assert 1 <= prop.building_floor <= 3

    def test_availability_filtering(self, test_db, property_repo):
        """Test availability filtering"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test available
        builder = PropertyQueryBuilder(test_db)
        available = builder.filter_by_availability(True).all()
        for prop in available:
            assert prop.is_available is True

        # Test unavailable
        builder2 = PropertyQueryBuilder(test_db)
        unavailable = builder2.filter_by_availability(False).all()
        for prop in unavailable:
            assert prop.is_available is False

    def test_ordering_methods(self, test_db, property_repo):
        """Test all ordering methods"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test price ordering
        builder = PropertyQueryBuilder(test_db)
        asc = builder.order_by_price(ascending=True).all()
        for i in range(len(asc) - 1):
            assert asc[i].price <= asc[i + 1].price

        builder2 = PropertyQueryBuilder(test_db)
        desc = builder2.order_by_price(ascending=False).all()
        for i in range(len(desc) - 1):
            assert desc[i].price >= desc[i + 1].price

        # Test rooms ordering
        builder3 = PropertyQueryBuilder(test_db)
        by_rooms = builder3.order_by_rooms(ascending=True).all()
        for i in range(len(by_rooms) - 1):
            assert by_rooms[i].rooms <= by_rooms[i + 1].rooms

        # Test square meters ordering
        builder4 = PropertyQueryBuilder(test_db)
        by_sqm = builder4.order_by_square_meters(ascending=False).all()
        for i in range(len(by_sqm) - 1):
            assert by_sqm[i].square_meters >= by_sqm[i + 1].square_meters

    def test_pagination_methods(self, test_db, property_repo):
        """Test pagination with skip and limit"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Test skip and limit separately
        builder = PropertyQueryBuilder(test_db)
        page_1 = builder.skip(0).limit(3).all()
        assert len(page_1) <= 3

        builder2 = PropertyQueryBuilder(test_db)
        page_2 = builder2.skip(3).limit(3).all()
        assert len(page_2) <= 3

        # Ensure no overlap
        page_1_ids = {prop.id for prop in page_1}
        page_2_ids = {prop.id for prop in page_2}
        assert page_1_ids.isdisjoint(page_2_ids)

        # Test paginate method
        builder3 = PropertyQueryBuilder(test_db)
        paginated = builder3.paginate(0, 5).all()
        assert len(paginated) <= 5

    def test_count_method(self, test_db, property_repo):
        """Test count method"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        total_count = builder.count()
        assert total_count == len(fixtures)

        # Test count with filters
        builder2 = PropertyQueryBuilder(test_db)
        filtered_count = builder2.filter_by_apartment(True).count()
        assert filtered_count > 0

    def test_exists_method(self, test_db, property_repo):
        """Test exists method"""
        test_data = get_specific_test_properties()[0]
        property_repo.create(test_data)

        # Should exist
        builder = PropertyQueryBuilder(test_db)
        exists = builder.filter_by_title(test_data["title"], exact=True).exists()
        assert exists is True

        # Should not exist
        builder2 = PropertyQueryBuilder(test_db)
        not_exists = builder2.filter_by_title("NonExistentTitle12345").exists()
        assert not_exists is False

    def test_first_method(self, test_db, property_repo):
        """Test first method"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        first_prop = builder.first()
        assert first_prop is not None

        # Test with filter that returns nothing
        builder2 = PropertyQueryBuilder(test_db)
        no_result = builder2.filter_by_price_min(999999999).first()
        assert no_result is None

    def test_complex_chaining(self, test_db, property_repo):
        """Test complex multi-filter chains"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        builder = PropertyQueryBuilder(test_db)
        results = (
            builder.filter_by_apartment(True)
            .filter_by_availability(True)
            .filter_by_price_range(100000, 500000)
            .filter_by_rooms(2, 4)
            .filter_by_square_meters(60, 150)
            .order_by_price(ascending=True)
            .limit(5)
            .all()
        )

        assert len(results) <= 5
        for prop in results:
            assert prop.is_apartment is True
            assert prop.is_available is True
            assert 100000 <= prop.price <= 500000
            assert 2 <= prop.rooms <= 4
            assert 60 <= prop.square_meters <= 150

    def test_get_query_method(self, test_db):
        """Test accessing raw SQLAlchemy query"""
        builder = PropertyQueryBuilder(test_db)
        raw_query = builder.filter_by_apartment(True).get_query()

        assert raw_query is not None
        # Should be able to execute the raw query
        results = raw_query.all()
        assert isinstance(results, list)


class TestPropertyRepository:
    """Test suite for PropertyRepository - tests repository-specific methods"""

    def test_repository_initialization(self, test_db):
        """Test repository initialization"""
        repo = PropertyRepository(test_db)
        assert repo.db == test_db

    def test_query_method_returns_builder(self, property_repo):
        """Test that query() returns a PropertyQueryBuilder"""
        builder = property_repo.query()
        assert isinstance(builder, PropertyQueryBuilder)

    def test_create_property(self, property_repo):
        """Test creating a single property"""
        test_data = get_specific_test_properties()[0]
        created = property_repo.create(test_data)

        assert created.id is not None
        assert created.title == test_data["title"]
        assert created.address == test_data["address"]
        assert created.price == test_data["price"]
        assert created.is_apartment == test_data["is_apartment"]

    def test_get_by_id(self, property_repo):
        """Test getting property by ID"""
        test_data = get_specific_test_properties()[0]
        created = property_repo.create(test_data)

        found = property_repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == test_data["title"]

    def test_get_all_with_pagination(self, property_repo):
        """Test get_all with pagination"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Get first page
        page_1 = property_repo.get_all(skip=0, limit=5)
        assert len(page_1) <= 5

        # Get second page
        page_2 = property_repo.get_all(skip=5, limit=5)
        assert len(page_2) <= 5

        # Ensure different results
        if len(page_1) > 0 and len(page_2) > 0:
            assert page_1[0].id != page_2[0].id

    def test_get_available(self, property_repo):
        """Test get_available method"""
        fixtures = get_specific_test_properties()
        available_count = sum(1 for f in fixtures if f["is_available"])

        for fixture in fixtures:
            property_repo.create(fixture)

        available = property_repo.get_available()
        assert len(available) == available_count

        for prop in available:
            assert prop.is_available is True

    def test_update_property(self, property_repo):
        """Test updating a property"""
        test_data = get_specific_test_properties()[0]
        created = property_repo.create(test_data)

        update_data = {"price": 450000.0, "rooms": 4, "is_available": False}

        updated = property_repo.update(created.id, update_data)

        assert updated is not None
        assert updated.price == 450000.0
        assert updated.rooms == 4
        assert updated.is_available is False
        assert updated.title == test_data["title"]  # Unchanged field

    def test_update_nonexistent_property(self, property_repo):
        """Test updating a property that doesn't exist"""
        result = property_repo.update(999999, {"price": 100000})
        assert result is None

    def test_delete_property(self, property_repo):
        """Test hard delete"""
        test_data = get_specific_test_properties()[0]
        created = property_repo.create(test_data)

        deleted = property_repo.delete(created.id)
        assert deleted is True

        # Verify deletion
        found = property_repo.get_by_id(created.id)
        assert found is None

    def test_delete_nonexistent_property(self, property_repo):
        """Test deleting a property that doesn't exist"""
        result = property_repo.delete(999999)
        assert result is False

    def test_soft_delete(self, property_repo):
        """Test soft delete (mark as unavailable)"""
        test_data = get_specific_test_properties()[0]
        created = property_repo.create(test_data)

        soft_deleted = property_repo.soft_delete(created.id)

        assert soft_deleted is not None
        assert soft_deleted.is_available is False

        # Property still exists
        found = property_repo.get_by_id(created.id)
        assert found is not None
        assert found.is_available is False

    def test_bulk_update_availability(self, property_repo):
        """Test bulk availability update"""
        fixtures = get_specific_test_properties()
        created_ids = []

        for fixture in fixtures:
            created = property_repo.create(fixture)
            created_ids.append(created.id)

        # Bulk update to unavailable
        updated_count = property_repo.bulk_update_availability(created_ids, False)
        assert updated_count == len(created_ids)

        # Verify all are unavailable
        for prop_id in created_ids:
            prop = property_repo.get_by_id(prop_id)
            assert prop.is_available is False

        # Bulk update back to available
        updated_count2 = property_repo.bulk_update_availability(created_ids, True)
        assert updated_count2 == len(created_ids)

        # Verify all are available
        for prop_id in created_ids:
            prop = property_repo.get_by_id(prop_id)
            assert prop.is_available is True

    def test_count_total(self, property_repo):
        """Test total count"""
        initial_count = property_repo.count_total()

        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        new_count = property_repo.count_total()
        assert new_count == initial_count + len(fixtures)

    def test_count_available(self, property_repo):
        """Test available count"""
        fixtures = get_specific_test_properties()
        expected_available = sum(1 for f in fixtures if f["is_available"])

        for fixture in fixtures:
            property_repo.create(fixture)

        available_count = property_repo.count_available()
        assert available_count == expected_available

    def test_count_by_type(self, property_repo):
        """Test count by type"""
        fixtures = get_seville_property_fixtures()
        expected_apartments = sum(1 for f in fixtures if f.get("is_apartment", False))
        expected_houses = sum(1 for f in fixtures if f.get("is_house", False))

        for fixture in fixtures:
            property_repo.create(fixture)

        counts = property_repo.count_by_type()

        assert "apartments" in counts
        assert "houses" in counts
        assert counts["apartments"] == expected_apartments
        assert counts["houses"] == expected_houses


class TestRepositoryDelegation:
    """Test suite for verifying __getattr__ delegation mechanism"""

    def test_filter_method_delegation(self, property_repo):
        """Test that filter methods are delegated to query builder"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # These should work via delegation
        result = property_repo.filter_by_price_min(200000)
        assert isinstance(result, PropertyQueryBuilder)

        # Chain should work
        properties = result.filter_by_apartment(True).all()
        assert isinstance(properties, list)
        for prop in properties:
            assert prop.price >= 200000
            assert prop.is_apartment is True

    def test_order_method_delegation(self, property_repo):
        """Test that order methods are delegated"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Should work via delegation
        result = property_repo.order_by_price(ascending=True)
        assert isinstance(result, PropertyQueryBuilder)

        properties = result.all()
        for i in range(len(properties) - 1):
            assert properties[i].price <= properties[i + 1].price

    def test_multiple_delegated_calls(self, property_repo):
        """Test chaining multiple delegated methods"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        # All these should work via delegation
        results = (
            property_repo.filter_by_apartment(True)
            .filter_by_price_range(100000, 400000)
            .filter_by_rooms(2, 4)
            .order_by_price(ascending=True)
            .limit(5)
            .all()
        )

        assert isinstance(results, list)
        assert len(results) <= 5

    def test_non_delegated_methods_work(self, property_repo):
        """Test that non-delegated methods still work normally"""
        test_data = get_specific_test_properties()[0]

        # These should NOT be delegated
        created = property_repo.create(test_data)
        assert created.id is not None

        found = property_repo.get_by_id(created.id)
        assert found is not None

        count = property_repo.count_total()
        assert isinstance(count, int)

    def test_invalid_method_raises_error(self, property_repo):
        """Test that invalid methods raise AttributeError"""
        with pytest.raises(AttributeError):
            property_repo.some_nonexistent_method()

    def test_delegation_preserves_chainability(self, property_repo):
        """Test that delegation preserves the chainable interface"""
        fixtures = get_specific_test_properties()
        for fixture in fixtures:
            property_repo.create(fixture)

        # Start with repo delegation
        builder = property_repo.filter_by_apartment(True)
        assert isinstance(builder, PropertyQueryBuilder)

        # Continue chaining on the builder
        results = builder.filter_by_availability(True).order_by_price().limit(3).all()

        assert isinstance(results, list)


class TestPropertySearchScenarios:
    """Integration tests with realistic search scenarios"""

    def test_young_couple_apartment_search(self, property_repo):
        """Scenario: Young couple looking for apartment in Triana, max 300k"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        results = (
            property_repo.filter_by_apartment(True)
            .filter_by_address("Triana")
            .filter_by_price_max(300000)
            .filter_by_availability(True)
            .order_by_price(ascending=True)
            .all()
        )

        assert isinstance(results, list)
        for prop in results:
            assert prop.is_apartment is True
            assert "Triana" in prop.address
            assert prop.price <= 300000
            assert prop.is_available is True

    def test_family_house_search(self, property_repo):
        """Scenario: Family looking for house with 3+ bedrooms, 150k-500k"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        results = (
            property_repo.filter_by_house(True)
            .filter_by_rooms(3)
            .filter_by_price_range(150000, 500000)
            .filter_by_availability(True)
            .order_by_square_meters(ascending=False)
            .all()
        )

        assert isinstance(results, list)
        for prop in results:
            assert prop.is_house is True
            assert prop.rooms >= 3
            assert 150000 <= prop.price <= 500000
            assert prop.is_available is True

    def test_investor_centro_historico_search(self, property_repo):
        """Scenario: Investor looking at all properties in Centro Histórico"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        results = (
            property_repo.filter_by_address("Centro")
            .order_by_price(ascending=True)
            .all()
        )

        assert isinstance(results, list)
        for prop in results:
            assert "Centro" in prop.address or "centro" in prop.address.lower()

    def test_budget_conscious_search(self, property_repo):
        """Scenario: Budget-conscious buyer looking for any property under 200k"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        results = (
            property_repo.filter_by_price_max(200000)
            .filter_by_availability(True)
            .order_by_square_meters(ascending=False)
            .limit(10)
            .all()
        )

        assert isinstance(results, list)
        assert len(results) <= 10
        for prop in results:
            assert prop.price <= 200000
            assert prop.is_available is True

    def test_luxury_search(self, property_repo):
        """Scenario: Luxury buyer looking for large properties"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        results = (
            property_repo.filter_by_price_min(400000)
            .filter_by_square_meters(120)
            .filter_by_rooms(3)
            .order_by_price(ascending=False)
            .all()
        )

        assert isinstance(results, list)
        for prop in results:
            assert prop.price >= 400000
            assert prop.square_meters >= 120
            assert prop.rooms >= 3

    def test_ground_floor_accessibility_search(self, property_repo):
        """Scenario: Buyer with mobility issues looking for ground floor"""
        fixtures = get_seville_property_fixtures()
        for fixture in fixtures:
            property_repo.create(fixture)

        results = (
            property_repo.filter_by_floor(0)
            .filter_by_availability(True)
            .order_by_price(ascending=True)
            .all()
        )

        assert isinstance(results, list)
        for prop in results:
            assert prop.building_floor == 0
            assert prop.is_available is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
