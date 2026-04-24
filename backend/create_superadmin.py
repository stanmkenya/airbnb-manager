#!/usr/bin/env python3
"""
Script to create a superadmin user in the system
"""

import sys
from datetime import datetime
from app.firebase_client import firebase_client

def create_superadmin(email: str):
    """
    Create or update a user to be a superadmin

    Args:
        email: Email of the user to make superadmin
    """
    print(f"\n{'='*60}")
    print(f"CREATING SUPERADMIN USER")
    print(f"{'='*60}\n")

    # Get all users from Firebase
    users_ref = firebase_client.get_database_ref('/users')
    all_users = users_ref.get() or {}

    # Find user by email
    user_id = None
    user_data = None

    for uid, data in all_users.items():
        if data.get('email') == email:
            user_id = uid
            user_data = data
            break

    if not user_id:
        print(f"❌ Error: No user found with email '{email}'")
        print("\nAvailable users:")
        for uid, data in all_users.items():
            print(f"  - {data.get('email')} (role: {data.get('role')})")
        return False

    print(f"✓ Found user: {email}")
    print(f"  Current role: {user_data.get('role')}")
    print(f"  Current collection: {user_data.get('collectionId')}")

    # Update user to superadmin
    update_data = {
        'role': 'superadmin',
        'updatedAt': datetime.utcnow().isoformat(),
        'madeSupadminAt': datetime.utcnow().isoformat()
    }

    # Remove collectionId for superadmin (they have access to all collections)
    user_ref = firebase_client.get_database_ref(f'/users/{user_id}')

    # First update with new data
    user_ref.update(update_data)

    # Then remove collectionId if it exists
    if user_data.get('collectionId'):
        user_ref.child('collectionId').delete()
        print(f"✓ Removed collectionId (superadmin has access to all collections)")

    print(f"\n{'='*60}")
    print(f"✅ SUCCESS: {email} is now a superadmin!")
    print(f"{'='*60}\n")

    print("Superadmin permissions:")
    print("  ✓ Create and manage collections")
    print("  ✓ Assign collection admins")
    print("  ✓ View all data across all collections")
    print("  ✓ Full system access")

    return True


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("\nUsage: python create_superadmin.py <email>")
        print("\nExample:")
        print("  python create_superadmin.py admin@luxbeyond.com")
        print("\nThis will make the specified user a superadmin.")
        sys.exit(1)

    email = sys.argv[1]

    # Confirm with user
    print(f"\n⚠️  WARNING: You are about to make '{email}' a superadmin.")
    print("Superadmins have full access to all collections and system functions.")

    confirm = input("\nType 'yes' to confirm: ")

    if confirm.lower() != 'yes':
        print("\n❌ Cancelled.")
        sys.exit(0)

    success = create_superadmin(email)

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
