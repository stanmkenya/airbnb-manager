#!/usr/bin/env python3
"""
Script to check and fix user roles in Firestore.
This helps diagnose why admins/superadmins cannot see add/update buttons.
"""

import os
import sys
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, firestore

# Load environment variables
load_dotenv()

# Initialize Firebase
cred_dict = eval(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'))
cred = credentials.Certificate(cred_dict)
initialize_app(cred)

db = firestore.client()

def list_all_users():
    """List all users and their roles"""
    print("\n" + "="*80)
    print("CURRENT USERS IN FIRESTORE")
    print("="*80)

    users_ref = db.collection('users')
    users = users_ref.stream()

    user_list = []
    for user_doc in users:
        user_data = user_doc.to_dict()
        user_list.append({
            'uid': user_doc.id,
            'email': user_data.get('email', 'N/A'),
            'role': user_data.get('role', 'N/A'),
            'displayName': user_data.get('displayName', 'N/A'),
            'collectionId': user_data.get('collectionId', 'N/A'),
            'isActive': user_data.get('isActive', True)
        })

    if not user_list:
        print("❌ No users found in Firestore!")
        return []

    print(f"\nFound {len(user_list)} user(s):\n")

    for idx, user in enumerate(user_list, 1):
        print(f"{idx}. {user['email']}")
        print(f"   UID: {user['uid']}")
        print(f"   Role: {user['role']}")
        print(f"   Display Name: {user['displayName']}")
        print(f"   Collection ID: {user['collectionId']}")
        print(f"   Active: {user['isActive']}")

        # Check if role allows admin functions
        if user['role'] in ['superadmin', 'collection_admin']:
            print(f"   ✅ This user CAN see add/update buttons")
        else:
            print(f"   ❌ This user CANNOT see add/update buttons (role: {user['role']})")
        print()

    return user_list

def update_user_role(uid, new_role, collection_id=None):
    """Update a user's role"""
    valid_roles = ['superadmin', 'collection_admin', 'manager', 'viewer']

    if new_role not in valid_roles:
        print(f"❌ Invalid role: {new_role}")
        print(f"   Valid roles: {', '.join(valid_roles)}")
        return False

    try:
        user_ref = db.collection('users').document(uid)
        update_data = {
            'role': new_role,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }

        # If not superadmin, require collectionId
        if new_role != 'superadmin':
            if not collection_id:
                print(f"❌ Collection ID required for role: {new_role}")
                return False
            update_data['collectionId'] = collection_id

        user_ref.update(update_data)
        print(f"✅ Successfully updated user role to: {new_role}")
        return True
    except Exception as e:
        print(f"❌ Error updating user role: {e}")
        return False

def check_collections():
    """Check available collections"""
    print("\n" + "="*80)
    print("AVAILABLE COLLECTIONS")
    print("="*80)

    collections_ref = db.collection('collections')
    collections = collections_ref.stream()

    collection_list = []
    for col_doc in collections:
        col_data = col_doc.to_dict()
        collection_list.append({
            'id': col_doc.id,
            'name': col_data.get('name', 'N/A'),
            'description': col_data.get('description', ''),
            'isActive': col_data.get('isActive', True)
        })

    if not collection_list:
        print("❌ No collections found! Super admin needs to create a collection first.")
        return []

    print(f"\nFound {len(collection_list)} collection(s):\n")

    for idx, col in enumerate(collection_list, 1):
        print(f"{idx}. {col['name']} (ID: {col['id']})")
        print(f"   Description: {col['description']}")
        print(f"   Active: {col['isActive']}")
        print()

    return collection_list

def interactive_fix():
    """Interactive mode to fix user roles"""
    print("\n" + "="*80)
    print("INTERACTIVE ROLE FIX")
    print("="*80)

    users = list_all_users()
    if not users:
        return

    collections = check_collections()

    print("\nSelect a user to update (enter number or 'q' to quit):")
    choice = input("> ").strip()

    if choice.lower() == 'q':
        return

    try:
        user_idx = int(choice) - 1
        if user_idx < 0 or user_idx >= len(users):
            print("❌ Invalid selection")
            return
    except ValueError:
        print("❌ Invalid input")
        return

    selected_user = users[user_idx]
    print(f"\nSelected: {selected_user['email']}")
    print(f"Current role: {selected_user['role']}")

    print("\nSelect new role:")
    print("1. superadmin (platform-wide access, can manage all collections)")
    print("2. collection_admin (full access within assigned collection)")
    print("3. manager (can add/edit expenses and bookings for assigned listings)")
    print("4. viewer (read-only access)")

    role_choice = input("> ").strip()

    role_map = {
        '1': 'superadmin',
        '2': 'collection_admin',
        '3': 'manager',
        '4': 'viewer'
    }

    new_role = role_map.get(role_choice)
    if not new_role:
        print("❌ Invalid role selection")
        return

    collection_id = None
    if new_role != 'superadmin':
        if not collections:
            print("❌ No collections available! Super admin needs to create one first.")
            return

        print("\nSelect collection to assign user to:")
        for idx, col in enumerate(collections, 1):
            print(f"{idx}. {col['name']} (ID: {col['id']})")

        col_choice = input("> ").strip()
        try:
            col_idx = int(col_choice) - 1
            if col_idx < 0 or col_idx >= len(collections):
                print("❌ Invalid collection selection")
                return
            collection_id = collections[col_idx]['id']
        except ValueError:
            print("❌ Invalid input")
            return

    print(f"\n⚠️  About to update:")
    print(f"   User: {selected_user['email']}")
    print(f"   New Role: {new_role}")
    if collection_id:
        print(f"   Collection: {collection_id}")

    confirm = input("\nProceed? (yes/no): ").strip().lower()
    if confirm == 'yes':
        update_user_role(selected_user['uid'], new_role, collection_id)
        print("\n✅ Done! User should now see the correct buttons in the UI.")
        print("   The user may need to log out and log back in for changes to take effect.")
    else:
        print("❌ Cancelled")

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                     USER ROLE DIAGNOSTIC & FIX TOOL                       ║
║                                                                           ║
║  This tool helps diagnose why admins/superadmins cannot see the          ║
║  Add/Update buttons in the frontend.                                     ║
║                                                                           ║
║  The frontend checks for these roles to show buttons:                    ║
║  • superadmin: Can see all admin buttons                                 ║
║  • collection_admin: Can see all admin buttons in their collection       ║
║  • manager: Can see add/edit buttons for expenses and bookings           ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_all_users()
        check_collections()
    else:
        interactive_fix()

if __name__ == '__main__':
    main()
