"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.core.config import Settings


# Mock Firebase for tests
@pytest.fixture
def mock_firebase():
    """Mock Firebase Admin SDK"""
    with patch('app.firebase_client.FirebaseClient') as mock:
        mock_instance = Mock()
        mock_instance.verify_token.return_value = {
            'uid': 'test-user-123',
            'email': 'test@example.com'
        }
        mock_instance.get_database_ref.return_value = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_settings():
    """Mock settings for tests"""
    return Settings(
        FIREBASE_SERVICE_ACCOUNT_JSON='{"test": "mock"}',
        FIREBASE_DATABASE_URL='https://test-db.firebaseio.com',
        ALLOWED_ORIGINS='http://localhost:3000',
        DEBUG=True
    )


@pytest.fixture
def client(mock_firebase):
    """Test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def admin_user():
    """Mock admin user"""
    return {
        'uid': 'admin-123',
        'email': 'admin@example.com',
        'role': 'admin',
        'active': True
    }


@pytest.fixture
def manager_user():
    """Mock manager user"""
    return {
        'uid': 'manager-123',
        'email': 'manager@example.com',
        'role': 'manager',
        'active': True,
        'assignedListings': ['listing-1', 'listing-2']
    }


@pytest.fixture
def viewer_user():
    """Mock viewer user"""
    return {
        'uid': 'viewer-123',
        'email': 'viewer@example.com',
        'role': 'viewer',
        'active': True,
        'assignedListings': ['listing-1']
    }


@pytest.fixture
def mock_auth_token():
    """Mock Firebase auth token"""
    return 'mock-firebase-token-123'


@pytest.fixture
def auth_headers(mock_auth_token):
    """Headers with auth token"""
    return {'Authorization': f'Bearer {mock_auth_token}'}
