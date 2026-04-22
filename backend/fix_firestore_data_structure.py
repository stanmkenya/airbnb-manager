"""
Fix Firestore Data Structure

This script fixes:
1. Adds missing listingId field to expenses documents
2. Moves data from 'income' to 'bookings' subcollection
3. Adds missing listingId field to bookings documents
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.firestore_helpers import get_documents, get_subcollection_documents, update_document, add_document
from app.firebase_client import firebase_client


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def fix_expenses_listingId(collection_id):
    """Add listingId field to expenses that are missing it"""
    print_header(f"FIXING EXPENSES in collection: {collection_id}")

    try:
        # Get all expenses
        expenses = get_subcollection_documents('collections', collection_id, 'expenses')

        if not expenses:
            print("No expenses found - skipping")
            return 0

        print(f"Found {len(expenses)} expense(s)")

        fixed_count = 0
        already_has_listing_id = 0

        for expense in expenses:
            expense_id = expense.get('id')

            # Check if it already has listingId
            if expense.get('listingId'):
                already_has_listing_id += 1
                print(f"  ✓ [{expense_id}] Already has listingId: {expense.get('listingId')}")
                continue

            # The expense document ID IS the listingId (from old structure)
            # Add it as a field
            print(f"  Fixing [{expense_id}] - Adding listingId: {expense_id}")

            try:
                update_document(
                    f'collections/{collection_id}/expenses',
                    expense_id,
                    {'listingId': expense_id}
                )
                fixed_count += 1
                print(f"  ✓ Fixed!")

            except Exception as e:
                print(f"  ❌ Error fixing expense {expense_id}: {str(e)}")

        print(f"\n✓ Fixed {fixed_count} expense(s)")
        print(f"✓ {already_has_listing_id} already had listingId")

        return fixed_count

    except Exception as e:
        print(f"❌ Error fixing expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def migrate_income_to_bookings(collection_id):
    """Move data from income subcollection to bookings subcollection"""
    print_header(f"MIGRATING INCOME → BOOKINGS in collection: {collection_id}")

    try:
        # Get all documents from income subcollection
        income_docs = get_subcollection_documents('collections', collection_id, 'income')

        if not income_docs:
            print("No income documents found - skipping")
            return 0

        print(f"Found {len(income_docs)} income document(s)")

        # Check if bookings already exist
        existing_bookings = get_subcollection_documents('collections', collection_id, 'bookings')

        if existing_bookings:
            print(f"\n⚠️  WARNING: {len(existing_bookings)} booking(s) already exist!")
            response = input("Continue with migration? This may create duplicates. (yes/no): ")
            if response.lower() != 'yes':
                print("Skipping migration")
                return 0

        migrated_count = 0

        for income_doc in income_docs:
            income_id = income_doc.get('id')

            # The income document ID is the listingId (from old structure)
            listing_id = income_id

            print(f"\n  Migrating income document [{income_id}]...")

            # Remove the 'id' field before copying
            booking_data = {k: v for k, v in income_doc.items() if k != 'id'}

            # Add listingId if missing
            if 'listingId' not in booking_data:
                booking_data['listingId'] = listing_id
                print(f"    Added listingId: {listing_id}")

            try:
                # Add to bookings subcollection
                new_booking_id = add_document(
                    f'collections/{collection_id}/bookings',
                    booking_data
                )

                migrated_count += 1
                print(f"  ✓ Migrated to bookings with ID: {new_booking_id}")

            except Exception as e:
                print(f"  ❌ Error migrating income {income_id}: {str(e)}")

        print(f"\n✓ Migrated {migrated_count} document(s) from income to bookings")

        if migrated_count > 0:
            print(f"\n⚠️  NOTE: Original income documents still exist.")
            print(f"   Review the data and delete income subcollection manually if needed.")

        return migrated_count

    except Exception as e:
        print(f"❌ Error migrating income to bookings: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def fix_bookings_listingId(collection_id):
    """Add listingId field to bookings that are missing it"""
    print_header(f"FIXING BOOKINGS in collection: {collection_id}")

    try:
        # Get all bookings
        bookings = get_subcollection_documents('collections', collection_id, 'bookings')

        if not bookings:
            print("No bookings found - skipping")
            return 0

        print(f"Found {len(bookings)} booking(s)")

        fixed_count = 0
        already_has_listing_id = 0

        for booking in bookings:
            booking_id = booking.get('id')

            # Check if it already has listingId
            if booking.get('listingId'):
                already_has_listing_id += 1
                print(f"  ✓ [{booking_id}] Already has listingId: {booking.get('listingId')}")
                continue

            # Need to determine listingId - might be in the data or need manual assignment
            print(f"  ⚠️  [{booking_id}] Missing listingId")

            # Try to infer from document structure or ask user
            print(f"     Guest: {booking.get('guestName', 'N/A')}, Check-in: {booking.get('checkIn', 'N/A')}")
            print(f"     Cannot auto-fix - listingId unknown")
            print(f"     You may need to add this manually or provide mapping")

        print(f"\n✓ {already_has_listing_id} booking(s) already have listingId")

        if fixed_count == 0 and already_has_listing_id == 0:
            print(f"⚠️  All {len(bookings)} bookings need manual listingId assignment")

        return fixed_count

    except Exception as e:
        print(f"❌ Error fixing bookings: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    print_header("FIRESTORE DATA STRUCTURE FIX")
    print("This tool will fix data structure issues found in the diagnostic.\n")

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

        # Fix expenses
        expenses_fixed = fix_expenses_listingId(collection_id)

        # Migrate income to bookings
        bookings_migrated = migrate_income_to_bookings(collection_id)

        # Fix bookings (if any exist after migration)
        bookings_fixed = fix_bookings_listingId(collection_id)

        # Summary
        print_header(f"SUMMARY for {collection_name}")
        print(f"Expenses fixed: {expenses_fixed}")
        print(f"Income documents migrated to bookings: {bookings_migrated}")
        print(f"Bookings fixed: {bookings_fixed}")

    print_header("MIGRATION COMPLETE!")
    print("Run diagnose_firestore_data.py again to verify the fixes.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
