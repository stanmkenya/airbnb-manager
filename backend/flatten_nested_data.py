"""
Flatten Nested Firestore Data Structure

The data was migrated from Realtime Database with nested structure:
  expenses/{listing_id}/{expense_id}: { data }

This needs to be flattened to:
  expenses/{expense_id}: { data, listingId }
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.firestore_helpers import get_documents, get_subcollection_documents, add_document, delete_document
from app.firebase_client import firebase_client


def print_header(title):
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def flatten_expenses(collection_id):
    """Flatten nested expense structure"""
    print_header(f"FLATTENING EXPENSES in collection: {collection_id}")

    try:
        # Get all expense documents
        expense_docs = get_subcollection_documents('collections', collection_id, 'expenses')

        if not expense_docs:
            print("No expense documents found")
            return 0

        print(f"Found {len(expense_docs)} expense container documents")

        flattened_count = 0
        total_expenses = 0

        for container in expense_docs:
            container_id = container.get('id')
            listing_id = container.get('listingId', container_id)

            print(f"\nProcessing container: {container_id}")
            print(f"  ListingId: {listing_id}")

            # Find all nested expense objects
            nested_expenses = []
            for key, value in container.items():
                # Skip metadata fields
                if key in ['id', 'listingId']:
                    continue

                # Check if this is a nested expense object
                if isinstance(value, dict) and 'amount' in value:
                    nested_expenses.append((key, value))

            if not nested_expenses:
                print(f"  No nested expenses found")
                continue

            print(f"  Found {len(nested_expenses)} nested expense(s)")

            # Create flat expense documents
            for expense_id, expense_data in nested_expenses:
                total_expenses += 1

                # Add listingId if missing
                if 'listingId' not in expense_data:
                    expense_data['listingId'] = listing_id

                print(f"    Creating flat expense: {expense_id}")
                print(f"      amount: {expense_data.get('amount')}")
                print(f"      category: {expense_data.get('category')}")
                print(f"      listingId: {expense_data.get('listingId')}")

                # Create new flat document
                try:
                    new_id = add_document(
                        f'collections/{collection_id}/expenses',
                        expense_data
                    )
                    flattened_count += 1
                    print(f"      ✓ Created with ID: {new_id}")

                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")

            # Delete the old container document
            print(f"  Deleting old container: {container_id}")
            try:
                delete_document(f'collections/{collection_id}/expenses', container_id)
                print(f"  ✓ Deleted")
            except Exception as e:
                print(f"  ⚠️  Could not delete: {str(e)}")

        print(f"\n✓ Created {flattened_count} flat expense documents")
        print(f"✓ Total expenses found: {total_expenses}")

        return flattened_count

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def flatten_bookings(collection_id):
    """Flatten nested booking structure"""
    print_header(f"FLATTENING BOOKINGS in collection: {collection_id}")

    try:
        # Get all booking documents
        booking_docs = get_subcollection_documents('collections', collection_id, 'bookings')

        if not booking_docs:
            print("No booking documents found")
            return 0

        print(f"Found {len(booking_docs)} booking container documents")

        flattened_count = 0
        total_bookings = 0

        for container in booking_docs:
            container_id = container.get('id')
            listing_id = container.get('listingId', container_id)

            print(f"\nProcessing container: {container_id}")
            print(f"  ListingId: {listing_id}")

            # Find all nested booking objects
            nested_bookings = []
            for key, value in container.items():
                # Skip metadata fields
                if key in ['id', 'listingId']:
                    continue

                # Check if this is a nested booking object
                if isinstance(value, dict) and ('guestName' in value or 'checkIn' in value or 'totalPaid' in value):
                    nested_bookings.append((key, value))

            if not nested_bookings:
                print(f"  No nested bookings found")
                continue

            print(f"  Found {len(nested_bookings)} nested booking(s)")

            # Create flat booking documents
            for booking_id, booking_data in nested_bookings:
                total_bookings += 1

                # Add listingId if missing
                if 'listingId' not in booking_data:
                    booking_data['listingId'] = listing_id

                print(f"    Creating flat booking: {booking_id}")
                print(f"      guestName: {booking_data.get('guestName')}")
                print(f"      totalPaid: {booking_data.get('totalPaid')}")
                print(f"      listingId: {booking_data.get('listingId')}")

                # Create new flat document
                try:
                    new_id = add_document(
                        f'collections/{collection_id}/bookings',
                        booking_data
                    )
                    flattened_count += 1
                    print(f"      ✓ Created with ID: {new_id}")

                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")

            # Delete the old container document
            print(f"  Deleting old container: {container_id}")
            try:
                delete_document(f'collections/{collection_id}/bookings', container_id)
                print(f"  ✓ Deleted")
            except Exception as e:
                print(f"  ⚠️  Could not delete: {str(e)}")

        print(f"\n✓ Created {flattened_count} flat booking documents")
        print(f"✓ Total bookings found: {total_bookings}")

        return flattened_count

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    print_header("FLATTEN NESTED DATA STRUCTURE")
    print("This will convert nested Realtime DB structure to flat Firestore structure.\n")

    # Get collections
    collections = get_documents('collections')

    if not collections:
        print("❌ No collections found!")
        return

    for collection in collections:
        collection_id = collection.get('id')
        collection_name = collection.get('name', 'Unknown')

        print(f"\n{'#'*80}")
        print(f"# Processing Collection: {collection_name} ({collection_id})")
        print(f"{'#'*80}")

        # Flatten expenses
        expenses_flattened = flatten_expenses(collection_id)

        # Flatten bookings
        bookings_flattened = flatten_bookings(collection_id)

        # Summary
        print_header(f"SUMMARY for {collection_name}")
        print(f"Expenses flattened: {expenses_flattened}")
        print(f"Bookings flattened: {bookings_flattened}")

    print_header("FLATTENING COMPLETE!")
    print("Run test_api_endpoints.py again to verify the data structure.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
