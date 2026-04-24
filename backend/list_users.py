#!/usr/bin/env python3
"""
List all users in the system
"""

from app.firebase_client import firebase_client

def list_users():
    """List all users"""
    print(f"\n{'='*80}")
    print(f"ALL USERS IN THE SYSTEM")
    print(f"{'='*80}\n")

    users_ref = firebase_client.get_database_ref('/users')
    all_users = users_ref.get() or {}

    if not all_users:
        print("No users found.")
        return

    print(f"Total users: {len(all_users)}\n")

    for uid, data in all_users.items():
        email = data.get('email', 'N/A')
        role = data.get('role', 'N/A')
        collection_id = data.get('collectionId', 'None')

        print(f"📧 {email}")
        print(f"   UID: {uid}")
        print(f"   Role: {role}")
        print(f"   Collection: {collection_id}")
        print()

    print(f"{'='*80}\n")


if __name__ == '__main__':
    list_users()
