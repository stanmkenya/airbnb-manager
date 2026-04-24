#!/usr/bin/env python3
"""
Script to create an admin user and generate a custom token for authentication.
"""
import sys
from app.firebase_client import firebase_client
from firebase_admin import auth
from datetime import datetime


def create_admin_user(email: str, password: str, display_name: str = "Admin User"):
    """
    Create an admin user in Firebase Auth and set their role in the database.
    Returns the user UID and a custom token for authentication.
    """
    try:
        # Check if user already exists
        try:
            user = auth.get_user_by_email(email)
            print(f"User with email {email} already exists.")
            print(f"UID: {user.uid}")
            uid = user.uid

            # Update user to mark email as verified
            auth.update_user(uid, email_verified=True)
            print("Marked email as verified")
        except auth.UserNotFoundError:
            # Create new user with email already verified
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=True  # Admin users have verified email by default
            )
            uid = user.uid
            print(f"Created new user: {email}")
            print(f"UID: {uid}")
            print("Email marked as verified")

        # Set user role to admin in database
        user_ref = firebase_client.get_database_ref(f'/users/{uid}')
        user_data = {
            'email': email,
            'displayName': display_name,
            'role': 'admin',
            'isActive': True,
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
        user_ref.set(user_data)
        print(f"Set user role to 'admin' in database")

        # Generate custom token
        custom_token = auth.create_custom_token(uid)
        custom_token_str = custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token

        print("\n" + "="*60)
        print("ADMIN USER CREATED SUCCESSFULLY")
        print("="*60)
        print(f"\nEmail: {email}")
        print(f"UID: {uid}")
        print(f"\nCustom Token (use this to get an ID token):")
        print(f"{custom_token_str}")
        print("\n" + "="*60)
        print("\nTo get an ID token (bearer token) for API requests:")
        print("1. Use this custom token to sign in via Firebase Auth")
        print("2. Or use the Firebase REST API:")
        print(f"\n   curl -X POST 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=YOUR_FIREBASE_API_KEY' \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"token\": \"{custom_token_str}\", \"returnSecureToken\": true}}'")
        print("\n3. The response will contain 'idToken' - use that as your bearer token")
        print("\nAlternatively, sign in with email/password through your frontend to get the token.")
        print("="*60)

        return uid, custom_token_str

    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Default admin credentials (change these!)
    EMAIL = "stanslausmwongela@gmail.com"
    PASSWORD = "Peppermint$#23"  # Change this to a secure password
    DISPLAY_NAME = "Admin User Stan"

    if len(sys.argv) > 1:
        EMAIL = sys.argv[1]
    if len(sys.argv) > 2:
        PASSWORD = sys.argv[2]
    if len(sys.argv) > 3:
        DISPLAY_NAME = sys.argv[3]

    print(f"Creating admin user: {EMAIL}")
    create_admin_user(EMAIL, PASSWORD, DISPLAY_NAME)
