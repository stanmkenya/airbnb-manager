#!/usr/bin/env python3
"""
Add listingId field to all expense and income records
"""

from app.firebase_client import firebase_client

def fix_listing_ids():
    """Add listingId to each expense and income record"""

    # Get all listings
    listings_ref = firebase_client.get_database_ref('/listings')
    listings = listings_ref.get() or {}

    print(f"Processing {len(listings)} listings...")

    total_fixed = 0

    for listing_id, listing_data in listings.items():
        listing_name = listing_data.get('name', 'Unknown')
        print(f"\n=== {listing_name} ({listing_id}) ===")

        # Fix expenses
        expenses_ref = firebase_client.get_database_ref(f'/expenses/{listing_id}')
        expenses = expenses_ref.get() or {}

        for expense_id, expense_data in expenses.items():
            if 'listingId' not in expense_data:
                expense_data['listingId'] = listing_id
                # Update the expense
                expense_ref = firebase_client.get_database_ref(f'/expenses/{listing_id}/{expense_id}')
                expense_ref.update({'listingId': listing_id})
                print(f"  ✓ Fixed expense {expense_id}")
                total_fixed += 1

        # Fix income/bookings
        income_ref = firebase_client.get_database_ref(f'/income/{listing_id}')
        income = income_ref.get() or {}

        for income_id, income_data in income.items():
            if 'listingId' not in income_data:
                income_data['listingId'] = listing_id
                # Update the income
                income_ref = firebase_client.get_database_ref(f'/income/{listing_id}/{income_id}')
                income_ref.update({'listingId': listing_id})
                print(f"  ✓ Fixed income {income_id}")
                total_fixed += 1

    print(f"\n✅ Fixed {total_fixed} records")


if __name__ == "__main__":
    print("=" * 60)
    print("FIX LISTING IDs IN EXPENSE/INCOME RECORDS")
    print("=" * 60)
    fix_listing_ids()
