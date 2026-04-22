"""
Collection helper utilities for multi-tenancy support.

Provides helper functions to resolve collection IDs based on user roles.
"""

from typing import List, Optional
from fastapi import HTTPException
from app.core.firestore_helpers import get_documents


def get_default_collection_for_superadmin() -> Optional[str]:
    """
    Get the first available collection for superadmin.
    This is used as a fallback when superadmin doesn't specify a collection.

    Returns:
        First collection ID if any exist, None otherwise
    """
    all_collections = get_documents('collections')
    collection_ids = [c.get('id') for c in all_collections]
    return collection_ids[0] if collection_ids else None


def get_user_collection_id(current_user: dict, requested_collection_id: Optional[str] = None) -> str:
    """
    Simple helper to get collection_id for any user, with superadmin support.

    For superadmin:
        - If requested_collection_id provided, use that
        - Otherwise, use first available collection

    For regular users:
        - Use their assigned collectionId
        - Raise error if none assigned

    Args:
        current_user: The authenticated user
        requested_collection_id: Optional collection ID from query parameter

    Returns:
        Collection ID to use

    Raises:
        HTTPException: If user has no collection and is not superadmin
    """
    if current_user.get('role') == 'superadmin':
        if requested_collection_id:
            return requested_collection_id
        # Default to first collection
        collection_id = get_default_collection_for_superadmin()
        if not collection_id:
            raise HTTPException(status_code=400, detail="No collections available in the system")
        return collection_id
    else:
        collection_id = current_user.get('collectionId')
        if not collection_id:
            raise HTTPException(status_code=400, detail="User not assigned to a collection")
        return collection_id


def get_collection_ids(
    current_user: dict,
    requested_collection_id: Optional[str] = None
) -> List[str]:
    """
    Resolve which collection IDs to query based on user role and request.

    For superadmins:
        - If requested_collection_id is provided, returns [requested_collection_id]
        - If no requested_collection_id, returns all collection IDs in the system

    For regular users (collection_admin, manager, viewer):
        - Returns [user's assigned collectionId]
        - Raises HTTPException if user has no collectionId assigned

    Args:
        current_user: The authenticated user dict from get_current_user()
        requested_collection_id: Optional collection ID from query parameter

    Returns:
        List of collection IDs to query

    Raises:
        HTTPException: If regular user has no collectionId assigned
    """
    # Superadmin logic - can access any/all collections
    if current_user.get('role') == 'superadmin':
        if requested_collection_id:
            # Superadmin specified a specific collection
            # TODO: Could add validation that collection exists
            return [requested_collection_id]
        else:
            # Superadmin wants data from all collections
            all_collections = get_documents('collections')
            return [c.get('id') for c in all_collections]

    # Regular user logic - restricted to their assigned collection
    else:
        collection_id = current_user.get('collectionId')
        if not collection_id:
            raise HTTPException(
                status_code=400,
                detail="User not assigned to a collection"
            )
        # Ignore requested_collection_id for regular users (security)
        return [collection_id]


def require_collection_id_for_mutation(
    current_user: dict,
    collection_id: Optional[str] = None
) -> str:
    """
    Get collection ID for mutation operations (POST/PUT/DELETE).

    For superadmins:
        - REQUIRES collection_id parameter to be specified
        - Cannot auto-detect which collection to mutate

    For regular users:
        - Uses their assigned collectionId
        - Ignores collection_id parameter (security)

    Args:
        current_user: The authenticated user dict from get_current_user()
        collection_id: Optional collection ID from query parameter

    Returns:
        Collection ID to use for the mutation

    Raises:
        HTTPException: If superadmin doesn't provide collection_id
        HTTPException: If regular user has no collectionId assigned
    """
    # Superadmin must specify which collection for mutations
    if current_user.get('role') == 'superadmin':
        if not collection_id:
            raise HTTPException(
                status_code=400,
                detail="Superadmin must specify collectionId parameter for create/update/delete operations"
            )
        return collection_id

    # Regular user uses their assigned collection
    else:
        user_collection_id = current_user.get('collectionId')
        if not user_collection_id:
            raise HTTPException(
                status_code=400,
                detail="User not assigned to a collection"
            )
        # Ignore provided collection_id for security
        return user_collection_id
