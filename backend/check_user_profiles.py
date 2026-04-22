"""
Diagnostic script to check user profiles in Firestore after migration.

This script verifies that all users have the required fields for their roles:
- Superadmin: role='superadmin', isActive
- Collection Admin: role='collection_admin', collectionId, isActive
- Manager: role='manager', collectionId, assignedListings, isActive
- Viewer: role='viewer', collectionId, assignedListings, isActive
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.firestore_helpers import get_documents
from app.firebase_client import firebase_client


def check_user_profiles():
    """Check all user profiles for required fields"""
    print(f"\n{'='*80}")
    print(f"Checking User Profiles in Firestore")
    print(f"{'='*80}\n")

    try:
        # Get all users from Firestore
        users = get_documents('users')

        if not users:
            print(f"❌ No users found in Firestore!")
            return

        print(f"✓ Found {len(users)} users\n")

        # Track issues
        issues = []
        warnings = []

        # Check each user
        for user in users:
            uid = user.get('id')
            email = user.get('email', 'N/A')
            role = user.get('role', 'N/A')
            collection_id = user.get('collectionId')
            is_active = user.get('isActive', True)
            assigned_listings = user.get('assignedListings', {})

            # Print user info
            print(f"\nUser: {email}")
            print(f"  UID: {uid}")
            print(f"  Role: {role}")
            print(f"  Active: {is_active}")
            print(f"  Collection ID: {collection_id or 'N/A'}")
            print(f"  Assigned Listings: {len(assigned_listings) if isinstance(assigned_listings, dict) else 0}")

            # Validate based on role
            if role == 'superadmin':
                # Superadmin doesn't need collectionId
                if not is_active:
                    warnings.append(f"⚠️  Superadmin {email} is inactive")
                print(f"  ✓ Superadmin profile is valid")

            elif role == 'collection_admin':
                # Collection admin MUST have collectionId
                if not collection_id:
                    issues.append(f"❌ Collection admin {email} missing collectionId field")
                    print(f"  ❌ MISSING collectionId - WILL FAIL TO CREATE LISTINGS")
                else:
                    print(f"  ✓ Has collectionId: {collection_id}")

                if not is_active:
                    warnings.append(f"⚠️  Collection admin {email} is inactive")

            elif role == 'manager':
                # Manager MUST have collectionId
                if not collection_id:
                    issues.append(f"❌ Manager {email} missing collectionId field")
                    print(f"  ❌ MISSING collectionId")
                else:
                    print(f"  ✓ Has collectionId: {collection_id}")

                # Manager should have assignedListings (but not required)
                if not assigned_listings or len(assigned_listings) == 0:
                    warnings.append(f"⚠️  Manager {email} has no assigned listings")
                    print(f"  ⚠️  No assigned listings")

                if not is_active:
                    warnings.append(f"⚠️  Manager {email} is inactive")

            elif role == 'viewer':
                # Viewer MUST have collectionId
                if not collection_id:
                    issues.append(f"❌ Viewer {email} missing collectionId field")
                    print(f"  ❌ MISSING collectionId")
                else:
                    print(f"  ✓ Has collectionId: {collection_id}")

            else:
                issues.append(f"❌ User {email} has invalid role: {role}")
                print(f"  ❌ INVALID ROLE: {role}")

        # Summary
        print(f"\n{'='*80}")
        print(f"Summary")
        print(f"{'='*80}\n")

        if issues:
            print(f"❌ CRITICAL ISSUES FOUND ({len(issues)}):")
            for issue in issues:
                print(f"  {issue}")
            print()

        if warnings:
            print(f"⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"  {warning}")
            print()

        if not issues and not warnings:
            print(f"✓ All user profiles are valid!")

        # Print simple table
        print(f"\nUser Profiles Overview:")
        print(f"{'Email':<30} {'Role':<20} {'Collection ID':<20} {'Active':<10} {'Status':<10}")
        print(f"{'-'*30} {'-'*20} {'-'*20} {'-'*10} {'-'*10}")
        for user in users:
            email = user.get('email', 'N/A')[:30]
            role = user.get('role', 'N/A')[:20]
            collection_id = (user.get('collectionId', 'N/A') or 'N/A')[:20]
            is_active = '✓' if user.get('isActive', True) else '✗'

            # Check for issues
            status = '✓'
            if role in ['collection_admin', 'manager', 'viewer'] and not user.get('collectionId'):
                status = '❌'

            print(f"{email:<30} {role:<20} {collection_id:<20} {is_active:<10} {status:<10}")

        # Return status
        return len(issues) == 0

    except Exception as e:
        print(f"❌ Error checking user profiles: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_collections():
    """Check collections in Firestore"""
    print(f"\n{'='*80}")
    print(f"Checking Collections in Firestore")
    print(f"{'='*80}\n")

    try:
        collections = get_documents('collections')

        if not collections:
            print(f"❌ No collections found in Firestore!")
            return False

        print(f"✓ Found {len(collections)} collection(s)\n")

        for collection in collections:
            collection_id = collection.get('id')
            name = collection.get('name', 'N/A')
            created_by = collection.get('createdBy', 'N/A')

            print(f"Collection: {name}")
            print(f"  ID: {collection_id}")
            print(f"  Created By: {created_by}\n")

        return True

    except Exception as e:
        print(f"❌ Error checking collections: {str(e)}")
        return False


if __name__ == '__main__':
    print(f"\n{'='*80}")
    print(f"Firestore Migration Diagnostic Tool")
    print(f"{'='*80}\n")

    # Check collections first
    collections_ok = check_collections()

    # Check user profiles
    users_ok = check_user_profiles()

    # Final status
    print(f"\n{'='*80}")
    print(f"Final Status")
    print(f"{'='*80}\n")

    if collections_ok and users_ok:
        print(f"✓ All checks passed!")
        sys.exit(0)
    else:
        print(f"❌ Some checks failed. Please review the issues above.")
        sys.exit(1)
