"""
Listings CRUD operations tests
"""
import pytest
from unittest.mock import patch, Mock


class TestListingsCRUD:
    """Test listings create, read, update, delete operations"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_create_listing_as_admin(self, listings_mock, auth_mock, client, admin_user):
        """Admin should be able to create listings"""
        # Setup auth
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        # Setup listings mock
        listings_ref = Mock()
        listings_ref.push.return_value = Mock(key='new-listing-id')
        listings_mock.get_database_ref.return_value = listings_ref

        listing_data = {
            "name": "Beach House",
            "address": "123 Ocean Dr",
            "description": "Beautiful beach house"
        }

        response = client.post(
            "/listings",
            headers={"Authorization": "Bearer admin-token"},
            json=listing_data
        )

        assert response.status_code == 201
        assert 'id' in response.json()

    @patch('app.core.auth.firebase_client')
    def test_create_listing_as_manager(self, auth_mock, client, manager_user):
        """Manager should not be able to create listings"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        listing_data = {
            "name": "Beach House",
            "address": "123 Ocean Dr"
        }

        response = client.post(
            "/listings",
            headers={"Authorization": "Bearer manager-token"},
            json=listing_data
        )

        assert response.status_code == 403

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_get_all_listings(self, listings_mock, auth_mock, client, admin_user):
        """User should be able to get all listings they have access to"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        listings_ref = Mock()
        listings_ref.get.return_value = {
            'listing-1': {'name': 'House 1', 'address': '123 St'},
            'listing-2': {'name': 'House 2', 'address': '456 Ave'}
        }
        listings_mock.get_database_ref.return_value = listings_ref

        response = client.get(
            "/listings",
            headers={"Authorization": "Bearer admin-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_get_single_listing(self, listings_mock, auth_mock, client, admin_user):
        """User should be able to get a specific listing"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        listings_ref = Mock()
        listings_ref.get.return_value = {'name': 'House 1', 'address': '123 St'}
        listings_mock.get_database_ref.return_value = listings_ref

        response = client.get(
            "/listings/listing-1",
            headers={"Authorization": "Bearer admin-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'House 1'

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_update_listing_as_admin(self, listings_mock, auth_mock, client, admin_user):
        """Admin should be able to update listings"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        listings_ref = Mock()
        listings_ref.get.return_value = {'name': 'Old Name', 'address': '123 St'}
        listings_mock.get_database_ref.return_value = listings_ref

        update_data = {
            "name": "New Name",
            "address": "456 Ave"
        }

        response = client.put(
            "/listings/listing-1",
            headers={"Authorization": "Bearer admin-token"},
            json=update_data
        )

        assert response.status_code == 200
        listings_ref.update.assert_called_once()

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_delete_listing_as_admin(self, listings_mock, auth_mock, client, admin_user):
        """Admin should be able to delete listings"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        listings_ref = Mock()
        listings_ref.get.return_value = {'name': 'House 1'}
        listings_mock.get_database_ref.return_value = listings_ref

        response = client.delete(
            "/listings/listing-1",
            headers={"Authorization": "Bearer admin-token"}
        )

        assert response.status_code == 200
        listings_ref.delete.assert_called_once()


class TestListingAccessControl:
    """Test listing-level access control"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_manager_can_only_see_assigned_listings(self, listings_mock, auth_mock, client, manager_user):
        """Manager should only see listings they're assigned to"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        listings_ref = Mock()
        listings_ref.get.return_value = {
            'listing-1': {'name': 'Assigned House'},
            'listing-2': {'name': 'Another Assigned House'},
            'listing-3': {'name': 'Not Assigned House'}
        }
        listings_mock.get_database_ref.return_value = listings_ref

        response = client.get(
            "/listings",
            headers={"Authorization": "Bearer manager-token"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should only see assigned listings
        listing_ids = [item['id'] for item in data]
        assert 'listing-1' in listing_ids
        assert 'listing-2' in listing_ids
        assert 'listing-3' not in listing_ids

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.listings.firebase_client')
    def test_manager_cannot_access_unassigned_listing(self, listings_mock, auth_mock, client, manager_user):
        """Manager should not access listings they're not assigned to"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        listings_ref = Mock()
        listings_ref.get.return_value = {'name': 'Unassigned House'}
        listings_mock.get_database_ref.return_value = listings_ref

        response = client.get(
            "/listings/listing-999",
            headers={"Authorization": "Bearer manager-token"}
        )

        assert response.status_code == 403
