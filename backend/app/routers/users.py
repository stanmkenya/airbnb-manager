from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from app.core.auth import get_current_user, require_admin
from app.firebase_client import firebase_client
import time

router = APIRouter()


class UserInvite(BaseModel):
    email: EmailStr
    displayName: str
    role: str  # 'admin', 'manager', 'viewer'
    assignedListings: Optional[Dict[str, bool]] = {}


class RoleUpdate(BaseModel):
    role: str


class ListingsUpdate(BaseModel):
    assignedListings: Dict[str, bool]


@router.get("")
async def get_users(current_user: dict = Depends(require_admin)):
    """
    Get all users (Admin only)
    """
    users_ref = firebase_client.get_database_ref('/users')
    all_users = users_ref.get() or {}

    users_list = []
    for uid, user_data in all_users.items():
        users_list.append({
            'uid': uid,
            **user_data
        })

    return users_list


@router.post("/invite")
async def invite_user(
    invite: UserInvite,
    current_user: dict = Depends(require_admin)
):
    """
    Invite a new user (Admin only)
    Creates user in Firebase Auth and sets up profile in database
    """
    try:
        # Generate a temporary password (user will reset via email)
        import secrets
        temp_password = secrets.token_urlsafe(16)

        # Create user in Firebase Auth
        firebase_user = firebase_client.create_user(
            email=invite.email,
            password=temp_password,
            display_name=invite.displayName
        )

        # Create user profile in database
        user_ref = firebase_client.get_database_ref(f'/users/{firebase_user.uid}')
        user_profile = {
            'email': invite.email,
            'displayName': invite.displayName,
            'photoURL': None,
            'role': invite.role,
            'assignedListings': invite.assignedListings or {},
            'createdAt': int(time.time() * 1000),
            'createdBy': current_user['uid'],
            'isActive': True
        }
        user_ref.set(user_profile)

        # In production, send password reset email here
        # firebase_admin.auth.generate_password_reset_link(invite.email)

        return {
            "message": "User invited successfully",
            "uid": firebase_user.uid,
            "email": invite.email,
            "tempPassword": temp_password  # In production, don't return this - send reset email instead
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")


@router.put("/{uid}/role")
async def update_user_role(
    uid: str,
    role_update: RoleUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update user role (Admin only)
    """
    if role_update.role not in ['admin', 'manager', 'viewer']:
        raise HTTPException(status_code=400, detail="Invalid role")

    user_ref = firebase_client.get_database_ref(f'/users/{uid}')
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user_ref.update({
        'role': role_update.role,
        'updatedAt': int(time.time() * 1000),
        'updatedBy': current_user['uid']
    })

    return {
        "message": "User role updated successfully",
        "uid": uid,
        "newRole": role_update.role
    }


@router.put("/{uid}/listings")
async def update_user_listings(
    uid: str,
    listings_update: ListingsUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update user's assigned listings (Admin only)
    """
    user_ref = firebase_client.get_database_ref(f'/users/{uid}')
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user_ref.update({
        'assignedListings': listings_update.assignedListings,
        'updatedAt': int(time.time() * 1000),
        'updatedBy': current_user['uid']
    })

    return {
        "message": "User listings updated successfully",
        "uid": uid,
        "assignedListings": listings_update.assignedListings
    }


@router.put("/{uid}/deactivate")
async def deactivate_user(
    uid: str,
    current_user: dict = Depends(require_admin)
):
    """
    Deactivate user (Admin only)
    Does not delete historical data
    """
    if uid == current_user['uid']:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user_ref = firebase_client.get_database_ref(f'/users/{uid}')
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Update in database
    user_ref.update({
        'isActive': False,
        'deactivatedAt': int(time.time() * 1000),
        'deactivatedBy': current_user['uid']
    })

    # Disable in Firebase Auth
    try:
        firebase_client.update_user(uid, disabled=True)
    except Exception as e:
        print(f"Warning: Failed to disable user in Firebase Auth: {e}")

    return {
        "message": "User deactivated successfully",
        "uid": uid
    }


@router.put("/{uid}/activate")
async def activate_user(
    uid: str,
    current_user: dict = Depends(require_admin)
):
    """
    Reactivate user (Admin only)
    """
    user_ref = firebase_client.get_database_ref(f'/users/{uid}')
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Update in database
    user_ref.update({
        'isActive': True,
        'reactivatedAt': int(time.time() * 1000),
        'reactivatedBy': current_user['uid']
    })

    # Enable in Firebase Auth
    try:
        firebase_client.update_user(uid, disabled=False)
    except Exception as e:
        print(f"Warning: Failed to enable user in Firebase Auth: {e}")

    return {
        "message": "User activated successfully",
        "uid": uid
    }


@router.delete("/{uid}")
async def delete_user(
    uid: str,
    current_user: dict = Depends(require_admin)
):
    """
    Permanently delete user (Admin only)
    WARNING: This will delete the user but preserve their historical data entries
    """
    if uid == current_user['uid']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user_ref = firebase_client.get_database_ref(f'/users/{uid}')
    user_data = user_ref.get()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete from database
    user_ref.delete()

    # Delete from Firebase Auth
    try:
        firebase_client.delete_user(uid)
    except Exception as e:
        print(f"Warning: Failed to delete user from Firebase Auth: {e}")

    return {
        "message": "User deleted successfully",
        "uid": uid
    }
