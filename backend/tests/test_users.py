"""
User management and RBAC tests
"""
import pytest
from unittest.mock import patch, Mock


class TestUserInvitation:
    """Test user invitation (Admin only)"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_admin_can_invite_user(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to invite new users"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        # Mock Firebase user creation
        users_mock.create_user.return_value = Mock(uid='new-user-123')

        users_ref = Mock()
        users_mock.get_database_ref.return_value = users_ref

        invite_data = {
            "email": "newuser@example.com",
            "role": "manager",
            "assignedListings": ["listing-1"]
        }

        response = client.post(
            "/users/invite",
            headers={"Authorization": "Bearer admin-token"},
            json=invite_data
        )

        assert response.status_code == 201
        assert 'tempPassword' in response.json()
        assert response.json()['user']['email'] == 'newuser@example.com'

    @patch('app.core.auth.firebase_client')
    def test_manager_cannot_invite_user(self, auth_mock, client, manager_user):
        """Manager should not be able to invite users"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        invite_data = {
            "email": "newuser@example.com",
            "role": "viewer"
        }

        response = client.post(
            "/users/invite",
            headers={"Authorization": "Bearer manager-token"},
            json=invite_data
        )

        assert response.status_code == 403


class TestUserManagement:
    """Test user CRUD operations"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_get_all_users(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to get all users"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        users_ref = Mock()
        users_ref.get.return_value = {
            'user-1': {
                'email': 'user1@example.com',
                'role': 'manager',
                'active': True
            },
            'user-2': {
                'email': 'user2@example.com',
                'role': 'viewer',
                'active': True
            }
        }
        users_mock.get_database_ref.return_value = users_ref

        response = client.get(
            "/users",
            headers={"Authorization": "Bearer admin-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_update_user_role(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to update user roles"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        user_ref = Mock()
        user_ref.get.return_value = {
            'email': 'user@example.com',
            'role': 'viewer',
            'active': True
        }
        users_mock.get_database_ref.return_value = user_ref

        update_data = {
            "role": "manager",
            "assignedListings": ["listing-1", "listing-2"]
        }

        response = client.put(
            "/users/user-123",
            headers={"Authorization": "Bearer admin-token"},
            json=update_data
        )

        assert response.status_code == 200
        user_ref.update.assert_called_once()

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_deactivate_user(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to deactivate users"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        user_ref = Mock()
        user_ref.get.return_value = {
            'email': 'user@example.com',
            'role': 'manager',
            'active': True
        }
        users_mock.get_database_ref.return_value = user_ref

        # Mock Firebase Auth disable
        users_mock.update_user = Mock()

        response = client.post(
            "/users/user-123/deactivate",
            headers={"Authorization": "Bearer admin-token"}
        )

        assert response.status_code == 200
        user_ref.update.assert_called_with({'active': False})

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_activate_user(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to activate users"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        user_ref = Mock()
        user_ref.get.return_value = {
            'email': 'user@example.com',
            'role': 'manager',
            'active': False
        }
        users_mock.get_database_ref.return_value = user_ref

        # Mock Firebase Auth enable
        users_mock.update_user = Mock()

        response = client.post(
            "/users/user-123/activate",
            headers={"Authorization": "Bearer admin-token"}
        )

        assert response.status_code == 200
        user_ref.update.assert_called_with({'active': True})


class TestListingAssignment:
    """Test listing assignment to users"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_assign_listings_to_manager(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to assign listings to managers"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        user_ref = Mock()
        user_ref.get.return_value = {
            'email': 'manager@example.com',
            'role': 'manager',
            'active': True,
            'assignedListings': ['listing-1']
        }
        users_mock.get_database_ref.return_value = user_ref

        update_data = {
            "assignedListings": ["listing-1", "listing-2", "listing-3"]
        }

        response = client.put(
            "/users/user-123",
            headers={"Authorization": "Bearer admin-token"},
            json=update_data
        )

        assert response.status_code == 200

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_unassign_all_listings(self, users_mock, auth_mock, client, admin_user):
        """Admin should be able to remove all listing assignments"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        user_ref = Mock()
        user_ref.get.return_value = {
            'email': 'manager@example.com',
            'role': 'manager',
            'active': True,
            'assignedListings': ['listing-1', 'listing-2']
        }
        users_mock.get_database_ref.return_value = user_ref

        update_data = {
            "assignedListings": []
        }

        response = client.put(
            "/users/user-123",
            headers={"Authorization": "Bearer admin-token"},
            json=update_data
        )

        assert response.status_code == 200


class TestRoleValidation:
    """Test role validation"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.users.firebase_client')
    def test_cannot_create_invalid_role(self, users_mock, auth_mock, client, admin_user):
        """Should not be able to create user with invalid role"""
        auth_mock.verify_token.return_value = {'uid': admin_user['uid'], 'email': admin_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = admin_user
        auth_mock.get_database_ref.return_value = auth_ref

        invite_data = {
            "email": "newuser@example.com",
            "role": "superuser"  # Invalid role
        }

        response = client.post(
            "/users/invite",
            headers={"Authorization": "Bearer admin-token"},
            json=invite_data
        )

        assert response.status_code == 422  # Validation error


class TestSelfManagement:
    """Test users managing their own profile"""

    @patch('app.core.auth.firebase_client')
    def test_user_can_view_own_profile(self, auth_mock, client, manager_user):
        """Users should be able to view their own profile"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer manager-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['email'] == manager_user['email']
        assert data['role'] == manager_user['role']
