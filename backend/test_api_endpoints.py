"""
Comprehensive API Endpoint Test

This script tests all API endpoints to diagnose why data isn't loading.
It simulates exactly what the frontend does.
"""

import sys
import os
import json
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.firestore_helpers import get_documents, get_subcollection_documents
from app.core.auth import get_current_user
from app.core.collection_helpers import get_user_collection_id
from app.routers import expenses, income, listings, reports


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def print_json(data, max_items=5):
    """Pretty print JSON data"""
    if isinstance(data, list):
        print(f"Array with {len(data)} items:")
        for i, item in enumerate(data[:max_items]):
            print(f"\n  Item {i+1}:")
            print(json.dumps(item, indent=4))
        if len(data) > max_items:
            print(f"\n  ... and {len(data) - max_items} more items")
    else:
        print(json.dumps(data, indent=2))


def test_direct_firestore_access():
    """Test direct Firestore access"""
    print_header("TEST 1: DIRECT FIRESTORE ACCESS")

    try:
        # Get collection
        collections = get_documents('collections')
        print(f"✓ Found {len(collections)} collection(s)")

        for collection in collections:
            cid = collection.get('id')
            name = collection.get('name')
            print(f"\n  Collection: {name} ({cid})")

            # Get listings
            listings_data = get_subcollection_documents('collections', cid, 'listings')
            print(f"    Listings: {len(listings_data)}")

            # Get expenses
            expenses_data = get_subcollection_documents('collections', cid, 'expenses')
            print(f"    Expenses: {len(expenses_data)}")

            # Check listingId
            with_listing_id = sum(1 for e in expenses_data if e.get('listingId'))
            print(f"      - With listingId: {with_listing_id}/{len(expenses_data)}")

            # Get bookings
            bookings_data = get_subcollection_documents('collections', cid, 'bookings')
            print(f"    Bookings: {len(bookings_data)}")

            # Check listingId
            with_listing_id = sum(1 for b in bookings_data if b.get('listingId'))
            print(f"      - With listingId: {with_listing_id}/{len(bookings_data)}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_expenses_endpoint():
    """Test expenses endpoint logic"""
    print_header("TEST 2: EXPENSES ENDPOINT LOGIC")

    try:
        # Simulate collection admin user
        mock_user = {
            'uid': 'test-admin-uid',
            'email': 'admin@luxbeyond.com',
            'role': 'collection_admin',
            'collectionId': '-default-lux-beyond',
            'isActive': True
        }

        print(f"Simulating user: {mock_user['email']}")
        print(f"Role: {mock_user['role']}")
        print(f"Collection: {mock_user['collectionId']}")

        # Get collection_id
        collection_id = get_user_collection_id(mock_user)
        print(f"\n✓ Collection ID resolved: {collection_id}")

        # Get listings for this collection
        all_listings = get_subcollection_documents('collections', collection_id, 'listings')
        listing_ids = [listing['id'] for listing in all_listings]
        print(f"✓ Found {len(listing_ids)} listing IDs: {listing_ids}")

        # Fetch all expenses from the collection
        all_collection_expenses = get_subcollection_documents('collections', collection_id, 'expenses')
        print(f"✓ Fetched {len(all_collection_expenses)} total expenses from Firestore")

        # Filter expenses by listing IDs
        filtered_expenses = []
        for expense in all_collection_expenses:
            expense_listing_id = expense.get('listingId')
            print(f"\n  Expense ID: {expense.get('id')}")
            print(f"    listingId: {expense_listing_id}")
            print(f"    amount: {expense.get('amount')}")
            print(f"    category: {expense.get('category')}")
            print(f"    date: {expense.get('date')}")

            # Check if expense belongs to one of the allowed listings
            if expense_listing_id not in listing_ids:
                print(f"    ❌ FILTERED OUT - listingId not in allowed listings!")
                continue

            print(f"    ✓ INCLUDED")
            filtered_expenses.append(expense)

        print(f"\n✓ After filtering: {len(filtered_expenses)} expenses")

        if filtered_expenses:
            print("\nSample expense data:")
            print_json(filtered_expenses[0])
        else:
            print("\n⚠️  NO EXPENSES RETURNED after filtering!")
            print("   This is why the API returns empty array!")

        return len(filtered_expenses) > 0

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_bookings_endpoint():
    """Test bookings/income endpoint logic"""
    print_header("TEST 3: BOOKINGS ENDPOINT LOGIC")

    try:
        # Simulate collection admin user
        mock_user = {
            'uid': 'test-admin-uid',
            'email': 'admin@luxbeyond.com',
            'role': 'collection_admin',
            'collectionId': '-default-lux-beyond',
            'isActive': True
        }

        print(f"Simulating user: {mock_user['email']}")
        print(f"Collection: {mock_user['collectionId']}")

        # Get collection_id
        collection_id = get_user_collection_id(mock_user)
        print(f"\n✓ Collection ID resolved: {collection_id}")

        # Get listings for this collection
        all_listings = get_subcollection_documents('collections', collection_id, 'listings')
        listing_ids = [listing['id'] for listing in all_listings]
        print(f"✓ Found {len(listing_ids)} listing IDs")

        # Fetch all bookings from the collection
        all_collection_bookings = get_subcollection_documents('collections', collection_id, 'bookings')
        print(f"✓ Fetched {len(all_collection_bookings)} total bookings from Firestore")

        # Filter bookings by listing IDs
        filtered_bookings = []
        for booking in all_collection_bookings:
            booking_listing_id = booking.get('listingId')
            print(f"\n  Booking ID: {booking.get('id')}")
            print(f"    listingId: {booking_listing_id}")
            print(f"    guestName: {booking.get('guestName')}")
            print(f"    totalPaid: {booking.get('totalPaid')}")
            print(f"    checkIn: {booking.get('checkIn')}")

            # Check if booking belongs to one of the allowed listings
            if booking_listing_id not in listing_ids:
                print(f"    ❌ FILTERED OUT - listingId not in allowed listings!")
                continue

            print(f"    ✓ INCLUDED")
            filtered_bookings.append(booking)

        print(f"\n✓ After filtering: {len(filtered_bookings)} bookings")

        if filtered_bookings:
            print("\nSample booking data:")
            print_json(filtered_bookings[0])
        else:
            print("\n⚠️  NO BOOKINGS RETURNED after filtering!")
            print("   This is why the API returns empty array!")

        return len(filtered_bookings) > 0

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_listings_endpoint():
    """Test listings endpoint logic"""
    print_header("TEST 4: LISTINGS ENDPOINT LOGIC")

    try:
        # Simulate collection admin user
        mock_user = {
            'uid': 'test-admin-uid',
            'email': 'admin@luxbeyond.com',
            'role': 'collection_admin',
            'collectionId': '-default-lux-beyond',
            'isActive': True
        }

        print(f"Simulating user: {mock_user['email']}")

        # Get collection IDs to query
        from app.core.collection_helpers import get_collection_ids
        collection_ids = get_collection_ids(mock_user, None)
        print(f"\n✓ Collection IDs to query: {collection_ids}")

        all_listings = []

        # Fetch listings from all relevant collections
        for cid in collection_ids:
            collection_listings = get_subcollection_documents('collections', cid, 'listings')
            print(f"✓ Collection {cid}: {len(collection_listings)} listings")

            for listing in collection_listings:
                listing['collectionId'] = cid
                all_listings.append(listing)

        print(f"\n✓ Total listings: {len(all_listings)}")

        if all_listings:
            print("\nSample listing:")
            print_json(all_listings[0])

        return len(all_listings) > 0

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_aggregation():
    """Test dashboard data aggregation"""
    print_header("TEST 5: DASHBOARD DATA AGGREGATION")

    try:
        # Simulate collection admin user
        mock_user = {
            'uid': 'test-admin-uid',
            'email': 'admin@luxbeyond.com',
            'role': 'collection_admin',
            'collectionId': '-default-lux-beyond',
            'isActive': True
        }

        collection_id = get_user_collection_id(mock_user)

        # Get all data
        all_listings = get_subcollection_documents('collections', collection_id, 'listings')
        listing_ids = [listing['id'] for listing in all_listings]

        all_expenses = get_subcollection_documents('collections', collection_id, 'expenses')
        all_bookings = get_subcollection_documents('collections', collection_id, 'bookings')

        # Filter by listing IDs
        filtered_expenses = [e for e in all_expenses if e.get('listingId') in listing_ids]
        filtered_bookings = [b for b in all_bookings if b.get('listingId') in listing_ids]

        # Calculate totals (like Dashboard.jsx does)
        total_expenses = sum(e.get('amount', 0) for e in filtered_expenses)
        commission_expenses = sum(b.get('commissionPaid', 0) for b in filtered_bookings)
        total_expenses_with_commission = total_expenses + commission_expenses

        total_revenue = sum(b.get('totalPaid', 0) for b in filtered_bookings)
        net_income = total_revenue - total_expenses_with_commission

        print(f"Listings: {len(all_listings)}")
        print(f"Expenses (raw): {len(all_expenses)}")
        print(f"Expenses (filtered): {len(filtered_expenses)}")
        print(f"Bookings (raw): {len(all_bookings)}")
        print(f"Bookings (filtered): {len(filtered_bookings)}")
        print()
        print(f"📊 DASHBOARD METRICS:")
        print(f"  Total Revenue: ${total_revenue}")
        print(f"  Total Expenses: ${total_expenses}")
        print(f"  Commission Expenses: ${commission_expenses}")
        print(f"  Combined Expenses: ${total_expenses_with_commission}")
        print(f"  Net Income: ${net_income}")

        if total_revenue == 0 and total_expenses == 0:
            print("\n⚠️  All amounts are $0 - Your data has zero values!")
            print("   The data structure is correct, but you need to add real amounts.")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_data_values():
    """Check if data has actual values or just placeholders"""
    print_header("TEST 6: DATA VALUES CHECK")

    try:
        collection_id = '-default-lux-beyond'

        # Check expenses
        expenses = get_subcollection_documents('collections', collection_id, 'expenses')
        print(f"Expenses:")
        for exp in expenses:
            print(f"  ID: {exp.get('id')}")
            print(f"    All fields: {list(exp.keys())}")
            print(f"    amount: {exp.get('amount')}")
            print(f"    category: {exp.get('category')}")
            print(f"    date: {exp.get('date')}")
            print(f"    listingId: {exp.get('listingId')}")
            print()

        # Check bookings
        bookings = get_subcollection_documents('collections', collection_id, 'bookings')
        print(f"Bookings:")
        for booking in bookings:
            print(f"  ID: {booking.get('id')}")
            print(f"    All fields: {list(booking.keys())}")
            print(f"    guestName: {booking.get('guestName')}")
            print(f"    totalPaid: {booking.get('totalPaid')}")
            print(f"    checkIn: {booking.get('checkIn')}")
            print(f"    listingId: {booking.get('listingId')}")
            print()

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header("COMPREHENSIVE API ENDPOINT TEST")
    print("This will test each step of the data flow to identify where it's breaking.\n")

    results = {}

    # Test 1: Direct Firestore access
    results['firestore'] = test_direct_firestore_access()

    # Test 2: Expenses endpoint
    results['expenses'] = test_expenses_endpoint()

    # Test 3: Bookings endpoint
    results['bookings'] = test_bookings_endpoint()

    # Test 4: Listings endpoint
    results['listings'] = test_listings_endpoint()

    # Test 5: Dashboard aggregation
    results['dashboard'] = test_dashboard_aggregation()

    # Test 6: Data values
    results['data_values'] = check_data_values()

    # Summary
    print_header("TEST SUMMARY")
    print(f"Direct Firestore Access: {'✅ PASS' if results['firestore'] else '❌ FAIL'}")
    print(f"Expenses Endpoint Logic: {'✅ PASS' if results['expenses'] else '❌ FAIL'}")
    print(f"Bookings Endpoint Logic: {'✅ PASS' if results['bookings'] else '❌ FAIL'}")
    print(f"Listings Endpoint Logic: {'✅ PASS' if results['listings'] else '❌ FAIL'}")
    print(f"Dashboard Aggregation:   {'✅ PASS' if results['dashboard'] else '❌ FAIL'}")
    print(f"Data Values Check:       {'✅ PASS' if results['data_values'] else '❌ FAIL'}")

    print("\n" + "="*80)
    if all(results.values()):
        print("✅ ALL TESTS PASSED - Backend can fetch data correctly!")
        print("\nIf frontend still shows no data, the issue is likely:")
        print("  1. Frontend not calling the API")
        print("  2. Authentication headers not being sent")
        print("  3. CORS blocking the requests")
        print("  4. Check browser console for errors")
    else:
        print("❌ SOME TESTS FAILED - Review output above for details")
        failed = [k for k, v in results.items() if not v]
        print(f"\nFailed tests: {', '.join(failed)}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
