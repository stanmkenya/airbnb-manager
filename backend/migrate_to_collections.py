"""
Migration script to move existing data to collection-based structure.

This script:
1. Creates a default "Lux Beyond" collection
2. Migrates all existing listings, income, expenses, and blocked dates to this collection
3. Updates all users with collectionId and role mapping (admin -> collection_admin)

Run this ONCE to migrate your existing data.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.firebase_client import firebase_client

# Load environment variables
load_dotenv()

DEFAULT_COLLECTION_ID = "-default-lux-beyond"
DEFAULT_COLLECTION_NAME = "Lux Beyond"


def create_default_collection():
    """Create the default Lux Beyond collection"""
    print("📦 Creating default collection...")

    collections_ref = firebase_client.get_database_ref('/collections')
    existing_collections = collections_ref.get() or {}

    if DEFAULT_COLLECTION_ID in existing_collections:
        print(f"   ✓ Default collection already exists: {DEFAULT_COLLECTION_NAME}")
        return DEFAULT_COLLECTION_ID

    collection_data = {
        'name': DEFAULT_COLLECTION_NAME,
        'description': 'Default collection for existing properties',
        'isActive': True,
        'createdAt': datetime.utcnow().isoformat(),
        'createdBy': 'system_migration'
    }

    collection_ref = firebase_client.get_database_ref(f'/collections/{DEFAULT_COLLECTION_ID}')
    collection_ref.set(collection_data)

    print(f"   ✓ Created default collection: {DEFAULT_COLLECTION_NAME}")
    return DEFAULT_COLLECTION_ID


def migrate_listings(collection_id):
    """Migrate listings to collection-based structure"""
    print("\n🏠 Migrating listings...")

    # Get existing listings
    old_listings_ref = firebase_client.get_database_ref('/listings')
    listings = old_listings_ref.get() or {}

    if not listings:
        print("   ℹ No listings to migrate")
        return

    # Create new collection-based listings
    new_listings_ref = firebase_client.get_database_ref(f'/collections/{collection_id}/listings')

    migrated_count = 0
    for listing_id, listing_data in listings.items():
        # Check if already migrated
        existing = new_listings_ref.child(listing_id).get()
        if existing:
            print(f"   - Listing {listing_id} already migrated, skipping")
            continue

        # Migrate listing
        new_listings_ref.child(listing_id).set(listing_data)
        migrated_count += 1
        print(f"   ✓ Migrated listing: {listing_data.get('name', listing_id)}")

    print(f"   ✓ Migrated {migrated_count} listings")


def migrate_income(collection_id):
    """Migrate income/bookings to collection-based structure"""
    print("\n💰 Migrating income/bookings...")

    old_income_ref = firebase_client.get_database_ref('/income')
    income_data = old_income_ref.get() or {}

    if not income_data:
        print("   ℹ No income records to migrate")
        return

    new_income_ref = firebase_client.get_database_ref(f'/collections/{collection_id}/income')

    migrated_count = 0
    for listing_id, bookings in income_data.items():
        if not isinstance(bookings, dict):
            continue

        for booking_id, booking_data in bookings.items():
            # Check if already migrated
            existing = new_income_ref.child(listing_id).child(booking_id).get()
            if existing:
                continue

            # Migrate booking
            new_income_ref.child(listing_id).child(booking_id).set(booking_data)
            migrated_count += 1

    print(f"   ✓ Migrated {migrated_count} income records")


def migrate_expenses(collection_id):
    """Migrate expenses to collection-based structure"""
    print("\n💸 Migrating expenses...")

    old_expenses_ref = firebase_client.get_database_ref('/expenses')
    expenses_data = old_expenses_ref.get() or {}

    if not expenses_data:
        print("   ℹ No expenses to migrate")
        return

    new_expenses_ref = firebase_client.get_database_ref(f'/collections/{collection_id}/expenses')

    migrated_count = 0
    for listing_id, expenses in expenses_data.items():
        if not isinstance(expenses, dict):
            continue

        for expense_id, expense_data in expenses.items():
            # Check if already migrated
            existing = new_expenses_ref.child(listing_id).child(expense_id).get()
            if existing:
                continue

            # Migrate expense
            new_expenses_ref.child(listing_id).child(expense_id).set(expense_data)
            migrated_count += 1

    print(f"   ✓ Migrated {migrated_count} expense records")


def migrate_blocked_dates(collection_id):
    """Migrate blocked dates to collection-based structure"""
    print("\n🚫 Migrating blocked dates...")

    old_blocked_ref = firebase_client.get_database_ref('/blocked-dates')
    blocked_data = old_blocked_ref.get() or {}

    if not blocked_data:
        print("   ℹ No blocked dates to migrate")
        return

    new_blocked_ref = firebase_client.get_database_ref(f'/collections/{collection_id}/blocked-dates')

    migrated_count = 0
    for listing_id, dates in blocked_data.items():
        if not isinstance(dates, dict):
            continue

        for date_id, date_data in dates.items():
            # Check if already migrated
            existing = new_blocked_ref.child(listing_id).child(date_id).get()
            if existing:
                continue

            # Migrate blocked date
            new_blocked_ref.child(listing_id).child(date_id).set(date_data)
            migrated_count += 1

    print(f"   ✓ Migrated {migrated_count} blocked date records")


def update_users(collection_id):
    """Update users with collectionId and role mapping"""
    print("\n👥 Updating users...")

    users_ref = firebase_client.get_database_ref('/users')
    users = users_ref.get() or {}

    if not users:
        print("   ℹ No users to update")
        return

    updated_count = 0
    for user_id, user_data in users.items():
        # Skip if already has collectionId (already migrated)
        if 'collectionId' in user_data:
            print(f"   - User {user_data.get('email')} already migrated, skipping")
            continue

        current_role = user_data.get('role', 'viewer')

        # Map old roles to new roles
        role_mapping = {
            'admin': 'collection_admin',
            'manager': 'manager',
            'viewer': 'viewer'
        }

        new_role = role_mapping.get(current_role, 'viewer')

        # Update user with collectionId and new role
        update_data = {
            'collectionId': collection_id,
            'role': new_role,
            'migratedAt': datetime.utcnow().isoformat()
        }

        users_ref.child(user_id).update(update_data)
        updated_count += 1
        print(f"   ✓ Updated user: {user_data.get('email')} (role: {current_role} -> {new_role})")

    print(f"   ✓ Updated {updated_count} users")


def main():
    """Run the migration"""
    print("=" * 60)
    print("🚀 COLLECTION MIGRATION STARTING")
    print("=" * 60)
    print()

    try:
        # Step 1: Create default collection
        collection_id = create_default_collection()

        # Step 2: Migrate all data
        migrate_listings(collection_id)
        migrate_income(collection_id)
        migrate_expenses(collection_id)
        migrate_blocked_dates(collection_id)

        # Step 3: Update users
        update_users(collection_id)

        print()
        print("=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print(f"Default collection ID: {collection_id}")
        print(f"Collection name: {DEFAULT_COLLECTION_NAME}")
        print()
        print("Next steps:")
        print("1. Deploy the updated backend code")
        print("2. Test the application")
        print("3. You can now create additional collections from the super admin panel")
        print()

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ MIGRATION FAILED!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print()
    print("⚠️  WARNING: This will migrate your data to a collection-based structure")
    print()
    response = input("Do you want to continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        main()
    else:
        print("Migration cancelled.")
        sys.exit(0)
