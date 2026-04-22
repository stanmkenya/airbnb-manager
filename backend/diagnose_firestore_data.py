"""
Comprehensive Firestore Data Diagnostic Script

This script checks:
1. What data exists in Firestore
2. The structure of the data
3. Whether data is in the correct location
4. If the API endpoints can fetch the data
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.firestore_helpers import get_documents, get_subcollection_documents
from app.firebase_client import firebase_client


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def check_collections():
    """Check all collections in Firestore"""
    print_header("COLLECTIONS")

    try:
        collections = get_documents('collections')

        if not collections:
            print("❌ No collections found!")
            return []

        print(f"✓ Found {len(collections)} collection(s):\n")

        for collection in collections:
            cid = collection.get('id')
            name = collection.get('name', 'N/A')
            print(f"  Collection: {name}")
            print(f"  ID: {cid}\n")

        return collections

    except Exception as e:
        print(f"❌ Error fetching collections: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def check_listings(collection_id):
    """Check listings in a collection"""
    print_header(f"LISTINGS in collection: {collection_id}")

    try:
        listings = get_subcollection_documents('collections', collection_id, 'listings')

        if not listings:
            print("❌ No listings found!")
            return []

        print(f"✓ Found {len(listings)} listing(s):\n")

        for listing in listings:
            lid = listing.get('id')
            name = listing.get('name', 'N/A')
            status = listing.get('status', 'N/A')
            print(f"  [{lid}] {name} - Status: {status}")

        print()
        return listings

    except Exception as e:
        print(f"❌ Error fetching listings: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def check_expenses(collection_id):
    """Check expenses in a collection"""
    print_header(f"EXPENSES in collection: {collection_id}")

    try:
        expenses = get_subcollection_documents('collections', collection_id, 'expenses')

        if not expenses:
            print("⚠️  No expenses found in collections/{}/expenses".format(collection_id))
            print("\nChecking if data might be in old structure...")
            return check_old_structure_expenses(collection_id)

        print(f"✓ Found {len(expenses)} expense(s):\n")

        # Group by listingId
        by_listing = {}
        no_listing_id = []

        for expense in expenses:
            eid = expense.get('id')
            listing_id = expense.get('listingId')
            amount = expense.get('amount', 0)
            date = expense.get('date', 'N/A')
            category = expense.get('category', 'N/A')

            if listing_id:
                if listing_id not in by_listing:
                    by_listing[listing_id] = []
                by_listing[listing_id].append(expense)
            else:
                no_listing_id.append(expense)

            print(f"  [{eid}] ${amount} - {category} - {date} - Listing: {listing_id or 'MISSING'}")

        print(f"\n  Summary:")
        print(f"  - Expenses with listingId: {sum(len(v) for v in by_listing.values())}")
        print(f"  - Expenses WITHOUT listingId: {len(no_listing_id)}")

        if no_listing_id:
            print(f"\n  ⚠️  WARNING: {len(no_listing_id)} expenses are missing listingId field!")
            print(f"  These expenses will NOT be returned by the API.")

        return expenses

    except Exception as e:
        print(f"❌ Error fetching expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def check_old_structure_expenses(collection_id):
    """Check if expenses are in old structure: collections/{cid}/expenses/{lid}"""
    print("\nChecking old structure: collections/{}/expenses/{{listing_id}}".format(collection_id))

    # Try to list all possible paths
    # We need to check if there are documents directly under collections/{cid}/expenses
    try:
        # Use Firestore client directly to check structure
        db = firebase_client.db
        expenses_ref = db.collection('collections').document(collection_id).collection('expenses')

        # Get all documents
        docs = expenses_ref.stream()

        found_docs = []
        for doc in docs:
            found_docs.append({'id': doc.id, **doc.to_dict()})

        if found_docs:
            print(f"\n✓ Found {len(found_docs)} document(s) in collections/{collection_id}/expenses:")
            for doc in found_docs:
                print(f"  - Document ID: {doc.get('id')}")
                print(f"    Data: {json.dumps({k: v for k, v in doc.items() if k != 'id'}, indent=4)}")

        # Check for subcollections under expenses (old structure)
        # This would be collections/{cid}/expenses/{doc_id}/...
        print("\nChecking for nested subcollections (OLD STRUCTURE)...")

        return found_docs

    except Exception as e:
        print(f"⚠️  Could not check old structure: {str(e)}")
        return []


def check_bookings(collection_id):
    """Check bookings in a collection"""
    print_header(f"BOOKINGS in collection: {collection_id}")

    try:
        bookings = get_subcollection_documents('collections', collection_id, 'bookings')

        if not bookings:
            print("⚠️  No bookings found in collections/{}/bookings".format(collection_id))
            print("\nChecking if data might be in 'income' subcollection...")
            return check_income_subcollection(collection_id)

        print(f"✓ Found {len(bookings)} booking(s):\n")

        # Group by listingId
        by_listing = {}
        no_listing_id = []

        for booking in bookings:
            bid = booking.get('id')
            listing_id = booking.get('listingId')
            guest_name = booking.get('guestName', 'N/A')
            total_paid = booking.get('totalPaid', 0)
            check_in = booking.get('checkIn', 'N/A')

            if listing_id:
                if listing_id not in by_listing:
                    by_listing[listing_id] = []
                by_listing[listing_id].append(booking)
            else:
                no_listing_id.append(booking)

            print(f"  [{bid}] {guest_name} - ${total_paid} - Check-in: {check_in} - Listing: {listing_id or 'MISSING'}")

        print(f"\n  Summary:")
        print(f"  - Bookings with listingId: {sum(len(v) for v in by_listing.values())}")
        print(f"  - Bookings WITHOUT listingId: {len(no_listing_id)}")

        if no_listing_id:
            print(f"\n  ⚠️  WARNING: {len(no_listing_id)} bookings are missing listingId field!")
            print(f"  These bookings will NOT be returned by the API.")

        return bookings

    except Exception as e:
        print(f"❌ Error fetching bookings: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def check_income_subcollection(collection_id):
    """Check if data is in 'income' instead of 'bookings'"""
    try:
        income_docs = get_subcollection_documents('collections', collection_id, 'income')

        if income_docs:
            print(f"\n✓ Found {len(income_docs)} document(s) in 'income' subcollection")
            print("⚠️  Data should be in 'bookings' subcollection, not 'income'!")
            return income_docs
        else:
            print("⚠️  No data in 'income' subcollection either")
            return []

    except Exception as e:
        print(f"⚠️  Could not check income subcollection: {str(e)}")
        return []


def check_blocked_dates(collection_id):
    """Check blocked dates in a collection"""
    print_header(f"BLOCKED DATES in collection: {collection_id}")

    try:
        blocked_dates = get_subcollection_documents('collections', collection_id, 'blocked-dates')

        if not blocked_dates:
            print("⚠️  No blocked dates found")
            return []

        print(f"✓ Found {len(blocked_dates)} blocked date(s):\n")

        # Group by listingId
        by_listing = {}
        no_listing_id = []

        for blocked in blocked_dates:
            bid = blocked.get('id')
            listing_id = blocked.get('listingId')
            date = blocked.get('date', 'N/A')
            reason = blocked.get('reason', 'N/A')

            if listing_id:
                if listing_id not in by_listing:
                    by_listing[listing_id] = []
                by_listing[listing_id].append(blocked)
            else:
                no_listing_id.append(blocked)

            print(f"  [{bid}] {date} - {reason} - Listing: {listing_id or 'MISSING'}")

        print(f"\n  Summary:")
        print(f"  - Blocked dates with listingId: {sum(len(v) for v in by_listing.values())}")
        print(f"  - Blocked dates WITHOUT listingId: {len(no_listing_id)}")

        if no_listing_id:
            print(f"\n  ⚠️  WARNING: {len(no_listing_id)} blocked dates are missing listingId field!")

        return blocked_dates

    except Exception as e:
        print(f"❌ Error fetching blocked dates: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def check_all_firestore_paths(collection_id):
    """Check all possible Firestore paths to find where data might be"""
    print_header(f"CHECKING ALL PATHS in collection: {collection_id}")

    try:
        db = firebase_client.db
        collection_ref = db.collection('collections').document(collection_id)

        # Get all subcollections
        subcollections = collection_ref.collections()

        print("Subcollections found:")
        for subcol in subcollections:
            print(f"\n  📁 {subcol.id}")

            # Get documents in this subcollection
            docs = subcol.limit(5).stream()
            doc_count = 0

            for doc in docs:
                doc_count += 1
                print(f"    - Document: {doc.id}")
                data = doc.to_dict()

                # Show first few fields
                if data:
                    fields = list(data.keys())[:5]
                    print(f"      Fields: {', '.join(fields)}")

                    # Check for listingId
                    if 'listingId' in data:
                        print(f"      ✓ Has listingId: {data['listingId']}")
                    else:
                        print(f"      ⚠️  Missing listingId field!")

            if doc_count == 0:
                print(f"    (empty)")
            elif doc_count >= 5:
                print(f"    ... (showing first 5)")

    except Exception as e:
        print(f"❌ Error checking paths: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    print_header("FIRESTORE DATA DIAGNOSTIC TOOL")
    print("This tool will check what data exists in Firestore and where it's located.\n")

    # Check collections
    collections = check_collections()

    if not collections:
        print("\n❌ No collections found! Cannot proceed.")
        return

    # Check each collection
    for collection in collections:
        collection_id = collection.get('id')
        collection_name = collection.get('name', 'Unknown')

        print(f"\n{'#'*80}")
        print(f"# Analyzing Collection: {collection_name} ({collection_id})")
        print(f"{'#'*80}")

        # Check listings (this works)
        listings = check_listings(collection_id)

        # Check expenses
        expenses = check_expenses(collection_id)

        # Check bookings
        bookings = check_bookings(collection_id)

        # Check blocked dates
        blocked_dates = check_blocked_dates(collection_id)

        # Check all paths
        check_all_firestore_paths(collection_id)

        # Summary for this collection
        print_header(f"SUMMARY for {collection_name}")
        print(f"Listings: {len(listings)}")
        print(f"Expenses: {len(expenses)}")
        print(f"Bookings: {len(bookings)}")
        print(f"Blocked Dates: {len(blocked_dates)}")

        # Recommendations
        print(f"\n📋 RECOMMENDATIONS:")

        if not expenses:
            print("  ⚠️  No expenses found - Data may need to be migrated or created")
        elif any(not e.get('listingId') for e in expenses):
            print("  ⚠️  Some expenses are missing listingId - Need to add listingId field")

        if not bookings:
            print("  ⚠️  No bookings found - Data may need to be migrated or created")
        elif any(not b.get('listingId') for b in bookings):
            print("  ⚠️  Some bookings are missing listingId - Need to add listingId field")

        if listings and not expenses and not bookings:
            print("  💡 You have listings but no financial data - Add some test data to verify functionality")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
