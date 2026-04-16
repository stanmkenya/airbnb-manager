"""
Income and bookings tests including auto-calculations
"""
import pytest
from unittest.mock import patch, Mock


class TestBookingsCRUD:
    """Test bookings create, read, update, delete operations"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_create_booking(self, income_mock, auth_mock, client, manager_user):
        """Manager should be able to create bookings"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        booking_data = {
            "listingId": "listing-1",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-05",
            "nightlyRate": 100,
            "platform": "Airbnb",
            "commissionPaid": 45
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['nights'] == 4  # Jan 5 - Jan 1
        assert data['totalPaid'] == 400  # 4 nights × $100
        assert data['netIncome'] == 355  # $400 - $45
        assert data['commissionPct'] == 11.25  # ($45 / $400) × 100

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_get_bookings_filtered_by_listing(self, income_mock, auth_mock, client, manager_user):
        """Get bookings filtered by listing"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.get.return_value = {
            'book-1': {
                'listingId': 'listing-1',
                'guestName': 'John',
                'totalPaid': 400
            },
            'book-2': {
                'listingId': 'listing-2',
                'guestName': 'Jane',
                'totalPaid': 500
            }
        }
        income_mock.get_database_ref.return_value = bookings_ref

        response = client.get(
            "/income?listingId=listing-1",
            headers={"Authorization": "Bearer manager-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['listingId'] == 'listing-1'


class TestBookingCalculations:
    """Test booking auto-calculations"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_nights_calculation(self, income_mock, auth_mock, client, manager_user):
        """Nights should be calculated correctly"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        # 7-night booking
        booking_data = {
            "listingId": "listing-1",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-08",
            "nightlyRate": 150,
            "platform": "Booking.com",
            "commissionPaid": 0
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['nights'] == 7

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_total_paid_calculation(self, income_mock, auth_mock, client, manager_user):
        """Total paid should be calculated from nights × rate"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        booking_data = {
            "listingId": "listing-1",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-04",
            "nightlyRate": 200,
            "platform": "Direct",
            "commissionPaid": 0
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['totalPaid'] == 600  # 3 nights × $200

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_net_income_calculation(self, income_mock, auth_mock, client, manager_user):
        """Net income should be totalPaid - commissionPaid"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        booking_data = {
            "listingId": "listing-1",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-03",
            "nightlyRate": 100,
            "platform": "Airbnb",
            "commissionPaid": 30
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['totalPaid'] == 200  # 2 nights × $100
        assert data['netIncome'] == 170  # $200 - $30
        assert data['commissionPct'] == 15  # ($30 / $200) × 100

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_commission_percentage_calculation(self, income_mock, auth_mock, client, manager_user):
        """Commission percentage should be calculated correctly"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        booking_data = {
            "listingId": "listing-1",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-06",
            "nightlyRate": 80,
            "platform": "Airbnb",
            "commissionPaid": 60  # 15% of $400
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['totalPaid'] == 400  # 5 nights × $80
        assert data['commissionPct'] == 15  # ($60 / $400) × 100

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firefox_client')
    def test_zero_commission_booking(self, income_mock, auth_mock, client, manager_user):
        """Direct bookings should have zero commission"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        booking_data = {
            "listingId": "listing-1",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-03",
            "nightlyRate": 100,
            "platform": "Direct",
            "commissionPaid": 0
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['commissionPaid'] == 0
        assert data['commissionPct'] == 0
        assert data['netIncome'] == data['totalPaid']


class TestGuestDirectory:
    """Test guest aggregation functionality"""

    @patch('app.core.auth.firebase_client')
    @patch('app.routers.income.firebase_client')
    def test_guest_data_stored_correctly(self, income_mock, auth_mock, client, manager_user):
        """Guest name and email should be stored"""
        auth_mock.verify_token.return_value = {'uid': manager_user['uid'], 'email': manager_user['email']}
        auth_ref = Mock()
        auth_ref.get.return_value = manager_user
        auth_mock.get_database_ref.return_value = auth_ref

        bookings_ref = Mock()
        bookings_ref.push.return_value = Mock(key='new-booking-id')
        income_mock.get_database_ref.return_value = bookings_ref

        booking_data = {
            "listingId": "listing-1",
            "guestName": "Jane Smith",
            "guestEmail": "jane@example.com",
            "guestPhone": "+1234567890",
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-03",
            "nightlyRate": 100,
            "platform": "Airbnb",
            "commissionPaid": 15
        }

        response = client.post(
            "/income",
            headers={"Authorization": "Bearer manager-token"},
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['guestName'] == 'Jane Smith'
        assert data['guestEmail'] == 'jane@example.com'
        assert data['guestPhone'] == '+1234567890'
