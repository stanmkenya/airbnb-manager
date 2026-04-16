"""
Authentication tests
"""
import pytest
from unittest.mock import patch, Mock


class TestAuthentication:
    """Test authentication endpoints and middleware"""

    def test_health_endpoint_no_auth(self, client):
        """Health endpoint should work without authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

    def test_root_endpoint_no_auth(self, client):
        """Root endpoint should work without authentication"""
        response = client.get("/")
        assert response.status_code == 200
        assert 'message' in response.json()

    @patch('app.core.auth.firebase_client')
    def test_protected_endpoint_without_token(self, mock_client, client):
        """Protected endpoints should reject requests without token"""
        response = client.get("/listings")
        assert response.status_code == 403

    @patch('app.core.auth.firebase_client')
    def test_protected_endpoint_with_invalid_token(self, mock_client, client):
        """Protected endpoints should reject invalid tokens"""
        mock_client.verify_token.side_effect = Exception("Invalid token")

        response = client.get(
            "/listings",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    @patch('app.core.auth.firebase_client')
    def test_protected_endpoint_with_valid_token(self, mock_client, client, admin_user):
        """Protected endpoints should accept valid tokens"""
        # Mock token verification
        mock_client.verify_token.return_value = {
            'uid': admin_user['uid'],
            'email': admin_user['email']
        }

        # Mock database user fetch
        mock_ref = Mock()
        mock_ref.get.return_value = admin_user
        mock_client.get_database_ref.return_value = mock_ref

        response = client.get(
            "/listings",
            headers={"Authorization": "Bearer valid-token"}
        )
        # Should not be 401 or 403
        assert response.status_code != 401
        assert response.status_code != 403


class TestRoleBasedAccess:
    """Test role-based access control"""

    @patch('app.core.auth.firebase_client')
    def test_admin_can_access_admin_endpoints(self, mock_client, client, admin_user):
        """Admin users should access admin-only endpoints"""
        mock_client.verify_token.return_value = {
            'uid': admin_user['uid'],
            'email': admin_user['email']
        }

        mock_ref = Mock()
        mock_ref.get.return_value = admin_user
        mock_client.get_database_ref.return_value = mock_ref

        response = client.get(
            "/users",
            headers={"Authorization": "Bearer admin-token"}
        )
        assert response.status_code != 403

    @patch('app.core.auth.firebase_client')
    def test_manager_cannot_access_admin_endpoints(self, mock_client, client, manager_user):
        """Manager users should not access admin-only endpoints"""
        mock_client.verify_token.return_value = {
            'uid': manager_user['uid'],
            'email': manager_user['email']
        }

        mock_ref = Mock()
        mock_ref.get.return_value = manager_user
        mock_client.get_database_ref.return_value = mock_ref

        response = client.post(
            "/users/invite",
            headers={"Authorization": "Bearer manager-token"},
            json={"email": "new@example.com", "role": "viewer"}
        )
        assert response.status_code == 403

    @patch('app.core.auth.firebase_client')
    def test_viewer_cannot_create_expenses(self, mock_client, client, viewer_user):
        """Viewer users should not be able to create expenses"""
        mock_client.verify_token.return_value = {
            'uid': viewer_user['uid'],
            'email': viewer_user['email']
        }

        mock_ref = Mock()
        mock_ref.get.return_value = viewer_user
        mock_client.get_database_ref.return_value = mock_ref

        response = client.post(
            "/expenses",
            headers={"Authorization": "Bearer viewer-token"},
            json={
                "listingId": "listing-1",
                "amount": 100,
                "category": "Cleaning",
                "date": "2024-01-01"
            }
        )
        assert response.status_code == 403


class TestUserStatus:
    """Test user active/inactive status"""

    @patch('app.core.auth.firebase_client')
    def test_inactive_user_cannot_access(self, mock_client, client):
        """Inactive users should not be able to access the system"""
        inactive_user = {
            'uid': 'inactive-123',
            'email': 'inactive@example.com',
            'role': 'manager',
            'active': False
        }

        mock_client.verify_token.return_value = {
            'uid': inactive_user['uid'],
            'email': inactive_user['email']
        }

        mock_ref = Mock()
        mock_ref.get.return_value = inactive_user
        mock_client.get_database_ref.return_value = mock_ref

        response = client.get(
            "/listings",
            headers={"Authorization": "Bearer inactive-token"}
        )
        assert response.status_code == 403
