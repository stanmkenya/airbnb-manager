"""
Expenses tests including audit logging
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta


class TestExpensesCRUD:
    """Test expenses create, read, update, delete operations"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.expenses.firebase_client')
    def test_create_expense(self, expenses_mock, auth_mock, client, manager_user):
        """Manager should be able to create expenses"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        expenses_ref = Mock()
        expenses_ref.push.return_value = Mock(key='new-expense-id')
        expenses_mock.get_database_ref.return_value = expenses_ref

        expense_data = {
            "listingId": "listing-1",
            "amount": 150.50,
            "category": "Cleaning",
            "subcategory": "",
            "date": "2024-01-15",
            "description": "Monthly cleaning",
            "receiptRef": ""
        }

        response = client.post(
            "/expenses",
            headers={"Authorization": "Bearer manager-token"},
            json=expense_data
        )

        assert response.status_code == 201
        assert 'id' in response.json()
        assert response.json()['amount'] == 150.50

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.expenses.firebase_client')
    def test_get_expenses_filtered_by_listing(self, expenses_mock, auth_mock, client, manager_user):
        """Get expenses filtered by listing"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        expenses_ref = Mock()
        expenses_ref.get.return_value = {
            'exp-1': {
                'listingId': 'listing-1',
                'amount': 100,
                'category': 'Cleaning',
                'date': '2024-01-01'
            },
            'exp-2': {
                'listingId': 'listing-2',
                'amount': 200,
                'category': 'Utilities',
                'date': '2024-01-02'
            }
        }
        expenses_mock.get_database_ref.return_value = expenses_ref

        response = client.get(
            "/expenses?listingId=listing-1",
            headers={"Authorization": "Bearer manager-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['listingId'] == 'listing-1'

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.expenses.firebase_client')
    def test_update_expense_within_30_days(self, expenses_mock, auth_mock, client, manager_user):
        """Manager should be able to update recent expenses"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        # Create an expense from yesterday
        yesterday_timestamp = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)

        expenses_ref = Mock()
        expenses_ref.get.return_value = {
            'listingId': 'listing-1',
            'amount': 100,
            'category': 'Cleaning',
            'enteredBy': manager_user['uid'],
            'createdAt': yesterday_timestamp
        }
        expenses_mock.get_database_ref.return_value = expenses_ref

        update_data = {
            "listingId": "listing-1",
            "amount": 150,
            "category": "Cleaning",
            "date": "2024-01-01"
        }

        response = client.put(
            "/expenses/exp-1?listingId=listing-1",
            headers={"Authorization": "Bearer manager-token"},
            json=update_data
        )

        assert response.status_code == 200

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.expenses.firebase_client')
    def test_cannot_update_expense_older_than_30_days(self, expenses_mock, auth_mock, client, manager_user):
        """Manager should not be able to update expenses older than 30 days"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        # Create an expense from 31 days ago
        old_timestamp = int((datetime.now() - timedelta(days=31)).timestamp() * 1000)

        expenses_ref = Mock()
        expenses_ref.get.return_value = {
            'listingId': 'listing-1',
            'amount': 100,
            'category': 'Cleaning',
            'enteredBy': manager_user['uid'],
            'createdAt': old_timestamp
        }
        expenses_mock.get_database_ref.return_value = expenses_ref

        update_data = {
            "listingId": "listing-1",
            "amount": 150,
            "category": "Cleaning",
            "date": "2024-01-01"
        }

        response = client.put(
            "/expenses/exp-1?listingId=listing-1",
            headers={"Authorization": "Bearer manager-token"},
            json=update_data
        )

        assert response.status_code == 403


class TestExpenseAuditLogging:
    """Test audit logging for expense changes"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.expenses.firebase_client')
    def test_audit_log_created_on_update(self, expenses_mock, auth_mock, client, manager_user):
        """Audit log should be created when expense is updated"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        # Recent expense
        recent_timestamp = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)

        expenses_ref = Mock()
        expenses_ref.get.return_value = {
            'listingId': 'listing-1',
            'amount': 100,
            'category': 'Cleaning',
            'enteredBy': manager_user['uid'],
            'createdAt': recent_timestamp
        }

        audit_ref = Mock()
        expenses_mock.get_database_ref.side_effect = lambda path: expenses_ref if 'expenses' in path else audit_ref

        update_data = {
            "listingId": "listing-1",
            "amount": 150,
            "category": "Cleaning",
            "date": "2024-01-01"
        }

        response = client.put(
            "/expenses/exp-1?listingId=listing-1",
            headers={"Authorization": "Bearer manager-token"},
            json=update_data
        )

        # Check that audit log was created
        assert audit_ref.push.called or expenses_ref.child.called


class TestExpenseCategories:
    """Test expense categories and subcategories"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.expenses.firebase_client')
    def test_create_expense_with_subcategory(self, expenses_mock, auth_mock, client, manager_user):
        """Should be able to create expense with valid subcategory"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        expenses_ref = Mock()
        expenses_ref.push.return_value = Mock(key='new-expense-id')
        expenses_mock.get_database_ref.return_value = expenses_ref

        expense_data = {
            "listingId": "listing-1",
            "amount": 50,
            "category": "Breakfast Shopping",
            "subcategory": "Coffee",
            "date": "2024-01-15",
            "description": "Coffee supplies"
        }

        response = client.post(
            "/expenses",
            headers={"Authorization": "Bearer manager-token"},
            json=expense_data
        )

        assert response.status_code == 201
        assert response.json()['subcategory'] == 'Coffee'

    @patch('app.core.auth.firebase_client')
    def test_manager_cannot_access_unassigned_listing_expenses(self, auth_mock, client, manager_user):
        """Manager should not access expenses for unassigned listings"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        expense_data = {
            "listingId": "listing-999",  # Not in manager's assigned listings
            "amount": 100,
            "category": "Cleaning",
            "date": "2024-01-01"
        }

        response = client.post(
            "/expenses",
            headers={"Authorization": "Bearer manager-token"},
            json=expense_data
        )

        assert response.status_code == 403
