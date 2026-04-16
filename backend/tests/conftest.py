"""
Test configuration and fixtures
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

# Set up environment variables before any imports
os.environ['FIREBASE_SERVICE_ACCOUNT_JSON'] = '{"type": "service_account", "project_id": "test"}'
os.environ['FIREBASE_DATABASE_URL'] = 'https://test-db.firebaseio.com'
os.environ['ALLOWED_ORIGINS'] = 'http://localhost:3000'
os.environ['DEBUG'] = 'true'


# Mock Firebase before importing the app
@pytest.fixture(scope='session', autouse=True)
def mock_firebase_init():
    """Mock Firebase initialization at module level"""
    with patch('firebase_admin.initialize_app'):
        with patch('firebase_admin.credentials.Certificate'):
            yield


@pytest.fixture
def mock_firebase():
    """Mock Firebase Admin SDK for individual tests"""
    mock_instance = MagicMock()
    mock_instance.verify_token.return_value = {
        'uid': 'test-user-123',
        'email': 'test@example.com'
    }
    mock_ref = MagicMock()
    mock_ref.get.return_value = None
    mock_instance.get_database_ref.return_value = mock_ref
    return mock_instance


@pytest.fixture
def client():
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
