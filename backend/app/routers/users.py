from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from app.core.auth import get_current_user
from app.firebase_client import firebase_client
from app.core.firestore_helpers import (
    get_documents, get_document, set_document,
    update_document, delete_document
)
import time

router = APIRouter()


class UserInvite(BaseModel):
    email: EmailStr
    displayName: str
    role: str  # 'collection_admin', 'manager', 'viewer'
    collectionId: Optional[str] = None  # Collection to assign user to
    assignedListings: Optional[Dict[str, bool]] = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    role: str


class CollectionAssignment(BaseModel):
    collectionId: str


class ListingsUpdate(BaseModel):
    assignedListings: Dict[str, bool]


@router.get("")
async def get_users(current_user: dict = Depends(get_current_user)):
    """
    Get users based on role:
    - Superadmin: See all users across all collections
    - Collection Admin: See only users in their collection
    """
    # Check if user has admin privileges
    user_role = current_user.get('role')
    if user_role not in ['superadmin', 'collection_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    # Superadmin sees all users
    if user_role == 'superadmin':
        users_list = get_documents('users')
        # Firestore returns docs with 'id' field, rename to 'uid' for compatibility
        for user in users_list:
            user['uid'] = user.pop('id')
        return users_list

    # Collection admin sees only users in their collection
    else:
        current_user_collection = current_user.get('collectionId')
        if not current_user_collection:
            raise HTTPException(
                status_code=400,
                detail="User not assigned to a collection"
            )

        # Filter users by collection
        filters = [('collectionId', '==', current_user_collection)]
        users_list = get_documents('users', filters=filters)

        # Rename 'id' to 'uid' for compatibility
        for user in users_list:
            user['uid'] = user.pop('id')

        return users_list


@router.post("/invite")
async def invite_user(
    invite: UserInvite,
    current_user: dict = Depends(get_current_user)
):
    """
    Invite a new user (Admin only)
    Creates user in Firebase Auth and sets up profile in database

    Superadmin: Can invite users to any collection (must specify collectionId)
    Collection admin: Can only invite users to their own collection
    """
    # Check admin privileges
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Determine which collection to assign user to
    if current_user.get('role') == 'superadmin':
        # Superadmin must specify which collection
        if not invite.collectionId:
            raise HTTPException(
                status_code=400,
                detail="Superadmin must specify collectionId when inviting users"
            )
        assigned_collection = invite.collectionId
    else:
        # Collection admin can only invite to their own collection
        assigned_collection = current_user.get('collectionId')
        if not assigned_collection:
            raise HTTPException(
                status_code=400,
                detail="User not assigned to a collection"
            )
        # Ignore invite.collectionId for security - use their own collection
        if invite.collectionId and invite.collectionId != assigned_collection:
            raise HTTPException(
                status_code=403,
                detail="Collection admins can only invite users to their own collection"
            )

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

        # Create user profile in Firestore
        user_profile = {
            'email': invite.email,
            'displayName': invite.displayName,
            'photoURL': None,
            'role': invite.role,
            'collectionId': assigned_collection,  # Assign to collection
            'assignedListings': invite.assignedListings or {},
            'createdAt': int(time.time() * 1000),
            'createdBy': current_user['uid'],
            'isActive': True
        }
        set_document('users', firebase_user.uid, user_profile)

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


@router.put("/{uid}/collection")
async def assign_user_to_collection(
    uid: str,
    assignment: CollectionAssignment,
    current_user: dict = Depends(get_current_user)
):
    """
    Assign or reassign a user to a collection.

    Superadmin: Can assign any user to any collection
    Collection admin: Cannot use this endpoint (403 error)
    """
    # Only superadmin can reassign users to different collections
    if current_user.get('role') != 'superadmin':
        raise HTTPException(
            status_code=403,
            detail="Only superadmin can assign users to collections"
        )

    # Get user
    user_data = get_document('users', uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify collection exists
    collection_data = get_document('collections', assignment.collectionId)

    if not collection_data:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Assign user to collection
    update_document('users', uid, {
        'collectionId': assignment.collectionId,
        'updatedAt': int(time.time() * 1000),
        'updatedBy': current_user['uid']
    })

    return {
        "message": "User assigned to collection successfully",
        "uid": uid,
        "collectionId": assignment.collectionId,
        "collectionName": collection_data.get('name')
    }


@router.put("/{uid}/role")
async def update_user_role(
    uid: str,
    role_update: RoleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user role.

    Superadmin: Can update any user's role (including creating other superadmins)
    Collection admin: Can only update roles of users in their collection (cannot create superadmins)
    """
    # Check admin privileges
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get user to update
    user_data = get_document('users', uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate role
    if current_user.get('role') == 'superadmin':
        # Superadmin can assign any role
        valid_roles = ['superadmin', 'collection_admin', 'manager', 'viewer']
    else:
        # Collection admin cannot create superadmins
        valid_roles = ['collection_admin', 'manager', 'viewer']

        # Collection admin can only update users in their collection
        current_user_collection = current_user.get('collectionId')
        target_user_collection = user_data.get('collectionId')

        if current_user_collection != target_user_collection:
            raise HTTPException(
                status_code=403,
                detail="Collection admins can only manage users in their own collection"
            )

    if role_update.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid roles: {', '.join(valid_roles)}")

    # Update role
    from google.cloud.firestore import DELETE_FIELD

    update_data = {
        'role': role_update.role,
        'updatedAt': int(time.time() * 1000),
        'updatedBy': current_user['uid']
    }

    # If changing to superadmin, remove collectionId
    if role_update.role == 'superadmin' and user_data.get('collectionId'):
        update_data['collectionId'] = DELETE_FIELD
        update_data['collectionIdRemovedAt'] = int(time.time() * 1000)

    update_document('users', uid, update_data)

    return {
        "message": "User role updated successfully",
        "uid": uid,
        "newRole": role_update.role
    }


@router.put("/{uid}/listings")
async def update_user_listings(
    uid: str,
    listings_update: ListingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user's assigned listings (Admin only)
    """
    # Check admin privileges
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    user_data = get_document('users', uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    update_document('users', uid, {
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
    current_user: dict = Depends(get_current_user)
):
    """
    Deactivate user.

    Superadmin: Can deactivate any user
    Collection admin: Can only deactivate users in their collection
    """
    # Check admin privileges
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    if uid == current_user['uid']:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user_data = get_document('users', uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Collection admin can only deactivate users in their collection
    if current_user.get('role') == 'collection_admin':
        current_user_collection = current_user.get('collectionId')
        target_user_collection = user_data.get('collectionId')

        if current_user_collection != target_user_collection:
            raise HTTPException(
                status_code=403,
                detail="Collection admins can only manage users in their own collection"
            )

    # Update in database
    update_document('users', uid, {
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
    current_user: dict = Depends(get_current_user)
):
    """
    Reactivate user.

    Superadmin: Can activate any user
    Collection admin: Can only activate users in their collection
    """
    # Check admin privileges
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    user_data = get_document('users', uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Collection admin can only activate users in their collection
    if current_user.get('role') == 'collection_admin':
        current_user_collection = current_user.get('collectionId')
        target_user_collection = user_data.get('collectionId')

        if current_user_collection != target_user_collection:
            raise HTTPException(
                status_code=403,
                detail="Collection admins can only manage users in their own collection"
            )

    # Update in database
    update_document('users', uid, {
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
    current_user: dict = Depends(get_current_user)
):
    """
    Permanently delete user.

    Superadmin: Can delete any user
    Collection admin: Can only delete users in their collection
    WARNING: This will delete the user but preserve their historical data entries
    """
    # Check admin privileges
    if current_user.get('role') not in ['superadmin', 'collection_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    if uid == current_user['uid']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user_data = get_document('users', uid)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Collection admin can only delete users in their collection
    if current_user.get('role') == 'collection_admin':
        current_user_collection = current_user.get('collectionId')
        target_user_collection = user_data.get('collectionId')

        if current_user_collection != target_user_collection:
            raise HTTPException(
                status_code=403,
                detail="Collection admins can only manage users in their own collection"
            )

    # Delete from database
    delete_document('users', uid)

    # Delete from Firebase Auth
    try:
        firebase_client.delete_user(uid)
    except Exception as e:
        print(f"Warning: Failed to delete user from Firebase Auth: {e}")

    return {
        "message": "User deleted successfully",
        "uid": uid
    }
