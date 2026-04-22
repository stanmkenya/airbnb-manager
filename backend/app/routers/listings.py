from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.core.auth import get_current_user
from app.core.collection_helpers import get_collection_ids, require_collection_id_for_mutation
from app.core.firestore_helpers import (
    get_subcollection_documents, get_document, add_document,
    update_document
)
import time

router = APIRouter()


class ListingCreate(BaseModel):
    name: str
    address: str
    airbnbUrl: Optional[str] = None
    defaultRate: float
    bedrooms: int
    bathrooms: int


class ListingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    airbnbUrl: Optional[str] = None
    defaultRate: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    status: Optional[str] = None


def require_collection_admin(current_user: dict = Depends(get_current_user)):
    """Require user to be a collection admin or super admin"""
    if current_user.get('role') not in ['collection_admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Collection admin access required")
    return current_user


@router.get("")
async def get_listings(
    collectionId: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all listings accessible by current user.

    Superadmin:
        - Without collectionId param: Returns all listings from all collections
        - With collectionId param: Returns listings from specified collection

    Collection admin/Regular users:
        - Returns listings from their assigned collection
    """
    # Get collection IDs to query
    collection_ids = get_collection_ids(current_user, collectionId)

    all_listings = []

    # Fetch listings from all relevant collections
    for cid in collection_ids:
        collection_listings = get_subcollection_documents('collections', cid, 'listings')
        for listing in collection_listings:
            listing['collectionId'] = cid  # Add collection context
            all_listings.append(listing)

    # Filter based on role
    if current_user['role'] in ['collection_admin', 'superadmin']:
        # Admins see all listings in their accessible collections
        return all_listings
    else:
        # Regular users see only their assigned listings
        assigned_listings = current_user.get('assignedListings', {})
        return [
            listing for listing in all_listings
            if listing['id'] in assigned_listings
        ]


@router.post("")
async def create_listing(
    listing: ListingCreate,
    collectionId: Optional[str] = Query(None),
    current_user: dict = Depends(require_collection_admin)
):
    """
    Create a new listing (Collection Admin only)

    Superadmin: Must specify collectionId parameter
    Collection admin: Uses their assigned collection
    """
    # Get collection ID for mutation (superadmin must specify, regular users use their own)
    collection_id = require_collection_id_for_mutation(current_user, collectionId)

    listing_data = {
        **listing.dict(),
        'status': 'active',
        'assignedManagers': {},
        'createdBy': current_user['uid'],
        'createdAt': int(time.time() * 1000)
    }

    listing_id = add_document(f'collections/{collection_id}/listings', listing_data)

    return {
        "id": listing_id,
        "collectionId": collection_id,  # Add collection context
        **listing_data
    }


@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    collectionId: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific listing.

    Superadmin: Can access any listing, must specify collectionId if querying specific collection
    Collection admin/Regular users: Access listings in their collection
    """
    # Get collection IDs to search
    collection_ids = get_collection_ids(current_user, collectionId)

    # Search for the listing across accessible collections
    listing = None
    found_collection_id = None

    for cid in collection_ids:
        listing_data = get_document(f'collections/{cid}/listings', listing_id)

        if listing_data:
            listing = listing_data
            found_collection_id = cid
            break

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check access for non-admin users
    if current_user['role'] not in ['collection_admin', 'superadmin']:
        assigned_listings = current_user.get('assignedListings', {})
        if listing_id not in assigned_listings:
            raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": listing_id,
        "collectionId": found_collection_id,
        **listing
    }


@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    listing_update: ListingUpdate,
    collectionId: Optional[str] = Query(None),
    current_user: dict = Depends(require_collection_admin)
):
    """
    Update a listing (Collection Admin only)

    Superadmin: Must specify collectionId parameter
    Collection admin: Uses their assigned collection
    """
    # Get collection ID for mutation (superadmin must specify, regular users use their own)
    collection_id = require_collection_id_for_mutation(current_user, collectionId)

    existing = get_document(f'collections/{collection_id}/listings', listing_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")

    update_data = {
        k: v for k, v in listing_update.dict(exclude_unset=True).items()
        if v is not None
    }
    update_data['updatedAt'] = int(time.time() * 1000)

    update_document(f'collections/{collection_id}/listings', listing_id, update_data)

    return {
        "message": "Listing updated successfully",
        "id": listing_id,
        "collectionId": collection_id
    }


@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    collectionId: Optional[str] = Query(None),
    current_user: dict = Depends(require_collection_admin)
):
    """
    Soft delete a listing (Collection Admin only)

    Superadmin: Must specify collectionId parameter
    Collection admin: Uses their assigned collection
    """
    # Get collection ID for mutation (superadmin must specify, regular users use their own)
    collection_id = require_collection_id_for_mutation(current_user, collectionId)

    existing = get_document(f'collections/{collection_id}/listings', listing_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")

    update_document(f'collections/{collection_id}/listings', listing_id, {
        'status': 'inactive',
        'deletedAt': int(time.time() * 1000),
        'deletedBy': current_user['uid']
    })

    return {
        "message": "Listing deleted successfully",
        "collectionId": collection_id
    }
