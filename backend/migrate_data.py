#!/usr/bin/env python3
"""
Script to migrate expenses and bookings data to the correct database structure.

Current (WRONG) structure:
  /expenses/Marina/{expense-id}
  /bookings/Marina/{booking-id}

Target (CORRECT) structure:
  /expenses/{listing-id}/{expense-id}
  /income/{listing-id}/{booking-id}
"""

from app.firebase_client import firebase_client

def migrate_data():
    """Migrate expenses and bookings to correct structure"""

    # Get listings to map names to IDs
    listings_ref = firebase_client.get_database_ref('/listings')
    listings = listings_ref.get() or {}

    name_to_id = {}
    for listing_id, listing_data in listings.items():
        name = listing_data.get('name')
        if name:
            name_to_id[name] = listing_id

    print(f"Found {len(name_to_id)} listings:")
    for name, lid in name_to_id.items():
        print(f"  {name} -> {lid}")

    # Migrate expenses
    print("\n=== Migrating Expenses ===")
    old_expenses_ref = firebase_client.get_database_ref('/expenses')
    old_expenses = old_expenses_ref.get() or {}

    total_migrated = 0
    for key, data in old_expenses.items():
        if key in name_to_id:
            # This is a listing name
            listing_id = name_to_id[key]
            print(f"\nMigrating expenses from '{key}' to listing ID '{listing_id}'")

            for expense_id, expense_data in (data or {}).items():
                # Copy to new location
                new_ref = firebase_client.get_database_ref(f'/expenses/{listing_id}/{expense_id}')
                new_ref.set(expense_data)
                print(f"  ✓ Migrated expense {expense_id}")
                total_migrated += 1

            # Delete old location
            old_ref = firebase_client.get_database_ref(f'/expenses/{key}')
            old_ref.delete()
            print(f"  ✓ Deleted old expenses for '{key}'")

    print(f"\n✅ Migrated {total_migrated} expenses")

    # Migrate bookings to income
    print("\n=== Migrating Bookings to Income ===")
    old_bookings_ref = firebase_client.get_database_ref('/bookings')
    old_bookings = old_bookings_ref.get() or {}

    total_migrated = 0
    for key, data in old_bookings.items():
        if key in name_to_id:
            # This is a listing name
            listing_id = name_to_id[key]
            print(f"\nMigrating bookings from '{key}' to income for listing ID '{listing_id}'")

            for booking_id, booking_data in (data or {}).items():
                # Copy to new location as income
                new_ref = firebase_client.get_database_ref(f'/income/{listing_id}/{booking_id}')
                new_ref.set(booking_data)
                print(f"  ✓ Migrated booking {booking_id}")
                total_migrated += 1

            # Delete old location
            old_ref = firebase_client.get_database_ref(f'/bookings/{key}')
            old_ref.delete()
            print(f"  ✓ Deleted old bookings for '{key}'")

    print(f"\n✅ Migrated {total_migrated} bookings to income")
    print("\n🎉 Migration complete!")


if __name__ == "__main__":
    print("=" * 60)
    print("DATA MIGRATION SCRIPT")
    print("=" * 60)
    print("\nThis will migrate:")
    print("  • /expenses/{name}/* → /expenses/{id}/*")
    print("  • /bookings/{name}/* → /income/{id}/*")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    input()

    migrate_data()
