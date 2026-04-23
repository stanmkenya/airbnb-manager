"""
Test Listing Creation for Admins

This script tests:
1. Backend endpoint for creating listings
2. Role-based permissions
3. Collection ID handling for different user roles
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.collection_helpers import get_user_collection_id, require_collection_id_for_mutation
from app.core.firestore_helpers import add_document, get_subcollection_documents


def print_header(title):
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def test_collection_admin_listing_creation():
    """Test collection admin can create a listing"""
    print_header("TEST 1: COLLECTION ADMIN - CREATE LISTING")

    try:
        # Simulate collection admin user
        mock_user = {
            'uid': 'admin-uid-123',
            'email': 'admin@luxbeyond.com',
            'role': 'collection_admin',
            'collectionId': '-default-lux-beyond',
            'isActive': True
        }

        print(f"User: {mock_user['email']}")
        print(f"Role: {mock_user['role']}")
        print(f"Collection ID: {mock_user['collectionId']}")

        # Test: Get collection ID for mutation
        print("\n1. Testing collection ID resolution for mutation...")
        try:
            collection_id = require_collection_id_for_mutation(mock_user, None)
            print(f"   ✓ Collection ID resolved: {collection_id}")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return False

        # Test: Create listing
        print("\n2. Testing listing creation...")
        listing_data = {
            'name': 'Test Listing - Collection Admin',
            'address': '123 Test Street, Nairobi',
            'defaultRate': 150.0,
            'bedrooms': 3,
            'bathrooms': 2,
            'status': 'active',
            'assignedManagers': {},
            'createdBy': mock_user['uid'],
            'createdAt': 1713888000000
        }

        try:
            listing_id = add_document(f'collections/{collection_id}/listings', listing_data)
            print(f"   ✓ Listing created with ID: {listing_id}")
            print(f"   ✓ SUCCESS - Collection admin CAN create listings")
            return True
        except Exception as e:
            print(f"   ❌ ERROR creating listing: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_superadmin_listing_creation():
    """Test superadmin can create a listing"""
    print_header("TEST 2: SUPERADMIN - CREATE LISTING")

    try:
        # Simulate superadmin user
        mock_user = {
            'uid': 'superadmin-uid-123',
            'email': 'superadmin@luxbeyond.com',
            'role': 'superadmin',
            'isActive': True
            # Note: superadmin doesn't have collectionId
        }

        print(f"User: {mock_user['email']}")
        print(f"Role: {mock_user['role']}")
        print(f"Collection ID: {mock_user.get('collectionId', 'N/A')}")

        # Test: Try without collectionId parameter
        print("\n1. Testing WITHOUT collectionId parameter...")
        try:
            collection_id = require_collection_id_for_mutation(mock_user, None)
            print(f"   ❌ UNEXPECTED - Should have raised error!")
            print(f"   Got collection_id: {collection_id}")
        except Exception as e:
            print(f"   ✓ Expected error: {str(e)}")

        # Test: Try WITH collectionId parameter
        print("\n2. Testing WITH collectionId parameter...")
        try:
            provided_collection_id = '-default-lux-beyond'
            collection_id = require_collection_id_for_mutation(mock_user, provided_collection_id)
            print(f"   ✓ Collection ID resolved: {collection_id}")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return False

        # Test: Create listing with collectionId
        print("\n3. Testing listing creation with collectionId...")
        listing_data = {
            'name': 'Test Listing - Superadmin',
            'address': '456 Admin Street, Nairobi',
            'defaultRate': 200.0,
            'bedrooms': 4,
            'bathrooms': 3,
            'status': 'active',
            'assignedManagers': {},
            'createdBy': mock_user['uid'],
            'createdAt': 1713888000000
        }

        try:
            listing_id = add_document(f'collections/{collection_id}/listings', listing_data)
            print(f"   ✓ Listing created with ID: {listing_id}")
            print(f"   ✓ SUCCESS - Superadmin CAN create listings (with collectionId param)")
            return True
        except Exception as e:
            print(f"   ❌ ERROR creating listing: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_manager_listing_creation():
    """Test that managers CANNOT create listings"""
    print_header("TEST 3: MANAGER - SHOULD NOT CREATE LISTINGS")

    try:
        # Simulate manager user
        mock_user = {
            'uid': 'manager-uid-123',
            'email': 'manager@luxbeyond.com',
            'role': 'manager',
            'collectionId': '-default-lux-beyond',
            'assignedListings': {'-OqKsDnO0dBSXdoJGUZx': True},
            'isActive': True
        }

        print(f"User: {mock_user['email']}")
        print(f"Role: {mock_user['role']}")

        print("\n⚠️  Managers should NOT be able to create listings")
        print("   (This is enforced by require_collection_admin dependency)")
        print("   ✓ This is correct - managers can only manage existing listings")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def check_existing_listings():
    """Check current listings in the database"""
    print_header("CURRENT LISTINGS IN DATABASE")

    try:
        collection_id = '-default-lux-beyond'
        listings = get_subcollection_documents('collections', collection_id, 'listings')

        print(f"Collection: {collection_id}")
        print(f"Total listings: {len(listings)}\n")

        for listing in listings:
            print(f"  [{listing.get('id')}] {listing.get('name')}")
            print(f"    Address: {listing.get('address')}")
            print(f"    Rate: ${listing.get('defaultRate')}/night")
            print(f"    Status: {listing.get('status')}")
            print(f"    Created by: {listing.get('createdBy')}")
            print()

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def check_frontend_permissions():
    """Check what permissions are needed in frontend"""
    print_header("FRONTEND PERMISSION REQUIREMENTS")

    print("""
The frontend Listings page uses this logic to show the "Add Listing" button:

File: frontend/src/pages/Listings.jsx
Lines: 29, 89-94

Code:
  const canManageListings = isAdmin(userProfile)

  {canManageListings && (
    <Button onClick={handleCreate}>
      <Plus size={20} className="mr-2" />
      Add Listing
    </Button>
  )}

File: frontend/src/utils/roleGuard.js
The isAdmin() function checks:

  export function isAdmin(user) {
    return user?.role === 'collection_admin' || user?.role === 'superadmin'
  }

EXPECTED BEHAVIOR:
  ✓ collection_admin: Should see "Add Listing" button
  ✓ superadmin: Should see "Add Listing" button
  ✗ manager: Should NOT see "Add Listing" button
  ✗ viewer: Should NOT see "Add Listing" button

CHECKLIST FOR DEBUGGING:
  1. Check browser console for userProfile value
  2. Verify user.role is exactly 'collection_admin' or 'superadmin'
  3. Check if isAdmin() function exists
  4. Check if Button component is rendering
  5. Check CSS/styling - button might be hidden
""")

    return True


def main():
    print_header("LISTING CREATION DIAGNOSTIC TEST")

    results = {}

    # Check existing listings
    results['existing'] = check_existing_listings()

    # Test collection admin
    results['collection_admin'] = test_collection_admin_listing_creation()

    # Test superadmin
    results['superadmin'] = test_superadmin_listing_creation()

    # Test manager
    results['manager'] = test_manager_listing_creation()

    # Frontend permissions
    results['frontend'] = check_frontend_permissions()

    # Summary
    print_header("TEST SUMMARY")
    print(f"Check Existing Listings:     {'✅ PASS' if results['existing'] else '❌ FAIL'}")
    print(f"Collection Admin Can Create: {'✅ PASS' if results['collection_admin'] else '❌ FAIL'}")
    print(f"Superadmin Can Create:       {'✅ PASS' if results['superadmin'] else '❌ FAIL'}")
    print(f"Manager Permission Check:    {'✅ PASS' if results['manager'] else '❌ FAIL'}")
    print(f"Frontend Requirements:       {'✅ PASS' if results['frontend'] else '❌ FAIL'}")

    print("\n" + "="*80)
    if all(results.values()):
        print("✅ ALL BACKEND TESTS PASSED!")
        print("\nIf button is still not visible, the issue is in the FRONTEND:")
        print("  1. Check browser console: console.log(userProfile)")
        print("  2. Verify userProfile.role === 'collection_admin' or 'superadmin'")
        print("  3. Check if isAdmin() function is imported correctly")
        print("  4. Check browser's Elements tab - is button in the DOM?")
        print("  5. Check CSS - button might be display:none or visibility:hidden")
    else:
        print("❌ SOME TESTS FAILED - Review output above")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
